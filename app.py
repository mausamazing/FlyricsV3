from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
from genius_scraper import GeniusScraper
import threading
import time
import json
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize Spotify client
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
        scope="user-read-currently-playing user-read-playback-state"
    )

# Initialize Genius scraper
genius_scraper = GeniusScraper()

# Global variables to store current song and lyrics
current_song_data = {
    'name': None,
    'artist': None,
    'lyrics': None,
    'lyrics_url': None,
    'timestamp': None
}

# Monitoring state
is_monitoring = False
monitoring_thread = None

def get_spotify_client():
    """Get Spotify client with current token"""
    try:
        token_info = session.get('token_info')
        if token_info:
            return spotipy.Spotify(auth=token_info['access_token'])
        return None
    except:
        return None

def get_currently_playing():
    """Get currently playing song from Spotify"""
    try:
        sp = get_spotify_client()
        if not sp:
            return None
            
        current_track = sp.currently_playing()
        
        if current_track and current_track['is_playing']:
            track = current_track['item']
            return {
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'id': track['id'],
                'is_playing': True,
                'progress_ms': current_track['progress_ms'],
                'duration_ms': track['duration_ms'],
                'album': track['album']['name'],
                'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None
            }
        return None
    except Exception as e:
        print(f"Error getting currently playing: {e}")
        return None

def fetch_lyrics_for_song(song_name, artist_name):
    """Fetch lyrics for a song using Genius scraper"""
    try:
        print(f"🎵 Fetching lyrics for: {song_name} by {artist_name}")
        lyrics_data = genius_scraper.get_lyrics_for_song(song_name, artist_name)
        
        if lyrics_data:
            return {
                'lyrics': lyrics_data['lyrics'],
                'url': lyrics_data['url'],
                'success': True
            }
        else:
            return {
                'lyrics': "❌ Lyrics not found for this song.",
                'url': None,
                'success': False
            }
    except Exception as e:
        print(f"Error fetching lyrics: {e}")
        return {
            'lyrics': f"❌ Error fetching lyrics: {str(e)}",
            'url': None,
            'success': False
        }

def monitor_spotify():
    """Background thread to monitor Spotify for song changes"""
    global current_song_data, is_monitoring
    
    last_song_id = None
    
    while is_monitoring:
        try:
            current_song = get_currently_playing()
            
            if current_song and current_song['id'] != last_song_id:
                print(f"🔄 New song detected: {current_song['name']} by {current_song['artist']}")
                
                # Update current song data
                current_song_data.update({
                    'name': current_song['name'],
                    'artist': current_song['artist'],
                    'lyrics': "🔄 Fetching lyrics...",
                    'lyrics_url': None,
                    'timestamp': datetime.now().isoformat(),
                    'album': current_song['album'],
                    'album_art': current_song['album_art'],
                    'progress_ms': current_song['progress_ms'],
                    'duration_ms': current_song['duration_ms']
                })
                
                # Fetch lyrics in background
                def fetch_lyrics_background():
                    lyrics_result = fetch_lyrics_for_song(current_song['name'], current_song['artist'])
                    current_song_data.update({
                        'lyrics': lyrics_result['lyrics'],
                        'lyrics_url': lyrics_result['url'],
                        'success': lyrics_result['success']
                    })
                    print("✅ Lyrics updated")
                
                # Start lyrics fetching in background thread
                lyrics_thread = threading.Thread(target=fetch_lyrics_background)
                lyrics_thread.daemon = True
                lyrics_thread.start()
                
                last_song_id = current_song['id']
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"Error in monitoring thread: {e}")
            time.sleep(10)

