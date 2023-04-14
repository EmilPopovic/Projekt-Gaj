import threading

import discord
import typing

from utils import (
    InteractionResponder as Responder,
    SqlSong,
    SqlException,
    ForbiddenQueryError,
    c_event,
    c_user,
    c_guild,
    Database
)
from .song_generator import SongGenerator


class ListManager:
    def __init__(self, main_bot, db):
        self.main_bot = main_bot
        self.db: Database = db

    def get_current_song(self, interaction) -> SongGenerator | None:
        """
        This function returns the currently playing song of the guild bot from the specified interation.

        Parameters:
            interaction (discord.Interaction): The interaction from which the bot's current song is being retrieved.

        Returns:
            If the current song is a valid and playable track, the function returns the current SongGenerator object.
            If no song is currently playing or the current song is invalid or unplayable, the function returns None.
        """
        guild_bot = self.main_bot.get_bot_from_interaction(interaction)

        song = guild_bot.queue.current

        if song is None or not song.is_good or song.from_file:
            return None
        return song

    @staticmethod
    def worker(lst, n, sql_song, interaction):
        song = SongGenerator(sql_song, interaction)
        lst[n] = song

    async def songs_from_playlist(
            self,
            interaction: discord.Interaction,
            playlist_name: str,
            scope: typing.Literal['user', 'server'],
            song_name: str = ''
    ) -> list[SongGenerator] | None:
        list_exists: bool | None = await self.list_exists(interaction, playlist_name, scope)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        try:
            list_songs: list[SqlSong]
            if scope == 'user':
                list_songs = self.db.get_songs_from_list(interaction.user.id, playlist_name)
            else:
                list_songs = self.db.get_songs_from_list(interaction.guild.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        except ForbiddenQueryError:
            await Responder.send('Forbidden list name.', interaction, fail=True)
            return
        else:
            if song_name:
                list_songs = [song for song in list_songs if song.song_name == song_name]


            song_objs = [None] * len(list_songs)
            threads = []

            for i, sql_song in enumerate(list_songs):
                t = threading.Thread(target = self.worker, args = (song_objs, i, sql_song, interaction))
                threads.append(t)
                t.start()

            for thread in threads:
                thread.join()

        return song_objs

    async def list_exists(
            self,
            interaction: discord.Interaction,
            playlist_name: str,
            scope: typing.Literal['user', 'server']
    ) -> None | bool:
        """
        This asynchronous function checks if a given playlist_name exists
        for the user or server id specified in the interaction.

        Parameters:
            interaction (discord.Interaction): The interaction from which the bot's current song is being retrieved.
            playlist_name (str): The name of the playlist to check for existence.
            scope ('user' or 'server'): Is the function called for a user or a server playlist.

        Returns:
            If the user list exists, the function returns True.
            If the user list does not exist, the function returns False.
            If an error occurs during the function execution, the function returns None.
        """
        try:
            lists: list[str]
            if scope == 'user':
                lists = self.db.get_user_lists(interaction.user.id)
            else:
                lists = self.db.get_server_lists(interaction.guild.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return None
        except ForbiddenQueryError:
            await Responder.send('Forbidden list name.', interaction, fail=True)
            return None
        else:
            if playlist_name in lists:
                return True
            return False

    async def add_to_playlist(
            self,
            interaction: discord.Interaction,
            playlist_name: str,
            query: str,
            scope: typing.Literal['user', 'server']
    ) -> None:
        """
        This asynchronous function adds a song to a user's or server's playlist. If the playlist does not exist,
        the function sends and error message.

        Parameters:
            interaction (discord.Interaction): The interaction from which the operation is being made.
            playlist_name (str): The name of the playlist to which the song is being added.
            query (str, optional): The query used to search for the song to add. If not provided, the function tries
                                   to add the current song being played.
            scope ('user' or 'server'): Is the function called for a user or a server playlist.

        Returns:
            This function does not return anything. If an error occurs during the function execution, the function
            sends an error message using the Responder.send() function.
        """
        # get the SongGenerator object of the song we want to add
        songs: list[SongGenerator]
        if query:
            songs = SongGenerator.get_songs(query, interaction, from_add_to_playlist = True)
        else:
            songs = [self.get_current_song(interaction)]
            if songs[0] is None:
                await Responder.send('No song to add.', interaction, fail=True)
                return

        songs = [song for song in songs if song.is_good]

        # check if the list we want to add the song to exists
        list_exists: bool | None = await self.list_exists(interaction, playlist_name, scope)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        # try to add the song to the list
        try:
            if scope == 'user':
                for song in songs:
                    self.db.add_to_user_playlist(song, interaction.user.id, playlist_name)
            else:
                for song in songs:
                    self.db.add_to_server_playlist(song, interaction.guild.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name.', interaction, fail=True)
        else:
            if len(songs) == 1:
                await Responder.send(f'Added song to "{playlist_name}".', interaction)
            else:
                await Responder.send(f'Added songs to "{playlist_name}".', interaction)

    async def create_playlist(
            self,
            interaction: discord.Interaction,
            playlist_name: str,
            scope: typing.Literal['user', 'server']
    ) -> None:
        """
        The function creates a new personal playlist for a user or server.

        Parameters:
            interaction (discord.Interaction): The interaction from which the operation is being made.
            playlist_name (str): The name of the playlist to be created.
            scope ('user' or 'server'): Is the function called for a user or a server playlist.

        Returns:
            This function doesn't return anything, but sends a success message to the user indicating that the
            playlist has been created. If an exception occurs during the creating of the playlist, the function
            sends an error message to the user. The max number of playlists allowed per user is 25.
        """
        # max number of personal playlists is 25 per user
        # playlist names have to be unique
        try:
            lists: list[str]
            if scope == 'user':
                lists = self.db.get_user_lists(interaction.user.id)
            else:
                lists = self.db.get_server_lists(interaction.guild.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            num_of_lists = len(lists)
            if num_of_lists >= 25:
                await Responder.send('Cannot have more than 25 lists.', interaction, fail=True)
                return
            elif playlist_name in lists:
                await Responder.send(f'Playlist named "{playlist_name}" already exists.', interaction, fail=True)
                return

        try:
            if scope == 'user':
                self.db.create_user_playlist(interaction.user.id, playlist_name)
            else:
                self.db.create_server_playlist(interaction.guild.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name', interaction, fail=True)
        else:
            if scope == 'user':
                print(f'{c_event("CREATED LIST")} for user {c_user(interaction.user.id)}')
            else:
                print(f'{c_event("CREATED LIST")} for guild {c_guild(interaction.guild.id)}')
            await Responder.send(f'Created playlist "{playlist_name}".', interaction)

    async def delete_playlist(
            self,
            interaction: discord.Interaction,
            playlist_name: str,
            scope: typing.Literal['user', 'server']
    ) -> None:
        """
        The function deletes a user or server playlist with a specified name.

        Parameters:
            interaction (discord.Interaction): The interaction from which the operation is being made.
            playlist_name (str): The name of the playlist to be deleted.
            scope ('user' or 'server'): Is the function called for a user or a server playlist.

        Returns:
            This function doesn't return anything, but sends a success message to the user indicating that the
            playlist has been deleted. If an exception occurs during the creating of the playlist, the function
            sends an error message to the user.
        """
        list_exists: bool | None = await self.list_exists(interaction, playlist_name, scope)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        try:
            if scope == 'user':
                self.db.delete_user_playlist(interaction.user.id, playlist_name)
            else:
                self.db.delete_server_playlist(interaction.guild.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            await Responder.send(f'Deleted playlist "{playlist_name}".', interaction)

    async def remove_from_playlist(
            self,
            interaction: discord.Interaction,
            playlist_name: str,
            song_name: str,
            scope: typing.Literal['user', 'server']
    ) -> None:
        """
        The function removes a song with a specified name from a user or server playlist.

        Parameters:
            interaction (discord.Interaction): The interaction from which the operation is being made.
            playlist_name (str): The name of the playlist of specified song.
            song_name (str): The name of the song to be removed.
            scope ('user' or 'server'): Is the function called for a user or a server playlist.

        Returns:
            This function doesn't return anything, but sends a success message to the user indicating that the
            song has been removed. If an exception occurs during the creating of the playlist, the function
            sends an error message to the user.
        """
        list_exists: bool | None = await self.list_exists(interaction, playlist_name, scope)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        try:
            list_songs: list[SqlSong]
            if scope == 'user':
                list_songs = self.db.get_songs_from_list(interaction.user.id, playlist_name)
            else:
                list_songs = self.db.get_songs_from_list(interaction.guild.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later', interaction, fail=True)
            return
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name.', interaction, fail=True)
            return
        else:
            song_names = [song.song_name for song in list_songs]
            if song_name not in song_names:
                await Responder.send(
                    f'Song named "{song_name}" not on the playlist "{playlist_name}".', interaction, fail=True
                )
                return
            song_id = 0
            for song in list_songs:
                if song.song_name == song_name:
                    song_id = song.global_id

        try:
            if scope == 'user':
                self.db.remove_from_user_playlist(interaction.user.id, playlist_name, song_id)
            else:
                self.db.remove_from_server_playlist(interaction.guild.id, playlist_name, song_id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            await Responder.send(f'Song named "{song_name}" is no longer.', interaction)

    async def show_playlists(
            self,
            interaction: discord.Interaction,
            scope: typing.Literal['user', 'server']
    ) -> None:
        """
        The function sends a message with a list of all playlist for a certain user or server, depending on the scope.

        Parameters:
            interaction (discord.Interaction): The interaction from which the operation is being made.
            scope ('user' or 'server'): Is the function called for a user or a server playlist.

        Returns:
            This function doesn't return anything, but sends a message with a list of all playlist for a certain user
            or server, depending on the scope. If an exception occurs during the creating of the playlist, the function
            sends an error message to the user.
        """
        try:
            lists: list[str]
            if scope == 'user':
                lists = self.db.get_user_lists(interaction.user.id)
            else:
                lists = self.db.get_server_lists(interaction.guild.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            if len(lists) == 0:
                await Responder.send('No lists.', interaction)
            else:
                await Responder.show_playlists(lists, interaction)

    async def show_playlist_songs(
            self,
            interaction: discord.Interaction,
            playlist_name: str,
            scope: typing.Literal['user', 'server']
    ) -> None:
        """
        The function sends a message with a list of all songs for a certain user or server playlist,
        depending on the scope and selected playlist.

        Parameters:
            interaction (discord.Interaction): The interaction from which the operation is being made.
            playlist_name (str): The name of the playlist of which to list songs.
            scope ('user' or 'server'): Is the function called for a user or a server playlist.

        Returns:
            This function doesn't return anything, but sends a message with a list of all playlist songs for a certain
            user or server playlist, depending on the scope. If an exception occurs during the creating of the playlist,
            the function sends an error message to the user.
        """
        list_exists: bool | None = await self.list_exists(interaction, playlist_name, scope)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        try:
            discord_id: int = interaction.user.id if scope == 'user' else interaction.guild.id
            playlist_songs: list[SqlSong] = self.db.get_songs_from_list(discord_id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            if len(playlist_songs) == 0:
                await Responder.send(f'No songs on "{playlist_name}".', interaction)
            else:
                await Responder.show_songs(playlist_songs, playlist_name, interaction)
