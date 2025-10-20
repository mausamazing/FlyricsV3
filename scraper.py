# scraper.py
import requests
from bs4 import BeautifulSoup
import re

def scrape_azlyrics_lyrics(url):
    """
    Scrape lyrics from AZLyrics website with detailed debugging
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print(f"🔍 Attempting to scrape: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch page. Status: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Debug: Check page title
        title = soup.find('title')
        if title:
            print(f"📄 Page title: {title.get_text()}")
        
        # Method 1: Find by comment (most reliable)
        comments = soup.find_all(string=lambda text: isinstance(text, str) and 'Usage of azlyrics.com content' in text)
        print(f"🔍 Found {len(comments)} comment(s) with usage text")
        
        for i, comment in enumerate(comments):
            print(f"📝 Processing comment #{i+1}")
            
            # Get the parent of the comment
            parent = comment.parent
            if parent:
                # Find the next div after the comment's parent
                lyrics_div = parent.find_next_sibling('div')
                if lyrics_div:
                    print("✅ Found lyrics div after comment")
                    raw_text = lyrics_div.get_text(separator='\n')
                    cleaned = clean_lyrics(raw_text)
                    if cleaned and len(cleaned) > 50:
                        print(f"✅ Successfully extracted {len(cleaned)} characters of lyrics")
                        return cleaned
                    else:
                        print("❌ Extracted text too short or empty")
        
        # Method 2: Look for specific div structure
        print("🔍 Trying method 2: div structure search")
        main_content = soup.find('div', class_='col-xs-12 col-lg-8 text-center')
        if main_content:
            print("✅ Found main content div")
            # Find all divs and check their content
            divs = main_content.find_all('div')
            print(f"🔍 Found {len(divs)} divs in main content")
            
            for i, div in enumerate(divs):
                text = div.get_text(strip=True)
                if len(text) > 200:
                    print(f"🔍 Div #{i} has {len(text)} chars: {text[:100]}...")
                    if any(phrase in text.lower() for phrase in ['i found', 'darling', 'baby', 'verse', 'chorus']):
                        print("✅ This looks like lyrics!")
                        raw_text = div.get_text(separator='\n')
                        cleaned = clean_lyrics(raw_text)
                        if cleaned:
                            return cleaned
        
        # Method 3: Search for lyrics in the entire page
        print("🔍 Trying method 3: full page search")
        all_text = soup.get_text()
        lines = all_text.split('\n')
        
        # Look for the lyrics section (usually between specific markers)
        lyrics_lines = []
        in_lyrics_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Start capturing after we see lyrics indicators
            if any(marker in line.lower() for marker in ['"lyrics"', 'lyrics']):
                in_lyrics_section = True
                continue
                
            # Stop capturing when we see these markers
            if any(marker in line.lower() for marker in ['submit corrections', 'writer(s):', 'thanks to']):
                break
                
            if in_lyrics_section and len(line) > 10:
                lyrics_lines.append(line)
        
        if lyrics_lines:
            print(f"✅ Found {len(lyrics_lines)} lines via full page search")
            return '\n'.join(lyrics_lines)
        
        print("❌ All methods failed to extract lyrics")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def clean_lyrics(raw_text):
    """
    Clean and format lyrics text
    """
    if not raw_text:
        return None
        
    lines = raw_text.split('\n')
    cleaned = []
    
    for line in lines:
        line = line.strip()
        # Remove empty lines and unwanted content
        if (line and 
            len(line) > 2 and
            not line.startswith('Submit Corrections') and
            not line.startswith('Writer(s):') and
            not line.startswith('Thanks to') and
            not line.startswith('if (') and  # Remove JavaScript
            'cookie' not in line.lower() and
            not re.match(r'^\d+\.?\s*$', line)):  # Remove numbered lines
            cleaned.append(line)
    
    result = '\n'.join(cleaned)
    
    # Final validation - lyrics should be substantial
    if len(result) < 50:
        print(f"❌ Cleaned text too short: {len(result)} characters")
        return None
        
    return result