import requests
from bs4 import BeautifulSoup
import re
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeniusScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def search_genius_direct(self, title, artist=None):
        """
        Search Genius directly without API using web scraping
        """
        try:
            # Skip the search page and go directly to URL construction
            print("🔄 Skipping search page, using direct URL approach...")
            return self.direct_url_approach(title, artist)
            
        except Exception as e:
            print(f"❌ Error searching Genius: {e}")
            return None

    def direct_url_approach(self, title, artist=None):
        """
        Try to construct URL directly and verify by actually loading the page
        """
        try:
            if artist:
                # Clean the strings for URL
                artist_clean = re.sub(r'[^\w\s-]', '', artist).strip().lower().replace(' ', '-')
                title_clean = re.sub(r'[^\w\s-]', '', title).strip().lower().replace(' ', '-')
                
                # Try different URL patterns
                url_patterns = [
                    f"https://genius.com/{artist_clean}-{title_clean}-lyrics",
                    f"https://genius.com/{artist_clean}-{title_clean}-song-lyrics",
                    f"https://genius.com/{title_clean}-{artist_clean}-lyrics",
                    f"https://genius.com/{title_clean}-lyrics",
                    f"https://genius.com/{artist_clean}-{title_clean}",
                ]
                
                # Also try with the romanized version
                if "romanized" in title.lower() or "romanizations" in artist.lower():
                    url_patterns.extend([
                        f"https://genius.com/Genius-romanizations-{artist_clean}-{title_clean}-romanized-lyrics",
                        f"https://genius.com/Genius-romanizations-{title_clean}-romanized-lyrics",
                    ])
                
                for url in url_patterns:
                    print(f"🔗 Testing URL: {url}")
                    try:
                        # Actually try to load the page content
                        response = requests.get(url, headers=self.headers, timeout=10)
                        if response.status_code == 200:
                            # Check if the page contains lyrics
                            soup = BeautifulSoup(response.content, 'html.parser')
                            lyrics_containers = soup.find_all('div', {'data-lyrics-container': 'true'})
                            if lyrics_containers:
                                print(f"✅ URL works and contains lyrics: {url}")
                                return url
                            else:
                                print(f"⚠️ URL works but no lyrics found: {url}")
                        else:
                            print(f"❌ URL returned status {response.status_code}: {url}")
                    except Exception as e:
                        print(f"❌ Error testing URL {url}: {e}")
                    
                    time.sleep(1)  # Be nice to the server
            
            return None
            
        except Exception as e:
            print(f"❌ Error in direct URL approach: {e}")
            return None

    def scrape_genius_lyrics(self, url):
        """
        Scrape lyrics from Genius.com with proper selectors
        """
        try:
            print(f"📄 Fetching lyrics from: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Look for the specific div with data-lyrics-container attribute
            lyrics_containers = soup.find_all('div', {'data-lyrics-container': 'true'})
            
            all_lyrics = []
            
            for container in lyrics_containers:
                # Get all text, preserving line breaks
                lyrics = container.get_text(separator='\n').strip()
                if lyrics and len(lyrics) > 10:  # Only add if meaningful content
                    all_lyrics.append(lyrics)
                    print(f"📝 Found lyrics container with {len(lyrics)} characters")
            
            if all_lyrics:
                combined_lyrics = '\n\n'.join(all_lyrics)
                # Clean up the lyrics
                combined_lyrics = re.sub(r'\n\s*\n', '\n\n', combined_lyrics)
                combined_lyrics = re.sub(r'[ \t]+', ' ', combined_lyrics)
                return combined_lyrics
            
            # Method 2: Look for lyrics in the page text more aggressively
            print("🔄 Trying aggressive lyrics search...")
            
            # Look for any element that might contain lyrics
            potential_elements = soup.find_all(['div', 'p', 'span'], string=re.compile(r'.{20,}'))  # Elements with substantial text
            
            for elem in potential_elements:
                text = elem.get_text().strip()
                # Check if this looks like lyrics (contains common lyric patterns)
                if (len(text) > 100 and 
                    any(pattern in text for pattern in ['[Verse', '[Chorus', '[Intro', '[Bridge', '\n\n']) and
                    not any(exclude in text for exclude in ['Advertisement', 'cookie', 'privacy policy'])):
                    print(f"📝 Found potential lyrics: {len(text)} characters")
                    return text
            
            # Method 3: Extract all text and look for lyric-like content
            all_text = soup.get_text()
            lines = all_text.split('\n')
            lyric_lines = []
            
            for line in lines:
                line = line.strip()
                if (len(line) > 20 and 
                    not any(exclude in line.lower() for exclude in ['advertisement', 'cookie', 'privacy', 'terms', 'sign up', 'login']) and
                    not re.match(r'^[0-9\W]+$', line)):
                    lyric_lines.append(line)
            
            if len(lyric_lines) > 5:  # If we found several potential lyric lines
                lyrics = '\n'.join(lyric_lines)
                print(f"📝 Found lyrics from text extraction: {len(lyrics)} characters")
                return lyrics
            
            print("❌ No lyrics containers found")
            return None
            
        except Exception as e:
            print(f"❌ Error scraping lyrics: {e}")
            return None

    def get_lyrics_for_song(self, title, artist=None):
        """
        Main function to get lyrics for a song using direct web scraping
        """
        print(f"🎵 Getting lyrics for: '{title}' by '{artist}'")
        
        # Try direct URL approach
        url = self.direct_url_approach(title, artist)
        
        if not url:
            print("❌ Could not find valid URL")
            return None
        
        print(f"🔗 Using URL: {url}")
        
        # Add small delay to be respectful to the server
        time.sleep(2)
        
        # Scrape the lyrics
        lyrics = self.scrape_genius_lyrics(url)
        
        if lyrics:
            print("✅ Lyrics found successfully!")
            return {
                'title': title,
                'artist': artist,
                'lyrics': lyrics,
                'url': url
            }
        else:
            print("❌ Could not extract lyrics")
            return None

    def save_lyrics_to_file(self, lyrics_data, filename=None):
        """
        Save lyrics to a text file
        """
        if not lyrics_data:
            print("❌ No lyrics data to save")
            return False
            
        if not filename:
            # Create filename from song title and artist
            title = lyrics_data['title'].replace(' ', '_').replace('/', '_')
            artist = lyrics_data['artist'].replace(' ', '_').replace('/', '_') if lyrics_data['artist'] else 'Unknown'
            filename = f"lyrics_{artist}_{title}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Title: {lyrics_data['title']}\n")
                if lyrics_data['artist']:
                    f.write(f"Artist: {lyrics_data['artist']}\n")
                f.write(f"URL: {lyrics_data['url']}\n")
                f.write("=" * 60 + "\n")
                f.write(lyrics_data['lyrics'])
                f.write("\n" + "=" * 60 + "\n")
            
            print(f"💾 Lyrics saved to: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving lyrics to file: {e}")
            return False

