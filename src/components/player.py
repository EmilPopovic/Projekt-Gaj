import asyncio
import random
import discord
from discord.ext import commands

from .song_generator import SongGenerator
from utils import CommandExecutionError, FailedToConnectError, InteractionResponder as Responder
from utils.colors import c_err, c_channel


class Player(commands.Cog):
    """
    Manages the audio playback of a Discord server.
    Methods of class include functionality for interacting with a queue of songs, such as
    adding and removing songs, shuffling and looping the queue, and skipping to the next
    song. There are also methods for controlling playback, such as pausing, resuming and
    stopping the audio. The object also includes methods for managing the connection to a
    voice channel in the Discord server, such as joining and disconnecting from the voice
    channel.
    """
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    def __init__(self,
                 guild_bot,
                 guild: discord.guild.Guild):
        self.guild: discord.guild.Guild = guild
        self.guild_bot = guild_bot

        # default player flags
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.is_looped: bool = False
        self.is_looped_single: bool = False
        self.is_shuffled: bool = False
        self.was_long_queue: bool = False

        # default indexes
        self.p_index = -1
        self.shuffle_start_index = None
        self.loop_start_index = None

        # song lists
        self.queue: list[SongGenerator] = []
        self.unshuffled_queue: list[SongGenerator] = []
        self.skipped_while_shuffled: list[SongGenerator] = []

        # initialize voice objects
        self.voice_client: discord.VoiceClient | None = None
        self.voice_channel: discord.VoiceChannel | None = None

        self.lock = asyncio.Lock()
        self.work_queue = asyncio.Queue()
        self.coro_id = 0

    def get_coro_id(self):
        self.coro_id += 1
        return self.coro_id

    def __reset_bot_states(self) -> None:
        """
        Resets certain states and flags to their default values.
        This method resets certain flags and indexes to their default values, empties
        certain lists, and sets the voice client and voice channel to `None`. It is
        called when the bot is disconnected or certain actions are performed.
        """
        # default player flags
        self.is_playing = False
        self.is_paused = False
        self.is_looped = False
        self.is_looped_single = False
        self.is_shuffled = False
        self.was_long_queue = False

        # default indexes
        self.p_index = -1
        self.shuffle_start_index = None
        self.loop_start_index = None

        # song lists
        self.queue = []
        self.unshuffled_queue = []
        self.skipped_while_shuffled = []

        # initialize voice
        self.voice_client = None
        self.voice_channel = None

        self.work_queue = asyncio.Queue()

    async def shuffle(self) -> None:
        """
        Shuffles the queue of songs.
        This method shuffles the remaining songs in the queue if the queue is not already shuffled,
        or restores the queue to its original order if it is already shuffled. It updates the
        message accordingly.
        """
        await self.work_queue.put(self.get_coro_id())
        async with self.lock:
            # lord forgive me for what I am about to code
            if self.queue[self.p_index + 1:]:
                if not self.is_shuffled:
                    # index of song where shuffling was started
                    self.shuffle_start_index = self.p_index
                    # unshuffled part of queue, used for restoring to unshuffled state
                    self.unshuffled_queue = self.queue[self.p_index + 1:]

                    shuffled_queue = self.queue[self.p_index + 1:]
                    random.shuffle(shuffled_queue)
                    self.queue = self.queue[:self.p_index + 1] + shuffled_queue
                    self.is_shuffled = True

                else:
                    # if this doesn't seem to make sense to you, don't be afraid, you are not alone
                    # there are most likely dozens of cases that break this code
                    # I wish nothing but the best of luck to you, brave explorer fixing this dumpster fire
                    current = self.queue[self.p_index]

                    never_shuffled_part = self.queue[:self.shuffle_start_index + 1]

                    new_skipped_unshuffled = [
                        song for song in self.skipped_while_shuffled
                        if song != self.queue[self.shuffle_start_index]
                    ]

                    new_unshuffled = [
                        song for song in self.unshuffled_queue
                        if song not in self.skipped_while_shuffled or song != current
                    ]

                    self.queue = never_shuffled_part + new_skipped_unshuffled + new_unshuffled  # todo: + [current] ???

                    self.is_shuffled = False

            else:
                raise CommandExecutionError('Queue is empty.')

            await self.guild_bot.update_msg()
        self.work_queue.task_done()

    async def previous(self) -> None:
        """
        Skips to the previous song in the queue.
        If the current song is the first song in the queue, this method does nothing.
        Otherwise, the method pauses the current song and plays the previous song in the queue.
        """
        await self.work_queue.put(self.get_coro_id())
        async with self.lock:
            if self.p_index == 0:
                return

            self.p_index -= 2
            self.voice_client.pause()
            await self.__play_next()
        self.work_queue.task_done()

    async def pause(self) -> None:
        """
        Pauses or resumes the current song.
        If the current song is playing, this method will pause it.
        If the current song is already paused, this method will resume it.
        The method will also update the command message to reflect the current
        playing or paused status of the song.
        """
        await self.work_queue.put(self.get_coro_id())
        async with self.lock:
            if self.is_playing:
                self.is_playing = False
                self.is_paused = True
                self.voice_client.pause()

            elif self.is_paused:
                self.is_playing = True
                self.is_paused = False
                self.voice_client.resume()

        asyncio.create_task(self.guild_bot.update_msg())
        self.work_queue.task_done()

    async def skip(self) -> None:
        """
        Skips the current song and plays the next song in the queue.
        If the current song is playing or paused, this method will pause it and
        play the next song in the queue. If the current song is the last song in
        the queue and the `is_looped_single` flag is set, the method will loop the
        current song instead of skipping it. If the `is_shuffled` flag is set, the
        method will record the current song as having been skipped and update the
        list of skipped songs.
        """
        await self.work_queue.put(self.get_coro_id())
        async with self.lock:
            if self.voice_client is None:
                raise CommandExecutionError('Bot is not in a voice channel.')

            self.voice_client.pause()
            # handle case if shuffled
            if self.is_shuffled:
                current = self.queue[self.p_index]

                if current not in self.skipped_while_shuffled:
                    self.skipped_while_shuffled.append(current)

            # if looped single, don't loop
            if self.is_looped_single:
                await self.loop()

            await self.__play_next()
        self.work_queue.task_done()

    async def loop(self) -> None:
        """
        Loops the current queue or single song.
        If the `is_looped` flag is not set and the `is_looped_single` flag is not set,
        this method sets the `is_looped` flag and marks the beginning of the looping
        section in the queue. If the `is_looped` flag is not set and the `is_looped_single`
        flag is set, this method unsets the `is_looped_single` flag. If the `is_looped` flag
        is set and the `is_looped_single` flag is not set, this method unsets the `is_looped`
        flag and sets the `is_looped_single` flag. The method will also update the command
        message to reflect the current looping status of the queue or single song.
        """
        await self.work_queue.put(self.get_coro_id())
        async with self.lock:
            if self.voice_client is None:
                raise CommandExecutionError('Bot is not in a voice channel.')

            # if not looped, loop queue
            elif not self.is_looped and not self.is_looped_single:
                self.is_looped = True
                # marks the beginning of the looping section
                self.loop_start_index = self.p_index

            # if looped single, don't loop
            elif not self.is_looped and self.is_looped_single:
                self.is_looped_single = False

            # if looped queue, loop single
            elif self.is_looped and not self.is_looped_single:
                self.is_looped = False
                self.is_looped_single = True

            asyncio.create_task(self.guild_bot.update_msg())
        self.work_queue.task_done()

    async def clear(self) -> None:
        """
        Clears the queue, resets certain flags, and skips to the next song.
        This method clears the queue, the list of skipped songs while shuffled, and resets the
        `is_looped`, `is_looped_single`, and `is_shuffled` flags. If the `is_paused` flag is set,
        the method will also unpause the current song. The method will also update the command
        message and delete the lyrics message, if it exists.
        """
        await self.work_queue.put(self.get_coro_id())
        async with self.lock:
            if self.voice_client is None:
                raise CommandExecutionError('Bot is not in a voice channel.')

            self.queue = []
            self.unshuffled_queue = []
            self.skipped_while_shuffled = []

            self.is_looped = False
            self.is_looped_single = False
            self.is_shuffled = False

            self.p_index = -2
            self.loop_start_index = None
            self.shuffle_start_index = None

            await self.skip()
            if self.is_paused:
                await self.pause()
            await self.guild_bot.delete_lyrics_message()

            asyncio.create_task(self.guild_bot.update_msg())
        self.work_queue.task_done()

    async def dc(self, disconnect: bool = True) -> None:
        """
        Disconnects the voice client and resets certain states and flags.
        This method disconnects the voice client, deletes the lyrics message if it exists,
        resets certain bot states, and resets certain flags. The method also updates the
        command message to reflect the changes.
        """
        await self.work_queue.put(self.get_coro_id())
        async with self.lock:
            if self.voice_client is None:
                return

            if disconnect:
                await self.voice_client.disconnect()
            await self.guild_bot.delete_lyrics_message()

            self.__reset_bot_states()
            self.guild_bot.reset_flags()

            asyncio.create_task(self.guild_bot.update_msg())
        self.work_queue.task_done()

    async def swap(self, i: int, j: int) -> None:
        """
        Swaps songs at indexes `i` and `j` in the queue.
        This method swaps the songs at indexes `i` and `j` in the `self.queue` list.
        The method also updates the command message to reflect the changes.
        Args:
        i: int: The index of the first song to swap.
        j: int: The index of the second song to swap.
        Returns:
        None
        """
        await self.work_queue.put(self.get_coro_id())
        async with self.lock:
            # todo: use transformers for this check
            queue_len = len(self.queue[self.p_index + 1:])
            if i == 0 and j == 0:
                raise CommandExecutionError('Arguments must be greater than 0.')
            if i == j:
                raise CommandExecutionError('Arguments must be different.')
            if i > queue_len or j > queue_len:
                raise CommandExecutionError('Arguments not in queue.')

            i, j = i + self.p_index, j + self.p_index
            self.queue[i], self.queue[j] = self.queue[j], self.queue[i]

            asyncio.create_task(self.guild_bot.update_msg())
        self.work_queue.task_done()

    async def remove(self, n: int) -> None:
        """
        Removes song at index `n` in the queue.
        n must be greater than 0 and in range.
        """
        await self.work_queue.put(self.get_coro_id())
        async with self.lock:
            queue_len = len(self.queue[self.p_index + 1:])
            if n <= 0:
                print('value less than 0')
                raise CommandExecutionError('Argument must be greater than 0.')
            if n > queue_len:
                raise CommandExecutionError('Argument not in queue.')

            self.queue.pop(n + self.p_index)
            asyncio.create_task(self.guild_bot.update_msg())
        self.work_queue.task_done()

    async def goto(self, n: int) -> None:
        await self.work_queue.put(self.get_coro_id())
        async with self.lock:
            queue_len = len(self.queue[self.p_index + 1:])
            if n <= 0:
                raise CommandExecutionError('Argument must be greater than 0.')
            if n > queue_len:
                raise CommandExecutionError('Argument not in queue.')
            if n == 1:
                await self.skip()
                return

            to_remove = self.queue[self.p_index + 1:self.p_index + n]
            for song in to_remove:
                self.queue.remove(song)

            await self.skip()
        self.work_queue.task_done()

    async def add_to_queue(self,
                           query: str,
                           voice_channel: discord.VoiceChannel,
                           number: int,
                           interaction: discord.Interaction):
        """
        Add songs to the music queue and potentially start playing them.
        Parameters:
        query (str): a string containing the name of a song or a playlist URL
        voice_state (discord.VoiceState): the voice state of the user requesting the songs
        number (int, optional): the index in the queue where the songs should be inserted.
            If not provided, the songs will be appended to the end of the queue.
        """
        await self.work_queue.put(self.get_coro_id())
        async with self.lock:
            if number is not None and number <= 0:
                raise CommandExecutionError('Invalid optional argument `number`.')

            self.voice_channel = voice_channel

            songs: list[SongGenerator] = SongGenerator.get_songs(query, interaction)
            if number is None or number >= len(self.queue) - self.p_index:
                self.queue.extend(songs)
            else:
                self.queue.insert(self.p_index + number, *songs)

            if self.is_shuffled and songs is not None:
                self.unshuffled_queue.extend(songs)

            if not self.is_playing:
                await self.__play_next()

        asyncio.create_task(self.guild_bot.update_msg())
        self.work_queue.task_done()

    async def __join(self):
        """
        Connects to or moves the voice client to the specified voice channel.
        If the voice client is not connected or does not exist, this method connects the voice
        client to the specified voice channel. If the voice client is already connected, this
        method moves the voice client to the specified voice channel. If the voice client fails
        to connect or move, a `FailedToConnectError` is raised.
        """
        if self.voice_client is None or not self.voice_client.is_connected():
            self.voice_client = await self.voice_channel.connect()
            if self.voice_client is None:
                raise FailedToConnectError()
        else:
            await self.voice_client.move_to(self.voice_channel)

    async def __play_audio(self, song: SongGenerator) -> None:
        try:
            await self.__join()
        except FailedToConnectError:
            print(f'{c_err()} failed to connect to vc in guild {c_channel(self.guild.id)}')
            await Responder.send('Failed to join voice channel.', song.interaction, followup=True, fail=True)
            return

        if not song.is_good:
            print(f'{c_err()} invalid song object: {song}')
            await Responder.send(f'Cannot find "{song.name}".', song.interaction, followup=True, fail=True)
            self.queue.pop(self.p_index)
            await self.skip()
            return

        self.is_playing = True
        asyncio.create_task(self.guild_bot.update_msg())

        audio_source = discord.FFmpegPCMAudio(song.source, **self.ffmpeg_options)
        self.voice_client.play(audio_source)

        while self.voice_client is not None and self.voice_client.is_playing() or self.is_paused:
            await asyncio.sleep(3)

        await self.__play_next()

    def __get_next(self):
        next_index = self.p_index
        if self.queue[self.p_index + 1:]:
            if not self.is_looped_single and self.is_playing or self.p_index == -1:
                next_index += 1
            if self.is_looped and self.p_index == len(self.queue):
                next_index = self.loop_start_index

            next_song: SongGenerator = self.queue[next_index]
            return next_song, next_index
        else:
            return None, None

    async def __play_next(self):
        next_song, next_index = self.__get_next()
        self.p_index = next_index
        if next_song is not None:
            asyncio.create_task(self.__play_audio(next_song))
        else:
            self.is_playing = False
            asyncio.create_task(self.guild_bot.update_msg())
