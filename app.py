import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, flash, jsonify, render_template, redirect, request, session
from flask_migrate import Migrate
from model_util import filter_playlists_for_track_insert, get_user, set_playlists, set_user
from models import db, connect_db
from dotenv import load_dotenv
from config import Config
from uuid import uuid4
import os
from functools import wraps

from spotify import Spotify


load_dotenv('.env')

# Configure logging
handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)
app.logger.addHandler(handler)

# initialize homemade Spotify requests handler.
spotify = Spotify(
    secrets={
        'SPOTIFY_CLIENT_ID': Config.SPOTIFY_CLIENT_ID,
        'SPOTIFY_CLIENT_REDIRECT_URI': Config.SPOTIFY_CLIENT_REDIRECT_URI,
        'SPOTIFY_CLIENT_SCOPE': Config.SPOTIFY_CLIENT_SCOPE,
        'SPOTIFY_CLIENT_SECRET': Config.SPOTIFY_CLIENT_SECRET
    }
)

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

        # redirect to Spotify auth url
        auth_url_str = spotify.build_auth_url(session_state)
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
            # Post to Spotify token API
            result = spotify.get_token(code)

            # handle error if exists
            if result == 'error':
                flash('Error retrieving user token. Please try again later.', 'danger')
                return redirect('/')
            else:

                # get data from API result
                access_token = result.get('access_token')
                refresh_token = result.get('refresh_token')
                user_id = result.get('user_id')

                # set session variables
                session['token'] = access_token
                session['refresh_token'] = refresh_token
                session['user_id'] = user_id

                # set and persist user info
                set_user(
                    user_id=user_id,
                    access_token=access_token,
                    refresh_token=refresh_token
                )

                # redirect user with success message
                flash('Authorization successful!', 'success')
                return redirect('/')
        else:
            # handle auth code (not token) error
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

        # get the user's playlists from the Spotify API
        playlists = spotify.get_user_playlists(token=session['token'])

        # get the user from the database via session user ID
        user = get_user(session['user_id'])

        # updated playlists with metadata
        set_playlists(playlists=playlists, user=user)

        # direct user to playlist list page
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

        # get playlist details from Spotify
        result = spotify.get_playlist_details(
            playlist_id=playlist_id,
            token=session['token']
        )

        # set variables for page details
        playlist_json = result.get('playlist_json')
        playlist_title = result.get('playlist_title')

        # direct user to playlist details page
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
        # get the search term from the request
        search_term = request.json.get('q', '')

        # process the search term and return the results
        return spotify.process_search_request(search_term=search_term, token=session['token'])

    except Exception as e:
        app.logger.error(f'Search Error: {e}')
        flash('Backend search failed. Please try again.', 'danger')
        return redirect('/')


@app.get('/track/<string:track_id>')
@login_required
def display_track(track_id: str):
    """Display the selected track (likely to add to a playlist)."""
    try:
        token = session['token']

        # get the track to retrieve
        track = spotify.get_track(track_id=track_id, token=token)

        # get the user's playlists
        unfiltered_playlists = spotify.get_user_playlists(token=token)

        # filter these playlists by user's ownership, as well as mapping them to (id, name) tuples.
        filtered_playlists = filter_playlists_for_track_insert(
            playlists=unfiltered_playlists, user_id=session['user_id'])

        # get the track name (for the page title)
        track_name = track.get('name')

        # direct user to track page
        return render_template('track.html', track=track, playlists=filtered_playlists, title=track_name)
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

        result = spotify.add_track_to_playlist(
            playlist_id=playlist_id,
            track_uri=track_uri,
            token=session['token']
        )

        return result
    except Exception as e:
        app.logger.error(f'Add Track Error: {e}')
        return jsonify({'error': 'Internal error occurred.'})


@app.delete('/playlists/<string:playlist_id>/tracks')
@login_required
def remove_track(playlist_id: str):
    """Remove selected track from playlist."""
    track_uri = request.json.get('track_uri', '')

    try:
        result = spotify.remove_track_from_playlist(
            playlist_id=playlist_id,
            track_uri=track_uri,
            token=session['token']
        )

        return result
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
        # get the session user id
        user_id = session.get('user_id')

        # attempt to create the spotify playlist
        result = spotify.create_playlist(
            user_id=user_id,
            playlist_title=title,
            playlist_description=description,
            token=session['token']
        )

        # return the persistence result
        return result

    except Exception as e:
        app.logger.error(f'Create Playlist Error: {e}')
        return jsonify({'error': 'Internal error occurred.'})


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
