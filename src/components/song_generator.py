"""
This file is part of Shteff which is released under the GNU General Public License v3.0.
See file LICENSE or go to <https://www.gnu.org/licenses/gpl-3.0.html> for full license details.
"""

# last changed 29/12/22
# commenting


from colorthief import ColorThief
from requests import get
from youtube_dl import YoutubeDL
from io import BytesIO
from datetime import timedelta
from threading import Thread

from spotify import (
    SpotifyInfo,
    SpotifySong,
    Author
)
from exceptions import (
    SpotifyExtractError,
    YTDLError
)
from genius import GeniusInfo


class SongGenerator:
    # TODO: write docstring
    YDL_OPTIONS = {
        'format': 'bestaudio',
        'audioquality': '0',
        'audio_format': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'geo_bypass': True,
        'skip_download': True,
        'youtube_skip_dash_manifest': True,
        'playlist_end': 1,
        'max_downloads': 1,
        'force_generic_extractor': True
    }

    # unique identifier of a SongGenerator object
    last_uid = 0

    @staticmethod
    def get_songs(query: str) -> list:
        if 'https://open.spotify.com/' in query:
            lst = [SongGenerator(song) for song in SpotifyInfo.spotify_get(query)]
        else:
            lst = [SongGenerator(SpotifyInfo.spotify_get(query)[0])]

        return [song for song in lst if song.is_good]


    def __init__(self, query):
        self.query = query
        self.error = None

        # the uid attribute makes every instance of Song class
        # unique even if identical data is stored
        # used to determine the order of songs being added
        self.uid = SongGenerator.last_uid
        SongGenerator.last_uid += 1

        # initialize attributes
        self.name: str | None             = None
        self.authors: list[Author] | None = None
        self.author: Author | None        = None
        self.duration: timedelta | None   = None
        self.thumbnail_link: str | None   = None
        self.spotify_link: str | None     = None
        self.yt_id: str | None            = None
        self.yt_link: str | None          = None
        self.color: tuple | None          = None
        self.source: str | None           = None
        self.lyrics: str | None           = None
        self.is_good: bool                = True

        if isinstance(query, str):
            if 'www.youtube.com' in query:
                # TODO: if song is YouTube link
                self.is_good = False
                return

            else:
                self.set_spotify_info(query)

        elif isinstance(query, SpotifySong):
            self.set_spotify_secondary(query)


    def set_spotify_info(self, query: str) -> bool|None:
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


    def get_source_color_lyrics(self) -> dict:
        # multithreading calculating color and extracting source info to save time
        source_thread = Thread(target = self.set_source, args = ())
        color_thread = Thread(target = self.set_color, args = ())
        lyrics_thread = Thread(target = self.set_lyrics, args = ())

        source_thread.start()
        color_thread.start()
        lyrics_thread.start()

        source_thread.join()
        color_thread.join()
        lyrics_thread.join()

        return {
            'source': self.source,
            'color': self.color,
            'lyrics': self.lyrics
        }


    def set_source(self) -> None:
        if self.source is not None:
            return

        try:
            yt_info = self.search_yt(f'{self.author} - {self.name}')
        except YTDLError:
            self.is_good = False
            return

        self.source = yt_info['source']
        self.yt_id = yt_info['id']
        self.yt_link = f'https://www.youtube.com/watch?v={self.yt_id}'


    def set_color(self) -> None:
        if self.color is not None:
            return
        if self.thumbnail_link is None:
            return

        # get image from url
        response = get(self.thumbnail_link)
        img = BytesIO(response.content)
        # convert image to ColorThief object
        color_thief = ColorThief(img)
        # extract color palette from image
        palette = color_thief.get_palette(color_count = 5)
        self.color = palette[0]


    def set_lyrics(self) -> None:
        if self.lyrics is not None:
            return

        try:
            self.lyrics = GeniusInfo.get_lyrics(self.author.name, self.name)
        except AttributeError:
            self.lyrics = 'No lyrics found for this song.'


    def to_msg_format(self) -> str:
        authors = ''.join(author.name + ', ' for author in self.authors).strip(', ')
        return f'{authors} - {self.name} ({self.timedelta_duration_to_str()})'


    def timedelta_duration_to_str(self) -> str:
        """
        Takes the self.duration attribute of SongGenerator object.
        self.duration is a datetime.timedelta object.
        Returns a string formatted as mm:ss.
        """
        minutes = self.duration.seconds // 60
        seconds = self.duration.seconds % 60
        return f'{minutes}:{seconds:02}'


    @staticmethod
    def search_yt(query: str) -> dict:
        with YoutubeDL(SongGenerator.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f'ytsearch:{query}', download = False)['entries'][0]
            except:
                raise YTDLError(query)

        return {
            'source': info['formats'][0]['url'],
            'title': info['title'],
            'id': info['id']
        }


    def __eq__(self, other) -> bool:
        return self.uid == other.uid


    def __gt__(self, other) -> bool:
        return self.uid > other.uid


    def __lt__(self, other) -> bool:
        return self.uid < other.uid


    def __repr__(self) -> str:
        return f'SongGenerator object | name: {self.name:<60} | url: {self.spotify_link}'
