import discord

from utils import (
    InteractionResponder as Responder,
    SqlSong,
    SqlException,
    ForbiddenQueryError,
    c_event,
    c_user,
    c_guild
)
from .song_generator import SongGenerator


class ListManager:
    def __init__(self, main_bot, db):
        # todo: song_in_user_playlist
        # todo: same for server
        self.main_bot = main_bot
        self.db = db

    def get_current_song(self, interaction):
        guild_bot = self.main_bot.get_bot_from_interaction(interaction)
        p_index = guild_bot.p_index
        queue = guild_bot.queue

        try:
            song = queue[p_index]
        except IndexError:
            return None
        else:
            if not song.is_good or song.from_file:
                return None
            return song

    async def user_list_exists(self, interaction: discord.Interaction, playlist_name: str) -> None | bool:
        try:
            user_lists: list[str] = self.db.get_user_lists(interaction.user.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return None
        except ForbiddenQueryError:
            await Responder.send('Forbidden list name.', interaction, fail=True)
            return None
        else:
            if playlist_name in user_lists:
                return True
            return False

    async def server_list_exists(self, interaction: discord.Interaction, playlist_name: str) -> None | bool:
        try:
            server_lists: list[str] = self.db.get_server_lists(interaction.guild.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return None
        except ForbiddenQueryError:
            await Responder.send('Forbidden list name.', interaction, fail=True)
            return None
        else:
            if playlist_name in server_lists:
                return True
            return False

    async def add(self, interaction: discord.Interaction, playlist_name: str, query: str) -> None:
        # get the SongGenerator object of the song we want to add
        if query:
            songs: list[SongGenerator] = SongGenerator.get_songs(query, interaction, set_all=True)
        else:
            songs: list[SongGenerator] = [self.get_current_song(interaction)]
            if songs[0] is None:
                await Responder.send('No song to add.', interaction, fail=True)
                return
            # todo: remove songs where is_good == False and where from_file == False

        # check if the list we want to add the song to exists
        list_exists: bool | None = await self.user_list_exists(interaction, playlist_name)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        # try to add the song to the list
        try:
            for song in songs:
                self.db.add_to_user_playlist(song, interaction.user.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name.', interaction, fail=True)
        else:
            if len(songs) == 1:
                await Responder.send(f'Added song to "{playlist_name}".', interaction)
            else:
                await Responder.send(f'Added songs to "{playlist_name}".', interaction)

    async def server_add(self, interaction: discord.Interaction, playlist_name: str, query: str) -> None:
        # get the SongGenerator object of the song we want to add
        if query:
            songs = SongGenerator.get_songs(query, interaction, set_all=True)
        else:
            songs = [self.get_current_song(interaction)]
            if songs == [None]:
                await Responder.send('No song to add.', interaction, fail=True)
                return
            # todo: remove songs where is_good == False and where from_file == False

        # check if the list we want to add the song to exists
        list_exists: bool | None = await self.server_list_exists(interaction, playlist_name)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        # try to add the song to the list
        try:
            for song in songs:
                print(f'added "{song.name}" to "{playlist_name}"')
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

    async def create(self, interaction: discord.Interaction, name: str) -> None:
        # max number of personal playlists is 25 per user
        # playlist names have to be unique
        try:
            user_lists = self.db.get_user_lists(interaction.user.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            num_of_lists = len(user_lists)
            if num_of_lists >= 25:
                await Responder.send('Cannot have more than 25 lists.', interaction, fail=True)
                return
            elif name in user_lists:
                await Responder.send(f'Playlist named "{name}" already exists.', interaction, fail=True)
                return

        try:
            self.db.create_user_playlist(interaction.user.id, name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name', interaction, fail=True)
        else:
            print(f'{c_event("CREATED LIST")} for user {c_user(interaction.user.id)}')
            await Responder.send(f'Created playlist "{name}".', interaction)

    async def server_create(self, interaction: discord.Interaction, name: str) -> None:
        # max number of server playlists is 25 per server
        # playlist names have to be unique
        try:
            server_lists = self.db.get_server_lists(interaction.guild.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            num_of_lists = len(server_lists)
            if num_of_lists >= 25:
                await Responder.send('Cannot have more than 25 lists.', interaction, fail=True)
                return
            elif name in server_lists:
                await Responder.send(f'Playlist named "{name}" already exists.', interaction, fail=True)
                return

        try:
            self.db.create_server_playlist(interaction.guild.id, name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name', interaction, fail=True)
        else:
            print(f'{c_event("CREATED LIST")} for guild {c_guild(interaction.guild.id)}')
            await Responder.send(f'Created playlist "{name}".', interaction)

    async def delete(self, interaction: discord.Interaction, playlist_name: str) -> None:
        list_exists: bool | None = await self.user_list_exists(interaction, playlist_name)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        try:
            self.db.delete_personal_playlist(interaction.user.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            await Responder.send(f'Deleted playlist "{playlist_name}".', interaction)

    async def server_delete(self, interaction: discord.Interaction, playlist_name: str) -> None:
        list_exists: bool | None = await self.user_list_exists(interaction, playlist_name)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        try:
            self.db.delete_server_playlist(interaction.guild.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            await Responder.send(f'Deleted playlist "{playlist_name}".', interaction)

    async def remove_from_personal(self, interaction: discord.Interaction, playlist_name: str, song_name: str) -> None:
        list_exists: bool | None = await self.user_list_exists(interaction, playlist_name)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        try:
            list_songs: list[str] = self.db.get_songs_from_list(interaction.user.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later', interaction, fail=True)
            return
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name.', interaction, fail=True)
            return
        else:
            if song_name not in list_songs:
                await Responder.send(
                    f'Song named "{song_name}" not on the playlist "{playlist_name}".', interaction, fail=True
                )
                return

        try:
            self.db.remove_from_personal_playlist(interaction.user.id, playlist_name, song_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            await Responder.send(f'Song named "{song_name}" is no longer.', interaction)

    async def remove_from_server(self, interaction: discord.Interaction, playlist_name: str, song_name: str) -> None:
        list_exists: bool | None = await self.server_list_exists(interaction, playlist_name)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        try:
            list_songs: list[str] = self.db.get_songs_from_list(interaction.guild.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later', interaction, fail=True)
            return
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name.', interaction, fail=True)
            return
        else:
            if song_name not in list_songs:
                await Responder.send(
                    f'Song named "{song_name}" not on the playlist "{playlist_name}".', interaction, fail=True
                )
                return

        try:
            self.db.remove_from_server_playlist(interaction.guild.id, playlist_name, song_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            await Responder.send(f'Song named "{song_name}" is no longer.', interaction)

    async def show_user_playlists(self, interaction: discord.Interaction) -> None:
        try:
            user_lists = self.db.get_user_lists(interaction.user.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            if len(user_lists) == 0:
                await Responder.send('No lists.', interaction)
            else:
                await Responder.show_playlists(user_lists, interaction)

    async def show_server_playlists(self, interaction: discord.Interaction) -> None:
        try:
            server_lists = self.db.get_server_lists(interaction.guild.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            if len(server_lists) == 0:
                await Responder.send('No lists.', interaction)
            else:
                await Responder.show_playlists(server_lists, interaction)

    async def show_user_playlist_songs(self, interaction: discord.Interaction, playlist_name: str) -> None:
        list_exists: bool | None = await self.user_list_exists(interaction, playlist_name)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        try:
            playlist_songs: list[SqlSong] = self.db.get_songs_from_list(interaction.user.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            await Responder.show_songs(playlist_songs, playlist_name, interaction)

    async def show_server_playlist_songs(self, interaction: discord.Interaction, playlist_name: str):
        list_exists: bool | None = await self.server_list_exists(interaction, playlist_name)
        if list_exists is None:
            return
        elif not list_exists:
            await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
            return

        try:
            playlist_songs: list[SqlSong] = self.db.get_songs_from_list(interaction.guild.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            await Responder.show_songs(playlist_songs, playlist_name, interaction)
