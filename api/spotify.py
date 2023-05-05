from requests import get, post
from datetime import timedelta
from dataclasses import dataclass

from utils import SpotifyExtractError
from settings import REFRESH_TOKEN, BASE_64


@dataclass
class Author:
    def __init__(self, name: str = 'No author', url: str = 'https://example.com/'):
        self.name = name
        self.url = url

    def print_with_url_format(self, new_line=False) -> str:
        name_with_url = f'[{self.name}]({self.url})'
        return f'{name_with_url}\n' if new_line else name_with_url

    def __repr__(self) -> str:
        return f'Name: {self.name} | url: {self.url}'


@dataclass
class SpotifySong:
    def __init__(
            self,
            name=None,
            url=None,
            authors=None,
            thumbnail_url=None,
            duration=None,
            audio_features=None,
            error=None):
        self.name = name
        self.url = url
        self.authors = authors
        self.thumbnail_url = thumbnail_url
        self.duration = duration
        self.audio_features = audio_features
        self.error = error

    def __repr__(self) -> str:
        return f'Name: {self.name:<50} | url: {self.url}'


class SpotifyInfo:
    spotify_token = ''

    @classmethod
    def spotify_get(cls, query) -> list[SpotifySong]:
        if '/track/' in query:
            return [cls.__get_track(query)]
        elif '/album/' in query:
            return cls.__get_album(query)
        elif '/playlist/' in query:
            return cls.__get_playlist(query)
        elif '/artist/' in query:
            return cls.__get_artist(query)
        else:
            return [cls.__search_spotify(query)]

    @classmethod
    def __get_track(cls, url: str) -> SpotifySong:
        cls.__call_refresh()

        track_id = url.split('track/')[1].split('?')[0]
        query = f'https://api.spotify.com/v1/tracks/{track_id}'
        data = cls.__get_response(query)

        try:
            song = SpotifySong(
                name=data['name'],
                url=url,
                authors=[
                    Author(
                        name=author['name'],
                        url=author['external_urls']['spotify']
                    )
                    for author in data['artists']
                ],
                thumbnail_url=data['album']['images'][-1]['url'],
                duration=timedelta(milliseconds=data['duration_ms'])
            )
            return song
        except KeyError:
            raise SpotifyExtractError(data)

    @classmethod
    def __search_spotify(cls, query: str) -> SpotifySong:
        cls.__call_refresh()

        query_parameter = query.replace(' ', '%20')
        query = f'https://api.spotify.com/v1/search?q={query_parameter}&type=track&limit=1&offset=0'
        data = cls.__get_response(query)

        try:
            item = data['tracks']['items'][0]

            return SpotifySong(
                name=item['name'],
                url=item['external_urls']['spotify'],
                authors=[
                    Author(
                        name=author['name'],
                        url=author['external_urls']['spotify']
                    )
                    for author in item['artists']
                ],
                thumbnail_url=item['album']['images'][0]['url'],
                duration=timedelta(milliseconds=item['duration_ms'])
            )
        except KeyError:
            raise SpotifyExtractError(data)

    @classmethod
    def __get_album(cls, url: str) -> list[SpotifySong]:
        cls.__call_refresh()

        album_id = url.split("album/")[1].split("?")[0]
        query = f'https://api.spotify.com/v1/albums/{album_id}/tracks'
        data = cls.__get_response(query)

        try:
            return [
                SpotifySong(
                    name=item['name'],
                    url=item['external_urls']['spotify'],
                    authors=[
                        Author(
                            name=author['name'],
                            url=author['external_urls']['spotify']
                        )
                        for author in item['artists']
                    ],
                    thumbnail_url='https://example.com',
                    duration=timedelta(milliseconds=item['duration_ms'])
                )
                for item in data['items']
            ]
        except KeyError:
            raise SpotifyExtractError(data)

    @classmethod
    def __get_playlist(cls, url: str) -> list[SpotifySong]:
        cls.__call_refresh()

        playlist_id = url.split('playlist/')[1].split('?')[0]
        query = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        data = cls.__get_response(query)

        try:
            return [
                SpotifySong(
                    name=item['track']['name'],
                    url=item['track']['external_urls']['spotify'],
                    authors=[
                        Author(
                            name=author['name'],
                            url=author['external_urls']['spotify']
                        )
                        for author in item['track']['artists']
                    ],
                    thumbnail_url=item['track']['album']['images'][0]['url'],
                    duration=timedelta(milliseconds=item['track']['duration_ms'])
                )
                for item in data['items']
            ]
        except KeyError:
            raise SpotifyExtractError(data)

    @classmethod
    def __get_artist(cls, url) -> list[SpotifySong]:
        cls.__call_refresh()
        artist_id = url.split('artist/')[1].split('?')[0]

        query = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=US'
        data = cls.__get_response(query)

        try:
            return [
                SpotifySong(
                    name=item['name'],
                    url=item['external_urls']['spotify'],
                    authors=[
                        Author(
                            name=author['name'],
                            url=author['external_urls']['spotify']
                        )
                        for author in item['artists']
                    ],
                    thumbnail_url=item['album']['images'][0]['url'],
                    duration=timedelta(milliseconds=item['duration_ms'])
                )
                for item in data['tracks']
            ]
        except KeyError:
            raise SpotifyExtractError(data)

    @classmethod
    def __get_response(cls, query: str) -> dict:
        response = get(
            query,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {cls.spotify_token}'
            }
        )
        return response.json()

    @classmethod
    def __call_refresh(cls) -> None:
        response = post(
            'https://accounts.spotify.com/api/token',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': REFRESH_TOKEN
            },
            headers={
                'Authorization': f'Basic {BASE_64}'
            }
        )
        response_json = response.json()
        cls.spotify_token = response_json['access_token']
