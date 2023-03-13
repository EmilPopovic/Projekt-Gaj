import discord

from utils import InteractionResponder as Responder, SqlException, ForbiddenQueryError, c_event, c_user, c_guild
from .song_generator import SongGenerator


class ListManager:
    def __init__(self, main_bot, db):
        # todo: playlist_in_user_playlists and song_in_user_playlist
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

    async def add(self, interaction, name: str, query: str):
        # get the SongGenerator object of the song we want to add
        if query:
            songs = SongGenerator.get_songs(query, interaction, set_all=True)
        else:
            songs = [self.get_current_song(interaction)]
            if songs == [None]:
                await Responder.send('No song to add.', interaction, fail=True)
                return

        # check if the list we want to add the song to exists
        try:
            lists = self.db.get_user_lists(interaction.user.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            if name not in lists:
                await Responder.send(f'Playlist named "{name}" does not exist.', interaction, fail=True)
                return

        # try to add the song to the list
        try:
            for song in songs:
                print(f'added "{song.name}" to "{name}"')
                self.db.add_to_personal_playlist(song, interaction.user.id, name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name.', interaction, fail=True)
        else:
            if len(songs) == 1:
                await Responder.send(f'Added song to "{name}".', interaction)
            else:
                await Responder.send(f'Added songs to "{name}".', interaction)

    async def server_add(self, interaction, name: str, query: str):
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
        try:
            lists = self.db.get_server_lists(interaction.guild.id)
            print(lists)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            if name not in lists:
                await Responder.send(f'Playlist named "{name}" does not exist.', interaction, fail=True)
                return

        # try to add the song to the list
        try:
            for song in songs:
                print(f'added "{song.name}" to "{name}"')
                self.db.add_to_server_playlist(song, interaction.guild.id, name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name.', interaction, fail=True)
        else:
            if len(songs) == 1:
                await Responder.send(f'Added song to "{name}".', interaction)
            else:
                await Responder.send(f'Added songs to "{name}".', interaction)

    async def create(self, interaction, name: str):
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
            self.db.create_personal_playlist(interaction.user.id, name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        except ForbiddenQueryError:
            await Responder.send('Forbidden song name', interaction, fail=True)
        else:
            print(f'{c_event("CREATED LIST")} for user {c_user(interaction.user.id)}')
            await Responder.send(f'Created playlist "{name}".', interaction)

    async def server_create(self, interaction, name: str):
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

    async def delete(self, interaction, name):
        try:
            user_lists = self.db.get_user_lists(interaction.user.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            if name not in user_lists:
                await Responder.send(f'Playlist named "{name}" does not exist.', interaction, fail=True)
                return

        try:
            self.db.delete_personal_playlist(interaction.user.id, name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            await Responder.send(f'Deleted playlist "{name}".', interaction)

    async def server_delete(self, interaction, name):
        try:
            server_lists = self.db.get_server_lists(interaction.guild.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            if name not in server_lists:
                await Responder.send(f'Playlist named "{name}" does not exist.', interaction, fail=True)
                return

        try:
            self.db.delete_server_playlist(interaction.guild.id, name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            await Responder.send(f'Deleted playlist "{name}".', interaction)

    async def remove_from_personal(self, interaction: discord.Interaction, playlist_name: str, song_name: str):
        try:
            user_lists = self.db.get_user_lists(interaction.user.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        except ForbiddenQueryError:
            await Responder.send('Forbidden playlist name.', interaction, fail=True)
            return
        else:
            if playlist_name not in user_lists:
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

    async def remove_from_server(self, interaction: discord.Interaction, playlist_name: str, song_name: str):
        try:
            server_lists = self.db.get_server_lists(interaction.guild.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        except ForbiddenQueryError:
            await Responder.send('Forbidden playlist name.', interaction, fail=True)
            return
        else:
            if playlist_name not in server_lists:
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

    async def show_server_playlist_songs(self, interaction: discord.Interaction, playlist_name: str):
        try:
            server_lists = self.db.get_server_lists(interaction.guild.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        except ForbiddenQueryError:
            await Responder.send('Forbidden playlist name.', interaction, fail=True)
            return
        else:
            if playlist_name not in server_lists:
                await Responder.send(f'Playlist named "{playlist_name}" does not exist.', interaction, fail=True)
                return

        try:
            playlist_songs: list[dict] = self.db.get_songs_from_list(interaction.guild.id, playlist_name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            await Responder.show_list(playlist_songs, playlist_name, interaction)
