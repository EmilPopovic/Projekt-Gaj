from lyricsgenius import Genius

from settings import api_key


class GeniusInfo:
    def __init__(self, song_name: str, author_name: str) -> None:
        # todo: versify
        self.lyrics = self.get_lyrics(song_name, author_name)
        self.verses = []

    @staticmethod
    def get_lyrics(song_name: str, author_name: str) -> str:
        lyrics_genius = Genius(api_key)
        song_info = lyrics_genius.search_song(author_name, song_name)
        lyrics = song_info.lyrics

        # remove junk in the beginning
        split_junk = lyrics.split('Lyrics')
        after_junk = ''.join(split_junk[1:])

        # remove junk in the end
        lyrics = after_junk.strip('You might also like50Embed')

        # clean text
        lyrics.replace('`', "'")

        return lyrics

    @staticmethod
    def versify(lyrics: str) -> list:
        verses = lyrics.split('\n\n')
        return verses
