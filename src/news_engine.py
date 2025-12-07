import feedparser
import json
import os
from datetime import datetime, timedelta
from time import mktime
from src.utils import stable_text_hash, limpiar_html, preprocesar_texto_para_fechas, cargar_configuracion, guardar_configuracion
from src.content_generator import identificar_fuente_original, extraer_entidades, resumir_noticia, analizar_sentimiento, extraer_localidad_con_ia

# --- CONFIGURACIÓN ---
CONFIG = cargar_configuracion()
GEN_CONFIG = CONFIG.get('generation_config', {})
DEDUP_THRESHOLD = GEN_CONFIG.get('dedup_similarity_threshold', 0.90)
CACHE_FILE = 'cache_noticias.json'

def cargar_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def guardar_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)

def parsear_fecha_segura(entry):
    for field in ['published_parsed', 'updated_parsed']:
        if hasattr(entry, field) and entry[field]:
            try:
                return datetime.fromtimestamp(mktime(entry[field]))
            except:
                continue
    return datetime.now()

def procesar_feeds(feeds_file: str, dias_atras: int = 3, min_items: int = 5):
    print(f"🔍 Procesando feeds desde {feeds_file}...")
    cache = cargar_cache()
    
    with open(feeds_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    limite = datetime.now() - timedelta(days=dias_atras)
    candidatas = []
    
    for url in urls:
        try:
            feed = feedparser.parse(url)
            sitio = feed.feed.get('title', 'Desconocido').replace(" on Facebook", "").strip()
            items_feed = 0
            for entry in feed.entries:
                fecha = parsear_fecha_segura(entry)
                if fecha < limite: 
                    # print(f"      🗑️ Descartada por fecha ({fecha}): {entry.get('title', '')[:30]}...")
                    continue
                
                contenido = entry.get('summary', entry.get('description', ''))
                if not contenido: 
                    print(f"      ⚠️ Descartada por falta de contenido: {entry.get('title', '')[:30]}...")
                    continue
                
                texto_crudo = limpiar_html(contenido)
                titulo = entry.get('title', '')
                h = stable_text_hash(titulo + " " + texto_crudo)
                
                candidatas.append({
                    'sitio': sitio,
                    'texto': texto_crudo,
                    'fecha': fecha,
                    'hash': h,
                    'link': entry.get('link', '')
                })
                items_feed += 1
            print(f"    ✅ {sitio}: {items_feed} noticias recientes.")
        except Exception as e:
            print(f"⚠️ Error en feed {url}: {e}")
            
    # Ordenar y seleccionar
    print(f"📊 Total candidatas: {len(candidatas)}")
    candidatas.sort(key=lambda x: x['fecha'], reverse=True)
    seleccionadas = candidatas[:min_items]
    print(f"✂️ Seleccionadas (Top {min_items}): {len(seleccionadas)}")
    
    procesadas = []
    nuevas_cache = {}
    
    for item in seleccionadas:
        h = item['hash']
        if h in cache:
            print(f"⏩ En caché: {item['sitio']}")
            procesadas.append(cache[h])
        else:
            print(f"🆕 Procesando nueva: {item['sitio']}")
            # Procesamiento con IA
            texto_prep = preprocesar_texto_para_fechas(item['texto'])
            fuente_orig = identificar_fuente_original(item['texto'])
            entidades = extraer_entidades(texto_prep)
            es_breve = len(texto_prep) < 150
            
            resumen = resumir_noticia(texto_prep, fuente_orig, entidades, es_breve)
            sentimiento = analizar_sentimiento(resumen)
            localidad = extraer_localidad_con_ia(item['texto'])
            
            noticia_proc = {
                'id': h,
                'fuente': f"{item['sitio']} ({fuente_orig})" if fuente_orig else item['sitio'],
                'resumen': resumen,
                'fecha': item['fecha'].strftime("%Y-%m-%d"),
                'localidad': localidad,
                'sentimiento': sentimiento,
                'entidades': entidades,
                'es_breve': es_breve,
                'link': item['link']
            }
            
            procesadas.append(noticia_proc)
            nuevas_cache[h] = noticia_proc
            
    if nuevas_cache:
        cache.update(nuevas_cache)
        guardar_cache(cache)
        
    return procesadas