# Authentication routes
@app.route('/login')
def login():
    """Redirect to Spotify authentication"""
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Spotify callback route"""
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/')
def index():
    """Main page"""
    # Check if user is authenticated
    token_info = session.get('token_info')
    is_authenticated = bool(token_info)
    
    return render_template('index.html', 
                         is_authenticated=is_authenticated,
                         current_song=current_song_data)

@app.route('/api/current_song')
def api_current_song():
    """API endpoint to get current song data"""
    try:
        # Check authentication
        if not get_spotify_client():
            return jsonify({'error': 'Not authenticated', 'authenticated': False})
        
        # Get fresh data from Spotify
        current_song = get_currently_playing()
        
        response_data = {**current_song_data, 'authenticated': True}
        
        if current_song:
            # Check if we need to fetch new lyrics
            if (not current_song_data.get('name') or 
                current_song_data.get('name') != current_song['name'] or
                current_song_data.get('artist') != current_song['artist']):
                
                # Update current song data
                current_song_data.update({
                    'name': current_song['name'],
                    'artist': current_song['artist'],
                    'lyrics': "🔄 Fetching lyrics...",
                    'lyrics_url': None,
                    'timestamp': datetime.now().isoformat(),
                    'album': current_song['album'],
                    'album_art': current_song['album_art'],
                    'progress_ms': current_song['progress_ms'],
                    'duration_ms': current_song['duration_ms'],
                    'success': None,
                    'lyrics_ready': False
                })
                
                # Fetch lyrics in background
                def fetch_lyrics():
                    lyrics_result = fetch_lyrics_for_song(current_song['name'], current_song['artist'])
                    current_song_data.update({
                        'lyrics': lyrics_result['lyrics'],
                        'lyrics_url': lyrics_result['url'],
                        'success': lyrics_result['success'],
                        'lyrics_ready': True
                    })
                    print(f"✅ Lyrics fetched for {current_song['name']}")
                
                threading.Thread(target=fetch_lyrics).start()
            
            # Update the response with latest data
            response_data.update(current_song_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'name': None,
            'artist': None,
            'lyrics': f"❌ Error: {str(e)}",
            'authenticated': True
        })

@app.route('/api/lyrics/<song_name>/<artist_name>')
def api_lyrics(song_name, artist_name):
    """API endpoint to manually fetch lyrics for a specific song"""
    try:
        lyrics_result = fetch_lyrics_for_song(song_name, artist_name)
        return jsonify(lyrics_result)
    except Exception as e:
        return jsonify({
            'lyrics': f"❌ Error: {str(e)}",
            'url': None,
            'success': False
        })

@app.route('/api/monitoring/start')
def api_start_monitoring():
    """Start automatic monitoring"""
    global is_monitoring, monitoring_thread
    
    # Check authentication
    if not get_spotify_client():
        return jsonify({'status': 'error', 'message': 'Not authenticated'})
    
    if not is_monitoring:
        is_monitoring = True
        monitoring_thread = threading.Thread(target=monitor_spotify)
        monitoring_thread.daemon = True
        monitoring_thread.start()
        return jsonify({'status': 'started', 'message': 'Monitoring started'})
    else:
        return jsonify({'status': 'already_running', 'message': 'Monitoring already running'})

@app.route('/api/monitoring/stop')
def api_stop_monitoring():
    """Stop automatic monitoring"""
    global is_monitoring
    is_monitoring = False
    return jsonify({'status': 'stopped', 'message': 'Monitoring stopped'})

@app.route('/api/monitoring/status')
def api_monitoring_status():
    """Get monitoring status"""
    return jsonify({'monitoring': is_monitoring, 'authenticated': bool(get_spotify_client())})

@app.route('/api/save_lyrics')
def api_save_lyrics():
    """Save current lyrics to file"""
    try:
        if current_song_data.get('name') and current_song_data.get('lyrics'):
            filename = f"lyrics_{current_song_data['name'].replace(' ', '_')}_{current_song_data['artist'].replace(' ', '_')}.txt"
            
            lyrics_data = {
                'title': current_song_data['name'],
                'artist': current_song_data['artist'],
                'lyrics': current_song_data['lyrics'],
                'url': current_song_data.get('lyrics_url', '')
            }
            
            success = genius_scraper.save_lyrics_to_file(lyrics_data, filename)
            
            if success:
                return jsonify({'status': 'success', 'filename': filename})
            else:
                return jsonify({'status': 'error', 'message': 'Failed to save file'})
        else:
            return jsonify({'status': 'error', 'message': 'No lyrics to save'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/search')
def api_search():
    """Search for songs on Spotify"""
    try:
        # Check authentication
        sp = get_spotify_client()
        if not sp:
            return jsonify({'error': 'Not authenticated'})
        
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'No query provided'})
        
        results = sp.search(q=query, type='track', limit=10)
        tracks = []
        
        for item in results['tracks']['items']:
            tracks.append({
                'name': item['name'],
                'artist': item['artists'][0]['name'],
                'album': item['album']['name'],
                'id': item['id'],
                'album_art': item['album']['images'][0]['url'] if item['album']['images'] else None
            })
        
        return jsonify({'tracks': tracks})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/auth_status')
def api_auth_status():
    """Check authentication status"""
    return jsonify({'authenticated': bool(get_spotify_client())})

if __name__ == '__main__':
    print("🎵 Starting Spotify Lyrics App...")
    print("📱 Server running on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)