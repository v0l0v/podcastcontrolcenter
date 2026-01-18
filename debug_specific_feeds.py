
import feedparser
from datetime import datetime
import time

def parsear_fecha_segura(entry):
    for field in ['published_parsed', 'updated_parsed']:
        if hasattr(entry, field) and entry[field]:
            try:
                return datetime.fromtimestamp(time.mktime(entry[field]))
            except (ValueError, TypeError):
                continue
    return datetime(2000, 1, 1)

def check_specific():
    targets = {
        "Alto Tajo (Recuenco expected)": "https://rss.app/feeds/5jAsbLo6wRk9PArL.xml",
        "Dulcinea (Yolanda Cobo expected)": "https://rss.app/feeds/cVA0VcRztLrfgRoM.xml"
    }

    for name, url in targets.items():
        print(f"\n--- Checking {name} ---")
        try:
            feed = feedparser.parse(url)
            print(f"Feed Title: {feed.feed.get('title', 'Unknown')}")
            for i, entry in enumerate(feed.entries): # Print all items
                dt = parsear_fecha_segura(entry)
                title = entry.get('title', 'No title').strip()
                print(f"[{i+1}] {dt} | {title[:80]}...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_specific()
