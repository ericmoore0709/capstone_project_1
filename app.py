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

            print(token_response)

            if 'error' in token_response:
                flash(token_response['error'], 'danger')
                return redirect('/')

            else:
                session['token'] = token_response['access_token']
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
        playlists = requests.get(
            (BASE_URI + '/me/playlists'), headers={'Authorization': ('Bearer ' + token)})
        print(playlists.status_code)
        print(playlists.json())
        return render_template('playlists.html', playlists=playlists.json())

    except Exception as err:
        print(type(err).__name__ + ': ' + str(err))
        flash('Failed to retrieve playlists.', 'danger')
        return redirect('/dashboard')
