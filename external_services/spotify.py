"""
This file is part of Shteff which is released under the GNU General Public License v3.0.
See file LICENSE or go to <https://www.gnu.org/licenses/gpl-3.0.html> for full license details.
"""

# last changed 26/12/22
# formatting changes
# removed thumbnail_url from artist
# started working on artist and album links

from requests import get, post
from datetime import timedelta
from dataclasses import dataclass

from secrets import refresh_token, base_64
from exceptions import SpotifyExtractError


@dataclass
class Author:
    def __init__(self, name, url):
        self.name = name
        self.url = url

    def print_with_url_format(self, new_line=False) -> str:
        name_with_url = f'[{self.name}]({self.url})'
        return f'{name_with_url}\n' if new_line else name_with_url

    def __repr__(self) -> str:
        return f'Name: {self.name:<25} | url: {self.url}'


@dataclass
class SpotifySong:
    def __init__(
            self,
            name=None,
            url=None,
            authors=None,
            thumbnail_url=None,
            duration=None,
            error=None
    ):
        self.name = name
        self.url = url
        self.authors = authors
        self.thumbnail_url = thumbnail_url
        self.duration = duration
        self.error = error

    def __repr__(self) -> str:
        return f'Name: {self.name:<50} | url: {self.url}'


class SpotifyInfo:
    # TODO: refresh_token wrapper
    # TODO: refresh token in regular intervals?
    spotify_token = ''


    @staticmethod
    def spotify_get(query) -> list[SpotifySong]:
        return []


    def __init__(self) -> None:
        pass


    @classmethod
    def get_track(cls, url: str) -> SpotifySong:
        cls.call_refresh()

        if 'track/' not in url:
            raise SpotifyExtractError()

        track_id = url.split('track/')[1].split('?')[0]
        json = cls.get_response(f'https://api.spotify.com/v1/tracks/{track_id}')

        try:
            song = SpotifySong(
                name = json['name'],
                url = url,
                authors = [
                    Author(
                        name = author['name'],
                        url = author['external_urls']['spotify']
                    )
                    for author in json['artists']
                ],
                thumbnail_url = json['album']['images'][-1]['url'],
                duration = timedelta(milliseconds = json['duration_ms'])
            )
            return song

        except KeyError:
            raise SpotifyExtractError(json)


    @classmethod
    def search_spotify(cls, query: str) -> SpotifySong:
        cls.call_refresh()

        query = f'https://api.spotify.com/v1/search?q={query.replace(" ", "%20")}&type=track&limit=1&offset=0'
        json = cls.get_response(query)

        try:
            item = json['tracks']['items'][0]

            return SpotifySong(
                name = item['name'],
                url = item['external_urls']['spotify'],
                authors = [
                    Author(
                        name = author['name'],
                        url = author['external_urls']['spotify']
                    )
                    for author in item['artists']
                ],
                thumbnail_url = item['album']['images'][0]['url'],
                duration = timedelta(milliseconds = item['duration_ms'])
            )

        except KeyError:
            raise SpotifyExtractError(json)


    @classmethod
    def get_album(cls, url: str) -> list[SpotifySong]:
        cls.call_refresh()

        if 'album/' not in url:
            raise SpotifyExtractError()

        query = f'https://api.spotify.com/v1/albums/{url.split("album/")[1].split("?")[0]}/tracks'
        json = cls.get_response(query)

        print(json)

        try:
            # todo: get `thumbnail_url`
            return [
                SpotifySong(
                    name = item['name'],
                    url =  item['external_urls']['spotify'],
                    authors = [
                        Author(
                            name = author['name'],
                            url = author['external_urls']['spotify']
                        )
                        for author in item['artists']
                    ],
                    thumbnail_url = None,
                    duration = timedelta(milliseconds = item['duration_ms'])
                )
                for item in json['items']
            ]

        except KeyError:
            raise SpotifyExtractError(json)


    @classmethod
    def get_playlist(cls, url: str) -> list[SpotifySong]:
        cls.call_refresh()
        playlist_id = url.split('playlist/')[1].split('?')[0]

        query = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        json = cls.get_response(query)

        try:
            return [
                SpotifySong(
                    name = item['track']['name'],
                    url = item['track']['external_urls']['spotify'],
                    authors = [
                        Author(
                            name = author['name'],
                            url = author['external_urls']['spotify']
                        )
                        for author in item['track']['artists']
                    ],
                    thumbnail_url = item['track']['album']['images'][0]['url'],
                    duration = timedelta(milliseconds = item['track']['duration_ms'])
                )
                for item in json['items']
            ]

        except KeyError:
            raise SpotifyExtractError(json)


    @classmethod
    def get_artist(cls, url) -> list[SpotifySong]:
        cls.call_refresh()
        # TODO: finish
        artist_id = url.split('artist/')[1].split('?')[0]

        artist_query = f'https://api.spotify.com/v1/artists/{artist_id}/tracks'
        print(artist_query)
        artist_json = cls.get_response(artist_query)
        print(artist_json)


    @classmethod
    def get_response(cls, query: str) -> dict:
        response = get(
            query,
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {cls.spotify_token}'
            }
        )
        return response.json()


    @classmethod
    def call_refresh(cls) -> None:
        response = post(
            'https://accounts.spotify.com/api/token',
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            },
            headers = {
                'Authorization': 'Basic ' + base_64
            }
        )
        response_json = response.json()
        cls.spotify_token = response_json['access_token']


link = 'https://open.spotify.com/album/6pUg9RDDoVyQQVJ48FkmXz'
SpotifyInfo.get_album(link)
