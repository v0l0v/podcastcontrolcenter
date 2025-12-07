import feedparser
import sys
from datetime import datetime
from time import mktime
from src.news_engine import parsear_fecha_segura

def check_all_feeds(feeds_file):
    print(f"📊 Checking freshness of all feeds in {feeds_file}...")
    with open(feeds_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"{'FEED NAME':<50} | {'LATEST ITEM DATE':<20} | {'STATUS':<10}")
    print("-" * 90)

    now = datetime.now()
    
    for url in urls:
        try:
            feed = feedparser.parse(url)
            title = feed.feed.get('title', url)[:45]
            
            if not feed.entries:
                print(f"{title:<50} | {'NO ENTRIES':<20} | 🔴 EMPTY")
                continue
                
            # Get latest date
            latest_date = None
            for entry in feed.entries:
                d = parsear_fecha_segura(entry)
                if latest_date is None or d > latest_date:
                    latest_date = d
            
            if latest_date:
                days_old = (now - latest_date).days
                date_str = latest_date.strftime("%Y-%m-%d")
                
                status = "🟢 FRESH" if days_old < 2 else ("🟡 STALE" if days_old < 7 else "🔴 DEAD")
                print(f"{title:<50} | {date_str:<20} | {status} ({days_old}d)")
            else:
                print(f"{title:<50} | {'UNKNOWN DATE':<20} | ⚪ UNKNOWN")

        except Exception as e:
            print(f"{url[:50]:<50} | {'ERROR':<20} | ❌ ERROR")

check_all_feeds('feeds.txt')
