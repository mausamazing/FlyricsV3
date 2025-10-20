import requests
from bs4 import BeautifulSoup
import re
import time

def search_genius_direct(title, artist=None):
    """
    Search Genius directly without API using web scraping
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        search_query = f"{title} {artist}" if artist else title
        search_url = f"https://genius.com/search?q={requests.utils.quote(search_query)}"
        
        print(f"🔍 Searching: {search_url}")
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for song results in search page
        # Genius search results are typically in divs with song links
        song_links = []
        
        # Method 1: Look for search result items
        results = soup.find_all('a', href=re.compile(r'/lyrics/|/songs/'))
        
        for result in results:
            href = result.get('href', '')
            if '/lyrics/' in href or '/songs/' in href:
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = 'https://genius.com' + href
                song_links.append(href)
        
        # Method 2: Look for mini-card elements
        if not song_links:
            cards = soup.find_all('div', class_=re.compile(r'mini_card|search_result'))
            for card in cards:
                links = card.find_all('a', href=re.compile(r'/lyrics/|/songs/'))
                for link in links:
                    href = link.get('href', '')
                    if href.startswith('/'):
                        href = 'https://genius.com' + href
                    song_links.append(href)
        
        # Remove duplicates and filter
        song_links = list(set(song_links))
        song_links = [link for link in song_links if 'genius.com' in link]
        
        print(f"✅ Found {len(song_links)} potential song links")
        
        # Find the best match
        for link in song_links:
            if title.lower() in link.lower():
                if not artist or any(artist_word in link.lower() for artist_word in artist.lower().split()):
                    print(f"🎯 Selected: {link}")
                    return link
        
        # Return first result if no perfect match
        if song_links:
            print(f"🎯 Using first result: {song_links[0]}")
            return song_links[0]
        
        return None
        
    except Exception as e:
        print(f"❌ Error searching Genius: {e}")
        return None

def scrape_genius_lyrics(url):
    """
    Scrape lyrics from Genius.com with proper selectors
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"📄 Fetching lyrics page...")
        response = requests.get(url, headers=headers)
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
        
        if all_lyrics:
            combined_lyrics = '\n\n'.join(all_lyrics)
            # Clean up the lyrics
            combined_lyrics = re.sub(r'\n\s*\n', '\n\n', combined_lyrics)
            combined_lyrics = re.sub(r'[ \t]+', ' ', combined_lyrics)
            return combined_lyrics
        
        # Method 2: Look for lyrics in specific class structure
        lyrics_div = soup.find('div', class_=re.compile(r'lyrics|Lyrics__Container'))
        if lyrics_div:
            lyrics = lyrics_div.get_text(separator='\n').strip()
            lyrics = re.sub(r'\n\s*\n', '\n\n', lyrics)
            lyrics = re.sub(r'[ \t]+', ' ', lyrics)
            return lyrics
            
        # Method 3: Extract from [data-lyrics-container] elements
        lyrics_elements = soup.select('[data-lyrics-container="true"]')
        if lyrics_elements:
            lyrics_parts = []
            for element in lyrics_elements:
                text = element.get_text(separator='\n').strip()
                if text:
                    lyrics_parts.append(text)
            if lyrics_parts:
                combined = '\n\n'.join(lyrics_parts)
                combined = re.sub(r'\n\s*\n', '\n\n', combined)
                combined = re.sub(r'[ \t]+', ' ', combined)
                return combined
        
        print("❌ No lyrics containers found")
        return None
        
    except Exception as e:
        print(f"❌ Error scraping lyrics: {e}")
        return None

def get_lyrics(title, artist=None):
    """
    Main function to get lyrics for a song using direct web scraping
    """
    print(f"🎵 Getting lyrics for: '{title}' by '{artist}'")
    
    # Search for the song directly
    url = search_genius_direct(title, artist)
    if not url:
        print("❌ Could not find song URL")
        return None
    
    print(f"🔗 Found URL: {url}")
    
    # Add small delay to be respectful to the server
    time.sleep(1)
    
    # Scrape the lyrics
    lyrics = scrape_genius_lyrics(url)
    
    if lyrics:
        print("✅ Lyrics found successfully!")
        print("\n" + "="*60)
        print("🎵 LYRICS:")
        print("="*60)
        print(lyrics)
        print("="*60)
        return lyrics
    else:
        print("❌ Could not extract lyrics")
        # Debug: show what we found
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Show all elements with data-lyrics-container
        containers = soup.find_all('div', {'data-lyrics-container': 'true'})
        print(f"🔍 Found {len(containers)} lyrics containers")
        
        for i, container in enumerate(containers):
            print(f"Container {i+1}: {len(container.get_text())} chars")
        
        return None

# Test with your song
if __name__ == "__main__":
    # Test the specific URL from your HTML file
    test_url = "https://genius.com/Genius-romanizations-aditya-rikhari-sahiba-romanized-lyrics"
    
    print("🔗 Testing with direct URL...")
    lyrics = scrape_genius_lyrics(test_url)
    
    if lyrics:
        print("✅ Successfully extracted lyrics from direct URL!")
        print("\n" + "="*60)
        print(lyrics)
        print("="*60)
    else:
        print("❌ Failed to extract lyrics from direct URL")
    
    # Also test with search
    print("\n" + "="*60)
    print("Testing search functionality...")
    print("="*60)
    
    get_lyrics("Sahiba", "Aditya Rikhari")