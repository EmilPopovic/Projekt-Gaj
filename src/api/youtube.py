import yt_dlp
from utils import YTDLError


class YouTubeInfo:
    ydl_options = {
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

    def __init__(self, query: str):
        self.source, self.title, self.id = self.search_yt(query)

    @classmethod
    def search_yt(cls, query: str) -> dict:
        with yt_dlp.YoutubeDL(cls.ydl_options) as ydl:
            try:
                info = ydl.extract_info(f'ytsearch:{query}', download = False)['entries'][0]

                source = info['formats'][0]['url']
                title  = info['title']
                yt_id     = info['id']

            except:
                raise YTDLError(query)

        return {
            'source': source,
            'title': title,
            'id': yt_id
        }
