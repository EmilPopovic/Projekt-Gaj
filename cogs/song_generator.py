"""
This file is part of Shteff which is released under the GNU General Public License v3.0.
See file LICENSE or go to <https://www.gnu.org/licenses/gpl-3.0.html> for full license details.
"""

# last changed 29/11/22

from colorthief import ColorThief
from requests import get
from youtube_dl import YoutubeDL
from io import BytesIO
import concurrent.futures
from datetime import timedelta
import discord
from threading import Thread

from spotify import (
    SpotifyInfo,
    SpotifySong,
    Author
)


class SongGenerator:
    # TODO: write docstring
    YDL_OPTIONS = {
        'format': 'bestaudio',
        'audioquality': '0',
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

        # the uid attribute makes every instance of Song class unique even if identical data is stored
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

        if isinstance(query, str):
            if 'www.youtube.com' in query:
                # TODO: if song is YouTube link
                self.error = 'YouTube link support coming soon!'
                return

            else:
                self.set_spotify_info(query)
                self.is_good = True

        elif isinstance(query, SpotifySong):
            self.url = query.url
            self.set_spotify_secondary(query)
            self.is_good = True

    def set_spotify_info(self, query):
        # TODO: handle spotify exceptions
        if 'open.spotify.com' in query:
            info: SpotifySong = SpotifyInfo.get_track(query)
        else:
            info: SpotifySong = SpotifyInfo.search_spotify(query)
        self.set_spotify_secondary(info)

    def set_spotify_secondary(self, info):
        self.name = info.name
        self.authors = info.authors
        self.author = self.authors[0]
        self.duration = info.duration
        self.thumbnail_link = info.thumbnail_url
        self.spotify_link = info.url

    def get_source_and_color(self):
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
            source_thread.join()
            color_thread.join()

        return {
            'source': self.source,
            'color': self.color
        }

    def set_source(self) -> None:
        yt_info = self.search_yt(f'{self.author} - {self.name}')
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
        self.color = discord.Color.from_rgb(*color)

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
    def search_yt(query: str) -> dict | bool:
        with YoutubeDL(SongGenerator.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f'ytsearch:{query}', download = False)['entries'][0]
            except Exception as e:
                print(e)
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title'], 'id': info['id']}

    @staticmethod
    def get_song_gens(query):
        return SongGenerator.multithread_extract(SpotifyInfo.get_playlist(query))

    @staticmethod
    def multithread_extract(songs: list[SpotifySong]):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            lst = [song for song in executor.map(SongGenerator, songs)]
        return sorted(lst)

    def __eq__(self, other) -> bool:
        return self.uid == other.uid

    def __gt__(self, other) -> bool:
        return self.uid > other.uid

    def __lt__(self, other) -> bool:
        return self.uid < other.uid

    def __repr__(self):
        return f'SongGenerator object | name: {self.name:<60} | url: {self.spotify_link}'
