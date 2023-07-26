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
import discord
import asyncio
from typing import Literal
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from components import (
    Help,
    CommandHandler,
    GuildBot,
    CommandButtons,
    ListManager,
    SongGenerator,
    SongQueue,
    UserListSelectModal,
    ServerListSelectModal
)
from utils import (
    Database,
    PermissionsCheck,
    InteractionResponder as Responder,
    SqlException,
    ForbiddenQueryError
)
from utils.colors import c_err, c_guild, c_event, c_login, c_user
from settings import TOKEN, COMMANDS, COMMAND_NAMES


class MainBot(commands.AutoShardedBot):
    """
    The MainBot class is the main Bot client of the application.

    This class contains:
    > callback functions for all application commands
    > autocomplete functions for certain application commands
    > discord event listeners
    > initialisation code for bot, GuildBots and the database connection
    """
    INCREMENT_TIME = 1
    DB_REFRESH_TIME = 600

    def __init__(self, intents=discord.Intents.all()):
        super().__init__(command_prefix='!', intents=intents)
        GuildBot.bot = self
        self.guild_bots = {}

        self.commands_synced = False

        list_manager = ListManager(self)
        command_handler = CommandHandler(self)

        SongQueue.Manager = list_manager
        UserListSelectModal.manager = list_manager
        ServerListSelectModal.manager = list_manager

        self.Manager = list_manager
        self.Handler = command_handler

        CommandButtons.command_handler = self.Handler
        CommandButtons.bot = self

        Responder.bot = self

        self.run_timer = 0

        self.database = None
        db = self.make_db(on_error=sys.exit)
        self.set_db(db)

        # SLASH COMMAND CALLBACK FUNCTIONS

        @self.tree.command(name='reset', description=COMMANDS['debug']['reset']['short_description'])
        async def reset_callback(interaction: discord.Interaction):
            guild = interaction.guild
            self.guild_bots[guild.id] = await GuildBot(guild)
            await Responder.send('Server reset.', interaction)

        @self.tree.command(name='refresh', description=COMMANDS['debug']['refresh']['short_description'])
        async def refresh_callback(interation: discord.Interaction):
            guild_bot = self.get_bot_from_interaction(interation)
            await guild_bot.update_message()

        @self.tree.command(name='help', description=COMMANDS['debug']['help']['short_description'])
        @app_commands.describe(command='The command you want described.')
        async def help_callback(interaction: discord.Interaction, command: str = None):
            await Help.start_help_flow(interaction, command)

        @self.tree.command(name='ping', description=COMMANDS['debug']['ping']['short_description'])
        async def ping_callback(interaction: discord.Interaction):
            latency_ms = round(self.latency * 1000)
            await Responder.send(f'Pong! My latency is {latency_ms} ms.', interaction)

        @self.tree.command(name='join', description=COMMANDS['player']['join']['short_description'])
        async def join_callback(interaction: discord.Interaction):
            await self.Handler.join(interaction)

        @self.tree.command(name='play', description=COMMANDS['player']['play']['short_description'])
        @app_commands.describe(song='The name or link of song/list.', place='Where to insert song.')
        async def play_callback(interaction: discord.Interaction, song: str, place: int = 1):
            await self.Handler.join(interaction, send_response=False)
            await self.Handler.play(interaction, song, place)

        @self.tree.command(name='file-play', description=COMMANDS['player']['file-play']['short_description'])
        @app_commands.describe(file='Audio file to play.', place='Where to insert song.')
        async def file_play_callback(interaction: discord.Interaction, file: discord.Attachment, place: int = None):
            await self.Handler.join(interaction, send_response=False)
            await self.Handler.file_play(interaction, file, place)

        @self.tree.command(name='skip', description=COMMANDS['player']['skip']['short_description'])
        async def skip_callback(interaction: discord.Interaction):
            await self.Handler.skip(interaction)

        @self.tree.command(name='loop', description=COMMANDS['player']['loop']['short_description'])
        async def loop_callback(interaction: discord.Interaction):
            await self.Handler.loop(interaction)

        @self.tree.command(name='clear', description=COMMANDS['player']['clear']['short_description'])
        async def clear_callback(interaction: discord.Interaction):
            await self.Handler.clear(interaction)

        @self.tree.command(name='dc', description=COMMANDS['player']['dc']['short_description'])
        async def disconnect_callback(interaction: discord.Interaction):
            await self.Handler.disconnect(interaction)

        @self.tree.command(name='back', description=COMMANDS['player']['back']['short_description'])
        async def back_callback(interaction: discord.Interaction):
            await self.Handler.previous(interaction)

        @self.tree.command(name='lyrics', description=COMMANDS['player']['lyrics']['short_description'])
        async def lyrics_callback(interaction: discord.Interaction):
            await self.Handler.lyrics(interaction)

        @self.tree.command(name='shuffle', description=COMMANDS['player']['shuffle']['short_description'])
        async def shuffle_callback(interaction: discord.Interaction):
            await self.Handler.shuffle(interaction)

        @self.tree.command(name='swap', description=COMMANDS['player']['swap']['short_description'])
        @app_commands.describe(
            first='Position of song you want to swap with second.',
            second='Position of song you want to swap with first.'
        )
        async def swap_callback(interaction: discord.Interaction, first: int, second: int):
            await self.Handler.swap(interaction, first, second)

        @self.tree.command(name='pause', description=COMMANDS['player']['pause']['short_description'])
        async def pause_callback(interaction: discord.Interaction):
            await self.Handler.pause(interaction)

        @self.tree.command(name='remove', description=COMMANDS['player']['remove']['short_description'])
        @app_commands.describe(place='Position of the song to remove.')
        async def remove_callback(interaction: discord.Interaction, place: int):
            await self.Handler.remove(interaction, place)

        @self.tree.command(name='goto', description=COMMANDS['player']['goto']['short_description'])
        @app_commands.describe(place='Position of the song to go to.')
        async def goto_callback(interaction: discord.Interaction, place: int):
            await self.Handler.goto(interaction, place)

        @self.tree.command(name='create', description=COMMANDS['playlist']['create']['short_description'])
        @app_commands.describe(playlist='Name of the playlist.')
        async def create_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.create_playlist(interaction, playlist, 'user')

        @self.tree.command(name='server-create', description=COMMANDS['playlist']['server-create']['short_description'])
        @app_commands.describe(playlist='Name of the playlist.')
        @app_commands.check(PermissionsCheck.interaction_has_permissions)
        async def server_create_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.create_playlist(interaction, playlist, 'server')

        @self.tree.command(name='delete', description=COMMANDS['playlist']['delete']['short_description'])
        @app_commands.describe(playlist='The name of the playlist to delete.')
        async def delete_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.delete_playlist(interaction, playlist, 'user')

        @self.tree.command(name='server-delete', description=COMMANDS['playlist']['server-delete']['short_description'])
        @app_commands.describe(playlist='The name of the playlist to delete.')
        @app_commands.check(PermissionsCheck.interaction_has_permissions)
        async def server_delete_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.delete_playlist(interaction, playlist, 'server')

        @self.tree.command(name='add', description=COMMANDS['playlist']['add']['short_description'])
        @app_commands.describe(
            playlist='The playlist the song will be added to.',
            song='The song or third party playlist you want to add to your playlist.'
        )
        async def add_callback(interaction: discord.Interaction, playlist: str, song: str = ''):
            await interaction.response.defer(ephemeral=True)
            await self.Manager.add_to_playlist(interaction, playlist, song, 'user')

        @self.tree.command(name='server-add', description=COMMANDS['playlist']['server-add']['short_description'])
        @app_commands.describe(
            playlist='The playlist the song will be added to.',
            song='The song or third party playlist you want to add to the server playlist.'
        )
        @app_commands.check(PermissionsCheck.interaction_has_permissions)
        async def server_add_callback(interaction: discord.Interaction, playlist: str, song: str = ''):
            await self.Manager.add_to_playlist(interaction, playlist, song, 'server')

        @self.tree.command(name='obliterate', description=COMMANDS['playlist']['obliterate']['short_description'])
        @app_commands.describe(
            playlist='The name of the playlist where you want the obliteration to take place.',
            song='The name of the song you want to obliterate.'
        )
        async def obliterate_callback(interaction: discord.Interaction, playlist: str, song: str):
            await self.Manager.remove_from_playlist(interaction, playlist, song, 'user')

        @self.tree.command(name='server-obliterate', description=COMMANDS['playlist']['server-obliterate']['short_description'])
        @app_commands.describe(
            playlist='The name of the playlist where you want the obliteration to take place.',
            song='The name of the song you want to obliterate.'
        )
        @app_commands.check(PermissionsCheck.interaction_has_permissions)
        async def server_obliterate_callback(interaction: discord.Interaction, playlist: str, song: str):
            await self.Manager.remove_from_playlist(interaction, playlist, song, 'server')

        @self.tree.command(name='catalogue', description=COMMANDS['playlist']['catalogue']['short_description'])
        async def catalogue(interaction: discord.Interaction):
            await self.Manager.show_playlists(interaction, 'user')

        @self.tree.command(name='server-catalogue', description=COMMANDS['playlist']['server-catalogue']['short_description'])
        async def server_catalogue_callback(interaction: discord.Interaction):
            await self.Manager.show_playlists(interaction, 'server')

        @self.tree.command(name='manifest', description=COMMANDS['playlist']['manifest']['short_description'])
        @app_commands.describe(playlist='Name of the playlist.')
        async def manifest_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.show_playlist_songs(interaction, playlist, 'user')

        @self.tree.command(name='server-manifest', description=COMMANDS['playlist']['server-manifest']['short_description'])
        @app_commands.describe(playlist='Name of the playlist.')
        async def server_manifest_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.show_playlist_songs(interaction, playlist, 'server')

        @self.tree.command(name='playlist', description=COMMANDS['playlist']['playlist']['short_description'])
        @app_commands.describe(
            playlist='The playlist you want to add to the queue.',
            song='The song to play.',
            place='Where to insert the playlist.'
        )
        async def playlist_callback(
                interaction: discord.Interaction,
                playlist: str,
                song: str = '',
                place: int = 1
        ) -> None:
            await self.Handler.join(interaction, send_response=False)
            await self.Handler.playlist_play(interaction, song, playlist, 'user', place)

        @self.tree.command(name='server-playlist', description=COMMANDS['playlist']['server-playlist']['short_description'])
        @app_commands.describe(
            playlist='The playlist you want to add to the queue.',
            song='The song to play.',
            place='Where to insert the playlist.'
        )
        async def server_playlist_callback(
                interaction: discord.Interaction,
                playlist: str,
                song: str = '',
                place: int = 1
        ) -> None:
            await self.Handler.join(interaction, send_response=False)
            await self.Handler.playlist_play(interaction, song, playlist, 'server', place)

        # COMMAND PERMISSION ERRORS

        @server_create_callback.error
        @server_add_callback.error
        @server_delete_callback.error
        @server_obliterate_callback.error
        async def no_permission_error(interaction: discord.Interaction, _):
            msg = 'You don\'t seem to be an admin or a dj, so you cant use this command.'
            await Responder.send(msg, interaction, fail=True)

        # AUTOCOMPLETE FUNCTIONS

        @help_callback.autocomplete(name='command')
        async def commands_list_autocomplete(
                _: discord.Interaction,
                current: str
        ) -> list[app_commands.Choice]:
            options: list[str] = COMMAND_NAMES + ['buttons']
            choices: list[app_commands.Choice] = make_choices(current, options)
            return choices

        @delete_callback.autocomplete(name='playlist')
        @add_callback.autocomplete(name='playlist')
        @obliterate_callback.autocomplete(name='playlist')
        @manifest_callback.autocomplete(name='playlist')
        @playlist_callback.autocomplete(name='playlist')
        async def user_lists_autocomplete(
                interaction: discord.Interaction,
                current: str
        ) -> list[app_commands.Choice]:
            options: list[str] = lists_options(interaction, 'user')
            choices: list[app_commands.Choice] = make_choices(current, options)
            return choices

        @server_delete_callback.autocomplete(name='playlist')
        @server_add_callback.autocomplete(name='playlist')
        @server_obliterate_callback.autocomplete(name='playlist')
        @server_manifest_callback.autocomplete(name='playlist')
        @server_playlist_callback.autocomplete(name='playlist')
        async def server_lists_autocomplete(
                interaction: discord.Interaction,
                current: str
        ) -> list[app_commands.Choice]:
            options: list[str] = lists_options(interaction, 'server')
            choices: list[app_commands.Choice] = make_choices(current, options)
            return choices

        @obliterate_callback.autocomplete(name='song')
        @playlist_callback.autocomplete(name='song')
        async def user_list_songs_autocomplete(
                interaction: discord.Interaction,
                current: str
        ) -> list[app_commands.Choice]:
            options: list[str] = list_songs_options(interaction, 'user')
            choices: list[app_commands.Choice] = make_choices(current, options)
            return choices

        @server_obliterate_callback.autocomplete(name='song')
        @server_playlist_callback.autocomplete(name='song')
        async def server_list_songs_autocomplete(
                interaction: discord.Interaction,
                current: str
        ) -> list[app_commands.Choice]:
            options: list[str] = list_songs_options(interaction, 'server')
            choices: list[app_commands.Choice] = make_choices(current, options)
            return choices

        def make_choices(current: str, choices: list[str]) -> list[app_commands.Choice]:
            lst = []
            for choice in choices:
                if current.lower() in choice.lower():
                    choice_obj = app_commands.Choice(name=choice, value=choice)
                    lst.append(choice_obj)
            return lst

        def lists_options(interaction: discord.Interaction, scope: Literal['user', 'server']) -> list[str]:
            try:
                owner_id: int = interaction.user.id if scope == 'user' else interaction.guild.id

                playlists = self.database.get_lists(owner_id, scope)
            except SqlException:
                return []
            except ForbiddenQueryError:
                return []
            else:
                return playlists

        def list_songs_options(
                interaction: discord.Interaction,
                scope: Literal['user', 'server']
        ) -> list[str]:
            """
            Function returns the list of song names that are contained in a playlist with a certain name.

            The name of the playlist is taken from the first input parameter of an application command.

            Parameters:
                interaction (discord.Interaction): interaction object of the application command being autocompleted
                scope (str 'user' or 'server'): determines if we are searching in a user or a server playlist

            Returns:
                list: the list of song names of the specified playlist
            """
            playlist_name = interaction.data['options'][0]['value']
            try:
                owner_id: int = interaction.user.id if scope == 'user' else interaction.guild.id

                songs = self.database.get_songs_from_list(owner_id, playlist_name, scope)
            except SqlException:
                return []
            except ForbiddenQueryError:
                return []
            else:
                return [song.name for song in songs]

        # BOT LISTENERS

        @self.event
        async def on_voice_state_update(member, before, after) -> None:
            if member != self.user or before.channel == after.channel:
                return

            guild_id = member.guild.id
            guild_bot = self.guild_bots[guild_id]

            if before.channel and not after.channel:
                print(f'{c_event("DISCONNECTED")} in {c_guild(guild_id)}')
                await guild_bot.disconnect(disconnect=False)
            elif not before.channel and after.channel:
                print(f'{c_event("CONNECTED")} in {c_guild(guild_id)}')
                pass
            else:
                print(f'{c_event("MOVED")} in {c_guild(guild_id)}')
                await guild_bot.disconnect(disconnect=True)

        @self.event
        async def on_message(message) -> None:
            if message.author == self.user:
                return

            guild_id = message.guild.id
            guild_bot = self.guild_bots.get(guild_id, None)
            command_channel_id = guild_bot.command_channel_id

            if message.channel.id == command_channel_id:
                await message.delete()

        @self.event
        async def on_guild_join(guild) -> None:
            self.guild_bots[guild.id] = await GuildBot(guild)

    async def sync_commands(self):
        print(f'{c_event("SYNCING COMMANDS")}')

        try:
            synced = await self.tree.sync()
        except Exception as e:
            print(f'{c_err()} failed to sync command(s)\n{c_event("EXITING")}, Exception:\n{e}')
            sys.exit()

        self.commands_synced = True
        print(f'{c_event("SYNCED")} {len(synced)} command(s)')

    async def on_ready(self) -> None:
        """
        Runs on bot login.
        """
        # sync commands
        if not self.commands_synced:
            await self.sync_commands()

        self.remove_command('help')

        # create music cog for every guild bot is in
        for guild in self.guilds:
            self.guild_bots[guild.id] = await GuildBot(guild)

        print(f'{c_login()} as {self.user} with user id: {c_user(self.user.id)}')

        await self.start_run_timer()

    async def start_run_timer(self) -> None:
        while True:
            start_time = datetime.now()

            # refresh messages
            for player in self.guild_bots.values():
                if player.needs_refreshing:
                    await player.guild_bot.update_message()

            # check for database timeout
            if self.run_timer % self.DB_REFRESH_TIME < self.INCREMENT_TIME:
                print(f'{c_event("DB REFRESH")}')
                try:
                    self.database.refresh_interactive_timeout()
                except SqlException:
                    db = self.make_db()
                    self.set_db(db)

            self.run_timer += self.INCREMENT_TIME
            end_time = datetime.now()
            delta = end_time - start_time
            time_to_wait = self.INCREMENT_TIME - delta.seconds
            await asyncio.sleep(time_to_wait)

    @staticmethod
    def make_db(on_error=None):
        print(f'{c_event("DB RESET")}')
        try:
            db = Database()
        except SqlException:
            print(f'{c_err()} cannot connect to database.')
            db = None
            _ = None if on_error is None else on_error()
        return db

    def set_db(self, db):
        self.database = db
        GuildBot.db = db
        PermissionsCheck.db = db
        SongGenerator.db = db
        self.Manager.db = db

    def get_bot_from_interaction(self, interaction: discord.Interaction) -> GuildBot:
        return self.guild_bots[interaction.guild.id]

    def get_bot_from_id(self, guild_id: int) -> GuildBot:
        return self.guild_bots[guild_id]

    def get_bot_from_guild(self, guild: discord.Guild) -> GuildBot:
        return self.guild_bots[guild.id]


if __name__ == '__main__':
    """Main is the beginning of everything."""
    bot = MainBot()
    bot.run(TOKEN)
