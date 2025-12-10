
import os
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import time

def analizar_frecuencia_fuentes(feeds_path):
    """
    Analiza la frecuencia de publicación de una lista de feeds RSS.
    Devuelve un DataFrame con el estado de salud y conteos detallados (24h, 7d, 30d, 1a).
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
    thirty_days_ago = now - timedelta(days=30)
    one_year_ago = now - timedelta(days=365)

    one_year_ago = now - timedelta(days=365)

    def reparar_codificacion(texto: str) -> str:
        if not texto: return ""
        try:
           return texto.encode('cp1252').decode('utf-8')
        except:
           try:
               return texto.encode('latin-1').decode('utf-8')
           except:
               return texto

    for url in urls:
        try:
            feed = feedparser.parse(url)
            
            # Nombre de la fuente (intentar sacar titulo)
            nombre_fuente = feed.feed.get('title', url)
            nombre_fuente = reparar_codificacion(nombre_fuente)
            
            if feed.bozo:
                # Error en el feed detectado por feedparser
                # A veces bozo es 1 por encoding warning, verificamos si hay entries
                if not feed.entries:
                     estado = "⚠️ Error Formato"
                     count_24h = 0
                     count_7d = 0
                     count_30d = 0
                     count_1y = 0
                else:
                    # Si tiene entries aunque tenga bozo, procesamos con warning
                    estado = "⚠️ Warning"
            else:
                estado = "✅ OK"

            # Si el estado es OK o Warning proceasble, contamos
            if not feed.entries and estado != "⚠️ Error Formato":
                estado = "💤 Inactivo/Vacío"
                count_24h = 0
                count_7d = 0
                count_30d = 0
                count_1y = 0
            elif feed.entries:
                count_24h = 0
                count_7d = 0
                count_30d = 0
                count_1y = 0
                
                last_entry_date = None
                
                for entry in feed.entries:
                    # Intentar parsear fecha
                    published_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                    
                    if published_parsed:
                        dt_entry = datetime.fromtimestamp(time.mktime(published_parsed))
                        
                        if dt_entry > one_day_ago:
                            count_24h += 1
                        if dt_entry > seven_days_ago:
                            count_7d += 1
                        if dt_entry > thirty_days_ago:
                            count_30d += 1
                        if dt_entry > one_year_ago:
                            count_1y += 1
                            
                        if not last_entry_date or dt_entry > last_entry_date:
                            last_entry_date = dt_entry
                
                # Ajuste de estado basado en actividad
                if count_7d > 0:
                    estado = "🟢 Muy Activo"
                elif count_30d > 0:
                    estado = "🟡 Activo"
                elif count_1y > 0:
                    estado = "🟠 Inactivo (>1 mes)"
                else:
                    estado = "🔴 Muerto (>1 año)"

            resultados.append({
                "Fuente": nombre_fuente,
                "Estado": estado,
                "24h": count_24h,
                "7d": count_7d,
                "30d": count_30d,
                "1 año": count_1y
            })

        except Exception as e:
            resultados.append({
                "Fuente": url,
                "Estado": "❌ Error Conexión",
                "24h": 0,
                "7d": 0,
                "30d": 0,
                "1 año": 0
            })

    return pd.DataFrame(resultados)
