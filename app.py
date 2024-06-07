"""Flask app for Cupcakes"""
from base64 import b64encode
import requests
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, render_template, redirect, request, session
import os
from uuid import uuid4

load_dotenv('.env')

# import .env variables
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_CLIENT_SCOPE = os.environ.get('SPOTIFY_CLIENT_SCOPE')
SPOTIFY_CLIENT_REDIRECT_URI = os.environ.get('SPOTIFY_CLIENT_REDIRECT_URI')

BASE_URI = 'https://api.spotify.com/v1'

app = Flask(__name__)
app.config['SECRET_KEY'] = str(uuid4())


@app.get('/')
def index():
    if session.get('token'):
        return redirect('/dashboard')
    return render_template('/index.html')


@app.get('/authorize')
def authorize():
    """Attempt to authorize user through Spotify API"""

    try:

        # create and set session state
        SESSION_STATE = uuid4()
        session['state'] = SESSION_STATE

        # build authorization URL and redirect
        AUTH_URL = 'https://accounts.spotify.com/authorize/'

        AUTH_URL_STR = str.format(
            '{}?client_id={}&response_type=code&redirect_uri={}&scope={}&state={}',
            AUTH_URL, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_REDIRECT_URI, SPOTIFY_CLIENT_SCOPE, SESSION_STATE)

        return redirect(AUTH_URL_STR)
    except:
        flash('Failed to retrieve Spotify authorization endpoint.', 'danger')
        return redirect('/')


@app.get('/redirect')
def on_redirect():

    try:
        code = request.args.get('code', '')

        if code:
            # send token API call
            basic_auth_encode = SPOTIFY_CLIENT_ID + ':' + SPOTIFY_CLIENT_SECRET
            encoded_auth = str(b64encode(str.encode(
                basic_auth_encode, 'utf-8')).decode())

            token_response = requests.post('https://accounts.spotify.com/api/token',
                                           data={
                                               'code': code,
                                               'redirect_uri': SPOTIFY_CLIENT_REDIRECT_URI,
                                               'grant_type': 'authorization_code'
                                           },
                                           headers={
                                               'content-type': 'application/x-www-form-urlencoded',
                                               'Authorization': 'Basic ' + encoded_auth
                                           }
                                           ).json()

            if 'error' in token_response:
                flash(token_response['error'], 'danger')
                return redirect('/')

            else:
                session['token'] = token_response['access_token']
                session['user_id'] = _get_userid()
                flash('Authorization successful!', 'success')
                return redirect('/dashboard')

        else:
            error = request.args.get('error', '')
            if error:
                print(error)
                flash(error, 'danger')
                return redirect('/')

        return redirect('/')
    except:
        flash('Failed to authorize user.')
        return redirect('/')


@app.get('/dashboard')
def display_dashboard():
    if not session.get('token'):
        flash('No session detected. Please Authorize.', 'danger')
        return redirect('/')

    return render_template('dashboard.html')


@app.get('/logout')
def process_logout():
    session.pop('state')
    session.pop('token')
    return redirect('/')


@app.get('/playlists')
def display_playlists():
    token = session.get('token', '')
    if not token:
        return redirect('/')

    try:
        playlists_json = requests.get(
            (BASE_URI + '/me/playlists'), headers={'Authorization': ('Bearer ' + token)}).json()
        playlists = playlists_json.get('items', [])
        return render_template('playlists.html', playlists=playlists)

    except Exception as err:
        print(type(err).__name__ + ': ' + str(err))
        flash('Failed to retrieve playlists.', 'danger')
        return redirect('/dashboard')


@app.get('/playlists/<string:playlist_id>')
def display_playlist_details(playlist_id: str):

    token = session.get('token', '')
    if not token:
        return redirect('/')

    try:
        playlist_response = requests.get(
            (BASE_URI + '/playlists/' + playlist_id),
            headers={'Authorization': ('Bearer ' + token)})

        if playlist_response.status_code == 200:
            playlist_json = playlist_response.json()
            return render_template('playlist.html', playlist=playlist_json)

    except Exception as err:
        print(type(err).__name__ + ': ' + str(err))
        flash('Failed to retrieve playlist details.', 'danger')
        return redirect('/playlists')


@app.post('/searchbar')
def retrieve_search_results():

    token = session.get('token', '')
    if not token:
        return redirect('/')

    try:
        search_term = request.json.get('q', '')

        search_request = requests.get(
            (BASE_URI + '/search'), params={'q': search_term, 'limit': 5, 'type': 'track'}, headers={'Authorization': ('Bearer ' + token)})

        return search_request.json()

    except Exception as err:
        flash('Backend search failed. Please try again.', 'danger')
        return redirect('/')


@app.get('/track/<string:track_id>')
def display_track(track_id: str):
    token = session.get('token', '')
    if not token:
        return redirect('/')

    try:
        track_response = requests.get(
            (BASE_URI + '/tracks/' + track_id), headers={'Authorization': ('Bearer ' + token)})

        playlist_response = requests.get(
            (BASE_URI + '/me/playlists'), headers={'Authorization': ('Bearer ' + token)}).json()

        playlists = [(playlist.get('id'), playlist.get('name'))
                     for playlist in playlist_response.get('items') if playlist.get('owner').get('id') == session['user_id']]

        return render_template('track.html', track=track_response.json(), playlists=playlists)

    except Exception as err:
        print(err)
        flash('Failed to retrieve track. Please try again.', 'danger')
        return redirect('/')


@app.post('/addtrack')
def add_track_to_playlist():
    token = session.get('token', '')
    if not token:
        return redirect('/')

    # get track id and playlist id from request
    track_uri = request.json.get('track_uri', '')
    playlist_id = request.json.get('playlist_id', '')

    print(track_uri)
    print(playlist_id)

    if not playlist_id:
        return jsonify({'error': 'Playlist required.'})

    try:

        # attempt to call spotify API to append track to playlist
        action_response = requests.post(
            (BASE_URI + '/playlists/' + playlist_id + '/tracks'),
            json={'uris': [track_uri]},
            headers={'Authorization': ('Bearer ' + token)}
        )

        print(action_response.status_code)
        print(action_response.json())

        return action_response.json()

    except Exception as err:
        print(err)
        return jsonify({'error': 'internal error occurred.'})


@app.delete('/playlists/<string:playlist_id>/tracks')
def remove_track(playlist_id: str):
    # boot out user if not authenticated
    token = session.get('token', '')
    if not token:
        return redirect('/')

    # get track URI from request
    track_uri = request.json.get('track_uri', '')

    # make API call
    remove_response = requests.delete(
        (f'{BASE_URI}/playlists/{playlist_id}/tracks'),
        json={'tracks': [{'uri': track_uri}]},
        headers={'Authorization': f'Bearer {token}',
                 'Content-Type': 'application/json'}
    )

    print(remove_response.status_code)
    print(remove_response.json())

    # return response
    return jsonify(remove_response.json(), remove_response.status_code)


def _get_userid():
    token = session.get('token', '')
    if not token:
        return

    try:
        user_data = requests.get(
            (BASE_URI + '/me'), headers={'Authorization': ('Bearer ' + token)})

        if user_data.status_code == 200:
            user_id = user_data.json().get('id')
            if user_id:
                return user_id
            else:
                raise Exception('Failed to retrieve user_id from user_data.')
        else:
            raise Exception(
                ('user_data returned status code of ' + str(user_data.status_code)))
    except Exception as err:
        print(err)
