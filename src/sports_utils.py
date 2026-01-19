
import feedparser
import datetime
from src.llm_utils import generar_texto_con_gemini

# Feeds específicos de deportes en CLM / Albacete
SPORTS_FEEDS = [
    "https://www.eldigitaldealbacete.com/category/deportes/albacete-balompie/feed/",
    "https://www.latribunadealbacete.es/rss/seccion/deportes",
    "https://www.encastillalamancha.es/seccion/deportes/feed/"
]

def obtener_resultados_futbol() -> str:
    """
    Busca noticias recientes sobre el Albacete Balompié y otros equipos de CLM.
    Devuelve un resumen breve del último resultado si lo encuentra.
    """
    print("   ⚽ Buscando resultados deportivos...")
    noticias_relevantes = []
    
    # 1. Buscar en feeds
    for url in SPORTS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # Solo las 5 últimas
                # Filtrar por fecha (solo últimos 3 días)
                # (Simplificación: asumimos que el feed trae lo reciente primero)
                
                texto_completo = (entry.title + " " + entry.get('description', '')).lower()
                
                # Palabras clave: Albacete, Talavera, Conquense, Toledo, Guadalajara
                equipos = ['albacete', 'talavera', 'conquense', 'toledo', 'guadalajara', 'ub conquense', 'cd toledo']
                
                if any(eq in texto_completo for eq in equipos):
                     noticias_relevantes.append(f"- {entry.title}: {entry.get('description', '')[:200]}")
                     
        except Exception as e:
            print(f"      ⚠️ Error leyendo feed deportes {url}: {e}")
            continue
            
    if not noticias_relevantes:
        return ""
        
    # 2. Usar LLM para extraer el resultado "limpio"
    texto_noticias = "\n".join(noticias_relevantes[:10]) # Max 10 noticias
    
    prompt = f"""
    Eres un analista deportivo. Revisa estos titulares de noticias recientes:
    
    ---
    {texto_noticias}
    ---
    
    TAREA:
    Identifica SI HUBO UN PARTIDO RECIENTE (ayer, hoy o fin de semana pasado) de alguno de estos equipos: Albacete Balompié, Toledo, Talavera, Conquense, Guadalajara.
    
    SI ENCUENTRAS UN RESULTADO:
    Devuelve una frase resumen con "pasión de aficionado". 
    Ejemplos: 
    - "¡Gran victoria del Albacete que se impuso 2-0!"
    - "Empate sufrido del Talavera en casa."
    - "Jornada dura para el Conquense que cayó derrotado."
    
    SI NO HAY RESULTADOS CLAROS O SON NOTICIAS ANTIGUAS/AGENDA:
    Devuelve "NO_RESULTADOS".
    
    ENTREGA: Solo la frase o NO_RESULTADOS.
    """
    
    try:
        resultado = generar_texto_con_gemini(prompt)
        if "NO_RESULTADOS" in resultado:
            return ""
        return resultado.strip()
    except Exception as e:
        print(f"      ⚠️ Error analizando deportes: {e}")
        return ""
