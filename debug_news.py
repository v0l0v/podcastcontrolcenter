import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import feedparser
from datetime import datetime, timedelta
from time import mktime
from src.news_engine import parsear_fecha_segura, limpiar_html

def debug_feeds(feeds_file):
    print(f"🔍 Debugging feeds from {feeds_file}...")
    with open(feeds_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    total_found = 0
    total_kept = 0
    
    limite = datetime.now() - timedelta(days=1) # Solo hoy/ayer para probar lo que dice el usuario
    print(f"📅 Fecha límite: {limite}")

    for url in urls:
        print(f"\n📡 Feed: {url}")
        try:
            feed = feedparser.parse(url)
            print(f"   Items en feed: {len(feed.entries)}")
            
            for i, entry in enumerate(feed.entries[:5]): # Solo ver los primeros 5 de cada feed para no saturar
                fecha = parsear_fecha_segura(entry)
                titulo = entry.get('title', 'Sin título')
                
                msg = f"   - [{i}] {fecha} | {titulo[:40]}..."
                
                if fecha < limite:
                    print(f"{msg} ❌ (Muy antigua)")
                else:
                    print(f"{msg} ✅ (Dentro de rango)")
                    total_kept += 1
                
            total_found += len(feed.entries)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n📊 Resumen: Encontrados {total_found}, Recientes (últimas 24h) {total_kept}")

debug_feeds('feeds.txt')
