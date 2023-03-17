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

    def __init__(self, query: str):
        self.source, self.title, self.id = self.search_yt(query)

    @classmethod
    def search_yt(cls, query: str) -> tuple[str, str, str]:
        with yt_dlp.YoutubeDL(cls.ydl_options) as ydl:
            source = None
            title = None
            yt_id = None

            try:
                video = ydl.extract_info(f'ytsearch:{query}', download=False)['entries'][0]
                formats = video['formats']
                for f in formats:
                    url = f['url']
                    # todo: this should be a different link
                    if 'googlevideo.com' in url:
                        break
                else:
                    url = None

                source = url
                title = video['title']
                yt_id = video['id']

            except:
                raise YTDLError(query)

        return source, title, yt_id
