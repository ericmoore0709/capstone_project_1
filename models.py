from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


def connect_db(app):
    db.app = app
    db.init_app(app)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(512), unique=True, nullable=False)
    access_token = db.Column(db.String(512), nullable=False)
    refresh_token = db.Column(db.String(512), nullable=False)


class PlaylistMetadata(db.Model):
    __tablename__ = 'playlist_metadata'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    playlist_id = db.Column(db.String(255), nullable=False)
    last_synced = db.Column(db.DateTime, nullable=False,
                            default=datetime.now(timezone.utc))
    custom_name = db.Column(db.String(255), nullable=True)
