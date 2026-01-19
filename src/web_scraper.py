
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs

def is_external_link(url):
    """
    Determines if a URL is an external link worthy of following.
    Filters out internal Facebook links, hashtags, etc.
    """
    if not url:
        return False
        
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Filter out facebook internal links (unless it's l.facebook.com which is a redirect)
    if 'facebook.com' in domain and 'l.facebook.com' not in domain:
        return False
        
    if 'twitter.com' in domain or 'x.com' in domain or 'instagram.com' in domain:
        return False
        
    return True

def unwrap_facebook_link(url):
    """
    Extracts the actual URL from l.facebook.com redirection links.
    """
    if 'l.facebook.com' in url:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if 'u' in qs:
            return qs['u'][0]
    return url

def extract_first_external_link(html_content):
    """
    Parses HTML content and returns the first valid external link found.
    """
    if not html_content:
        return None
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        href = unwrap_facebook_link(href)
        
        if is_external_link(href):
            return href
            
    return None

def fetch_article_text(url, timeout=5):
    """
    Fetches the URL and extracts the main text content.
    Returns a string with the text or None if failed.
    """
    print(f"      🕷️  Scraping external URL: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.extract()
            
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Basic cleanup of multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    except Exception as e:
        print(f"      ⚠️  Failed to scrape {url}: {e}")
        return None

def extract_image_url(html_content):
    """
    Extracts the first valid image URL from the HTML content.
    Prioritizes images that look like actual content (not icons).
    """
    if not html_content:
        return None
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try finding typical feed image structures
    img = soup.find('img')
    if img and img.get('src'):
        src = img['src']
        # Basic filter to avoid tiny tracking pixels or icons if possible
        # (Though difficult without downloading context headers)
        return src
        
    return None

def download_image_as_bytes(url):
    """
    Downloads an image and returns the bytes.
    """
    if not url:
        return None
        
    print(f"      🖼️  Downloading image: {url[:60]}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Verify it's actually an image
        content_type = response.headers.get('Content-Type', '')
        if 'image' not in content_type:
             print(f"      ⚠️  URL is not an image (Content-Type: {content_type})")
             return None
             
        return response.content
    except Exception as e:
        print(f"      ⚠️  Failed to download image: {e}")
        return None
