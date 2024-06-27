from datetime import UTC, datetime
from models import PlaylistMetadata, User, db


def set_user(user_id, access_token, refresh_token):
    """ Creates user if not exists, or updates user info if exists. """

    user = User.query.filter_by(spotify_id=user_id).first()
    if user is None:
        user = User(
            spotify_id=user_id, access_token=access_token, refresh_token=refresh_token)
        db.session.add(user)
    else:
        user.access_token = access_token
        user.refresh_token = refresh_token

    db.session.commit()


def get_user(spotify_user_id):
    """ Gets the user from the database """
    return User.query.filter_by(spotify_id=spotify_user_id).first()


def set_playlists(playlists, user):
    """ Persists playlists and playlist metadata to database. """
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


def filter_playlists_for_track_insert(playlists, user_id):
    """ Filters user's playlists by ownership and returns (id, name) tuples."""

    return [(playlist.get('id'), playlist.get('name'))
            for playlist in playlists
            if playlist.get('owner').get('id') == user_id]
