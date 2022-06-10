import json, requests
from secrets import spotify_user_id
from refresh import Refresh


class GetSongs:
    def __init__(self, link):
        self.user_id = spotify_user_id
        self.spotify_token = ''
        self.link = link


    def find_songs(self):        
        playlist_id = self.link.split('playlist/')[1].split('?')[0]
        query = 'https://api.spotify.com/v1/playlists/{}/tracks'.format(playlist_id)

        response = requests.get(query, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(self.spotify_token)})

        response_json = response.json()

        lista = []

        for i in response_json['items']:
            data = i['track']
            name = data['name']
            artist = data['album']['artists'][0]['name']
            lista.append(f'{name} {artist}')

        return lista
    

    def call_refresh(self):
        print('Refreshing token...')
        refreshCaller = Refresh()
        self.spotify_token = refreshCaller.refresh()
        lista = self.find_songs()

        return lista