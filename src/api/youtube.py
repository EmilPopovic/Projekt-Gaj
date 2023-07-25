import yt_dlp
from dataclasses import dataclass

from utils import YTDLError


class YTDLError(Exception):
    def __init__(self, _):
        print('An error occurred.')


@dataclass
class YtSong:
    def __init__(self, source: str, title: str, yt_id: str, author_name: str):
        self.source = source
        self.title = title
        self.yt_id = yt_id
        self.author_name = author_name


class YtExtractor:
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
        'force_generic_extractor': True,
        'use-extractors': 'youtube'
    }

    @staticmethod
    def _get_playlist_id(url: str) -> str:
        for elm in url.split('&'):
            if 'list' in elm:
                return elm.split('=')[1]

    @staticmethod
    def _get_url_domain(url: str) -> str:
        return url.split('/')[2]

    @classmethod
    def yt_get(cls, query: str, url=False) -> list[YtSong]:
        if url:
            if 'list=' in query:
                playlist_id = cls._get_playlist_id(query)
                domain = cls._get_url_domain(query)

                playlist_query = f'https://{domain}/playlist?list={playlist_id}'

                list_items: tuple = cls.search_yt_by_playlist_url(playlist_query)

                return [YtSong(*item) for item in list_items]

            else:
                return [YtSong(*cls.search_yt_by_url(query))]

        else:
            return [YtSong(*cls.search_yt(query))]

    @classmethod
    def search_yt(cls, query: str) -> tuple[str, str, str, str]:

        with yt_dlp.YoutubeDL(cls.YDL_OPTIONS) as ydl:
            try:
                video = ydl.extract_info(f'ytsearch:{query.replace(" ", "_")}', download=False)['entries'][0]
            except Exception as _:
                raise YTDLError(query)

        formats = video['formats']
        for f in formats:
            url = f['url']
            if 'googlevideo.com' in url:
                break
        else:
            url = None

        source = url
        title = video['title']
        yt_id = video['id']
        author_name = video['uploader']

        return source, title, yt_id, author_name

    @classmethod
    def search_yt_by_url(cls, url: str) -> tuple[str, str, str, str]:

        with yt_dlp.YoutubeDL(cls.YDL_OPTIONS) as ydl:
            try:
                video = ydl.extract_info(url, download=False)
            except Exception as _:
                raise YTDLError(url)

        formats = video['formats']
        for f in formats:
            url = f['url']
            if 'googlevideo.com' in url:
                break
        else:
            url = None

        source = url
        title = video['title']
        yt_id = video['id']
        author_name = video['uploader']

        return source, title, yt_id, author_name

    @classmethod
    def search_yt_by_playlist_url(cls, url: str) -> tuple[str, str, str, str]:

        print(url)

        with yt_dlp.YoutubeDL(cls.YDL_OPTIONS) as ydl:
            try:
                playlist = ydl.extract_info(url, download=False)
            except Exception as _:
                raise YTDLError(url)

        print(playlist)

        source = ''
        title = ''
        yt_id = ''
        author_name = ''

        return source, title, yt_id, author_name


# link = 'https://www.youtube.com/watch?v=XXYlFuWEuKI&list=RDQMgEzdN5RuCXE&start_radio=1'

# YtExtractor.yt_get(link, url=True)
