import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, flash, jsonify, render_template, redirect, request, session
from flask_migrate import Migrate
from models import PlaylistMetadata, User, db, connect_db
import requests
from dotenv import load_dotenv
from config import Config
from base64 import b64encode
from uuid import uuid4
from datetime import datetime, UTC
import os
from functools import wraps

load_dotenv('.env')

# Configure logging
handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)
app.logger.addHandler(handler)

# Initialize database and migrations
connect_db(app)
migrate = Migrate(app, db)

app.config['SECRET_KEY'] = str(uuid4())
app.config['SESSION_COOKIE_SECURE'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600


BASE_URI = 'https://api.spotify.com/v1'

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT)

with app.app_context():
    db.create_all()


def login_required(f):
    '''Wrapper function that checks for session token before continuing. Redirects to "/" if session not found.'''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('token'):
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


@app.get('/')
def index():
    """Direct user to either landing page or dashboard."""
    if session.get('token'):
        return render_template('dashboard.html', title='Dashboard')
    return render_template('index.html', title='Landing Page')


@app.get('/authorize')
def authorize():
    """Attempt to authorize user through Spotify API"""
    try:
        # create and set session state
        session_state = str(uuid4())
        session['state'] = session_state

        # build authorization URL and redirect
        auth_url = 'https://accounts.spotify.com/authorize/'
        auth_url_str = f"""{auth_url}?client_id={Config.SPOTIFY_CLIENT_ID}&response_type=code&redirect_uri={
            Config.SPOTIFY_CLIENT_REDIRECT_URI}&scope={Config.SPOTIFY_CLIENT_SCOPE}&state={session_state}"""
        return redirect(auth_url_str)
    except Exception as e:
        app.logger.error(f'Authorization Error: {e}')
        flash('Failed to retrieve Spotify authorization endpoint.', 'danger')
        return redirect('/')


@app.get('/redirect')
def on_redirect():
    """Get the user auth token from Spotify and redirect the user."""
    try:
        code = request.args.get('code', '')
        if code:
            basic_auth_encode = f"{Config.SPOTIFY_CLIENT_ID}:{
                Config.SPOTIFY_CLIENT_SECRET}"
            encoded_auth = b64encode(
                basic_auth_encode.encode('utf-8')).decode()
            token_response = requests.post('https://accounts.spotify.com/api/token',
                                           data={
                                               'code': code,
                                               'redirect_uri': Config.SPOTIFY_CLIENT_REDIRECT_URI,
                                               'grant_type': 'authorization_code'
                                           },
                                           headers={
                                               'content-type': 'application/x-www-form-urlencoded',
                                               'Authorization': f'Basic {encoded_auth}'
                                           }).json()

            if 'error' in token_response:
                flash(token_response['error'], 'danger')
                return redirect('/')
            else:
                access_token = token_response.get('access_token')
                refresh_token = token_response.get('refresh_token')
                session['token'] = access_token
                session['refresh_token'] = refresh_token
                user_id = _get_userid()
                session['user_id'] = user_id

                user = User.query.filter_by(spotify_id=user_id).first()
                if user is None:
                    user = User(
                        spotify_id=user_id, access_token=access_token, refresh_token=refresh_token)
                    db.session.add(user)
                else:
                    user.access_token = access_token
                    user.refresh_token = refresh_token

                db.session.commit()
                flash('Authorization successful!', 'success')
                return redirect('/')
        else:
            error = request.args.get('error', '')
            if error:
                app.logger.error(f'Spotify Redirect Error: {error}')
                flash(error, 'danger')
                return redirect('/')
        return redirect('/')
    except Exception as e:
        app.logger.error(f'Authorization Redirect Error: {e}')
        flash('Failed to authorize user.')
        return redirect('/')


@app.get('/logout')
def process_logout():
    """Log out the user."""
    session.pop('state', None)
    session.pop('token', None)
    session.pop('user_id', None)
    return redirect('/')


@app.get('/playlists')
@login_required
def display_playlists():
    """Display the list of playlists saved to the user's library."""
    try:
        playlists_json = requests.get(
            f'{BASE_URI}/me/playlists', headers={'Authorization': f'Bearer {session["token"]}'}).json()
        playlists = playlists_json.get('items', [])

        user = User.query.filter_by(spotify_id=session['user_id']).first()

        for playlist in playlists:
            metadata = PlaylistMetadata.query.filter_by(
                user_id=user.id, playlist_id=playlist['id']).first()
            if metadata is None:
                metadata = PlaylistMetadata(
                    user_id=user.id, playlist_id=playlist['id'], last_synced=datetime.now(UTC))
                db.session.add(metadata)
            else:
                metadata.last_synced = datetime.now(UTC)

        db.session.commit()
        return render_template('playlists.html', playlists=playlists, title='My Playlists')
    except Exception as e:
        app.logger.error(f'Display Playlists Error: {e}')
        flash('Failed to retrieve playlists.', 'danger')
        return redirect('/')