# For testing with the specific song
def test_specific_url():
    """Test with the specific URL we know works"""
    scraper = GeniusScraper()
    
    # Test with the exact URL from your HTML
    test_url = "https://genius.com/Genius-romanizations-aditya-rikhari-sahiba-romanized-lyrics"
    print(f"🧪 Testing specific URL: {test_url}")
    
    lyrics = scraper.scrape_genius_lyrics(test_url)
    
    if lyrics:
        print("✅ SUCCESS! Lyrics found:")
        print("=" * 60)
        print(lyrics[:500] + "..." if len(lyrics) > 500 else lyrics)
        print("=" * 60)
        
        # Save to file
        lyrics_data = {
            'title': 'Sahiba (Romanized)',
            'artist': 'Aditya Rikhari',
            'lyrics': lyrics,
            'url': test_url
        }
        scraper.save_lyrics_to_file(lyrics_data, "test_lyrics.txt")
    else:
        print("❌ FAILED: No lyrics found")

if __name__ == "__main__":
    # First test the specific URL we know works
    test_specific_url()
    
    print("\n" + "="*60)
    print("Now testing the general approach...")
    print("="*60)
    
    # Then test the general approach
    scraper = GeniusScraper()
    test_data = scraper.get_lyrics_for_song("Sahiba", "Aditya Rikhari")
    if test_data:
        print("\n✅ General approach successful!")
        print(f"Title: {test_data['title']}")
        print(f"Artist: {test_data['artist']}")
        print(f"URL: {test_data['url']}")
        print(f"Lyrics length: {len(test_data['lyrics'])} characters")
    else:
        print("\n❌ General approach failed!")