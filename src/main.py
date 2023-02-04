"""
Shteff  Copyright (C) 2022 Mjolnir2425, OvajStup

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# last changed 30/12/22
# commenting
# added CommandExecutionError to some commands
# added handling of undocumented errors to some commands
# rewrote the `play` command


import sys
import json

import discord
from discord import app_commands
from discord.ext import commands

from components import (
    AntiSpamCog,
    HelpCog,
    CommandHandler,
    GuildBot
)

from utils.sql_bridge import Database as db
from utils.colors import *
from utils.checks import PermissionsCheck

with open('secrets.json', 'r') as f:
    data = json.load(f)
token = data['discord']['discord_token']


class MainBot(commands.AutoShardedBot):
    """
    This is the MainBot docstring, please finish it.
    """
    # TODO: docstring
    def __init__(self, intents=discord.Intents.all()):
        super().__init__(command_prefix = '!', intents = intents)
        GuildBot.bot = self
        self.guild_bots = {}

        self.database = db()
        GuildBot.db = self.database
        # ListAdder.db = self.database
        PermissionsCheck.db = self.database

        self.command_handler = CommandHandler(self)

        @self.tree.command(name = 'play', description = 'Adds a song/list to queue.')
        @app_commands.describe(song = 'The name or link of song/list.')
        async def play_callback(interaction: discord.Interaction, song: str, number: int = None) -> None:
            await self.command_handler.play(interaction, song, number)

        @self.tree.command(name = 'skip', description = 'Skips to the next queued song.')
        async def skip_callback(interaction: discord.Interaction) -> None:
            await self.command_handler.skip(interaction)

        @self.tree.command(name = 'loop', description = 'Loops queue or single song.')
        async def loop_callback(interaction: discord.Interaction) -> None:
            await self.command_handler.loop(interaction)

        @self.tree.command(name = 'clear', description = 'Clears queue and history, stops playing.')
        async def clear_callback(interaction: discord.Interaction) -> None:
            await self.command_handler.clear(interaction)

        @self.tree.command(name = 'dc', description = 'Disconnects bot from voice channel.')
        async def disconnect_callback(interaction: discord.Interaction) -> None:
            await self.command_handler.disconnect(interaction)

        @self.tree.command(name = 'previous', description = 'Skips current song and plays previous.')
        async def previous_callback(interaction: discord.Interaction) -> None:
            await self.command_handler.previous(interaction)

        @self.tree.command(name = 'queue', description = 'Toggles queue display type (short/long).')
        async def queue_callback(interaction: discord.Interaction) -> None:
            await self.command_handler.queue(interaction)

        @self.tree.command(name = 'history', description = 'Toggles history display type (show/hide).')
        async def history_callback(interaction: discord.Interaction) -> None:
            await self.command_handler.history(interaction)

        @self.tree.command(name = 'lyrics', description = 'Toggles lyrics display (show/hide).')
        async def lyrics_callback(interaction: discord.Interaction) -> None:
            await self.command_handler.lyrics(interaction)

        @self.tree.command(name = 'shuffle', description = 'Toggles queue shuffle.')
        async def shuffle_callback(interaction: discord.Interaction):
            await self.command_handler.shuffle(interaction)

        @self.tree.command(name = 'swap', description = 'Swap places of queued songs.')
        @app_commands.describe(song1 = 'Place of first song in queue.', song2 = 'Place of second song in the queue.')
        async def swap_callback(interaction: discord.Interaction, song1: int, song2: int) -> None:
            await self.command_handler.swap(interaction, song1, song2)

        @self.tree.command(name = 'pause', description = 'Pauses or unpauses playing.')
        async def pause_callback(interaction: discord.Interaction) -> None:
            await self.command_handler.pause(interaction)

        @self.tree.command(name = 'remove', description = 'Removes song with given index from the queue.')
        async def remove_callback(interaction: discord.Interaction, number: int) -> None:
            await self.command_handler.remove(interaction, number)

        @self.tree.command(name = 'goto', description = 'Jumps to the song with given index, removes skipped songs.')
        async def goto_callback(interaction: discord.Interaction, number: int) -> None:
            await self.command_handler.goto(interaction, number)

        # @self.tree.command(name = 'create', description = 'Add a song to a playlist.')
        # async def create_callback(interaction: discord.Interaction, name: str) -> None:
        #     await self.command_handler.create(interaction, name)

        # @self.tree.command(name = 'add', description = 'Add a song to a playlist.')
        # async def add_callback(interaction: discord.Interaction, number: int = 0) -> None:
        #     await self.command_handler.add(interaction, number)

    # todo: on guild join

    async def on_ready(self) -> None:
        """
        Runs on bot login.
        Syncs slash commands.
        Creates GuildBot objects for every guild.
        """
        # sync commands
        print(f'{c_event("SYNCING COMMANDS")}')
        try:
            synced = await self.tree.sync()
            print(f'{c_event("SYNCED")} {len(synced)} command(s)')
        except Exception as e:
            print(f'{c_err()} failed to sync command(s)\n{c_event("EXITING")}, Exception:\n{e}')
            sys.exit()

        self.remove_command('help')
        await self.add_cog(AntiSpamCog(self))

        # create music cog for every guild bot is in
        for guild in self.guilds:
            self.guild_bots[guild.id] = await GuildBot(guild)

        print(f'{c_login()} as {self.user} with user id: {c_user(self.user.id)}')


if __name__ == '__main__':
    """Main is the beginning of everything."""
    bot = MainBot()
    bot.run(token)