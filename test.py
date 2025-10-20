# test_scraper.py
from genius_scraper import GeniusScraper

def test_scraper():
    scraper = GeniusScraper()
    
    # Test with known working song
    test_songs = [
        ("Sahiba", "Aditya Rikhari"),
        ("Blinding Lights", "The Weeknd"),
        ("Shape of You", "Ed Sheeran")
    ]
    
    for title, artist in test_songs:
        print(f"\n{'='*50}")
        print(f"Testing: {title} by {artist}")
        print('='*50)
        
        lyrics_data = scraper.get_lyrics_for_song(title, artist)
        
        if lyrics_data:
            print(f"✅ SUCCESS: Found {len(lyrics_data['lyrics'])} characters of lyrics")
            # Save to file
            scraper.save_lyrics_to_file(lyrics_data)
        else:
            print("❌ FAILED: Could not get lyrics")

if __name__ == "__main__":
    test_scraper()