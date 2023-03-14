import dataclasses
import mysql.connector
from mysql.connector import Error

from .colors import *
from .exceptions import SqlException
from settings import host_name, user_name, user_password, db_name, port_number


@dataclasses.dataclass
class SqlSong:
    def __init__(self, song_id: int, global_id: int, song_name: str, author_name: str, source: str):
        self.song_id = song_id
        self.global_id = global_id
        self.song_name = song_name
        self.author_name = author_name
        self.source = source


class Database:
    def __init__(self):
        """
        Establishes connection to MySQL server.

        Parameters (taken from secrets.json):
            host_name (str): hostname for the MySQL server.
            user_name (str): username for the MySQL server.
            user_password (str): password for the MySQL server.
            db_name (str): name of the database to connect to.
            port_number (int): port number for the MySQL server.
        """
        self.connection = None
        try:
            self.connection = mysql.connector.connect(
                host=host_name,
                user=user_name,
                passwd=user_password,
                database=db_name,
                port=port_number
            )
            print(f'{c_event("DATABASE CONNECTED")}')
        except Error as err:
            raise SqlException(str(err))

    def execute_query(self, query) -> None:
        """
        Executes specified MySQL query.

        Parameters:
            query (str): the MySQL query to execute.

        Returns:
            None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
        except Error as err:
            raise SqlException(str(err))

    def read_query(self, query):
        """
        Executes specified MySQL SELECT query and returns the result.

        Parameters:
            query (str): the MySQL SELECT query to execute.

        Returns:
            result: a list of tuples containing the query result.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
        except Error as err:
            raise SqlException(str(err))
        else:
            return result

    # TODO: Error handling
    def get_channel_id(self, guild_id):
        """
        Retrieves the channel_id for a given guild_id from the 'guilds' table.

        Parameters:
            guild_id (int): the guild_id to look up.

        Returns:
            channel_id (int): the channel_id for the given guild_id.
        """
        query = f"""SELECT channel_id
                    FROM guilds 
                    WHERE guild_id={guild_id} """

        return self.read_query(query)[0][0]

    def update_channel_id(self, guild_id, channel_id):
        """
        Updates the channel_id for a given guild_id in the 'guilds' table.

        Parameters:
            guild_id (int): the guild_id to update.
            channel_id (int): the new channel_id for the given guild_id.

        Returns:
            None
        """
        query = f"""UPDATE guilds
                    SET channel_id = {channel_id}
                    WHERE guild_id = {guild_id}"""

        self.execute_query(query)

    def add_channel_id(self, guild_id, channel_id):
        """
        Adds a new guild_id and channel_id pair to the 'guilds' table.

        Parameters:
            guild_id (int): the guild_id to add.
            channel_id (int): the channel_id for the given guild_id.

        Returns:
            None
        """
        query = f"""INSERT INTO guilds(guild_id, channel_id) 
                    VALUES ({guild_id}, {channel_id})"""

        self.execute_query(query)

    def get_server_lists(self, guild_id):
        """
        Retrieves a list of playlists for a given server.
        Parameters:
            guild_id (int): The ID of the server to retrieve playlists for.
        Returns:
            list: A list of playlist names for the specified server.
        """
        query = f"""SELECT playlist_name FROM ServerPlaylists WHERE guild_id={guild_id};"""

        retval = self.read_query(query)
        lists = [elm[0] for elm in retval]
        return lists

    def get_user_lists(self, user_id):
        """
        Retrieves a list of personal playlists for a given user.
        Parameters:
            user_id (int): The ID of the user to retrieve playlists for.
        Returns:
            list: A list of playlist names for the specified user.
        """
        query = f"""SELECT playlist_name FROM PersonalPlaylists WHERE user_id={user_id};"""

        retval = self.read_query(query)
        lists = [elm[0] for elm in retval]
        return lists

    def get_song_id(self, song):
        """
        Retrieves the ID of a song from the database. If the song does not exist in the database, it is added first.
        Parameters:
            song (Song): The Song object to retrieve the ID for.
        Returns:
            int: The ID of the specified song.
        """
        # Check if the song already exists in the database
        query1 = f"""SELECT song_id FROM Songs WHERE song_name='{song.name}' AND author_name='{song.author.name}'"""
        song_id = self.read_query(query1)

        # If the song does not exist, add it to the database
        if not song_id:
            query2 = f"""INSERT INTO Songs(song_name, author_name, song_link) VALUES ('{song.name}', '{song.author.name}', '{song.source}');"""
            self.execute_query(query2)
            query3 = f"""SELECT song_id FROM Songs WHERE song_name='{song.name}' AND author_name='{song.author.name}'"""
            song_id = self.read_query(query3)

        # Return the ID of the song
        return song_id[0][0]

    def add_to_server_playlist(self, song, guild_id, playlist_name):
        """
        Adds a song to a server playlist in the database.
        Parameters:
            song (Song): The Song object to add to the playlist.
            guild_id (int): The ID of the server the playlist belongs to.
            playlist_name (str): The name of the playlist to add the song to.
        Returns:
            None
        """
        # Get the ID of the song from the database
        song_id = self.get_song_id(song)

        # Construct and execute the query to add the song to the playlist
        query = f"""INSERT INTO `{playlist_name}_{guild_id}`(actual_id) VALUES ({song_id})"""
        self.execute_query(query)

        # Print a success message
        print("Song successfully added to playlist.")

    def add_to_user_playlist(self, song, user_id, playlist_name):
        """
        Adds a song to a personal playlist in the database.
        Parameters:
            song (Song): The Song object to add to the playlist.
            user_id (int): The ID of the user the playlist belongs to.
            playlist_name (str): The name of the playlist to add the song to.
        Returns:
            None
        """
        # Get the ID of the song from the database
        song_id = self.get_song_id(song)

        # Construct and execute the query to add the song to the playlist
        query = f"""INSERT INTO `{playlist_name}_{user_id}`(actual_id) VALUES ({song_id})"""
        self.execute_query(query)

        # Print a success message
        print("Song successfully added to playlist.")

    def create_server_playlist(self, guild_id, playlist_name):
        """
        Creates a new server playlist table in the database.
        Parameters:
            guild_id (int): The ID of the server the playlist belongs to.
            playlist_name (str): The name of the new playlist.
        Returns:
            None
        """
        # Construct and execute the query to create the new playlist table
        query = f"""CREATE TABLE `{playlist_name}_{guild_id}`(
            local_id int NOT NULL auto_increment,
            actual_id int NOT NULL UNIQUE,
            PRIMARY KEY(local_id),
            FOREIGN KEY (actual_id) REFERENCES Songs(song_id) ON DELETE CASCADE
            );"""
        query2 = f"""INSERT INTO ServerPlaylists (playlist_name, guild_id) VALUES ('{playlist_name}', {guild_id});"""
        self.execute_query(query)
        self.execute_query(query2)

    def create_user_playlist(self, user_id, playlist_name):
        """
        Creates a new personal playlist table in the database.
        Parameters:
            user_id (int): The ID of the user the playlist belongs to.
            playlist_name (str): The name of the new playlist.
        Returns:
            None
        """
        # Construct and execute the query to create the new playlist table
        query = f"""CREATE TABLE `{playlist_name}_{user_id}`(
            local_id int NOT NULL auto_increment,
            actual_id int NOT NULL UNIQUE,
            PRIMARY KEY(local_id),
            FOREIGN KEY (actual_id) REFERENCES Songs(song_id) ON DELETE CASCADE
            );"""
        self.execute_query(query)

    def delete_server_playlist(self, guild_id, playlist_name):
        query1 = f"""DROP TABLE `{playlist_name}_{guild_id}`;"""
        query2 = f"""DELETE FROM ServerPlaylists WHERE guild_id={guild_id} AND playlist_name='{playlist_name}';"""

        self.execute_query(query1)
        self.execute_query(query2)

    def remove_from_server_playlist(self, guild_id, playlist_name, song):
        song_id = self.get_song_id(song)
        query1 = f"""DELETE FROM `{playlist_name}_{guild_id}` WHERE actual_id={song_id};"""

        self.execute_query(query1)

    def get_songs_from_list(self, discord_id: int, playlist_name: str) -> list[SqlSong]:
        query = f"""SELECT * FROM `{playlist_name}_{discord_id}`;"""
        song_pairs = self.read_query(query)

        ret_list: list[SqlSong] = []
        for song in song_pairs:
            query2 = f"""SELECT song_id, song_name, author_name, song_link FROM Songs WHERE song_id={song[1]};"""
            retval = self.read_query(query2)[0]
            song_obj: SqlSong = SqlSong(
                song_id=song[0],
                global_id=retval[0],
                song_name=retval[1],
                author_name=retval[2],
                source=retval[3]
            )
            ret_list.append(song_obj)

        return ret_list



