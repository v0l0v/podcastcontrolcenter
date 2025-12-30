import feedparser
from datetime import datetime, timedelta
import time
import sys

# Functions from dorototal.py for consistency
def parsear_fecha_segura(entry):
    for field in ['published_parsed', 'updated_parsed']:
        if hasattr(entry, field) and entry[field]:
            try:
                return datetime.fromtimestamp(time.mktime(entry[field]))
            except (ValueError, TypeError):
                continue
    return datetime(2000, 1, 1)

def check_feeds(feed_file, hours=48):
    print(f"Checking feeds in {feed_file} for items in last {hours} hours...")
    try:
        with open(feed_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    now = datetime.now()
    limit = now - timedelta(hours=hours)
    
    total_items = 0
    recent_items = 0
    
    # Check first 5 feeds
    for url in urls[:5]:
        print(f"\nChecking: {url}")
        try:
            feed = feedparser.parse(url)
            print(f"  Title: {feed.feed.get('title', 'Unknown')}")
            print(f"  Entries: {len(feed.entries)}")
            
            count = 0
            for entry in feed.entries:
                dt = parsear_fecha_segura(entry)
                print(f"    - {dt} | {entry.get('title', 'No title')[:40]}...")
                if dt > limit:
                    count += 1
            
            print(f"  => Recent items (> {hours}h): {count}")
            recent_items += count
            total_items += len(feed.entries)
            
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\nTotal recent items in checked feeds: {recent_items}")

if __name__ == "__main__":
    check_feeds("feeds_castillalamancha.txt", 36)
