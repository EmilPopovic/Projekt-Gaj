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

import sys
import json

import discord
from discord import app_commands
from discord.ext import commands

from components import (
    AntiSpamCog,
    HelpCog,
    CommandHandler,
    GuildBot,
    CommandButtons
)
from utils import *

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

        self.database = Database()
        GuildBot.db = self.database
        # ListAdder.db = self.database
        PermissionsCheck.db = self.database

        self.command_handler = CommandHandler(self)
        self.command_handler.bot = self

        CommandButtons.command_handler = self.command_handler
        CommandButtons.bot = self

        # BOT COMMANDS #

        @self.tree.command(name='help', description='Get help using the bot.')
        async def help_callback(interaction: discord.Interaction):
            await HelpCog.send_message(interaction)

        @self.tree.command(name='ping', description='Pings Shteff.')
        async def ping_callback(interaction: discord.Interaction):
            latency_ms = round(self.latency * 1000)
            await interaction.response.send_message(f'Pong! My latency is {latency_ms} ms.', ephemeral=True)

        @self.tree.command(name = 'play', description = 'Adds a song/list to queue.')
        @app_commands.describe(song = 'The name or link of song/list.')
        async def play_callback(interaction: discord.Interaction, song: str, number: int = None):
            await self.command_handler.play(interaction, song, number)

        @self.tree.command(name = 'skip', description = 'Skips to the next queued song.')
        async def skip_callback(interaction: discord.Interaction):
            await self.command_handler.skip(interaction)

        @self.tree.command(name = 'loop', description = 'Loops queue or single song.')
        async def loop_callback(interaction: discord.Interaction):
            await self.command_handler.loop(interaction)

        @self.tree.command(name = 'clear', description = 'Clears queue and history, stops playing.')
        async def clear_callback(interaction: discord.Interaction):
            await self.command_handler.clear(interaction)

        @self.tree.command(name = 'dc', description = 'Disconnects bot from voice channel.')
        async def disconnect_callback(interaction: discord.Interaction):
            await self.command_handler.disconnect(interaction)

        @self.tree.command(name = 'back', description = 'Skips current song and plays previous.')
        async def back_callback(interaction: discord.Interaction):
            await self.command_handler.previous(interaction)

        @self.tree.command(name = 'queue', description = 'Toggles queue display type (short/long).')
        async def queue_callback(interaction: discord.Interaction):
            await self.command_handler.queue(interaction)

        @self.tree.command(name = 'history', description = 'Toggles history display type (show/hide).')
        async def history_callback(interaction: discord.Interaction):
            await self.command_handler.history(interaction)

        @self.tree.command(name = 'lyrics', description = 'Toggles lyrics display (show/hide).')
        async def lyrics_callback(interaction: discord.Interaction):
            await self.command_handler.lyrics(interaction)

        @self.tree.command(name = 'shuffle', description = 'Toggles queue shuffle.')
        async def shuffle_callback(interaction: discord.Interaction):
            await self.command_handler.shuffle(interaction)

        @self.tree.command(name = 'swap', description = 'Swap places of queued songs.')
        @app_commands.describe(song1 = 'Place of first song in queue.', song2 = 'Place of second song in the queue.')
        async def swap_callback(interaction: discord.Interaction, song1: int, song2: int):
            await self.command_handler.swap(interaction, song1, song2)

        @self.tree.command(name = 'pause', description = 'Pauses or unpauses playing.')
        async def pause_callback(interaction: discord.Interaction):
            await self.command_handler.pause(interaction)

        @self.tree.command(name = 'remove', description = 'Removes song with given index from the queue.')
        async def remove_callback(interaction: discord.Interaction, number: int):
            await self.command_handler.remove(interaction, number)

        @self.tree.command(name = 'goto', description = 'Jumps to the song with given index, removes skipped songs.')
        async def goto_callback(interaction: discord.Interaction, number: int):
            await self.command_handler.goto(interaction, number)

        # @self.tree.command(name = 'create', description = 'Add a song to a playlist.')
        # async def create_callback(interaction: discord.Interaction, name: str) -> None:
        #     await self.command_handler.create(interaction, name)

        # @self.tree.command(name = 'add', description = 'Add a song to a playlist.')
        # async def add_callback(interaction: discord.Interaction, number: int = 0) -> None:
        #     await self.command_handler.add(interaction, number)

        # BOT LISTENERS #

        @self.event
        async def on_voice_state_update(member, before, after):
            if member != self.user or before.channel == after.channel:
                return

            guild_id = member.guild.id
            guild_bot = self.guild_bots[guild_id]

            if before.channel and not after.channel:
                print(f'{c_event("DISCONNECTED")} in {c_guild(guild_id)}')
                await guild_bot.dc(disconnect = False)
            elif not before.channel and after.channel:
                print(f'{c_event("CONNECTED")} in {c_guild(guild_id)}')
                pass
            else:
                print(f'{c_event("MOVED")} in {c_guild(guild_id)}')
                await guild_bot.dc(disconnect = False)

        @self.event
        async def on_guild_join(guild):
            self.guild_bots[guild.id] = await GuildBot(guild)
            # todo: delete GuildBot and database entry when leaving guild

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


    def get_bot(self, interaction):
        return self.guild_bots[interaction.guild.id]


if __name__ == '__main__':
    """Main is the beginning of everything."""
    bot = MainBot()
    bot.run(token)
