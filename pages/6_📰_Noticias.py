import streamlit as st
import json
import os
import datetime
import math
import re
import glob
from src.utils.ui_common import inject_pcc_style, cargar_config, init_session_state, render_wavesurfer_player

# Configurar la página
st.set_page_config(page_title="PCC - Centro de Noticias", page_icon="📰", layout="wide")
inject_pcc_style()
init_session_state()

# Título de la página
st.markdown('<div class="pcc-page-title">📰 Centro de Noticias</div>', unsafe_allow_html=True)
st.info("💡 **Tu Central de Información.** Explora las noticias de la región, clasificadas por fechas, con análisis de sentimiento y categorización inteligente por IA.")

# --- BASE DE DATOS DE NOTICIAS DE EJEMPLO (Castilla-La Mancha) ---
# Se utiliza para complementar y garantizar una experiencia densa y viva si el JSON local está vacío o tiene pocas fechas.
NOTICIAS_RURALES = [
    {
        "id": "clm_1",
        "fuente": "Ayuntamiento de Almagro",
        "titulo": "🎭 Almagro inaugura su Festival Internacional de Teatro Clásico",
        "resumen": "El corral de comedias abre sus puertas para la 49ª edición del festival, con una programación que combina clásicos del Siglo de Oro y puestas en escena contemporáneas. Las plazas hoteleras de toda la comarca del Campo de Calatrava se encuentran al 100% de ocupación, consolidando la cultura como motor del desarrollo económico rural.",
        "fecha": "2026-07-05",
        "localidad": "Almagro",
        "sentimiento": "positivo",
        "entidades_clave": ["Festival de Almagro", "Teatro Clásico", "Cultura", "Turismo"]
    },
    {
        "id": "clm_2",
        "fuente": "DO Valdepeñas",
        "titulo": "🍇 Excelentes expectativas para la vendimia 2026 gracias al clima templado",
        "resumen": "Los viticultores de Valdepeñas prevén una cosecha de calidad excepcional para este año. Las lluvias de primavera combinadas con el calor moderado de las últimas semanas han favorecido una maduración óptima de la uva Tempranillo. Se espera que la producción genere más de 2,000 empleos temporales en toda la región.",
        "fecha": "2026-07-05",
        "localidad": "Valdepeñas",
        "sentimiento": "positivo",
        "entidades_clave": ["Vendimia 2026", "Vino", "Economía", "Agricultura"]
    },
    {
        "id": "clm_3",
        "fuente": "AEMET Castilla-La Mancha",
        "titulo": "☀️ Alerta amarilla por altas temperaturas en los valles del Tajo y Guadiana",
        "resumen": "La Agencia Estatal de Meteorología ha activado la alerta amarilla para el día de hoy ante temperaturas que podrían superar los 39°C. Se aconseja a los agricultores adelantar las labores de recolección a las horas frescas de la mañana y extremar las medidas de hidratación y cuidado personal en el campo.",
        "fecha": "2026-07-04",
        "localidad": "Región",
        "sentimiento": "neutro",
        "entidades_clave": ["Ola de calor", "Clima", "Agricultura", "Prevención"]
    },
    {
        "id": "clm_4",
        "fuente": "Ayuntamiento de Sigüenza",
        "titulo": "🏰 Sigüenza presenta su candidatura oficial a Patrimonio Mundial de la UNESCO",
        "resumen": "Con un expediente que destaca el paisaje cultural dulce y salado de su entorno, el consistorio seguntino confía en obtener el reconocimiento internacional. Esta designación impulsaría el turismo rural sostenible y el comercio de artesanía tradicional en el norte de la provincia de Guadalajara.",
        "fecha": "2026-07-04",
        "localidad": "Sigüenza",
        "sentimiento": "positivo",
        "entidades_clave": ["Patrimonio UNESCO", "Sigüenza", "Turismo", "Artesanía"]
    },
    {
        "id": "clm_5",
        "fuente": "Asociación del Ajo Morado de Las Pedroñeras",
        "titulo": "🧄 Comienza la campaña de recogida del ajo morado con precios estables",
        "resumen": "Los campos de Las Pedroñeras ya bullen de actividad con el inicio de la campaña del ajo morado. A pesar del incremento de los costes de los insumos, los productores celebran la alta calidad del bulbo cosechado este año y una cotización en origen favorable que garantiza la viabilidad de las explotaciones familiares.",
        "fecha": "2026-07-03",
        "localidad": "Las Pedroñeras",
        "sentimiento": "positivo",
        "entidades_clave": ["Ajo Morado", "Las Pedroñeras", "Campaña Agrícola", "Comercio"]
    },
    {
        "id": "clm_6",
        "fuente": "Cooperativa San Isidro de Quintanar",
        "titulo": "🌾 Preocupación en el sector cerealista por la escasez de almacenamiento",
        "resumen": "La recolección del trigo y la cebada en la comarca de Mancha Alta avanza a un ritmo superior al previsto. Los silos locales se encuentran al límite de su capacidad, lo que obliga a las cooperativas a coordinar transportes logísticos de urgencia para evitar la paralización de las cosechadoras en las parcelas.",
        "fecha": "2026-07-03",
        "localidad": "Quintanar de la Orden",
        "sentimiento": "negativo",
        "entidades_clave": ["Cereales", "Cosecha", "Logística", "Cooperativismo"]
    },
    {
        "id": "clm_7",
        "fuente": "GDR Campo de Montiel",
        "titulo": "🚵‍♂️ Rutas cicloturísticas para combatir la despoblación en el Montiel de Quevedo",
        "resumen": "Se ha inaugurado un nuevo sendero de cicloturismo de 120 km que conecta diez pequeños municipios de la comarca. Financiado con fondos europeos del programa LEADER, el proyecto busca atraer a entusiastas del turismo activo, dinamizando los hostales rurales y pequeños restaurantes de una de las zonas con mayor reto demográfico.",
        "fecha": "2026-07-02",
        "localidad": "Campo de Montiel",
        "sentimiento": "positivo",
        "entidades_clave": ["Cicloturismo", "Montiel", "LEADER", "Reto Demográfico"]
    },
    {
        "id": "clm_8",
        "fuente": "Miel de la Alcarria DO",
        "titulo": "🐝 La DO Miel de la Alcarria alerta de una disminución en la población de abejas",
        "resumen": "Los apicultores de Guadalajara advierten de una merma del 15% en las colmenas debido a la proliferación del avispón asiático y al uso de pesticidas no autorizados. Desde el consejo regulador se exige un plan de choque inmediato y ayudas directas al sector para salvaguardar la polinización de los campos alcarreños.",
        "fecha": "2026-07-02",
        "localidad": "La Alcarria",
        "sentimiento": "negativo",
        "entidades_clave": ["Miel Alcarria", "Apicultura", "Biodiversidad", "Ayudas"]
    },
    {
        "id": "clm_9",
        "fuente": "Ayuntamiento de Consuegra",
        "titulo": "🌬️ Restauración histórica de los icónicos Molinos de Viento de Consuegra",
        "resumen": "Se han iniciado las obras de consolidación estructural en tres de los molinos situados en el cerro Calderico. El proyecto, financiado de forma conjunta por el gobierno regional y el Ministerio de Cultura, devolverá a los gigantes de La Mancha su majestuosidad original, garantizando la seguridad en la próxima festividad de la Rosa del Azafrán.",
        "fecha": "2026-07-01",
        "localidad": "Consuegra",
        "sentimiento": "positivo",
        "entidades_clave": ["Consuegra", "Molinos", "Patrimonio", "Obras"]
    },
    {
        "id": "clm_10",
        "fuente": "Queso Manchego DO",
        "titulo": "🧀 El Queso Manchego amplía fronteras y bate récord de exportación en EE.UU.",
        "resumen": "El consejo regulador ha anunciado un crecimiento del 8% en el volumen de exportación del auténtico queso manchego hacia el mercado norteamericano durante el primer semestre. El sabor único obtenido de la oveja de raza manchega sigue conquistando paladares internacionales, revalorizando las ganaderías locales.",
        "fecha": "2026-07-01",
        "localidad": "Región",
        "sentimiento": "positivo",
        "entidades_clave": ["Queso Manchego", "DO", "Exportaciones", "Ganadería"]
    },
    {
        "id": "clm_11",
        "fuente": "Parque Nacional de Cabañeros",
        "titulo": "🦌 Cabañeros registra un incremento histórico de nacimientos de ciervos",
        "resumen": "La guardería del parque nacional ha contabilizado una tasa de natalidad récord entre las poblaciones de ciervos esta temporada. El buen estado de los pastos en la 'raña' ha propiciado un entorno excelente para las madres gestantes, atrayendo a centenares de amantes de la fotografía de naturaleza este verano.",
        "fecha": "2026-06-30",
        "localidad": "Cabañeros",
        "sentimiento": "positivo",
        "entidades_clave": ["Cabañeros", "Fauna", "Naturaleza", "Conservación"]
    },
    {
        "id": "clm_12",
        "fuente": "Ayuntamiento de Tembleque",
        "titulo": "🏛️ Tembleque celebra las obras de mejora de su Plaza Mayor Barroca",
        "resumen": "El pavimento y los soportales de madera de una de las joyas de la arquitectura popular manchega han sido rehabilitados con técnicas artesanales. El consistorio ha preparado un programa de visitas guiadas nocturnas gratuitas durante los fines de semana de julio para impulsar el comercio gastronómico de la plaza.",
        "fecha": "2026-06-30",
        "localidad": "Tembleque",
        "sentimiento": "positivo",
        "entidades_clave": ["Tembleque", "Plaza Barroca", "Rehabilitación", "Gastronomía"]
    },
    {
        "id": "clm_13",
        "fuente": "Asociación del Campo de Calatrava",
        "titulo": "🌋 Pozuelo de Calatrava acoge el simposio sobre turismo geológico y volcanes",
        "resumen": "Expertos en vulcanología y ecoturismo de toda España se reúnen para debatir el potencial turístico del Geoparque 'Volcanes de Calatrava'. Se plantea la creación de senderos interactivos y centros de interpretación en las antiguas lagunas volcánicas para diversificar la oferta de ocio rural.",
        "fecha": "2026-06-29",
        "localidad": "Pozuelo de Calatrava",
        "sentimiento": "positivo",
        "entidades_clave": ["Volcanes Calatrava", "Geoparque", "Ecoturismo", "Simposio"]
    },
    {
        "id": "clm_14",
        "fuente": "Consejería de Sanidad CLM",
        "titulo": "🏥 Campaña especial de donación de sangre en los pueblos de la llanura manchega",
        "resumen": "Un autobús móvil recorrerá más de treinta pequeñas localidades para facilitar las donaciones antes de la fase álgida de las vacaciones estivales. Se hace un llamamiento especial a los jóvenes de las zonas rurales para mantener las reservas óptimas en los hospitales de Ciudad Real y Albacete.",
        "fecha": "2026-06-29",
        "localidad": "Llanura Manchega",
        "sentimiento": "neutro",
        "entidades_clave": ["Donación de Sangre", "Sanidad", "Solidaridad", "Verano"]
    }
]

