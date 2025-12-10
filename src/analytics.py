
import os
import json
import feedparser
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
import time

def analizar_frecuencia_fuentes(feeds_path):
    """
    Analiza la frecuencia de publicación de una lista de feeds RSS.
    Devuelve un DataFrame con el estado de salud y conteos.
    """
    if not os.path.exists(feeds_path):
        return pd.DataFrame()

    with open(feeds_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    resultados = []
    
    # Fecha de corte
    now = datetime.now()
    one_day_ago = now - timedelta(days=1)
    seven_days_ago = now - timedelta(days=7)

    for url in urls:
        try:
            feed = feedparser.parse(url)
            
            # Nombre de la fuente (intentar sacar titulo)
            nombre_fuente = feed.feed.get('title', url)
            
            if feed.bozo:
                # Error en el feed
                estado = "⚠️ Error"
                count_24h = 0
                count_7d = 0
            else:
                # Contar entradas
                count_24h = 0
                count_7d = 0
                
                entries = feed.entries
                if not entries:
                    estado = "💤 Inactivo"
                else:
                    # Analizar fechas de entradas
                    last_entry_date = None
                    
                    for entry in entries:
                        # Intentar parsear fecha
                        published_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                        if published_parsed:
                            dt_entry = datetime.fromtimestamp(time.mktime(published_parsed))
                            
                            if dt_entry > one_day_ago:
                                count_24h += 1
                            if dt_entry > seven_days_ago:
                                count_7d += 1
                                
                            if not last_entry_date or dt_entry > last_entry_date:
                                last_entry_date = dt_entry
                    
                    # Determinar estado
                    if count_7d > 0:
                        estado = "✅ Activo"
                    else:
                        estado = "⚠️ Sin actividad reciente"

            resultados.append({
                "Fuente": nombre_fuente,
                "Estado": estado,
                "24h": count_24h,
                "7 días": count_7d
            })

        except Exception as e:
            resultados.append({
                "Fuente": url,
                "Estado": "❌ Error Conexión",
                "24h": 0,
                "7 días": 0
            })

    return pd.DataFrame(resultados)

def analizar_contenido_noticias(cache_path, min_date=None):
    """
    Analiza un archivo JSON de noticias (cache) y extrae estadísticas de
    poblaciones, grupos GAL y temas.
    
    Returns:
        tuple: (dict_poblaciones, dict_gal, dict_temas)
    """
    if not os.path.exists(cache_path):
        return {}, {}, {}

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            noticias = json.load(f)
    except:
        return {}, {}, {}

    if not isinstance(noticias, list):
        return {}, {}, {}

    # Filtro por fecha si se requiere
    # (Asumiendo que las noticias tienen campo 'fecha' o similar parseable)
    # Por simplicidad en esta restauración, procesamos todas si no hay formato claro
    
    # Contadores
    poblaciones = Counter()
    gal = Counter()
    temas = Counter()

    for noticia in noticias:
        # Aquí tendríamos lógica para extraer entidades del texto de la noticia
        # Como no tenemos el NLP original, usamos heurísticos simples sobre el título/resumen
        
        texto = (noticia.get('titulo', '') + " " + noticia.get('resumen', '')).lower()
        
        # 1. Extracción de Temas (Heurística simple basada en palabras clave comunes)
        keywords = ['agricultura', 'turismo', 'subvención', 'cultura', 'jovenes', 'mujer', 'desarrollo', 'inovación']
        for k in keywords:
            if k in texto:
                temas[k] += 1
        
        # 2. Extracción de Poblaciones/GAL
        # Esto requeriría una lista conocida. 
        # Si la noticia ya tiene metadatos de entidades, los usamos.
        if 'entidades' in noticia:
            for ent in noticia['entidades']:
                poblaciones[ent] += 1
                
        # Si tiene campo 'grupo' o 'fuente'
        if 'sitio' in noticia:
            gal[noticia['sitio']] += 1

    return dict(poblaciones), dict(gal), dict(temas)
