import json
import mysql.connector
from mysql.connector import Error

from .colors import *
from .exceptions import SqlException

with open('secrets.json', 'r') as f:
    data = json.load(f)

host_name = data['database']['host_name']
user_name = data['database']['user_name']
user_password = data['database']['user_password']
db_name = data['database']['db_name']
port_number = data['database']['port_number']


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
            print("Query successful")
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
        query1 = f"""SELECT song_id FROM Songs WHERE song_name={song.name}, song_author={song.author}"""
        song_id = self.read_query(query1)

        # If the song does not exist, add it to the database
        if not song_id:
            query2 = f"""INSERT INTO Songs(song_name, song_author, song_link) VALUES ({song.name}, {song.author}, {song.yt_link});"""
            self.execute_query(query2)
            query3 = f"""SELECT song_id FROM Songs WHERE song_name={song.name}, song_author={song.author}"""
            song_id = self.read_query(query3)

        # Return the ID of the song
        return song_id

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
        query = f"""INSERT INTO {playlist_name}_{guild_id}(actual_id) VALUES ({song_id})"""
        self.execute_query(query)

        # Print a success message
        print("Song successfully added to playlist.")

    def add_to_personal_playlist(self, song, user_id, playlist_name):
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
        query = f"""INSERT INTO {playlist_name}_{user_id}(actual_id) VALUES ({song_id})"""
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
        query = f"""CREATE TABLE {playlist_name}_{guild_id}(
            local_id int NOT NULL auto_increment,
            actual_id int NOT NULL UNIQUE,
            PRIMARY KEY(local_id),
            FOREIGN KEY (actual_id) REFERENCES Songs(song_id) ON DELETE CASCADE
            );"""
        self.execute_query(query)

    def create_personal_playlist(self, user_id, playlist_name):
        """
        Creates a new personal playlist table in the database.
        Parameters:
            user_id (int): The ID of the user the playlist belongs to.
            playlist_name (str): The name of the new playlist.
        Returns:
            None
        """
        # Construct and execute the query to create the new playlist table
        query = f"""CREATE TABLE {playlist_name}_{user_id}(
            local_id int NOT NULL auto_increment,
            actual_id int NOT NULL UNIQUE,
            PRIMARY KEY(local_id),
            FOREIGN KEY (actual_id) REFERENCES Songs(song_id) ON DELETE CASCADE
            );"""
        self.execute_query(query)