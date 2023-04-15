import discord
from colorthief import ColorThief
from requests import get
from io import BytesIO
from datetime import timedelta
from threading import Thread

from api import SpotifyInfo, SpotifySong, Author, YouTubeInfo, GeniusInfo
from utils.sql_song import SqlSong
from utils import SpotifyExtractError, YTDLError


class SongGenerator:
    # unique identifier of a SongGenerator object
    last_uid = 0
    db = None

    @staticmethod
    def get_songs(
            query: str,
            interaction: discord.Interaction,
            set_all: bool = False,
            from_add_to_playlist: bool = False
    ) -> list:
        if 'https://open.spotify.com/' in query:
            lst = [
                SongGenerator(song, interaction, set_all, from_add_to_playlist=from_add_to_playlist)
                for song in SpotifyInfo.spotify_get(query)
            ]
        elif 'cdn.discordapp.com' in query:
            lst = [SongGenerator(query, interaction, set_all, from_add_to_playlist=from_add_to_playlist)]
        elif 'www.youtube.com' in query and 'playlist' not in query:
            lst = [SongGenerator(query, interaction, from_add_to_playlist=from_add_to_playlist)]
        else:
            lst = [
                SongGenerator(SpotifyInfo.spotify_get(query)[0], interaction, from_add_to_playlist=from_add_to_playlist)
            ]

        return [song for song in lst if song.is_good]

    def __init__(
            self,
            query: str | SpotifySong | SqlSong,
            interaction: discord.Interaction,
            set_all: bool = True,
            from_add_to_playlist: bool = False
    ):
        self.query = query
        self.interaction = interaction
        self.error = None

        # the uid attribute makes every instance of Song class
        # unique even if identical data is stored
        # used to determine the order of songs being added
        self.uid = SongGenerator.last_uid
        SongGenerator.last_uid += 1

        # initialize attributes
        self.name: str | None = None
        self.authors: list[Author] | None = None
        self.author: Author | None = None
        self.duration: timedelta | None = None
        self.thumbnail_link: str | None = None
        self.spotify_link: str | None = None
        self.yt_id: str | None = None
        self.yt_link: str | None = None
        self.color: tuple | None = None
        self.source: str | None = None
        self.lyrics: str | None = None
        self.is_good: bool = True
        self.from_file: bool = False
        self.from_playlist: bool = False

        if isinstance(query, str):
            if 'www.youtube.com' in query and 'playlist' not in query:
                print('we are searching for a youtube song')

                yt_info = YouTubeInfo(query, url=True)

                self.source = yt_info.source
                self.yt_id = yt_info.id
                self.yt_link = f'https://www.youtube.com/watch?v={self.yt_id}'

                yt_author_name = yt_info.author_name
                yt_title = yt_info.title

                self.set_spotify_info(f'{yt_author_name} - {yt_title}')

            elif 'cdn.discordapp.com' in query:
                self.from_file = True
                self.source = query
                self.name = query.split('/')[-1].split('.')[0].replace('_', ' ')
                self.author = Author()
                return

            else:
                self.set_spotify_info(query)

            t = Thread(target=self.set_source_color_lyrics)
            t.start()

            if set_all:
                t.join()

        elif isinstance(query, SpotifySong):
            self.set_spotify_secondary(query)
            if from_add_to_playlist:
                self.set_source()

        elif isinstance(query, SqlSong):
            self.from_playlist = True
            self.name = query.song_name

            spotify_info: SpotifySong = SpotifyInfo.spotify_get(f'{self.name} - {query.author_name}')[0]

            self.authors = spotify_info.authors
            self.author = self.authors[0]

            self.duration = spotify_info.duration
            self.thumbnail_link = spotify_info.thumbnail_url
            self.spotify_link = spotify_info.url

            self.source = query.source
            print(self.source)
            if self.source is None:
                self.is_good = False

            self.set_source_color_lyrics()

    def set_spotify_info(self, query: str) -> bool | None:
        try:
            if 'open.spotify.com' in query:
                info: SpotifySong = SpotifyInfo.spotify_get(query)[0]
            else:
                info: SpotifySong = SpotifyInfo.spotify_get(query)[0]

        except SpotifyExtractError:
            self.is_good = False
            return

        self.set_spotify_secondary(info)

    def set_spotify_secondary(self, info: SpotifySong) -> None:
        self.name = info.name
        self.authors = info.authors
        self.author = self.authors[0]
        self.duration = info.duration
        self.thumbnail_link = info.thumbnail_url
        self.spotify_link = info.url

    def set_source_color_lyrics(self, _=None):
        # multithreading calculating color and extracting source info to save time
        source_thread = Thread(target=self.set_source, args=())
        color_thread = Thread(target=self.set_color, args=())
        lyrics_thread = Thread(target=self.set_lyrics, args=())

        source_thread.start()
        color_thread.start()
        lyrics_thread.start()

        source_thread.join()
        color_thread.join()
        lyrics_thread.join()

    def set_source(self) -> None:
        if self.source is not None:
            return

        try:
            yt_info = YouTubeInfo(f'{self.author.name} {self.name}')
        except YTDLError:
            self.is_good = False
            return

        self.source = yt_info.source
        self.yt_id = yt_info.id
        self.yt_link = f'https://www.youtube.com/watch?v={self.yt_id}'

        if self.source is None:
            self.is_good = False

    def set_color(self) -> None:
        if self.color is not None:
            return
        if self.thumbnail_link is None:
            return

        response = get(self.thumbnail_link)
        img = BytesIO(response.content)

        color_thief = ColorThief(img)

        palette = color_thief.get_palette(color_count=5)
        self.color = palette[0]

    def set_lyrics(self) -> None:
        if self.lyrics is not None:
            return

        try:
            self.lyrics = GeniusInfo.get_lyrics(self.author.name, self.name)
        except AttributeError:
            self.lyrics = 'No lyrics found for this song.'

    def to_msg_format(self) -> str:
        if self.from_file:
            return self.name
        else:
            authors = ''.join(author.name + ', ' for author in self.authors).strip(', ')
            return f'{authors} - {self.name} ({self.timedelta_duration_to_str()})'

    def timedelta_duration_to_str(self) -> str:
        """
        Takes the duration attribute of SongGenerator object.
        self.duration is a datetime.timedelta object.
        Returns a string formatted as mm:ss.
        """
        minutes = self.duration.seconds // 60
        seconds = self.duration.seconds % 60
        return f'{minutes}:{seconds:02}'

    def cmd_message_print(self, number: int, is_current=False) -> str:
        if is_current:
            return f'**{number} {self.author.name} - {self.name}**'
        else:
            return f'**{number}** {self.author.name} - {self.name}'

    def __eq__(self, other) -> bool:
        return self.uid == other.uid

    def __gt__(self, other) -> bool:
        return self.uid > other.uid

    def __lt__(self, other) -> bool:
        return self.uid < other.uid

    def __hash__(self):
        return hash(self.uid)

    def __repr__(self) -> str:
        return f'SongGenerator object | name: {self.name} | url: {self.spotify_link}'
