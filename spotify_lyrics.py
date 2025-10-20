import spotipy
from spotipy.oauth2 import SpotifyOAuth
from genius_scraper import GeniusScraper
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SpotifyLyricsFetcher:
    def __init__(self):
        # Spotify setup
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
            scope="user-read-currently-playing"
        ))
        
        # Genius scraper
        self.genius_scraper = GeniusScraper()
        
        # Track currently processed song to avoid duplicates
        self.current_track_id = None
    
    def get_currently_playing(self):
        """
        Get currently playing song from Spotify
        """
        try:
            current_track = self.sp.currently_playing()
            
            if current_track and current_track['is_playing']:
                track = current_track['item']
                track_name = track['name']
                artist_name = track['artists'][0]['name']  # Primary artist
                track_id = track['id']
                
                return {
                    'name': track_name,
                    'artist': artist_name,
                    'id': track_id,
                    'is_playing': True
                }
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error getting currently playing track: {e}")
            return None
    
    def process_current_song(self):
        """
        Process the currently playing song and fetch lyrics
        """
        current_song = self.get_currently_playing()
        
        if not current_song:
            print("❌ No song currently playing")
            return None
        
        # Check if we've already processed this song
        if current_song['id'] == self.current_track_id:
            print("🔄 Song already processed, skipping...")
            return None
        
        print(f"\n🎵 Now Playing: {current_song['name']} by {current_song['artist']}")
        
        # Get lyrics from Genius
        lyrics_data = self.genius_scraper.get_lyrics_for_song(
            current_song['name'], 
            current_song['artist']
        )
        
        if lyrics_data:
            # Save lyrics to file
            filename = f"currently_playing_lyrics.txt"
            self.genius_scraper.save_lyrics_to_file(lyrics_data, filename)
            
            # Update current track ID
            self.current_track_id = current_song['id']
            
            return lyrics_data
        else:
            print("❌ Could not get lyrics for current song")
            return None
    
    def monitor_spotify(self, interval=30):
        """
        Continuously monitor Spotify for song changes and fetch lyrics
        """
        print("🎧 Starting Spotify lyrics monitor...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.process_current_song()
                print(f"⏳ Waiting {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopped lyrics monitor")

def main():
    """
    Main function to run the Spotify lyrics fetcher
    """
    fetcher = SpotifyLyricsFetcher()
    
    # Test with current song
    print("🧪 Testing Spotify integration...")
    print("=" * 60)
    
    lyrics_data = fetcher.process_current_song()
    
    if lyrics_data:
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Lyrics fetched and saved.")
        print("=" * 60)
        
        # Ask if user wants to start continuous monitoring
        response = input("\n🔍 Start continuous monitoring? (y/n): ").lower()
        if response == 'y':
            fetcher.monitor_spotify()
    else:
        print("❌ Failed to get lyrics for current song")

if __name__ == "__main__":
    main()