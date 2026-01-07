import feedparser
from datetime import datetime, timedelta
import time
import sys
import html

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
    
    recent_items_total = 0
    
    for url in urls:
        print(f"\nChecking: {url}")
        try:
            feed = feedparser.parse(url)
            print(f"  Feed Title: {feed.feed.get('title', 'Unknown').replace(' on Facebook', '')}")
            print(f"  Entries: {len(feed.entries)}")
            
            count = 0
            # Check first 3 items of each feed
            for i, entry in enumerate(feed.entries[:3]):
                dt = parsear_fecha_segura(entry)
                title = entry.get('title', 'No title').strip()
                summary = entry.get('summary', entry.get('description', '')).strip()
                # Simple cleanup for display
                summary_clean = html.unescape(summary).replace('\n', ' ')[:80]
                
                print(f"    Item {i+1}:")
                print(f"       Date : {dt}")
                print(f"       Title: {title[:80]}...")
                print(f"       Desc : {summary_clean}...")
                
                if dt > limit:
                    count += 1
            
            print(f"  => Recent items (> {hours}h): {count}")
            recent_items_total += count
            
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\nTotal recent items in checked feeds: {recent_items_total}")

if __name__ == "__main__":
    check_feeds("feeds_castillalamancha.txt", 48)
