import asyncio
import discord
import typing
import threading
import multiprocessing
import time
from discord.ext import commands

from .song_queue import SongQueue as Queue
from utils import CommandExecutionError, FailedToConnectError, c_err, c_channel


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

        self.queue = Queue()

        self.looped_status: typing.Literal['none', 'queue', 'single'] = 'none'
        self.is_playing = False
        self.is_paused = False

        self.voice_client: discord.VoiceClient | None = None
        self.voice_channel: discord.VoiceChannel | None = None

        self.lock = asyncio.Lock()

        self.playing_thread: threading.Thread | None = None

        self.playing_process: multiprocessing.Process | None = None

    @staticmethod
    def await_update_message(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            print('--------------------- updating message ---------------------')
            # await args[0].guild_bot.update_msg()
            return result
        return wrapper

    async def connect(self) -> None:
        async with self.lock:
            await self.join()

    # @await_update_message
    async def reset_bot_states(self) -> None:
        async with self.lock:
            self.looped_status = 'none'
            self.is_playing = False
            self.is_paused = False

            self.queue = Queue()

            # todo: should we reset this
            self.voice_client = None
            self.voice_channel = None

            # todo: add reset method to guild bot class
            self.guild_bot.reset()

    # @await_update_message
    async def shuffle_queue(self) -> None:
        async with self.lock:
            if self.queue.is_shuffled:
                self.queue.unshuffle()
            else:
                self.queue.shuffle()

    # @await_update_message
    async def cycle_loop(self) -> None:
        async with self.lock:
            if self.queue.loop_status == 'none':
                self.queue.loop_status = 'queue'
            elif self.queue.loop_status == 'queue':
                self.queue.loop_status = 'single'
            elif self.queue.loop_status == 'single':
                self.queue.loop_status = 'none'

    # @await_update_message
    async def go_to_previous(self) -> None:
        async with self.lock:
            self.queue.previous()

    # @await_update_message
    async def pause(self) -> None:
        async with self.lock:
            if self.is_paused:
                self.is_paused = False
                self.voice_client.resume()
            else:
                print('pausing')
                self.is_paused = True
                self.voice_client.pause()

    # @await_update_message
    async def skip(self) -> None:
        async with self.lock:
            if self.voice_client is not None:
                self.voice_client.pause()
            if self.looped_status == 'single':
                self.looped_status = 'queue'
            self.queue.next(force_skip=True)
            self.playing_process.terminate()

    # @await_update_message
    async def previous(self) -> None:
        async with self.lock:
            if self.voice_client is not None:
                self.voice_client.pause()
            if self.looped_status == 'single':
                self.looped_status = 'queue'
            self.queue.previous()
            self.playing_process.terminate()

    # @await_update_message
    async def clear(self) -> None:
        async with self.lock:
            self.queue = Queue()

            self.is_playing = False
            self.is_paused = False

            self.guild_bot.reset()

    # @await_update_message
    async def disconnect(self, disconnect=True) -> None:
        async with self.lock:
            if disconnect:
                asyncio.create_task(self.voice_client.disconnect())
            await self.reset_bot_states()
            self.guild_bot.reset()

    # @await_update_message
    async def swap(self, i: int, j: int) -> None:
        async with self.lock:
            try:
                self.queue.swap(i, j)
            except ValueError as e:
                error_msg = e.args[0]
                raise CommandExecutionError(error_msg)

    # @await_update_message
    async def remove(self, i: int) -> None:
        async with self.lock:
            try:
                self.queue.remove(i)
            except ValueError as e:
                error_msg = e.args[0]
                raise CommandExecutionError(error_msg)

    # @await_update_message
    async def goto(self, i: int) -> None:
        async with self.lock:
            try:
                self.queue.goto(i)
            except ValueError as e:
                error_msg = e.args[0]
                raise CommandExecutionError(error_msg)

    # @await_update_message
    async def add(
            self,
            query: str,
            voice_channel: discord.VoiceChannel,
            insert_place: int,
            interaction: discord.Interaction
    ) -> None:
        if insert_place <= 0:
            raise CommandExecutionError('Must be inserted into a place with a positive number.')
        self.voice_channel = voice_channel
        try:
            self.queue.add_songs(query, interaction, insert_place)
        except ValueError as e:
            error_msg = e.args[0]
            raise CommandExecutionError(error_msg)

        if self.playing_thread is None:
            self.playing_thread = threading.Thread(target = self.play_music, args = ())
            self.playing_thread.start()

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

    async def play_current(self):
        try:
            await self.join()
        except FailedToConnectError:
            print(f'{c_err()} failed to connect to vc in guild {c_channel(self.guild.id)}')
            return
        print(self.queue)

        print(self.queue.current)

        if self.voice_client is not None and self.voice_client.is_playing():
            self.voice_client.stop()

        song = self.queue.current

        if song is None:
            self.is_playing = False
            return

        song.set_source_color_lyrics()

        if not song.is_good:
            self.queue.next()
            return

        await self.guild_bot.update_msg()

        self.playing_thread = threading.Thread(target=self._play_audio_thread, args=(song,))

        self.playing_thread.start()

    # @await_update_message
    def _play_audio_thread(self, song):
        audio_source = discord.FFmpegPCMAudio(song.source, **self.ffmpeg_options)
        self.is_playing = True
        self.voice_client.play(audio_source)
        try:
            while self.voice_client.is_playing() or self.is_paused:
                time.sleep(1)
        except threading.ThreadError:
            self.voice_client.stop()
        finally:
            self.voice_client.stop()

    def update_ui(self):
        loop = asyncio.new_event_loop()
        loop.create_task(self.guild_bot.update_msg())

    def play_music(self):
        while True:
            if self.voice_client is None:
                raise CommandExecutionError('Bot is not in a voice channel.')

            if self.voice_client.is_playing() or self.is_paused:
                time.sleep(1)
                continue
            else:
                self.queue.next()

            song = self.queue.current

            if song is None:
                self.is_playing = False
                return

            song.set_source_color_lyrics()

            if not song.is_good:
                self.queue.next()
                continue

            self.update_ui()

            self.playing_process = multiprocessing.Process(target = self._play_audio_thread, args = (song,))
            self.playing_process.start()