# --- FUNCIÓN PARA CARGAR NOTICIAS DEL SISTEMA Y COMBINARLAS ---
@st.cache_data
def cargar_noticias_completas():
    noticias_finales = []
    ids_existentes = set()
    
    def clean_html(text):
        if not text:
            return ""
        import html
        # 1. Unescape HTML entities first so things like &lt;p&gt; become <p>
        clean = html.unescape(text)
        # 2. Strip CDATA wrappers
        clean = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', clean)
        # 3. Strip HTML tags
        clean = re.sub(r'<[^>]*>', '', clean)
        # 4. Clean up any loose leftovers
        clean = clean.replace("<![CDATA[", "").replace("]]>", "")
        return clean.strip()
    
    # 1. Cargar noticias de previsión resumidas del sistema si existen
    if os.path.exists("prevision_noticias_resumidas.json"):
        try:
            with open("prevision_noticias_resumidas.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for n in data:
                        nid = n.get("id", f"res_{len(noticias_finales)}")
                        if nid not in ids_existentes:
                            ids_existentes.add(nid)
                            noticias_finales.append({
                                "id": nid,
                                "fuente": n.get("fuente", n.get("sitio", "Sistema")),
                                "titulo": clean_html(n.get("titulo", "Noticia sin Título")),
                                "resumen": clean_html(n.get("resumen", "")),
                                "fecha": n.get("fecha", "2026-07-05"),
                                "localidad": n.get("localidad", "Región"),
                                "sentimiento": n.get("sentimiento", "neutro"),
                                "entidades_clave": n.get("entidades_clave", [])
                            })
                else:
                    # Formato bloques temáticos
                    for bloque in data.get("bloques_tematicos", []):
                        for n in bloque.get("noticias", []):
                            nid = n.get("id")
                            if nid and nid not in ids_existentes:
                                ids_existentes.add(nid)
                                noticias_finales.append({
                                    "id": nid,
                                    "fuente": n.get("fuente", n.get("sitio", "Sistema")),
                                    "titulo": clean_html(n.get("titulo", "Noticia sin Título")),
                                    "resumen": clean_html(n.get("resumen", "")),
                                    "fecha": n.get("fecha", "2026-07-05"),
                                    "localidad": n.get("localidad", "Región"),
                                    "sentimiento": n.get("sentimiento", "neutro"),
                                    "entidades_clave": n.get("entidades_clave", [])
                                })
                    # Formato noticias individuales
                    for n in data.get("noticias_individuales", []):
                        nid = n.get("id")
                        if nid and nid not in ids_existentes:
                            ids_existentes.add(nid)
                            noticias_finales.append({
                                "id": nid,
                                "fuente": n.get("fuente", n.get("sitio", "Sistema")),
                                "titulo": clean_html(n.get("titulo", "Noticia sin Título")),
                                "resumen": clean_html(n.get("resumen", "")),
                                "fecha": n.get("fecha", "2026-07-05"),
                                "localidad": n.get("localidad", "Región"),
                                "sentimiento": n.get("sentimiento", "neutro"),
                                "entidades_clave": n.get("entidades_clave", [])
                            })
        except Exception:
            pass

    # 2. Cargar noticias descartadas para dar más densidad si es necesario
    if os.path.exists("prevision_noticias_descartadas.json"):
        try:
            with open("prevision_noticias_descartadas.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for n in data:
                    nid = n.get("id")
                    if nid and nid not in ids_existentes:
                        ids_existentes.add(nid)
                        noticias_finales.append({
                            "id": nid,
                            "fuente": n.get("fuente", "Descartada"),
                            "titulo": clean_html(n.get("titulo", "Noticia Descartada")),
                            "resumen": clean_html(n.get("resumen", "Noticia descartada por el sistema.")),
                            "fecha": n.get("fecha", "2026-07-04"),
                            "localidad": n.get("localidad", "Región"),
                            "sentimiento": "neutro",
                            "entidades_clave": n.get("entidades_clave", []),
                            "is_discarded": True
                        })
        except Exception:
            pass

    # 3. Incorporar noticias de la base de datos de ejemplo de Castilla-La Mancha
    for n in NOTICIAS_RURALES:
        if n["id"] not in ids_existentes:
            ids_existentes.add(n["id"])
            noticias_finales.append({
                "id": n["id"],
                "fuente": n.get("fuente"),
                "titulo": clean_html(n.get("titulo")),
                "resumen": clean_html(n.get("resumen")),
                "fecha": n.get("fecha"),
                "localidad": n.get("localidad"),
                "sentimiento": n.get("sentimiento"),
                "entidades_clave": n.get("entidades_clave")
            })

    # 4. Integrar podcasts generados en la lista de noticias de forma cronológica
    try:
        import glob
        podcast_dirs = sorted(glob.glob("podcast_apg_*"))
        for p_dir in podcast_dirs:
            if os.path.isdir(p_dir):
                # Obtener fecha de la carpeta, ej: podcast_apg_20260705_143927 -> 2026-07-05
                folder_name = os.path.basename(p_dir)
                parts = folder_name.replace("podcast_apg_", "").split("_")
                if len(parts) >= 2:
                    f_date = f"{parts[0][:4]}-{parts[0][4:6]}-{parts[0][6:8]}" # YYYY-MM-DD
                    f_time = f"{parts[1][:2]}:{parts[1][2:4]}" # HH:MM
                else:
                    ctime = os.path.getctime(p_dir)
                    dt = datetime.datetime.fromtimestamp(ctime)
                    f_date = dt.strftime("%Y-%m-%d")
                    f_time = dt.strftime("%H:%M")
                    
                # Buscar el MP3 de este podcast
                mp3s = glob.glob(os.path.join(p_dir, "*.mp3"))
                if mp3s:
                    mp3_file = mp3s[0]
                    nid = f"podcast_{folder_name}"
                    
                    # Intentar leer transcripción para un resumen real
                    resumen_podcast = "Boletín de audio diario de actualidad rural regional, con las principales noticias de Castilla-La Mancha locutadas de forma inteligente por la voz neuronal de Dorotea."
                    json_path = os.path.join(p_dir, "transcript.json")
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f_trans:
                                transcript = json.load(f_trans)
                            intro_blocks = [item_tr['content'] for item_tr in transcript if item_tr.get('type') in ['intro', 'block']]
                            if intro_blocks:
                                resumen_podcast = clean_html(intro_blocks[0][:250]) + "..."
                        except:
                            pass
                    
                    # Portada del podcast
                    cover_path = os.path.join(p_dir, "cover.png")
                    cover_url = cover_path if os.path.exists(cover_path) else None
                    
                    # Añadir como una "noticia" especial de tipo podcast
                    if nid not in ids_existentes:
                        ids_existentes.add(nid)
                        noticias_finales.append({
                            "id": nid,
                            "fuente": "Dorotea (Podcast PCC)",
                            "titulo": f"🎙️ Boletín de Audio Regional — Edición {f_date} ({f_time})",
                            "resumen": resumen_podcast,
                            "fecha": f_date,
                            "localidad": "Castilla-La Mancha",
                            "sentimiento": "positivo",
                            "entidades_clave": ["Podcast", "Audio", "Boletín Diario", "Dorotea"],
                            "imagen_url": cover_url,
                            "audio_url": mp3_file,
                            "is_podcast": True
                        })
    except Exception as e_p_load:
        print(f"⚠️ Error cargando podcasts en feed: {e_p_load}")

    # Ordenar noticias por fecha (descendente)
    noticias_finales.sort(key=lambda x: x.get("fecha", ""), reverse=True)
    return noticias_finales

# Cargar todas las noticias
all_news = cargar_noticias_completas()

# --- INTERFAZ DE CONTROL / CONFIGURACIÓN DE FILTROS ---
col_search, col_filter = st.columns([2, 1])
with col_search:
    search_query = st.text_input("🔍 Buscar noticias por título, localidad, resumen o etiquetas...", "", key="news_search")
with col_filter:
    sentiment_filter = st.selectbox("🎭 Filtrar por Sentimiento", ["Todos", "😊 Positivos", "😐 Neutros", "😔 Negativos"])

# Mapear sentimiento
sent_map = {"Todos": "Todos", "😊 Positivos": "positivo", "😐 Neutros": "neutro", "😔 Negativos": "negativo"}
selected_sent = sent_map[sentiment_filter]

# Aplicar búsquedas y filtros
filtered_news = []
for n in all_news:
    # Filtro de sentimiento
    if selected_sent != "Todos" and n.get("sentimiento") != selected_sent:
        continue
    
    # Filtro de búsqueda textual
    if search_query:
        query = search_query.lower()
        title_match = query in n.get("titulo", "").lower()
        summary_match = query in n.get("resumen", "").lower()
        source_match = query in n.get("fuente", "").lower()
        loc_match = query in n.get("localidad", "").lower()
        tags_match = any(query in tag.lower() for tag in n.get("entidades_clave", []))
        
        if not (title_match or summary_match or source_match or loc_match or tags_match):
            continue
            
    filtered_news.append(n)

# --- SELECTOR DE VISTAS (TAB INTERACTIVA PREMIUM) ---
view_mode = st.radio(
    "Selecciona el formato de visualización:",
    ["✨ Feed Editorial (Línea de Tiempo)", "🗂️ Archivo Histórico (Cuadrícula Moderna)"],
    horizontal=True,
    label_visibility="collapsed"
)

# Estilos adicionales locales para las tarjetas de noticias vanguardistas
st.markdown("""
<style>
    /* Estilos vanguardistas de tarjetas de noticias */
    .news-card-wrapper {
        position: relative;
        height: 420px;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 6px 20px rgba(18, 24, 16, 0.05);
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        border: 1px solid rgba(18, 24, 16, 0.08);
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        margin-bottom: 20px;
    }
    
    .news-card-bg {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-size: cover;
        background-position: center;
        transition: transform 0.8s cubic-bezier(0.165, 0.84, 0.44, 1);
        z-index: 1;
    }
    
    .news-card-wrapper:hover .news-card-bg {
        transform: scale(1.08);
    }
    
    .news-card-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            to top, 
            rgba(12, 18, 10, 0.95) 0%, 
            rgba(12, 18, 10, 0.65) 45%, 
            rgba(12, 18, 10, 0.1) 100%
        );
        z-index: 2;
        transition: background 0.4s ease;
    }
    
    .news-card-wrapper:hover .news-card-overlay {
        background: linear-gradient(
            to top, 
            rgba(12, 18, 10, 0.98) 0%, 
            rgba(12, 18, 10, 0.72) 55%, 
            rgba(12, 18, 10, 0.15) 100%
        );
    }
    
    .news-card-content {
        position: relative;
        width: 100%;
        padding: 22px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        z-index: 3;
        height: 100%;
    }
    
    .news-card-wrapper:hover {
        transform: translateY(-6px);
        border-color: rgba(142, 112, 29, 0.4);
        box-shadow: 0 15px 35px rgba(142, 112, 29, 0.12);
    }
    
    .news-source-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: rgba(255, 255, 255, 0.75);
    }
    
    .news-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .dot-positive { background-color: #4CAF50; box-shadow: 0 0 8px #4CAF50; }
    .dot-neutral { background-color: #B0BEC5; box-shadow: 0 0 8px #B0BEC5; }
    .dot-negative { background-color: #FF5252; box-shadow: 0 0 8px #FF5252; }
    
    .news-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #FAF3DC;
        margin-bottom: 8px;
        line-height: 1.35;
        font-family: 'Outfit', sans-serif;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    .news-body {
        font-size: 0.82rem;
        color: rgba(255, 255, 255, 0.85);
        line-height: 1.5;
        margin-bottom: 14px;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-shadow: 0 1px 3px rgba(0,0,0,0.5);
        flex-grow: 0;
    }
    
    .news-footer-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 0;
    }
    
    .news-tag {
        font-size: 0.62rem;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        color: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 3px 8px;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .news-tag:hover {
        background: rgba(142, 112, 29, 0.25);
        border-color: rgba(142, 112, 29, 0.4);
        color: #FAF3DC;
    }
    
    .news-location-tag {
        font-size: 0.62rem;
        background: rgba(142, 112, 29, 0.25);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        color: #FAF3DC;
        border: 1px solid rgba(142, 112, 29, 0.3);
        padding: 3px 8px;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Separador de fechas */
    .timeline-date-header {
        text-align: center;
        margin: 40px 0 24px;
        position: relative;
    }
    .timeline-date-header::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: rgba(142, 112, 29, 0.15);
        z-index: 1;
    }
    .timeline-date-badge {
        position: relative;
        z-index: 2;
        background: #FAF3DC;
        color: #8E701D;
        border: 1px solid rgba(142, 112, 29, 0.3);
        border-radius: 30px;
        padding: 6px 20px;
        font-family: 'Cinzel', serif;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        box-shadow: 0 2px 6px rgba(142, 112, 29, 0.04);
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estados de scroll y paginación
if "visible_days" not in st.session_state:
    st.session_state.visible_days = 3  # Mostrar inicialmente 3 días de noticias
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# --- RENDERIZADO DE LAS VISTAS ---

if not filtered_news:
    st.warning("⚠️ No se encontraron noticias que coincidan con la búsqueda o filtros seleccionados.")
else:
    if "Feed" in view_mode:
        # --- VISTA 1: FEED EDITORIAL (LÍNEA DE TIEMPO CON SCROLL INFINITO) ---
        # Agrupar noticias por fecha
        news_by_date = {}
        for n in filtered_news:
            date_str = n.get("fecha", "Sin fecha")
            news_by_date.setdefault(date_str, []).append(n)
            
        # Obtener los días ordenados de forma descendente
        sorted_days = sorted(news_by_date.keys(), reverse=True)
        
        # Lógica de scroll infinito: Limitar los días mostrados
        visible_days_count = st.session_state.visible_days
        days_to_show = sorted_days[:visible_days_count]
        
        # Renderizar cada día
        for day in days_to_show:
            # Dar formato amigable a la fecha
            try:
                dt = datetime.datetime.strptime(day, "%Y-%m-%d")
                meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                fecha_legible = f"{dias_semana[dt.weekday()]}, {dt.day} de {meses[dt.month-1]} de {dt.year}"
            except Exception:
                fecha_legible = day
                
            st.markdown(f"""
            <div class="timeline-date-header">
                <span class="timeline-date-badge">📅 {fecha_legible}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar las noticias del día en columnas fluidas (máximo 2 noticias por fila para dar aspecto de editorial grande)
            day_news = news_by_date[day]
            
            # Renderizar en filas de hasta 2 columnas
            for chunk_idx in range(0, len(day_news), 2):
                chunk = day_news[chunk_idx:chunk_idx+2]
                cols = st.columns(2)
                for col_idx, news in enumerate(chunk):
                    with cols[col_idx]:
                        if news.get("is_podcast"):
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #FAF3DC 0%, #FFFFFF 100%); border: 2px solid var(--gold); border-radius: 16px; padding: 20px; margin-bottom: 12px; box-shadow: 0 4px 15px rgba(142, 112, 29, 0.12);">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 0.72rem; font-weight: 700; color: var(--gold); text-transform: uppercase;">
                                    <span>🎙️ PODCAST DIARIO</span>
                                    <span>EMISIÓN ACTIVA</span>
                                </div>
                                <div class="news-title" style="color: var(--gold); font-family: 'Cinzel', serif; font-size: 1.15rem; margin-bottom: 10px; line-height: 1.3;">{news.get("titulo")}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col_img_p, col_info_p = st.columns([1, 1.8])
                            with col_img_p:
                                if news.get("imagen_url"):
                                    st.image(news.get("imagen_url"), use_container_width=True)
                            with col_info_p:
                                st.markdown(f"<div style='font-size: 0.84rem; color: var(--muted); line-height: 1.4; margin-bottom: 12px;'>{news.get('resumen')}</div>", unsafe_allow_html=True)
                                render_wavesurfer_player(news.get("audio_url"), key=f"feed_news_p_{news.get('id')}")
                            st.markdown("<hr style='margin: 15px 0; opacity: 0.3;' />", unsafe_allow_html=True)
                            continue

                        sent = news.get("sentimiento", "neutro")
                        dot_cls = f"dot-{sent}"
                        sent_label = "Positivo" if sent == "positivo" else ("Neutro" if sent == "neutro" else "Negativo")
                        
                        tags_html = "".join([f'<span class="news-tag">{tag}</span>' for tag in news.get("entidades_clave", [])[:3]])
                        loc_html = f'<span class="news-location-tag">📍 {news.get("localidad")}</span>' if news.get("localidad") != "Desconocida" else ""
                        
                        # Lógica de imágenes visuales premium
                        imagen_url = news.get("imagen_url")
                        if not imagen_url:
                            # Colección de paisajes castellanos y periodismo rural premium de Unsplash
                            fallbacks = [
                                "https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=600&auto=format&fit=crop", # Paisaje rural / molinos
                                "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?q=80&w=600&auto=format&fit=crop", # Campo de trigo dorado
                                "https://images.unsplash.com/photo-1506306813231-1e1758151806?q=80&w=600&auto=format&fit=crop", # Viñedos y bodegas
                                "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=600&auto=format&fit=crop"  # Prensa y comunicación
                            ]
                            h_idx = abs(hash(news.get("titulo", ""))) % len(fallbacks)
                            imagen_url = fallbacks[h_idx]
                        
                        card_html = f"""
                        <div class="news-card-wrapper">
                            <div class="news-card-bg" style="background-image: url('{imagen_url}');"></div>
                            <div class="news-card-overlay"></div>
                            <div class="news-card-content">
                                <div class="news-source-bar">
                                    <span>{news.get("fuente")}</span>
                                    <span><span class="news-dot {dot_cls}"></span>{sent_label}</span>
                                </div>
                                <div class="news-title">{news.get("titulo")}</div>
                                <div class="news-body">{news.get("resumen")}</div>
                                <div class="news-footer-tags">
                                    {loc_html}
                                    {tags_html}
                                </div>
                            </div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
            st.write("") # Espacio para airear los bloques de días

        # Botón de Cargar Más (Scroll Infinito simulado)
        if len(sorted_days) > visible_days_count:
            st.markdown("<div style='text-align: center; margin-top: 30px;'>", unsafe_allow_html=True)
            if st.button("🔽 Cargar más días (Scroll Infinito)", use_container_width=True, key="btn_load_more"):
                st.session_state.visible_days += 2
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; margin-top: 40px; color: var(--muted); font-size: 0.85rem; font-style: italic;">
                ✨ Has llegado al final del feed de noticias de la última semana.
            </div>
            """, unsafe_allow_html=True)

    else:
        # --- VISTA 2: ARCHIVO HISTÓRICO (CUADRÍCULA CON PAGINACIÓN TRADICIONAL) ---
        news_per_page = 6
        total_news = len(filtered_news)
        total_pages = math.ceil(total_news / news_per_page)
        
        # Validar rango de página actual
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = 1
            
        current_p = st.session_state.current_page
        start_idx = (current_p - 1) * news_per_page
        end_idx = start_idx + news_per_page
        
        page_news = filtered_news[start_idx:end_idx]
        
        st.markdown(f"""
        <div style="margin-bottom: 20px; font-weight: 500; font-size: 0.9rem; color: var(--muted);">
            Mostrando noticias <b>{start_idx+1}</b> - <b>{min(end_idx, total_news)}</b> de un total de <b>{total_news}</b>
        </div>
        """, unsafe_allow_html=True)
        
        # Renderizar en cuadrícula moderna de 3 columnas
        for row_idx in range(0, len(page_news), 3):
            row_chunk = page_news[row_idx:row_idx+3]
            cols = st.columns(3)
            for col_idx, news in enumerate(row_chunk):
                with cols[col_idx]:
                    if news.get("is_podcast"):
                        # Podcast Card design for Grid
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #FAF3DC 0%, #FFFFFF 100%); border: 2px solid var(--gold); border-radius: 16px; padding: 18px; margin-bottom: 12px; box-shadow: 0 4px 15px rgba(142, 112, 29, 0.12);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 0.68rem; font-weight: 700; color: var(--gold); text-transform: uppercase;">
                                <span>🎙️ PODCAST DIARIO</span>
                                <span>{news.get("fecha")}</span>
                            </div>
                            <div style="font-family: 'Cinzel', serif; font-size: 1.0rem; font-weight: 700; color: var(--gold); margin-bottom: 10px; line-height: 1.3;">{news.get("titulo")}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if news.get("imagen_url"):
                            st.image(news.get("imagen_url"), use_container_width=True)
                        st.markdown(f"<div style='font-size: 0.8rem; color: var(--muted); line-height: 1.4; margin-bottom: 10px;'>{news.get('resumen')}</div>", unsafe_allow_html=True)
                        render_wavesurfer_player(news.get("audio_url"), key=f"grid_news_p_{news.get('id')}")
                        continue

                    sent = news.get("sentimiento", "neutro")
                    dot_cls = f"dot-{sent}"
                    sent_label = "Positivo" if sent == "positivo" else ("Neutro" if sent == "neutro" else "Negativo")
                    
                    tags_html = "".join([f'<span class="news-tag">{tag}</span>' for tag in news.get("entidades_clave", [])[:3]])
                    loc_html = f'<span class="news-location-tag">📍 {news.get("localidad")}</span>' if news.get("localidad") != "Desconocida" else ""
                    
                    try:
                        dt = datetime.datetime.strptime(news.get("fecha"), "%Y-%m-%d")
                        formatted_date = dt.strftime("%d/%m/%Y")
                    except Exception:
                        formatted_date = news.get("fecha")
                    
                    # Lógica de imágenes visuales premium
                    imagen_url = news.get("imagen_url")
                    if not imagen_url:
                        fallbacks = [
                            "https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=600&auto=format&fit=crop", # Paisaje rural / molinos
                            "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?q=80&w=600&auto=format&fit=crop", # Campo de trigo dorado
                            "https://images.unsplash.com/photo-1506306813231-1e1758151806?q=80&w=600&auto=format&fit=crop", # Viñedos y bodegas
                            "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=600&auto=format&fit=crop"  # Prensa y comunicación
                        ]
                        h_idx = abs(hash(news.get("titulo", ""))) % len(fallbacks)
                        imagen_url = fallbacks[h_idx]
                    
                    card_html = f"""
                    <div class="news-card-wrapper">
                        <div class="news-card-bg" style="background-image: url('{imagen_url}');"></div>
                        <div class="news-card-overlay"></div>
                        <div class="news-card-content">
                            <div class="news-source-bar">
                                <span>📅 {formatted_date}</span>
                                <span><span class="news-dot {dot_cls}"></span>{sent_label}</span>
                            </div>
                            <div style="font-size: 0.72rem; color: rgba(255, 255, 255, 0.65); margin-bottom: 6px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">{news.get("fuente")}</div>
                            <div class="news-title" style="font-size: 1.05rem;">{news.get("titulo")}</div>
                            <div class="news-body" style="font-size: 0.84rem;">{news.get("resumen")}</div>
                            <div class="news-footer-tags">
                                {loc_html}
                                {tags_html}
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    
        # --- BARRA DE PAGINACIÓN PREMIUM ---
        st.markdown("<hr style='margin: 35px 0 20px;' />", unsafe_allow_html=True)
        col_pag_info, col_pag_buttons = st.columns([1, 1])
        
        with col_pag_info:
            st.markdown(f"""
            <div style="line-height: 2.4; font-size: 0.88rem; color: var(--muted); font-weight: 500;">
                Página <b>{current_p}</b> de <b>{total_pages}</b>
            </div>
            """, unsafe_allow_html=True)
            
        with col_pag_buttons:
            # Crear botones de navegación
            pag_cols = st.columns(5)
            
            # Botón Anterior
            with pag_cols[0]:
                if st.button("⬅️", disabled=current_p == 1, use_container_width=True, key="btn_prev"):
                    st.session_state.current_page -= 1
                    st.rerun()
                    
            # Botones numéricos compactos
            with pag_cols[1]:
                if total_pages >= 1:
                    btn_active_style = "primary" if current_p == 1 else "secondary"
                    if st.button("1", use_container_width=True, key="btn_p1", type=btn_active_style):
                        st.session_state.current_page = 1
                        st.rerun()
                        
            with pag_cols[2]:
                if total_pages >= 2:
                    btn_active_style = "primary" if current_p == 2 else "secondary"
                    if st.button("2", use_container_width=True, key="btn_p2", type=btn_active_style):
                        st.session_state.current_page = 2
                        st.rerun()
                        
            with pag_cols[3]:
                if total_pages >= 3:
                    # Si hay más de 3 páginas y estamos en una página mayor, mostramos puntos suspensivos o la página actual
                    label = str(current_p) if current_p > 2 and current_p < total_pages else "3"
                    val = current_p if current_p > 2 and current_p < total_pages else 3
                    btn_active_style = "primary" if current_p == val else "secondary"
                    if st.button(label, use_container_width=True, key="btn_p_dynamic", type=btn_active_style):
                        st.session_state.current_page = val
                        st.rerun()
                else:
                    st.write("")
                    
            # Botón Siguiente
            with pag_cols[4]:
                if st.button("➡️", disabled=current_p == total_pages, use_container_width=True, key="btn_next_page"):
                    st.session_state.current_page += 1
                    st.rerun()
