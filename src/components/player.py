import asyncio
import discord
import typing
import threading
import time
from discord.ext import commands

from .song_queue import SongQueue
from utils import CommandExecutionError, FailedToConnectError
from utils.colors import c_event, c_guild


class Player(commands.Cog):
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    def __init__(
            self,
            guild_bot,
            guild: discord.Guild
    ):
        self.guild: discord.Guild = guild
        self.guild_bot = guild_bot

        self.queue = SongQueue()

        self.looped_status: typing.Literal['none', 'queue', 'single'] = 'none'
        self.is_playing = False
        self.is_paused = False

        self.voice_client: discord.VoiceClient | None = None
        self.voice_channel: discord.VoiceChannel | None = None

        self.lock = asyncio.Lock()

        self.play_music_thread: threading.Thread | None = None
        self.previous_event = threading.Event()
        self.skip_event = threading.Event()


        self.playing_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.goto_event = threading.Event()

        self.update_message_loop = asyncio.new_event_loop()

    async def connect(self) -> None:
        async with self.lock:
            await self.join()

    async def reset_bot_states(self) -> None:
        async with self.lock:
            self.looped_status = 'none'
            self.is_playing = False
            self.is_paused = False

            self.queue = SongQueue()

            # todo: should we reset this?
            self.voice_client = None
            self.voice_channel = None

            await self.guild_bot.reset()

            await self.guild_bot.update_message()

    async def shuffle_queue(self) -> None:
        async with self.lock:
            if self.queue.is_shuffled:
                self.queue.unshuffle()
            else:
                self.queue.shuffle()

            await self.guild_bot.update_message()

    async def cycle_loop(self) -> None:
        async with self.lock:
            if self.queue.loop_status == 'none':
                self.queue.loop_status = 'queue'
            elif self.queue.loop_status == 'queue':
                self.queue.loop_status = 'single'
            elif self.queue.loop_status == 'single':
                self.queue.loop_status = 'none'

            await self.guild_bot.update_message()

    async def go_to_previous(self) -> None:
        async with self.lock:
            self.queue.previous()

            await self.guild_bot.update_message()

    async def pause(self) -> None:
        async with self.lock:
            if self.is_paused:
                self.is_paused = False
                self.voice_client.resume()
            else:
                self.is_paused = True
                self.voice_client.pause()

            await self.guild_bot.update_message()

    async def skip(self) -> None:
        async with self.lock:
            if self.voice_client is not None:
                self.voice_client.pause()
            if self.looped_status == 'single':
                self.looped_status = 'queue'

            self.skip_event.set()
            self.stop_play_audio_thread()

            await self.guild_bot.update_message()

    async def previous(self) -> None:
        async with self.lock:
            if self.voice_client is not None:
                self.voice_client.pause()
            if self.looped_status == 'single':
                self.looped_status = 'queue'
            self.queue.previous()

            self.previous_event.set()
            self.stop_play_audio_thread()

            await self.guild_bot.update_message()

    async def clear(self) -> None:
        async with self.lock:
            self.queue = SongQueue()

            self.is_playing = False
            self.is_paused = False

            await self.guild_bot.reset()

            await self.guild_bot.update_message()

    async def disconnect(self, disconnect=True) -> None:
        async with self.lock:
            if disconnect:
                asyncio.create_task(self.voice_client.disconnect())
            await self.reset_bot_states()
            await self.guild_bot.reset()

            await self.guild_bot.update_message()

    async def swap(self, i: int, j: int) -> None:
        async with self.lock:
            try:
                self.queue.swap(i, j)
            except ValueError as e:
                error_msg = e.args[0]
                raise CommandExecutionError(error_msg)

            await self.guild_bot.update_message()

    async def remove(self, i: int) -> None:
        async with self.lock:
            try:
                self.queue.remove(i)
            except ValueError as e:
                error_msg = e.args[0]
                raise CommandExecutionError(error_msg)

            await self.guild_bot.update_message()

    async def goto(self, i: int) -> None:
        async with self.lock:
            try:
                self.queue.goto(i)
            except ValueError as e:
                error_msg = e.args[0]
                raise CommandExecutionError(error_msg)

            self.goto_event.set()
            self.stop_play_audio_thread()

            await self.guild_bot.update_message()

    # @await_update_message
    async def add(
            self,
            query: str,
            voice_channel: discord.VoiceChannel,
            insert_place: int,
            interaction: discord.Interaction,
            playlist_name: str = None,
            playlist_scope: typing.Literal['user', 'server'] = None
    ) -> None:
        if insert_place <= 0:
            raise CommandExecutionError('Must be inserted into a place with a positive number.')
        self.voice_channel = voice_channel
        try:
            if playlist_name is None:
                self.queue.add_songs(query, interaction, insert_place)
            else:
                await self.queue.add_playlist(playlist_name, interaction, playlist_scope, query, insert_place)
        except ValueError as e:
            error_msg = e.args[0]
            raise CommandExecutionError(error_msg)

        await self.guild_bot.update_message()

        if self.play_music_thread is None:
            self.start_session()

    async def join(self, channel=None):
        """
        Connects to or moves the voice client to the specified voice channel.
        If the voice client is not connected or does not exist, this method connects the voice
        client to the specified voice channel. If the voice client is already connected, this
        method moves the voice client to the specified voice channel. If the voice client fails
        to connect or move, a `FailedToConnectError` is raised.
        """
        if self.voice_client is None or not self.voice_client.is_connected():
            vc = self.voice_channel if channel is None else channel
            self.voice_client = await vc.connect()
            if self.voice_client is None:
                raise FailedToConnectError()
        else:
            return

    def update_ui(self):
        loop = asyncio.new_event_loop()
        loop.create_task(self.guild_bot.update_message())

    # @await_update_message
    def start_session(self):
        self.play_music_thread = threading.Thread(target = self.play_music, args = ())
        self.play_music_thread.start()

        self.is_playing = True

        print(f'{c_event("started session")} in {c_guild(self.guild.id)}')

    def close_session(self):
        self.is_playing = False

        self.play_music_thread = None
        self.playing_thread = None

        self.is_paused = False
        self.queue = SongQueue()

        print(f'{c_event("closed session")} in {c_guild(self.guild.id)}')

    def play_music(self):
        is_first = True
        while True:
            if self.voice_client is None:
                raise CommandExecutionError('Bot is not in a voice channel.')

            if self.voice_client.is_playing() or self.is_paused:
                time.sleep(1)
                continue

            if not self.previous_event.is_set() and not self.goto_event.is_set():
                if not is_first or self.queue.played:
                    self.queue.next(force_skip = self.skip_event.is_set())

            self.skip_event.clear()
            self.previous_event.clear()
            self.goto_event.clear()

            is_first = False

            song = self.queue.current

            if song is None:
                self.close_session()
                return

            song.set_source_color_lyrics()

            if not song.is_good:
                self.queue.next()
                continue

            audio_source = discord.FFmpegPCMAudio(song.source, **self.ffmpeg_options)
            try:
                self.voice_client.play(audio_source)
            except discord.ClientException:
                continue

            self.playing_thread = threading.Thread(target = self._play_audio_thread(), args = ())
            self.playing_thread.start()

    def stop_play_audio_thread(self):
        self.stop_event.set()
        if self.voice_client.is_playing():
            self.voice_client.stop()

    def _play_audio_thread(self):
        while self.voice_client.is_playing() or self.is_paused:
            if self.stop_event.is_set():
                break
            time.sleep(1)
