import discord
import typing

from utils import (
    InteractionResponder as Responder,
    SqlException,
    ForbiddenQueryError,
    c_event,
    c_user,
    c_guild,
    Database
)
from .song_generator import SongGenerator


class ListManager:
    def __init__(self, main_bot):
        self.main_bot = main_bot
        self.db: Database = None

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
    ) -> list[SongGenerator | None] | None:
        """
        This asynchronous function returns a list of songs from a specified playlist.

        Parameters:
            interaction (discord.Interaction): The interaction from which the bot's current song is being retrieved.
            playlist_name (str): The name of the playlist to check for existence.
            scope ('user' or 'server'): Is the function called for a user or a server playlist.
            song_name (str, optional): The name of the song to get from playlist. Returns the entire
                                       playlist if not given.

        Returns:
            If `song_name` is given, the function returns a list containing the `SongGenerator` object of the song.
            If `song_name` is not given, the function returns a list of `SongGenerator` objects of all songs
            on that playlist.
            If an error occurs during the function execution, the function returns None.
        """
        list_exists: bool | None = await self.list_exists(interaction, playlist_name, scope)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(
                f'Playlist named "{playlist_name}" does not exist.',
                interaction,
                fail=True,
                followup=True
            )
            return

        try:
            list_songs: list[SongGenerator]
            owner_id: int = interaction.user.id if scope == 'user' else interaction.guild.id
                
            list_songs = self.db.get_songs_from_list(owner_id, playlist_name, scope)
        
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        except ForbiddenQueryError:
            await Responder.send('Forbidden list name.', interaction, fail=True)
            return
        else:
            if song_name:
                list_songs = [song for song in list_songs if song.name == song_name]
            
        return list_songs

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
            owner_id: int = interaction.user.id if scope == 'user' else interaction.guild.id
    
            lists = self.db.get_lists(owner_id, scope)
        
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
            songs = SongGenerator.get_songs(query, interaction, from_add_to_playlist=True)
        else:
            songs = [self.get_current_song(interaction)]
            if songs[0] is None:
                await Responder.send('No song to add.', interaction, fail=True)
                return

        songs = [song for song in songs if song.is_good]
        for song in songs:
            song.set_source_color_lyrics() 

        # check if the list we want to add the song to exists
        list_exists: bool | None = await self.list_exists(interaction, playlist_name, scope)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        # try to add the song to the list
        try:
            owner_id: int = interaction.user.id if scope == 'user' else interaction.guild.id
            for song in songs:
                self.db.add_to_playlist(song, owner_id, playlist_name, scope)
        
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name.', interaction, fail=True)
        else:
            if len(songs) == 1:
                await Responder.send(f'Added song to "{playlist_name}".', interaction, followup=True)
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
            owner_id: int = interaction.user.id if scope == 'user' else interaction.guild.id   
            
            lists = self.db.get_lists(owner_id, scope)
        
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
            owner_id: int = interaction.user.id if scope == 'user' else interaction.guild.id
            
            self.db.create_playlist(owner_id, playlist_name, scope)
        
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
            owner_id: int = interaction.user.id if scope == 'user' else interaction.guild.id

            self.db.delete_playlist(owner_id, playlist_name, scope)
        
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
            list_songs: list[SongGenerator]
            owner_id: int = interaction.user.id if scope == 'user' else interaction.guild.id
                
            list_songs = self.db.get_songs_from_list(owner_id, playlist_name, scope)
        
        except SqlException:
            await Responder.send('Database error, try again later', interaction, fail=True)
            return
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name.', interaction, fail=True)
            return
        else:
            song_names = [song.name for song in list_songs]
            if song_name not in song_names:
                await Responder.send(
                    f'Song named "{song_name}" not on the playlist "{playlist_name}".', interaction, fail=True
                )
                return
            song_id = 0
            for song in list_songs:
                if song.name == song_name:
                    song_id = self.db.get_song_id(song)

        try:
            owner_id: int = interaction.user.id if scope == 'user' else interaction.guild.id
            self.db.remove_from_playlist(owner_id, playlist_name, song_id, scope)
        
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
            owner_id: int = interaction.user.id if scope == 'user' else interaction.guild.id
            
            lists = self.db.get_lists(owner_id, scope)
        
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
            playlist_songs: list[SongGenerator] = self.db.get_songs_from_list(discord_id, playlist_name, scope)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            if len(playlist_songs) == 0:
                await Responder.send(f'No songs on "{playlist_name}".', interaction)
            else:
                await Responder.show_songs(playlist_songs, playlist_name, interaction)
