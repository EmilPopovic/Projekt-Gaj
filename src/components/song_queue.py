import random
import typing
import discord

from .song_generator import SongGenerator
from utils import Queue, Stack


class SongQueue:
    Manager = None

    def __init__(self):
        self.upcoming: Queue = Queue()
        self.played: Stack = Stack()

        self.current = None

        self.unshuffled: Queue = Queue()
        self.skipped_while_shuffled: set = set()

        self.is_shuffled = False
        self.loop_status: typing.Literal['none', 'queue', 'single'] = 'none'

    @staticmethod
    def copy_queue(q: Queue, leading=False) -> Queue:
        new_q = Queue()
        if leading:
            new_q.enqueue(leading)
        for elem in q:
            new_q.enqueue(elem)
        return new_q

    def shuffle(self):
        self.is_shuffled = True

        self.unshuffled = self.copy_queue(self.upcoming)

        upcoming_lst = list(self.upcoming)
        random.shuffle(upcoming_lst)

        new_queue = Queue()
        for song in upcoming_lst:
            new_queue.enqueue(song)
        self.upcoming = new_queue

    def unshuffle(self):
        self.is_shuffled = False

        new_queue = Queue()
        for song in self.unshuffled:
            if song not in self.skipped_while_shuffled and song != self.current:
                new_queue.enqueue(song)
        self.upcoming = new_queue

        self.unshuffled = Queue()
        self.skipped_while_shuffled = set()

    def swap(self, m: int, n: int):
        queue_len = len(self.upcoming)
        m, n = m-1, n-1

        if m < 0 or n < 0:
            raise ValueError('Arguments cannot be less than or equal to 0.')
        elif m >= queue_len or n >= queue_len:
            raise ValueError('Arguments not in queue.')

        self.upcoming[m], self.upcoming[n] = self.upcoming[n], self.upcoming[m]

    def remove(self, n: int):
        queue_len = len(self.upcoming)
        n -= 1

        if n < 0:
            raise ValueError('Argument cannot be less than or equal to 0.')
        elif n >= queue_len:
            raise ValueError('Argument not in queue.')

        to_remove = self.upcoming[n]
        self.upcoming.remove(to_remove)

    def previous(self):
        if self.played.is_empty():
            return
        self.upcoming = self.copy_queue(self.upcoming, leading=self.current)
        self.current = self.played.pop()

    def goto(self, n: int):
        queue_len = len(self.upcoming)

        if n <= 0:
            raise ValueError('Argument cannot be less than or equal to 0.')
        elif n > queue_len:
            raise ValueError('Argument not in queue.')

        for _ in range(n):
            self.next(force_skip=True)

    def next(self, force_skip=False):
        if self.loop_status == 'singe' and not force_skip:
            return

        elif (self.loop_status == 'none') or (self.loop_status == 'single' and force_skip):
            if self.current is not None:
                self.played.push(self.current)

                if self.is_shuffled:
                    self.skipped_while_shuffled.add(self.current)

            if self.upcoming.is_empty():
                self.current = None
            else:
                self.current = self.upcoming.dequeue()

        elif self.loop_status == 'queue':
            if self.current is not None:
                self.played.push(self.current)

                if self.is_shuffled:
                    self.skipped_while_shuffled.add(self.current)

                self.current = None

            if self.upcoming.is_empty():
                new_queue = Queue()
                for song in self.played:
                    new_queue.enqueue(song)
                self.upcoming = new_queue
                self.played = Stack()
                self.next()
            else:
                self.current = self.upcoming.dequeue()

    def add_songs(
            self,
            query: str,
            interaction: discord.Interaction,
            insert_place: int = 1
    ) -> None:
        if insert_place <= 0:
            raise ValueError('Must be inserted into a place with a positive number.')

        songs: list[SongGenerator] = SongGenerator.get_songs(query, interaction)
        self.extend_list(insert_place, songs)

    async def add_playlist(
            self,
            playlist_name: str,
            interaction: discord.Interaction,
            scope: typing.Literal['user', 'server'],
            song_name: str = '',
            insert_place: int = 1
    ) -> None:
        if insert_place <= 0:
            raise ValueError('Must be inserted into a place with a positive number.')

        playlist_songs = await self.Manager.songs_from_playlist(interaction, playlist_name, scope, song_name)

        self.extend_list(insert_place, playlist_songs)

    def extend_list(self, insert_place: int, songs: list[SongGenerator]):
        if insert_place == 1:
            self.upcoming.extend(songs)
        else:
            for song in songs[::-1]:
                self.upcoming.insert(insert_place-1, song)

        if self.is_shuffled:
            self.unshuffled.extend(songs)

        if self.current is None:
            self.next()

    def __test_add(self, objects):
        for obj in objects:
            self.upcoming.enqueue(obj)
            if self.is_shuffled:
                self.unshuffled.append(obj)

    def __repr__(self):
        retstr = ''
        for song in self.played:
            retstr += f'   {song}\n'
        retstr += f'-> {self.current}\n'
        for song in self.upcoming:
            retstr += f'   {song}\n'
        return retstr
