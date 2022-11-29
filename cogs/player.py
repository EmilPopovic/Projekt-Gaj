"""
This file is part of Shteff which is released under the GNU General Public License v3.0.
See file LICENSE or go to <https://www.gnu.org/licenses/gpl-3.0.html> for full license details.
"""

import asyncio
import random

import discord
from discord.ext import commands

from cogs.song_generator import SongGenerator
from exceptions import *
from colors import *


class Player(commands.Cog):
    # TODO: write docstring
    # TODO: update_msg wrapper
    # encoder options
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    def __init__(self, guild_bot, guild: discord.guild.Guild):
        self.guild = guild
        self.guild_bot = guild_bot

        self.is_playing = False
        self.is_paused = False
        self.is_looped = False
        self.is_looped_single = False
        self.is_shuffled = False
        self.is_downloading = False
        self.short_queue = False
        self.show_history = False
        self.was_long_queue = False
        self.p_index = -1
        self.shuffle_start_index = None
        self.loop_start_index = None

        # song lists
        self.music_queue = []
        self.unshuffled_queue = []
        self.skipped_while_shuffled = []

        # initiate voice
        self.vc = None
        self.v_channel = None

    def reset_bot_states(self) -> None:
        # default bot states
        self.is_playing = False
        self.is_paused = False
        self.is_looped = False
        self.is_looped_single = False
        self.is_shuffled = False
        self.is_downloading = False
        self.short_queue = False
        self.show_history = False
        self.was_long_queue = False
        self.p_index = -1
        self.shuffle_start_index = None
        self.loop_start_index = None

        # song lists
        self.music_queue = []
        self.unshuffled_queue = []
        self.skipped_while_shuffled = []

        # initiate voice
        self.vc = None

    async def shuffle(self) -> None:
        # lord forgive me for what I am about to code
        if self.music_queue[self.p_index + 1:]:
            if not self.is_shuffled:
                # index of song where shuffling was started
                self.shuffle_start_index = self.p_index
                # unshuffled part of queue, used for restoring to unshuffled state
                self.unshuffled_queue = self.music_queue[self.p_index + 1:]

                shuffled_queue = self.music_queue[self.p_index + 1:]
                random.shuffle(shuffled_queue)
                self.music_queue = self.music_queue[:self.p_index + 1] + shuffled_queue
                self.is_shuffled = True

            else:
                # if this doesn't seem to make sense to you, don't be afraid, you are not alone
                # there are most likely dozens of cases that break this code
                # I wish nothing but the best of luck to you, brave explorer fixing this dumpster fire
                current = self.music_queue[self.p_index]

                never_shuffled_part = self.music_queue[:self.shuffle_start_index + 1]

                new_skipped_unshuffled = [song for song in self.skipped_while_shuffled
                                          if song != self.music_queue[self.shuffle_start_index]]

                new_unshuffled = [song for song in self.unshuffled_queue
                                  if song not in self.skipped_while_shuffled and song != current]

                self.music_queue = never_shuffled_part + new_skipped_unshuffled + [current] + new_unshuffled

                self.is_shuffled = False

        await self.guild_bot.update_msg()

    async def previous(self) -> None:
        # can't go to previous if pointer is on the first song
        if self.p_index == 0:
            return

        self.p_index -= 2

        self.vc.pause()
        await self.play_music()

    def pause(self) -> None:
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()

        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    async def skip(self) -> None:
        self.vc.pause()

        # handle case if shuffled
        if self.is_shuffled:
            current = self.music_queue[self.p_index]

            if current not in self.skipped_while_shuffled:
                self.skipped_while_shuffled.append(current)

        # if looped single, don't loop
        if self.is_looped_single:
            self.loop()

        await self.play_music()

    def loop(self) -> None:

        if self.vc is None:
            pass

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

    async def clear(self) -> None:
        self.music_queue = []

        self.p_index = -2
        await self.skip()

        self.is_looped = False
        self.is_looped_single = False
        self.is_shuffled = False
        if self.is_paused:
            self.pause()

        await self.guild_bot.update_msg()

    async def dc(self) -> None:
        await self.vc.disconnect()
        self.reset_bot_states()
        await self.guild_bot.update_msg()

    async def queue(self) -> None:
        if self.short_queue:
            self.short_queue = False
        else:
            self.short_queue = True

        await self.guild_bot.update_msg()

    async def history(self) -> None:
        if self.show_history:
            self.show_history = False

            if self.was_long_queue:
                self.short_queue = False

        else:
            self.show_history = True

            if not self.short_queue:
                self.was_long_queue = True
                self.short_queue = True

        await self.guild_bot.update_msg()

    async def join(self):
        # connect to voice if not connected
        # move if in another voice channel
        if self.vc is None or not self.vc.is_connected():
            self.vc = await self.v_channel.connect()
            if self.vc is None:
                raise FailedToConnectError()
        else:
            await self.vc.move_to(self.v_channel)

    async def play_music(self) -> None:
        if self.music_queue[self.p_index + 1:]:
            # do not move pointer if looped single
            # move pointer if not.is_looped_single
            if not self.is_looped_single:
                self.p_index += 1
            # move to start of loop when we get to the end of self.music_queue
            if self.is_looped and self.p_index == len(self.music_queue):
                self.p_index = self.loop_start_index

            # set source and color of current SongGenerator object
            # if not already set
            current = self.music_queue[self.p_index]
            m_url = current.get_source_and_color()['source']

            # join vc
            try:
                await self.join()
            except FailedToConnectError:
                print(f'{c_time()} {c_err()} failed to connect to vc in guild {c_channel(self.guild.id)}')
                return

            self.is_playing = True
            await self.guild_bot.update_msg()

            # start playing
            # Alan Turing himself poured his essence into this piece of code
            # for the love of all that is good don't touch the lines below
            loop = asyncio.get_event_loop()
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                         after = lambda _: loop.create_task(self.play_music()))

        else:
            # if we finished playing the last song in queue
            self.is_playing = False
            await self.guild_bot.update_msg()

    async def add_to_queue(self, query, vc):
        self.is_downloading = True
        await self.guild_bot.update_msg()
        self.v_channel = vc

        song = None

        if 'https://open.spotify.com/track/' in query:
            self.music_queue.append(SongGenerator(query))

        elif 'https://open.spotify.com/album/' in query:
            # TODO: remove test timer
            # TODO: get album
            t0 = datetime.now()
            print('Starting extract.')

            # self.music_queue += self.multiprocess_get_songs(SpotifyInfo.songs_from_album(query))

            t1 = datetime.now()
            print(t1 - t0)
            print('extract ended')

        elif 'https://open.spotify.com/playlist/' in query:
            self.music_queue += SongGenerator.get_song_gens(query)

        else:
            song = SongGenerator(query)
            self.music_queue.append(song)

        if self.is_shuffled:
            self.unshuffled_queue.append(song)
        if not self.is_playing:
            await self.play_music()

        self.is_downloading = False
        await self.guild_bot.update_msg()

    async def swap(self, i: int, j: int) -> None:
        """
        Swaps songs on indexes i and j in self.music_queue.
        Skips to next song if -1 passed as argument.
        Updates message.
        """
        i, j = i + self.p_index, j + self.p_index
        self.music_queue[i], self.music_queue[j] = self.music_queue[j], self.music_queue[i]
        await self.guild_bot.update_msg()

    def update_ui(self, func):
        # TODO: use decorator for ui update after method
        def wrapper():
            func()
            self.guild_bot.update_msg()

        return wrapper()
