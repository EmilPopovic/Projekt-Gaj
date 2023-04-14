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

from components import (
    HelpCog,
    CommandHandler,
    GuildBot,
    CommandButtons,
    ListManager,
    SongGenerator,
    SongQueue
)
from utils import (
    Database,
    PermissionsCheck,
    InteractionResponder as Responder,
    SqlException,
    ForbiddenQueryError
)
from utils.colors import c_err, c_guild, c_event, c_login, c_user
from settings import TOKEN


class MainBot(commands.AutoShardedBot):
    """
    The MainBot class is the main Bot client of the application.

    This class contains:
    > callback functions for all application commands
    > autocomplete functions for certain application commands
    > discord event listeners
    > initialisation code for bot, GuildBots and the database connection
    """

    def __init__(self, intents=discord.Intents.all()):
        super().__init__(command_prefix='!', intents=intents)
        GuildBot.bot = self
        self.guild_bots = {}

        self.database = database

        GuildBot.db = self.database
        PermissionsCheck.db = self.database
        SongGenerator.db = self.database

        list_manager = ListManager(self, database)
        command_handler = CommandHandler(self)

        SongQueue.Manager = list_manager

        self.Manager = list_manager
        self.Handler = command_handler

        CommandButtons.command_handler = self.Handler
        CommandButtons.bot = self

        # SLASH COMMAND CALLBACK FUNCTIONS

        @self.tree.command(name='help', description='Get help using the bot.')
        async def help_callback(interaction: discord.Interaction):
            await HelpCog.send_message(interaction)

        @self.tree.command(name='ping', description='Pings Shteff.')
        async def ping_callback(interaction: discord.Interaction):
            latency_ms = round(self.latency * 1000)
            await Responder.send(f'Pong! My latency is {latency_ms} ms.', interaction)

        @self.tree.command(name='join', description='Conjures the bot in your auditory dimension.')
        async def join_callback(interaction: discord.Interaction):
            await self.Handler.join(interaction)

        @self.tree.command(name='play', description='Adds a song/list to queue.')
        @app_commands.describe(song= 'The name or link of song/list.', place= 'Where to insert song.')
        async def play_callback(interaction: discord.Interaction, song: str, place: int = 1):
            await self.Handler.join(interaction, send_response = False)
            await self.Handler.play(interaction, song, place)

        @self.tree.command(name='file-play', description='Add a song from a file to queue.')
        @app_commands.describe(file= 'Audio file to play.', place= 'Where to insert song.')
        async def file_play_callback(interaction: discord.Interaction, file: discord.Attachment, place: int = None):
            await self.Handler.join(interaction, send_response = False)
            await self.Handler.file_play(interaction, file, place)

        @self.tree.command(name='connect', description='Connect Shteff to your voice channel.')
        async def connect_callback(interaction: discord.Interaction):
            await self.Handler.connect(interaction)

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
        @app_commands.describe(
            first='Index of song you want to swap with second.',
            second='Index of song you want to swap with first.'
        )
        async def swap_callback(interaction: discord.Interaction, first: int, second: int):
            await self.Handler.swap(interaction, first, second)

        @self.tree.command(name='pause', description='Pauses or unpauses playing.')
        async def pause_callback(interaction: discord.Interaction):
            await self.Handler.pause(interaction)

        @self.tree.command(name='remove', description='Removes song with given index from the queue.')
        async def remove_callback(interaction: discord.Interaction, number: int):
            await self.Handler.remove(interaction, number)

        @self.tree.command(name='goto', description='Jumps to the song with given index, removes skipped songs.')
        async def goto_callback(interaction: discord.Interaction, number: int):
            await self.Handler.goto(interaction, number)

        @self.tree.command(name='create', description='Create a personal playlist.')
        @app_commands.describe(playlist= 'Name of the playlist.')
        async def create_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.create_playlist(interaction, playlist, 'user')

        @self.tree.command(name='server-create', description='Create a server playlist.')
        @app_commands.describe(playlist= 'Name of the playlist.')
        @app_commands.check(PermissionsCheck.interaction_has_permissions)
        async def server_create_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.create_playlist(interaction, playlist, 'server')

        @self.tree.command(name='delete', description='Deletes a personal playlist.')
        @app_commands.describe(playlist= 'The name of the playlist to delete.')
        async def delete_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.delete_playlist(interaction, playlist, 'user')

        @self.tree.command(name='server-delete', description='Deletes a server playlist.')
        @app_commands.describe(playlist= 'The name of the playlist to delete.')
        @app_commands.check(PermissionsCheck.interaction_has_permissions)
        async def server_delete_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.delete_playlist(interaction, playlist, 'server')

        @self.tree.command(name='add', description='Add currently playing song to personal playlist.')
        @app_commands.describe(
            playlist='The playlist the song will be added to.',
            song='The song or third party playlist you want to add to your playlist.'
        )
        async def add_callback(interaction: discord.Interaction, playlist: str, song: str = ''):
            await self.Manager.add_to_playlist(interaction, playlist, song, 'user')

        @self.tree.command(name='server-add', description='Add currently playing song to server playlist.')
        @app_commands.describe(
            playlist= 'The playlist the song will be added to.',
            song='The song or third party playlist you want to add to the server playlist.'
        )
        @app_commands.check(PermissionsCheck.interaction_has_permissions)
        async def server_add_callback(interaction: discord.Interaction,
                                      playlist: str,
                                      song: str = ''):
            await self.Manager.add_to_playlist(interaction, playlist, song, 'server')

        @self.tree.command(
            name='obliterate',
            description='Obliterates a song, removing it completely from existence (or the playlist at least).'
        )
        @app_commands.describe(
            playlist='The name of the playlist where you want the obliteration to take place.',
            song='The name of the song you want to obliterate.'
        )
        async def obliterate_callback(interaction: discord.Interaction, playlist: str, song: str):
            await self.Manager.remove_from_playlist(interaction, playlist, song, 'user')

        @self.tree.command(
            name='server-obliterate',
            description='Obliterates a song, removing it completely from existence (or the playlist at least).'
        )
        @app_commands.describe(
            playlist='The name of the playlist where you want the obliteration to take place.',
            song='The name of the song you want to obliterate.'
        )
        @app_commands.check(PermissionsCheck.interaction_has_permissions)
        async def server_obliterate_callback(interaction: discord.Interaction, playlist: str, song: str):
            await self.Manager.remove_from_playlist(interaction, playlist, song, 'server')

        @self.tree.command(name='catalogue', description='Lists out your vast catalogue of playlists.')
        async def catalogue(interaction: discord.Interaction):
            await self.Manager.show_playlists(interaction, 'user')

        @self.tree.command(name='server-catalogue', description='Lists out your server\'s vast catalogue of playlists.')
        async def server_catalogue_callback(interaction: discord.Interaction):
            await self.Manager.show_playlists(interaction, 'server')

        @self.tree.command(
            name='manifest',
            description='Forces the songs from your list to take a corporeal form and appear before your eyes.'
        )
        @app_commands.describe(playlist= 'Name of the playlist.')
        async def manifest_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.show_playlist_songs(interaction, playlist, 'user')

        @self.tree.command(
            name='server-manifest',
            description='Forces the songs from your server list to take a corporeal form and appear before your eyes.'
        )
        @app_commands.describe(playlist= 'Name of the playlist.')
        async def server_manifest_callback(interaction: discord.Interaction, playlist: str):
            await self.Manager.show_playlist_songs(interaction, playlist, 'server')

        @self.tree.command(name='playlist', description='Adds songs from selected playlist to the queue.')
        @app_commands.describe(
            playlist='The playlist you want to add to the queue.',
            song='The song to play.',
            place = 'Where to insert the playlist.'
        )
        async def playlist_callback(
                interaction: discord.Interaction,
                playlist: str,
                song: str = '',
                place: int = 1
        ) -> None:
            await self.Handler.join(interaction, send_response = False)
            await self.Handler.playlist_play(interaction, song, playlist, 'user', place)

        @self.tree.command(name='server-playlist', description='Adds songs from selected playlist to the queue.')
        @app_commands.describe(
            playlist='The playlist you want to add to the queue.',
            song='The song to play.',
            place ='Where to insert the playlist.'
        )
        async def server_playlist_callback(
                interaction: discord.Interaction,
                playlist: str,
                song: str = '',
                place: int = 1
        ) -> None:
            await self.Handler.join(interaction, send_response = False)
            await self.Handler.playlist_play(interaction, song, playlist, 'server', place)

        # COMMAND PERMISSION ERRORS

        @server_create_callback.error
        @server_add_callback.error
        @server_delete_callback.error
        @server_obliterate_callback.error
        async def server_add_callback_error(interaction: discord.Interaction, _):
            print(_)
            msg = 'You don\'t seem to be an admin or a dj, so you cant use this command.'
            await Responder.send(msg, interaction, fail=True)

        # AUTOCOMPLETE FUNCTIONS

        @delete_callback.autocomplete(name='playlist')
        @add_callback.autocomplete(name='playlist')
        @obliterate_callback.autocomplete(name='playlist')
        @manifest_callback.autocomplete(name='playlist')
        @server_playlist_callback.autocomplete(name='playlist')
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

        def make_choices(current: str, choices: list[str]) -> list[app_commands.Choice]:
            lst = []
            for choice in choices:
                if current.lower() in choice.lower():
                    choice_obj = app_commands.Choice(name=choice, value=choice)
                    lst.append(choice_obj)
            return lst

        def lists_options(interaction: discord.Interaction, scope: Literal['user', 'server']) -> list[str]:
            try:
                if scope == 'user':
                    playlists = self.database.get_user_lists(interaction.user.id)
                else:
                    playlists = self.database.get_server_lists(interaction.guild.id)
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
                if scope == 'user':
                    songs = self.database.get_songs_from_list(interaction.user.id, playlist_name)
                else:
                    songs = self.database.get_songs_from_list(interaction.guild.id, playlist_name)
            except SqlException:
                return []
            except ForbiddenQueryError:
                return []
            else:
                return [song.song_name for song in songs]

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
                await guild_bot.disconnect(disconnect=False)

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

        await self.check_for_update_request()

    async def check_for_update_request(self) -> None:
        while True:
            await asyncio.sleep(1)

            for player in self.guild_bots.values():
                await player.guild_bot.update_message()

    def get_bot_from_interaction(self, interaction: discord.Interaction) -> GuildBot:
        return self.guild_bots[interaction.guild.id]

    def get_bot_from_id(self, guild_id: int) -> GuildBot:
        return self.guild_bots[guild_id]

    def get_bot_from_guild(self, guild: discord.Guild) -> GuildBot:
        return self.guild_bots[guild.id]


if __name__ == '__main__':
    """Main is the beginning of everything."""
    database = Database()
    bot = MainBot()
    bot.run(TOKEN)
