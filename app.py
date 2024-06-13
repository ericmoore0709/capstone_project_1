"""Flask app for Spotify API"""
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
if __name__ == 'main':
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT)


@app.get('/')
def index():
    """Direct user to either landing page or dashboard."""

    # if logged in, direct to dashboard
    if session.get('token'):
        return render_template('dashboard.html', title='Dashboard')

    # else, direct to landing page
    return render_template('/index.html', title='Landing Page')


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
        # flash error and redirect
        flash('Failed to retrieve Spotify authorization endpoint.', 'danger')
        return redirect('/')


@app.get('/redirect')
def on_redirect():
    """ Get the user auth token from Spotify and redirect the user."""

    try:
        # get code from Spotify redirection
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

            # handle token response error, if exists
            if 'error' in token_response:
                flash(token_response['error'], 'danger')
                return redirect('/')

            # set session variables, alert user of success, and redirect
            else:
                session['token'] = token_response['access_token']
                session['user_id'] = _get_userid()
                flash('Authorization successful!', 'success')
                return redirect('/')

        # if no code was provided, an error occurred.
        else:
            error = request.args.get('error', '')
            if error:
                print(error)
                flash(error, 'danger')
                return redirect('/')

        return redirect('/')
    except:
        # auth failed. Alert and redirect user
        flash('Failed to authorize user.')
        return redirect('/')


@app.get('/logout')
def process_logout():
    """Log out the user."""

    # remove session variables and redirect
    session.pop('state')
    session.pop('token')
    return redirect('/')


@app.get('/playlists')
def display_playlists():
    """Display the list of playlists saved to the user's library."""

    # boot out user if not authenticated
    token = session.get('token', '')
    if not token:
        return redirect('/')

    try:
        # attempt to retrieve playlists from Spotify
        playlists_json = requests.get(
            (BASE_URI + '/me/playlists'), headers={'Authorization': ('Bearer ' + token)}).json()
        playlists = playlists_json.get('items', [])
        return render_template('playlists.html', playlists=playlists, title='My Playlists')

    except Exception as err:
        print(type(err).__name__ + ': ' + str(err))
        flash('Failed to retrieve playlists.', 'danger')
        return redirect('/')


@app.get('/playlists/<string:playlist_id>')
def display_playlist_details(playlist_id: str):
    """Display the tracklist of the selected playlist."""

    # boot out user if not authenticated
    token = session.get('token', '')
    if not token:
        return redirect('/')

    try:
        # attempt to retrieve playlist
        playlist_response = requests.get(
            (BASE_URI + '/playlists/' + playlist_id),
            headers={'Authorization': ('Bearer ' + token)})

        # display the playlist if successful
        if playlist_response.status_code == 200:
            playlist_json = playlist_response.json()
            playlist_title = playlist_json.get('name')
            return render_template('playlist.html', playlist=playlist_json, title=playlist_title)

    except Exception as err:
        # there was an error. Alert the user and redirect to playlist list page
        print(type(err).__name__ + ': ' + str(err))
        flash('Failed to retrieve playlist details.', 'danger')
        return redirect('/playlists')


@app.post('/searchbar')
def retrieve_search_results():
    """JSON Query tracks for the navbar searchbar."""

    # boot out user if not authenticated
    token = session.get('token', '')
    if not token:
        return redirect('/')

    try:
        search_term = request.json.get('q', '')

        # attempt to query five tracks from the given q text.
        search_request = requests.get(
            (BASE_URI + '/search'), params={'q': search_term, 'limit': 5, 'type': 'track'}, headers={'Authorization': ('Bearer ' + token)})

        return search_request.json()

    except Exception as err:
        flash('Backend search failed. Please try again.', 'danger')
        return redirect('/')


@app.get('/track/<string:track_id>')
def display_track(track_id: str):
    """Display the selected track (likely to add to a playlist)."""

    # boot out user if not authenticated
    token = session.get('token', '')
    if not token:
        return redirect('/')

    try:
        # retrieve the track from the Spotify API
        track_response = requests.get(
            (BASE_URI + '/tracks/' + track_id), headers={'Authorization': ('Bearer ' + token)})

        # retrieve the list of playlists for playlist selection
        playlist_response = requests.get(
            (BASE_URI + '/me/playlists'), headers={'Authorization': ('Bearer ' + token)}).json()

        # filter in only the id and name of each playlist (because we don't need the rest)
        playlists = [(playlist.get('id'), playlist.get('name'))
                     for playlist in playlist_response.get('items') if playlist.get('owner').get('id') == session['user_id']]

        track_name = track_response.get('name')

        return render_template('track.html', track=track_response.json(), playlists=playlists, title=track_name)

    except Exception as err:
        print(err)
        flash('Failed to retrieve track. Please try again.', 'danger')
        return redirect('/')


@app.post('/addtrack')
def add_track_to_playlist():
    """Add selected track to selected playlist."""

    # boot out user if not authenticated
    token = session.get('token', '')
    if not token:
        return redirect('/')

    # get track id and playlist id from request
    track_uri = request.json.get('track_uri', '')
    playlist_id = request.json.get('playlist_id', '')

    # return error if playlist_id not provided
    if not playlist_id:
        return jsonify({'error': 'Playlist required.'})

    try:

        # attempt to call spotify API to append track to playlist
        action_response = requests.post(
            (BASE_URI + '/playlists/' + playlist_id + '/tracks'),
            json={'uris': [track_uri]},
            headers={'Authorization': ('Bearer ' + token)}
        )

        return action_response.json()

    except Exception as err:
        print(err)
        return jsonify({'error': 'internal error occurred.'})


@app.delete('/playlists/<string:playlist_id>/tracks')
def remove_track(playlist_id: str):
    """Remove selected track from playlist."""

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

    # return response
    return jsonify(remove_response.json(), remove_response.status_code)


@app.post('/playlists')
def create_playlist():
    """Create a playlist."""
    # boot out user if not authenticated
    token = session.get('token', '')
    if not token:
        return redirect('/')

    # get title and optional description from request
    title = request.json.get('title', '')
    description = request.json.get('description', '')

    if not title:
        return jsonify({'error': 'title is required'})

    user_id = session.get('user_id')

    playlist_add_response = requests.post(
        (f'{BASE_URI}/users/{user_id}/playlists'),
        json={'name': title, 'description': description},
        headers={'Authorization': f'Bearer {token}',
                 'Content-Type': 'application/json'}
    )

    return jsonify(playlist_add_response.json())


def _get_userid():
    """Returns the user ID from the auth token."""
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
