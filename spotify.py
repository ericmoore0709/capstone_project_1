from base64 import b64encode

from flask import jsonify
from os import environ

import requests

BASE_URI = 'https://api.spotify.com/v1'


class Spotify:

    def __init__(self, secrets):
        self.secrets = secrets

    def build_auth_url(self, state):
        """ Builds the Spotify Authorization URL for Spotify Authorization Redirection """

        client_id = self.secrets['SPOTIFY_CLIENT_ID']
        redirect_uri = self.secrets['SPOTIFY_CLIENT_REDIRECT_URI']
        client_scope = self.secrets['SPOTIFY_CLIENT_SCOPE']

        # build authorization URL and redirect
        auth_url = 'https://accounts.spotify.com/authorize/'
        auth_url_str = f"""{auth_url}?client_id={client_id}&response_type=code&redirect_uri={
            redirect_uri}&scope={client_scope}&state={state}"""

        return auth_url_str

    def build_auth_header(self):
        """ Encodes the Authorization details necessary for posting to the Spotify API Token endpoint """

        client_id = self.secrets['SPOTIFY_CLIENT_ID']
        client_secret = self.secrets['SPOTIFY_CLIENT_SECRET']

        basic_auth_encode = f"""{client_id}:{client_secret}"""
        encoded_auth = b64encode(basic_auth_encode.encode('utf-8')).decode()
        return encoded_auth

    def get_token(self, code):
        """ Attempts to post to the Spotify API Token endpoint. 
            Returns `error` if unsucessesful.
            Returns `access_token`, `refresh_token`, and `user_id` if successful.  """

        redirect_uri = self.secrets['SPOTIFY_CLIENT_REDIRECT_URI']

        encoded_auth = self.build_auth_header()

        token_response = requests.post('https://accounts.spotify.com/api/token',
                                       data={
                                           'code': code,
                                           'redirect_uri': redirect_uri,
                                           'grant_type': 'authorization_code'
                                       },
                                       headers={
                                           'content-type': 'application/x-www-form-urlencoded',
                                           'Authorization': f'Basic {encoded_auth}'
                                       }).json()

        if 'error' in token_response:
            error = token_response['error']
            print(f'Spotify Token Error: {error}')
            return 'error'
        else:
            access_token = token_response.get('access_token')
            refresh_token = token_response.get('refresh_token')
            user_id = self._get_userid(access_token)

            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_id': user_id
            }

    def get_user_playlists(self, token):
        """ Attempts to get playlists from Spotify User's profile. """

        playlists_json = requests.get(
            f'{BASE_URI}/me/playlists', headers={'Authorization': f'Bearer {token}'}).json()

        playlists = playlists_json.get('items', [])
        return playlists

    def _get_userid(self, token):
        """Returns the user ID from the auth token."""
        if not token:
            return None

        try:
            user_data = requests.get(
                f'{BASE_URI}/me', headers={'Authorization': f'Bearer {token}'})
            if user_data.status_code == 200:
                user_id = user_data.json().get('id')
                if user_id:
                    return user_id
                else:
                    raise Exception(
                        'Failed to retrieve user_id from user_data.')
            else:
                raise Exception(f'''user_data returned status code of {
                                user_data.status_code}''')
        except Exception as e:
            print(f'Get UserID Error: {e}')
            return None

    def get_playlist_details(self, playlist_id, token):
        """ Attempts to get track list from Spotify playlist."""

        playlist_response = requests.get(
            f'{BASE_URI}/playlists/{playlist_id}',
            headers={'Authorization': f'Bearer {token}'}
        )

        if playlist_response.status_code == 200:
            playlist_json = playlist_response.json()
            playlist_title = playlist_json.get('name')

            return {
                'playlist_json': playlist_json,
                'playlist_title': playlist_title
            }

    def process_search_request(self, search_term, token):
        """ Attempts to retrieve track info from Spotify's search endpoint. """
        search_request = requests.get(
            f'{BASE_URI}/search',
            params={
                'q': search_term,
                'limit': 5,
                'type': 'track'
            },
            headers={
                'Authorization': f'Bearer {token}'
            }
        )

        return search_request.json()

    def get_track(self, track_id, token):
        """Attempts to get track details from Spotify API"""

        track_response = requests.get(
            f'{BASE_URI}/tracks/{track_id}', headers={'Authorization': f'Bearer {token}'})

        return track_response.json()

    def add_track_to_playlist(self, playlist_id, track_uri, token):
        """ Attempts to add track to Spotify playlist."""

        return requests.post(
            f'{BASE_URI}/playlists/{playlist_id}/tracks',
            json={'uris': [track_uri]},
            headers={'Authorization': f'Bearer {token}'}
        ).json()

    def remove_track_from_playlist(self, playlist_id, track_uri, token):
        """Attempts to remove track from Spotify playlist"""

        remove_response = requests.delete(
            f'{BASE_URI}/playlists/{playlist_id}/tracks',
            json={'tracks': [{'uri': track_uri}]},
            headers={'Authorization': f'Bearer {token}'}
        )

        return jsonify(remove_response.json(), remove_response.status_code)

    def create_playlist(self, user_id, playlist_title, playlist_description, token):
        """ Attempts to create Spotify playlist """

        playlist_add_response = requests.post(
            f'{BASE_URI}/users/{user_id}/playlists',
            json={'name': playlist_title, 'description': playlist_description},
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})

        return jsonify(playlist_add_response.json())
