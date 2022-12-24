"""
This file is part of Shteff which is released under the GNU General Public License v3.0.
See file LICENSE or go to <https://www.gnu.org/licenses/gpl-3.0.html> for full license details.
"""

# last changed 23/12/22
# separated functions with two blank lines
# renamed music_queue to queue
# added typehints
# command queue doesn't work, at all, nothing
# added guard clause to skip
# added some comments

import asyncio
import random

import discord
from discord.ext import commands
from threading import Thread

from components.song_generator import SongGenerator
from exceptions import *
from colors import *


class Player(commands.Cog):
    # TODO: write docstring
    # encoder options
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }


    def __init__(self, guild_bot, guild: discord.guild.Guild):
        self.guild: discord.guild.Guild = guild
        self.guild_bot = guild_bot

        # default player flags
        self.is_playing:       bool = False
        self.is_paused:        bool = False
        self.is_looped:        bool = False
        self.is_looped_single: bool = False
        self.is_shuffled:      bool = False
        self.was_long_queue:   bool = False

        # default indexes
        self.p_index             = -1
        self.shuffle_start_index = None
        self.loop_start_index    = None

        # song lists
        self.queue:                  list[SongGenerator] = []
        self.unshuffled_queue:       list[SongGenerator] = []
        self.skipped_while_shuffled: list[SongGenerator] = []

        # initialize voice objects
        self.voice_client:   discord.VoiceClient | None = None
        self.voice_channel: discord.VoiceChannel | None = None

        # todo: doesn't work
        # initialize command queue
        self.command_queue = []
        command_thread = Thread(target = self.check_for_commands, args = ())
        command_thread.start()


    def reset_bot_states(self) -> None:
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

        self.command_queue = []


    async def check_for_commands(self):
        # todo: broken af
        while True:
            if len(self.command_queue) > 0:
                command_dict = self.command_queue.pop(0)
                await self.execute_command(
                    command_dict['command'],
                    *command_dict['args']
                )


    async def queue_command(self, command, *args):
        # todo: all of this needs to go
        if args:
            self.command_queue.append(
                {'command': command, 'args': list(args)}
            )


    @staticmethod
    async def execute_command(command, *args):
        if args:
            await command(*args)
        else:
            await command()


    async def shuffle(self) -> None:
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

                new_skipped_unshuffled = [song for song in self.skipped_while_shuffled
                                          if song != self.queue[self.shuffle_start_index]]

                new_unshuffled = [song for song in self.unshuffled_queue
                                  if song not in self.skipped_while_shuffled and song != current]

                self.queue = never_shuffled_part + new_skipped_unshuffled + [current] + new_unshuffled

                self.is_shuffled = False

        await self.guild_bot.update_msg()


    async def previous(self) -> None:
        # can't go to previous if pointer is on the first song
        if self.p_index == 0:
            return

        self.p_index -= 2
        self.voice_client.pause()
        await self.play_music()


    async def pause(self) -> None:
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.voice_client.pause()

        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.voice_client.resume()

        await self.guild_bot.update_msg()


    async def skip(self) -> None:
        if self.voice_client is None:
            return

        self.voice_client.pause()
        # handle case if shuffled
        if self.is_shuffled:
            current = self.queue[self.p_index]

            if current not in self.skipped_while_shuffled:
                self.skipped_while_shuffled.append(current)

        # if looped single, don't loop
        if self.is_looped_single:
            await self.loop()

        await self.play_music()


    async def loop(self) -> None:
        if self.voice_client is None:
            return

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

        await self.guild_bot.update_msg()


    async def clear(self) -> None:
        if self.voice_client is None:
            return

        # clear all song lists
        self.queue = []
        self.unshuffled_queue = []
        self.skipped_while_shuffled = []

        # reset some flags
        self.is_looped = False
        self.is_looped_single = False
        self.is_shuffled = False

        # todo: what? why -2?
        # todo: will this work if clear happens while looping a single song?
        self.p_index = -2
        await self.skip()

        # unpause if paused
        if self.is_paused:
            await self.pause()

        await self.guild_bot.update_msg()


    async def dc(self) -> None:
        if self.voice_client is None:
            return

        await self.voice_client.disconnect()
        self.reset_bot_states()
        await self.guild_bot.update_msg()


    async def join(self):
        # connect to voice if not connected
        # move if in another voice channel
        # todo: what if bot was disconnected
        if self.voice_client is None or not self.voice_client.is_connected():
            self.voice_client = await self.voice_channel.connect()
            if self.voice_client is None:
                raise FailedToConnectError()
        else:
            await self.voice_client.move_to(self.voice_channel)


    async def play_music(self) -> None:
        if self.queue[self.p_index + 1:]:
            # do not move pointer if looped single
            # move pointer if not.is_looped_single
            if not self.is_looped_single:
                self.p_index += 1
            # move to start of loop when we get to the end of self.queue
            if self.is_looped and self.p_index == len(self.queue):
                self.p_index = self.loop_start_index

            # set source and color of current SongGenerator object
            # if not already set
            current = self.queue[self.p_index]
            current.set_lyrics()
            m_url = current.get_source_and_color()['source']

            # todo: test this
            # if YouTube extract fails
            if not current.is_good:
                print(f'{c_err()} invalid song object: {current}')
                self.queue.pop(self.p_index)
                # skip current track
                await self.skip()

            # join voice_client
            try:
                await self.join()
            except FailedToConnectError:
                print(f'{c_err()} failed to connect to vc in guild {c_channel(self.guild.id)}')
                return

            self.is_playing = True
            await self.guild_bot.update_msg()

            # start playing
            # Alan Turing himself poured his essence into this piece of code
            # for the love of all that is good don't touch the lines below
            loop = asyncio.get_event_loop()
            self.voice_client.play(
                discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                after = lambda _: loop.create_task(self.play_music())
            )

        else:
            # if we finished playing the last song in queue
            # todo: i don't know what this is doing but it doesn't do what it should
            self.is_playing = False
            await self.guild_bot.update_msg()


    async def add_to_queue(self, query, voice_state):
        # todo: find out what we use this for
        self.voice_channel = voice_state

        song = None
        songs = None

        if 'https://open.spotify.com/track/' in query:
            song = SongGenerator(query)
            self.queue.append(song)
        elif 'https://open.spotify.com/album/' in query:
            songs = SongGenerator.get_song_gens(query)
            self.queue.extend(songs)
        elif 'https://open.spotify.com/playlist/' in query:
            songs = SongGenerator.get_song_gens(query)
            self.queue.extend(songs)
        else:
            song = SongGenerator(query)
            self.queue.append(song)

        if self.is_shuffled:
            if song is not None:
                self.unshuffled_queue.append(song)
            elif songs is not None:
                self.unshuffled_queue.extend(songs)

        if not self.is_playing:
            await self.play_music()

        await self.guild_bot.update_msg()


    async def swap(self, i: int, j: int) -> None:
        """
        Swaps songs on indexes i and j in self.queue.
        Skips to next song if -1 passed as argument.
        Updates message.
        """
        i, j = i + self.p_index, j + self.p_index
        self.queue[i], self.queue[j] = self.queue[j], self.queue[i]
        await self.guild_bot.update_msg()
