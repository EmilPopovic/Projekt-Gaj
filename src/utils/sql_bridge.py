import json
import mysql.connector
from mysql.connector import Error
from colors import *

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
        Returns:
        connection: a connection object to the MySQL server.
        """
        self.connection = None
        try:
            self.connection = mysql.connector.connect(
                host = host_name,
                user = user_name,
                passwd = user_password,
                database = db_name,
                port = port_number
            )
            print(f'{c_event("DATABASE CONNECTED")}')
        except Error as err:
            print(f'{c_err()} {err}')


    def execute_query(self, query):
        """
        Executes specified MySQL query.
        Parameters:
        connection (object): a connection object to the MySQL server.
        query (str): the MySQL query to execute.
        Returns:
        None
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()
            print("Query successful")
        except Error as err:
            print(f"Error: '{err}'")


    def read_query(self, query):
        """
        Executes specified MySQL SELECT query and returns the result.
        Parameters:
        connection (object): a connection object to the MySQL server.
        query (str): the MySQL SELECT query to execute.
        Returns:
        result: a list of tuples containing the query result.
        """
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(query)
            result = cursor.fetchall()
        except Error as err:
            print(f"Error: '{err}'")
        return result

    # TODO: Error handling
    def get_channel_id(self, guild_id):
        """
        Retrieves the channel_id for a given guild_id from the 'guilds' table.
        Parameters:
        connection (object): a connection object to the MySQL server.
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
        connection (object): a connection object to the MySQL server.
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
        connection (object): a connection object to the MySQL server.
        guild_id (int): the guild_id to add.
        channel_id (int): the channel_id for the given guild_id.
        Returns:
        None
        """
        query = f"""INSERT INTO guilds(guild_id, channel_id) 
                    VALUES ({guild_id}, {channel_id})"""

        self.execute_query(query)


    def get_server_lists(self, guild_id):
        return


    def get_user_lists(self, user_id):
        query = f"""SELECT list_name FROM personal_playlists WHERE list_owner={user_id};"""

        retval = self.read_query(query)
        lists = [elm[0] for elm in retval]
        return lists


    def add_to_server_playlist(self, song, user_id, guild_id, playlist_name):
        return
        song_name = song.name
        song_author = song.author
        pass


    def add_to_personal_playlist(self, song, user_id, playlist_name):
        return
        song_name = song.name
        song_author = song.author

        query = f""""""

        self.execute_query(query)
        pass


    def create_server_playlist(self, guild_id, playlist_name):
        query = f"""INSERT INTO server_playlists (guild_id, list_name) VALUES ({guild_id}, {playlist_name});"""
        self.execute_query(query)


    def create_personal_playlist(self, user_id, playlist_name):
        query = f"""INSERT INTO personal_playlists (list_name, list_owner) VALUES({playlist_name}, {user_id});"""
        self.execute_query(query)
