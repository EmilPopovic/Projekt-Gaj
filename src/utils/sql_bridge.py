import mysql.connector
from mysql.connector import Error
import typing
from datetime import timedelta

from .colors import *
from .exceptions import SqlException
from settings import HOST_NAME, USER_NAME, USER_PASSWORD, DB_NAME, PORT_NUMBER
from components.song_generator import SongGenerator, Author


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
                host=HOST_NAME,
                user=USER_NAME,
                passwd=USER_PASSWORD,
                database=DB_NAME,
                port=PORT_NUMBER
            )
        except Error as err:
            raise SqlException(str(err))

        print(f'{c_event("DATABASE CONNECTED")}')

    def __repr__(self):
        return f'MySQL connection to {DB_NAME} on {HOST_NAME}:{PORT_NUMBER}.'

    def refresh_interactive_timeout(self):
        self.connection.reconnect()

    def execute_query(self, query: str) -> None:
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

    def read_query(self, query: str):
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

    def get_channel_id(self, guild_id: int):
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

        try:
            return self.read_query(query)[0][0]
        except IndexError:
            return None

    def update_channel_id(self, guild_id: int, channel_id: int):
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

    def add_channel_id(self, guild_id: int, channel_id: int):
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

    def get_lists(self, owner_id: int, scope: typing.Literal['user', 'server']) -> list:
        """
        Retrieves a list of playlists for a given server.
        Parameters:
            :param owner_id: The ID of the server to retrieve playlists for.
            :param scope: The scope of the request ('user' or 'server').
        """
        query = f"""SELECT playlist_name FROM {scope}playlists WHERE owner_id={owner_id};"""

        retval = self.read_query(query)
        lists = [elm[0] for elm in retval]
        return lists
    
    def get_color_id(self, song):
        red = song.color[0]
        green = song.color[1]
        blue = song.color[2]

        query = f"""SELECT color_id FROM Colors WHERE red={red} AND green={green} AND blue={blue};"""
        color_id = self.read_query(query)

        if not color_id:
            query2 = f"""INSERT INTO Colors(red, green, blue) VALUES ({red}, {green}, {blue});"""
            self.execute_query(query2)
            color_id = self.read_query(query)

        return color_id[0][0]

    def get_song_id(self, song: SongGenerator) -> int:
        """
        Retrieves the ID of a song from the database. If the song does not exist in the database, it is added first.
        Parameters:
            song (Song): The Song object to retrieve the ID for.
        Returns:
            int: The ID of the specified song.
        """
        # Check if the song already exists in the database
        author_id = self.get_author_id(song)

        query1 = f"""SELECT song_id FROM Songs WHERE song_name="{song.name}" AND author_id="{author_id}";"""
        song_id = self.read_query(query1)

        # If the song does not exist, add it to the database
        if not song_id:
            color_id = self.get_color_id(song)
            query2 = f"""INSERT INTO Songs(
                                        song_name,
                                        author_id,
                                        duration_s,
                                        thumbnail_link,
                                        spotify_link,
                                        yt_id,
                                        yt_link,
                                        color_id,
                                        song_link,
                                        lyrics                                        
                                        )             
                                    VALUES(
                                        "{song.name}", 
                                        {author_id}, 
                                        {int(song.duration.total_seconds())}, 
                                        "{song.thumbnail_link}",
                                        "{song.spotify_link}",
                                        "{song.yt_id}",
                                        "{song.yt_link}",
                                        {color_id},
                                        "{song.source}",
                                        "{song.lyrics}"
                                        );"""
            self.execute_query(query2)
            song_id = self.read_query(query1)

        # Return the ID of the song
        return song_id[0][0]
    
    def get_author_id(self, song: SongGenerator) -> int:
        """
        """
        query = f"""SELECT author_id FROM Authors WHERE author_name="{song.author.name}" AND author_link='{song.author.url}'; """
        author_id = self.read_query(query)

        if not author_id:
            query2 = f"""INSERT INTO Authors(author_name, author_link) VALUES("{song.author.name}", '{song.author.url}');"""
            self.execute_query(query2)
            author_id = self.read_query(query)

        return author_id[0][0]

    def get_playlist_id(self, owner_id: int, playlist_name: str, scope: typing.Literal['user', 'server']) -> int:
        """
        Retrieves the ID of a server playlist from the database.
        Parameters:
            playlist_name (str): The name of the playlist to return the ID for.
        Returns:
            int: The ID of the specified list.
        """
        query1 = f"""SELECT playlist_id FROM {scope}playlists WHERE owner_id='{owner_id}' AND playlist_name ='{playlist_name}';"""
        playlist_id = self.read_query(query1)
        
        return playlist_id[0][0]

    def add_to_playlist(self, song: SongGenerator, owner_id: int, playlist_name: str, scope: typing.Literal['user', 'server']) -> None:
        """
        Adds a song to a server playlist in the database.
        Parameters:
            song (Song): The Song object to add to the playlist.
            owner_id (int): The ID of the server the playlist belongs to.
            playlist_name (str): The name of the playlist to add the song to.
        Returns:
            None
        """
        # Get the ID of the song and playlist from the database
        song_id = self.get_song_id(song)
        playlist_id = self.get_playlist_id(owner_id, playlist_name, scope)
        
        query1 = f"""SELECT MAX(local_id) FROM {scope}playlistssongs WHERE playlist_id={playlist_id};"""
        local_id = self.read_query(query1)[0][0]
        if local_id is None:
            local_id = 0
        
        # Construct and execute the query to add the song to the playlist
        query2 = f"""INSERT INTO {scope}playlistssongs(playlist_id, song_id, local_id) VALUES ({playlist_id}, {song_id}, {local_id+1});"""
        self.execute_query(query2)
        
        # Print a success message
        print("Song successfully added to playlist.")

    def create_playlist(self, owner_id: int, playlist_name: str, scope: typing.Literal['user', 'server']):
        """
        Creates a new server playlist table in the database.
        Parameters:
            owner_id (int): The ID of the server the playlist belongs to.
            playlist_name (str): The name of the new playlist.
        Returns:
            None
        """
        # Construct and execute the query to create the new playlist table
        query = f"""INSERT INTO {scope}playlists (playlist_name, owner_id) VALUES ('{playlist_name}', {owner_id});"""
        self.execute_query(query)

    def delete_playlist(self, owner_id: int, playlist_name: str, scope: typing.Literal['user', 'server']):
        query = f"""DELETE FROM {scope}playlists WHERE owner_id={owner_id} AND playlist_name='{playlist_name}';"""
        self.execute_query(query)

    def remove_from_playlist(self, owner_id: int, playlist_name: str, song_id: int, scope: typing.Literal['user', 'server']):
        playlist_id = self.get_playlist_id(owner_id, playlist_name, scope)
        query = f"""DELETE FROM {scope}playlistssongs WHERE playlist_id={playlist_id} AND song_id={song_id};"""
        self.execute_query(query)

    def get_songs_from_list(self, owner_id: int, playlist_name: str, scope: typing.Literal['user', 'server']) -> list[SongGenerator]:
        playlist_id = self.get_playlist_id(owner_id, playlist_name, scope)
        query = f"""SELECT song_id FROM {scope}playlistssongs WHERE playlist_id={playlist_id} ORDER BY local_id;"""
        song_ids = self.read_query(query)
        ret_list: list[SongGenerator] = []
        for song in song_ids:
            query2 = f"""SELECT song_name, author_id, duration_s, thumbnail_link, spotify_link, yt_id, yt_link, color_id, song_link, lyrics FROM Songs WHERE song_id={song[0]};"""
            retval = self.read_query(query2)[0]
            song_obj: SongGenerator = SongGenerator(query=None, interaction=None)
            song_obj.name = retval[0]
            
            query3 = f"""SELECT author_name, author_link FROM Authors WHERE author_id={retval[1]};"""
            author_retval = self.read_query(query3)[0]
            author_name = author_retval[0]
            author_link = author_retval[1]
            song_obj.author = Author(author_name, author_link)
            song_obj.authors = [song_obj.author]
            
            song_obj.duration = timedelta(milliseconds=(retval[2]*1000))
            song_obj.thumbnail_link = retval[3]
            song_obj.spotify_link = retval[4]
            song_obj.yt_id = retval[5]
            song_obj.yt_link = retval[6]
            
            query4 = f"""SELECT red, green, blue FROM Colors WHERE color_id={retval[7]};"""
            color = self.read_query(query4)[0]
            song_obj.color = (color[0], color[1], color[2])
            
            song_obj.source = retval[8]
            song_obj.lyrics = retval[9]
            ret_list.append(song_obj)
        return ret_list
