"""
This file is part of Shteff which is released under the GNU General Public License v3.0.
See file LICENSE or go to <https://www.gnu.org/licenses/gpl-3.0.html> for full license details.
"""

# last changed 23/12/22
# started adding lyrics support

import discord
from colorthief import ColorThief
from requests import get
from youtube_dl import YoutubeDL
from io import BytesIO
from datetime import timedelta
from threading import Thread

from external_services.spotify import (
    SpotifyInfo,
    SpotifySong,
    Author
)
from exceptions import (
    SpotifyExtractError,
    YTDLError
)
from external_services.genius import GeniusInfo


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
    ind = 0

    def __init__(self, query):
        self.query = query
        self.error = None

        # the uid attribute makes every instance of Song class
        # unique even if identical data is stored
        # used to determine the order of songs being added
        self.uid = SongGenerator.ind
        SongGenerator.ind += 1

        # initialize attributes
        self.name: str | None             = None
        self.authors: list[Author] | None = None
        self.author: Author | None        = None
        self.duration: timedelta | None   = None
        self.thumbnail_link: str | None   = None
        self.spotify_link: str | None     = None
        self.yt_id: str | None            = None
        self.yt_link: str | None          = None
        self.color: int | None            = None
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
                info: SpotifySong = SpotifyInfo.get_track(query)
            else:
                info: SpotifySong = SpotifyInfo.search_spotify(query)
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

    def get_source_and_color(self) -> dict:
        if self.source and self.color:
            pass
        elif self.source and self.color is None:
            self.set_color()
        elif self.source is None and self.color:
            self.set_source()
        else:
            # multithreading calculating color and extracting source info to save time
            # TODO: set color and source for songs in background
            source_thread = Thread(target = self.set_source, args = ())
            color_thread = Thread(target = self.set_color, args = ())

            source_thread.start()
            color_thread.start()
            # todo: wtf error
            source_thread.join()
            color_thread.join()

        return {
            'source': self.source,
            'color': self.color
        }

    def set_source(self) -> None:
        try:
            yt_info = self.search_yt(f'{self.author} - {self.name}')
        except YTDLError:
            self.is_good = False
            return

        self.source = yt_info['source']
        self.yt_id = yt_info['id']
        self.yt_link = f'https://www.youtube.com/watch?v={self.yt_id}'

    def set_color(self) -> None:
        # get image from url
        response = get(self.thumbnail_link)
        img = BytesIO(response.content)
        # convert image to ColorThief object
        color_thief = ColorThief(img)
        # extract color palette from image
        palette = color_thief.get_palette(color_count = 5)
        color = palette[0]
        # set preferred embed color
        # todo: format to discord in message update, not in song gen
        self.color = discord.Color.from_rgb(*color)

    def set_lyrics(self) -> None:
        # todo: test errors
        if self.lyrics is None:
            try:
                self.lyrics = GeniusInfo.get_lyrics(self.author.name, self.name)
            except AttributeError:
                self.lyrics = 'No lyrics found for this song.'
        else:
            return

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

    def check_if_good(self) -> bool:
        return self.is_good

    @classmethod
    def get_song_gens(cls, query: str):
        # todo: decide where this if should be
        songs = []
        if 'https://open.spotify.com/album/' in query:
            songs = SpotifyInfo.get_album(query)
        elif 'https://open.spotify.com/playlist/' in query:
            songs = SpotifyInfo.get_playlist(query)

        lst = [SongGenerator(song) for song in songs]
        return filter(cls.check_if_good, lst)

    def __eq__(self, other) -> bool:
        return self.uid == other.uid

    def __gt__(self, other) -> bool:
        return self.uid > other.uid

    def __lt__(self, other) -> bool:
        return self.uid < other.uid

    def __repr__(self) -> str:
        return f'SongGenerator object | name: {self.name:<60} | url: {self.spotify_link}'
