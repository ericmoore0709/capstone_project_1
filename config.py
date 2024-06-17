import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 'postgresql://username:password@localhost/yourdatabase')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
    SPOTIFY_CLIENT_SCOPE = os.environ.get('SPOTIFY_CLIENT_SCOPE')
    SPOTIFY_CLIENT_REDIRECT_URI = os.environ.get('SPOTIFY_CLIENT_REDIRECT_URI')
