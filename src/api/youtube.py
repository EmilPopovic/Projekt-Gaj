import yt_dlp

from utils import YTDLError


class YouTubeInfo:
    ydl_options = {
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

    def __init__(self, query: str, url=False):
        if url:
            self.source, self.title, self.id, self.author_name = self.search_yt_by_url(query)
        else:
            self.source, self.title, self.id, self.author_name = self.search_yt(query)

    @classmethod
    def search_yt(cls, query: str) -> tuple[str, str, str, str]:

        with yt_dlp.YoutubeDL(cls.ydl_options) as ydl:
            try:
                video = ydl.extract_info(f'ytsearch:{query.replace(" ", "_")}', download = False)['entries'][0]
            except:
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

        with yt_dlp.YoutubeDL(cls.ydl_options) as ydl:
            try:
                video = ydl.extract_info(url, download = False)
            except:
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
