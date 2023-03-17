import dataclasses


@dataclasses.dataclass
class SqlSong:
    def __init__(self, song_id: int, global_id: int, song_name: str, author_name: str, source: str):
        self.song_id = song_id
        self.global_id = global_id
        self.song_name = song_name
        self.author_name = author_name
        self.source = source