@app.get('/playlists/<string:playlist_id>')
@login_required
def display_playlist_details(playlist_id: str):
    """Display the tracklist of the selected playlist."""
    try:
        playlist_response = requests.get(f'{BASE_URI}/playlists/{playlist_id}', headers={
                                         'Authorization': f'Bearer {session["token"]}'})
        if playlist_response.status_code == 200:
            playlist_json = playlist_response.json()
            playlist_title = playlist_json.get('name')
            return render_template('playlist.html', playlist=playlist_json, title=playlist_title)
    except Exception as e:
        app.logger.error(f'Display Playlist Details Error: {e}')
        flash('Failed to retrieve playlist details.', 'danger')
        return redirect('/playlists')


@app.post('/searchbar')
@login_required
def retrieve_search_results():
    """JSON Query tracks for the navbar searchbar."""
    try:
        search_term = request.json.get('q', '')
        search_request = requests.get(f'{BASE_URI}/search', params={'q': search_term, 'limit': 5,
                                      'type': 'track'}, headers={'Authorization': f'Bearer {session["token"]}'})
        return search_request.json()
    except Exception as e:
        app.logger.error(f'Search Error: {e}')
        flash('Backend search failed. Please try again.', 'danger')
        return redirect('/')


@app.get('/track/<string:track_id>')
@login_required
def display_track(track_id: str):
    """Display the selected track (likely to add to a playlist)."""
    try:
        track_response = requests.get(
            f'{BASE_URI}/tracks/{track_id}', headers={'Authorization': f'Bearer {session["token"]}'})
        playlist_response = requests.get(
            f'{BASE_URI}/me/playlists', headers={'Authorization': f'Bearer {session["token"]}'}).json()
        playlists = [(playlist.get('id'), playlist.get('name')) for playlist in playlist_response.get(
            'items') if playlist.get('owner').get('id') == session['user_id']]
        track_name = track_response.json().get('name')
        return render_template('track.html', track=track_response.json(), playlists=playlists, title=track_name)
    except Exception as e:
        app.logger.error(f'Display Track Error: {e}')
        flash('Failed to retrieve track. Please try again.', 'danger')
        return redirect('/')


@app.post('/addtrack')
@login_required
def add_track_to_playlist():
    """Add selected track to selected playlist."""
    track_uri = request.json.get('track_uri', '')
    playlist_id = request.json.get('playlist_id', '')

    if not playlist_id:
        return jsonify({'error': 'Playlist required.'})

    try:
        action_response = requests.post(f'{BASE_URI}/playlists/{playlist_id}/tracks', json={
                                        'uris': [track_uri]}, headers={'Authorization': f'Bearer {session["token"]}'})
        return action_response.json()
    except Exception as e:
        app.logger.error(f'Add Track Error: {e}')
        return jsonify({'error': 'Internal error occurred.'})


@app.delete('/playlists/<string:playlist_id>/tracks')
@login_required
def remove_track(playlist_id: str):
    """Remove selected track from playlist."""
    track_uri = request.json.get('track_uri', '')

    try:
        remove_response = requests.delete(f'{BASE_URI}/playlists/{playlist_id}/tracks', json={
                                          'tracks': [{'uri': track_uri}]}, headers={'Authorization': f'Bearer {session["token"]}'})
        return jsonify(remove_response.json(), remove_response.status_code)
    except Exception as e:
        app.logger.error(f'Remove Track Error: {e}')
        return jsonify({'error': 'Internal error occurred.'})


@app.post('/playlists')
@login_required
def create_playlist():
    """Create a playlist."""
    title = request.json.get('title', '')
    description = request.json.get('description', '')

    if not title:
        return jsonify({'error': 'Title is required'})

    try:
        user_id = session.get('user_id')
        playlist_add_response = requests.post(f'{BASE_URI}/users/{user_id}/playlists', json={'name': title, 'description': description}, headers={
                                              'Authorization': f'Bearer {session["token"]}', 'Content-Type': 'application/json'})
        return jsonify(playlist_add_response.json())
    except Exception as e:
        app.logger.error(f'Create Playlist Error: {e}')
        return jsonify({'error': 'Internal error occurred.'})


def _get_userid():
    """Returns the user ID from the auth token."""
    token = session.get('token', '')
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
                raise Exception('Failed to retrieve user_id from user_data.')
        else:
            raise Exception(f'user_data returned status code of {
                            user_data.status_code}')
    except Exception as e:
        app.logger.error(f'Get UserID Error: {e}')
        return None


@app.errorhandler(404)
def not_found_error(error):
    '''A handler function for 404 errors'''
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    '''A handler function for 500 errors'''
    db.session.rollback()
    app.logger.error(f'Server Error: {error}, route: {request.url}')
    return render_template('500.html'), 500
