
import feedparser
from datetime import datetime, timedelta
import time
import sys
import html
import re

def limpiar_html(texto):
    if not texto: return ""
    texto = html.unescape(texto)
    clean = re.sub('<[^<]+?>', '', texto)
    return clean.strip()

def parsear_fecha_segura(entry):
    for field in ['published_parsed', 'updated_parsed']:
        if hasattr(entry, field) and entry[field]:
            try:
                return datetime.fromtimestamp(time.mktime(entry[field]))
            except (ValueError, TypeError):
                continue
    return datetime(2000, 1, 1)

def check():
    feeds_file = "feeds_castillalamancha.txt"
    try:
        with open(feeds_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Load config dynamically
    try:
        with open('podcast_config.json', 'r') as f:
            import json
            conf = json.load(f)
            gen_conf = conf.get('generation_config', {})
            audio_conf = conf.get('audio_config', {})
            
            window_hours = gen_conf.get('news_window_hours', 48)
            max_items = gen_conf.get('max_news_items', 20)
            min_words = audio_conf.get('min_words_for_audio', 33)
            print(f"Loaded config: Window={window_hours}h, Max={max_items}, MinWords={min_words}")
    except Exception as e:
        print(f"Error reading config: {e}. Using defaults.")
        window_hours = 48
        max_items = 20
        min_words = 33
    
    now = datetime.now()
    
    
    limit = now - timedelta(hours=window_hours)
    
    all_candidates = []
    
    targets = ["Recuenco", "FAO", "Yolanda Cobo", "Organización de las Naciones Unidas"]
    
    print(f"Scanning {len(urls)} feeds. Window: {window_hours}h.")
    
    found_targets = []
    
    for url in urls:
        try:
            feed = feedparser.parse(url)
            sitio = feed.feed.get('title', 'Unknown').replace(" on Facebook", "")
            print(f"FEED: {sitio} ({url})")
            
            for entry in feed.entries:
                dt = parsear_fecha_segura(entry)
                if dt < limit:
                    continue
                    
                content = entry.get('summary', entry.get('description', ''))
                texto_crudo = limpiar_html(content)
                title = entry.get('title', '')
                
                # Check targets
                for t in targets:
                    if t.lower() in title.lower() or t.lower() in texto_crudo.lower():
                        item = {
                            'target': t,
                            'feed': sitio,
                            'date': dt,
                            'title': title,
                            'words': len(texto_crudo.split())
                        }
                        found_targets.append(item)
                        print(f"  >>> FOUND TARGET '{t}': {title[:50]}... ({dt})")

        except Exception as e:
            print(f"Error parsing {url}: {e}")

    print("\n--- RESULTS ---")
    current_limit_date = now - timedelta(hours=48)
    print(f"Current Limit Date (48h): {current_limit_date}")
    
    for item in found_targets:
        status = "✅ OK"
        if item['date'] < current_limit_date:
            status = "❌ TOO OLD (>48h)"
        elif item['words'] < 33: # Config limit
            status = "❌ TOO SHORT (<33 words)"
            
        print(f"[{item['target']}] {status} | Date: {item['date']} | Words: {item['words']} | Feed: {item['feed']} | Title: {item['title'][:60]}")

if __name__ == "__main__":
    check()
