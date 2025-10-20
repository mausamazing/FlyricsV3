# spotify_auth.py
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import session
import json
import time

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', 'your_spotify_client_id')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', 'your_spotify_client_secret')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:5000/callback')

# Updated scopes to include currently playing track
SCOPE = 'user-read-private user-read-email user-library-read playlist-read-private user-read-currently-playing user-read-playback-state'

def create_spotify_oauth():
    """Create Spotify OAuth instance"""
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        cache_path=".spotify_cache"
    )

def get_spotify_client():
    """Get Spotify client with cached tokens"""
    sp_oauth = create_spotify_oauth()
    
    # Try to get cached token
    token_info = sp_oauth.get_cached_token()
    
    if not token_info:
        # Check if we have token in session
        if 'token_info' in session:
            token_info = session['token_info']
            
            # Check if token is expired
            if sp_oauth.is_token_expired(token_info):
                token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                session['token_info'] = token_info
        else:
            return None
    
    return spotipy.Spotify(auth=token_info['access_token'])

def save_token_to_file(token_info, user_id):
    """Save token info to local file for persistence"""
    try:
        with open('spotify_tokens.json', 'r') as f:
            tokens = json.load(f)
    except FileNotFoundError:
        tokens = {}
    
    tokens[user_id] = {
        'access_token': token_info['access_token'],
        'refresh_token': token_info['refresh_token'],
        'expires_at': token_info['expires_at'],
        'scope': token_info['scope']
    }
    
    with open('spotify_tokens.json', 'w') as f:
        json.dump(tokens, f, indent=2)

def load_token_from_file(user_id):
    """Load token info from local file"""
    try:
        with open('spotify_tokens.json', 'r') as f:
            tokens = json.load(f)
            return tokens.get(user_id)
    except FileNotFoundError:
        return None

def is_token_expired(token_info):
    """Check if token is expired"""
    return time.time() > token_info['expires_at']