import feedparser
import sys
from datetime import datetime
from time import mktime

def inspect_feed(url):
    print(f"🕵️‍♂️ Inspecting: {url}")
    d = feedparser.parse(url)
    print(f"   Feed Title: {d.feed.get('title', 'Unknown')}")
    print(f"   Bozo (Error): {d.get('bozo', 0)}")
    if d.get('bozo_exception'):
        print(f"   Bozo Exception: {d.get('bozo_exception')}")
    
    print(f"   Entries found: {len(d.entries)}")
    
    for i, entry in enumerate(d.entries[:5]):
        print(f"\n   --- Entry {i+1} ---")
        print(f"   Title: {entry.get('title', 'No Title')}")
        print(f"   Link: {entry.get('link', 'No Link')}")
        
        # Date fields
        print(f"   Raw 'published': {entry.get('published', 'N/A')}")
        print(f"   Parsed 'published_parsed': {entry.get('published_parsed', 'N/A')}")
        print(f"   Raw 'updated': {entry.get('updated', 'N/A')}")
        print(f"   Parsed 'updated_parsed': {entry.get('updated_parsed', 'N/A')}")
        
        # Content
        summary = entry.get('summary', '')
        desc = entry.get('description', '')
        print(f"   Summary len: {len(summary)}")
        print(f"   Description len: {len(desc)}")

if __name__ == "__main__":
    # Test with a few feeds from the list
    urls = [
        "https://rss.app/feeds/xQwS9d8teF6zSlfk.xml", # ADEL Sierra Norte
        "https://rss.app/feeds/isQf3IY7IdDqJgEM.xml", # Sierra del Segura
        "https://rss.app/feeds/cVA0VcRztLrfgRoM.xml"  # Manchuela
    ]
    for url in urls:
        inspect_feed(url)
        print("\n" + "="*50 + "\n")
