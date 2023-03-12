"""
Shteff  Copyright (C) 2023 Mjolnir2425, OvajStup

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

from components import HelpCog, CommandHandler, GuildBot, CommandButtons, ListManager
from utils import Database, PermissionsCheck, InteractionResponder as Responder, SqlException
from utils.colors import c_err, c_guild, c_event, c_login, c_user


with open('secrets.json', 'r') as f:
    data = json.load(f)

token = data['discord']['discord_token']


class MainBot(commands.AutoShardedBot):
    """
    This is the MainBot docstring, please finish it.
    """

    # TODO: docstring
    def __init__(self, intents=discord.Intents.all()):
        super().__init__(command_prefix='!', intents=intents)
        GuildBot.bot = self
        self.guild_bots = {}

        self.database = Database()

        GuildBot.db = self.database
        PermissionsCheck.db = self.database

        self.Manager = ListManager(self, self.database)
        self.Handler = CommandHandler(self)

        CommandButtons.command_handler = self.Handler
        CommandButtons.bot = self

        # BOT COMMANDS #

        @self.tree.command(name='help', description='Get help using the bot.')
        async def help_callback(interaction: discord.Interaction):
            await HelpCog.send_message(interaction)

        @self.tree.command(name='ping', description='Pings Shteff.')
        async def ping_callback(interaction: discord.Interaction):
            latency_ms = round(self.latency * 1000)
            await Responder.send(f'Pong! My latency is {latency_ms} ms.', interaction)

        @self.tree.command(name='play', description='Adds a song/list to queue.')
        @app_commands.describe(song='The name or link of song/list.', place='Where to insert song.')
        async def play_callback(interaction: discord.Interaction, song: str, place: int = None):
            await self.Handler.play(interaction, song, place)

        @self.tree.command(name='file-play', description='Add a song from a file to queue.')
        @app_commands.describe(file='Audio file to play.', place='Where to insert song.')
        async def file_play_callback(interaction: discord.Interaction, file: discord.Attachment, place: int = None):
            await self.Handler.file_play(interaction, file, place)

        @self.tree.command(name='skip', description='Skips to the next queued song.')
        async def skip_callback(interaction: discord.Interaction):
            await self.Handler.skip(interaction)

        @self.tree.command(name='loop', description='Loops queue or single song.')
        async def loop_callback(interaction: discord.Interaction):
            await self.Handler.loop(interaction)

        @self.tree.command(name='clear', description='Clears queue and history, stops playing.')
        async def clear_callback(interaction: discord.Interaction):
            await self.Handler.clear(interaction)

        @self.tree.command(name='dc', description='Disconnects bot from voice channel.')
        async def disconnect_callback(interaction: discord.Interaction):
            await self.Handler.disconnect(interaction)

        @self.tree.command(name='back', description='Skips current song and plays previous.')
        async def back_callback(interaction: discord.Interaction):
            await self.Handler.previous(interaction)

        @self.tree.command(name='queue', description='Toggles queue display type (short/long).')
        async def queue_callback(interaction: discord.Interaction):
            await self.Handler.queue(interaction)

        @self.tree.command(name='history', description='Toggles history display type (show/hide).')
        async def history_callback(interaction: discord.Interaction):
            await self.Handler.history(interaction)

        @self.tree.command(name='lyrics', description='Toggles lyrics display (show/hide).')
        async def lyrics_callback(interaction: discord.Interaction):
            await self.Handler.lyrics(interaction)

        @self.tree.command(name='shuffle', description='Toggles queue shuffle.')
        async def shuffle_callback(interaction: discord.Interaction):
            await self.Handler.shuffle(interaction)

        @self.tree.command(name='swap', description='Swap places of queued songs.')
        @app_commands.describe(song1='Place of first song in queue.', song2='Place of second song in the queue.')
        async def swap_callback(interaction: discord.Interaction, song1: int, song2: int):
            await self.Handler.swap(interaction, song1, song2)

        @self.tree.command(name='pause', description='Pauses or unpauses playing.')
        async def pause_callback(interaction: discord.Interaction):
            await self.Handler.pause(interaction)

        @self.tree.command(name='remove', description='Removes song with given index from the queue.')
        async def remove_callback(interaction: discord.Interaction, number: int):
            await self.Handler.remove(interaction, number)

        @self.tree.command(name='goto', description='Jumps to the song with given index, removes skipped songs.')
        async def goto_callback(interaction: discord.Interaction, number: int):
            await self.Handler.goto(interaction, number)

        @self.tree.command(name='add', description='Add currently playing song to personal playlist.')
        @app_commands.describe(playlist='The playlist the song will be added to.')
        async def add_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.add(interaction, playlist)

        @add_callback.autocomplete
        async def personal_lists_autocomplete(interaction: discord.Interaction, current: str):
            try:
                user_playlists = self.database.get_user_lists(interaction.user.id)
            except SqlException:
                return []

            choices = []
            for playlist in user_playlists:
                if current.lower() in playlist.lower():
                    choice = app_commands.Choice.name(name=playlist, value=playlist)
                    choices.append(choice)
            return choices

        @self.tree.command(name='server-add', description='Add currently playing song to server playlist.')
        @app_commands.check(PermissionsCheck.interaction_has_permissions)
        @app_commands.describe(playlist='The playlist the song will be added to.')
        async def server_add_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.server_add(interaction, playlist)

        @server_add_callback.autocomplete
        async def server_lists_autocomplete(interaction: discord.Interaction, current: str):
            try:
                server_playlists = self.database.get_server_lists(interaction.guild.id)
            except SqlException:
                return []

            choices = []
            for playlist in server_playlists:
                if current.lower() in playlist.lower():
                    choice = app_commands.Choice.name(name=playlist, value=playlist)
                    choices.append(choice)
            return choices

        @server_add_callback.error
        async def server_add_callback_error(interaction: discord.Interaction, _):
            await Responder.send('Not allowed!', interaction, fail=True)

        @self.tree.command(name='create', description='Create a personal playlist.')
        @app_commands.describe(name='Name of the playlist.')
        async def create_callback(interaction: discord.Interaction, name: str):
            await self.Manager.create(interaction, name)

        @self.tree.command(name='server-create', description='Create a server playlist.')
        @app_commands.describe(name='Name of the playlist.')
        @app_commands.check(PermissionsCheck.interaction_has_permissions)
        async def server_create_callback(interaction: discord.Interaction, name: str):
            await self.Manager.server_create(interaction, name)

        @server_create_callback.error
        async def server_add_callback_error(interaction: discord.Interaction, _):
            await Responder.send('Not allowed!', interaction, fail=True)

        # BOT LISTENERS #

        @self.event
        async def on_voice_state_update(member, before, after):
            if member != self.user or before.channel == after.channel:
                return

            guild_id = member.guild.id
            guild_bot = self.guild_bots[guild_id]

            if before.channel and not after.channel:
                print(f'{c_event("DISCONNECTED")} in {c_guild(guild_id)}')
                await guild_bot.dc(disconnect=False)
            elif not before.channel and after.channel:
                print(f'{c_event("CONNECTED")} in {c_guild(guild_id)}')
                pass
            else:
                print(f'{c_event("MOVED")} in {c_guild(guild_id)}')
                await guild_bot.dc(disconnect=False)

        @self.event
        async def on_message(message):
            if message.author == self.user:
                return

            guild_id = message.guild.id
            guild_bot = self.guild_bots.get(guild_id, None)
            command_channel_id = guild_bot.command_channel_id

            if message.channel.id == command_channel_id:
                await message.delete()

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

        # create music cog for every guild bot is in
        for guild in self.guilds:
            self.guild_bots[guild.id] = await GuildBot(guild)

        print(f'{c_login()} as {self.user} with user id: {c_user(self.user.id)}')

    def get_bot_from_interaction(self, interaction):
        return self.guild_bots[interaction.guild.id]

    def get_bot_from_id(self, guild_id):
        return self.guild_bots[guild_id]

    def get_bot_from_guild(self, guild):
        return self.guild_bots[guild.id]


if __name__ == '__main__':
    """Main is the beginning of everything."""
    bot = MainBot()
    bot.run(token)
