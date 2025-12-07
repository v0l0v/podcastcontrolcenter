import streamlit as st
import json
import os
import subprocess
import threading
import threading
import time
import shutil
import datetime
import random
import pandas as pd
# import matplotlib
# matplotlib.use('Agg') # Configurar backend no interactivo para servidor
# import matplotlib.pyplot as plt
# from wordcloud import WordCloud
from src.analytics import analizar_frecuencia_fuentes, analizar_contenido_noticias

# Configuración de la página
st.set_page_config(
    page_title=" Podcast Control Center V0.92",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define Palette (Light Mode Enforced)
colors = {
    "verge_orange": "#e21b3c",
    "verge_purple": "#c209c1",
    "neon_green": "#ccff00",
    "bright_orange": "#ff6600",
    "sunny_yellow": "#ffcc00",
    "deep_black": "#121212",
    "off_white": "#fdfdfd",
    "gray_100": "#f3f3f3", # Light gray for light mode
    "gray_200": "#e0e0e0",
    "gray_800": "#2c2c2c", # Dark text for light mode
    "text_color": "#121212",
    "bg_color": "#ffffff"
}

# Estilos CSS personalizados
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    :root {{
        --verge-orange: {colors['verge_orange']};
        --verge-purple: {colors['verge_purple']};
        --neon-green: {colors['neon_green']};
        --bright-orange: {colors['bright_orange']};
        --sunny-yellow: {colors['sunny_yellow']};
        --deep-black: {colors['deep_black']};
        --off-white: {colors['off_white']};
        --gray-100: {colors['gray_100']};
        --gray-200: {colors['gray_200']};
        --gray-800: {colors['gray_800']};
        --text-color: {colors['text_color']};
        --bg-color: {colors['bg_color']};
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
        background-color: var(--bg_color);
    }}
    
    /* Force Streamlit main container background */
    .stApp {{
        background-color: var(--bg-color);
        color: var(--text-color);
    }}

    /* Main Headers */
    .main-header {{
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 3rem;
        background: linear-gradient(90deg, var(--verge-orange), var(--verge-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
        letter-spacing: -1px;
    }}

    /* Sub Headers */
    .sub-header {{
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.8rem;
        border-bottom: 4px solid var(--neon-green);
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        display: inline-block;
        color: var(--text-color);
    }}

    /* Buttons */
    .stButton > button {{
        border-radius: 0px; /* Sharp corners */
        font-weight: 700;
        border: 2px solid transparent;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .stButton > button:hover {{
        border-color: var(--sunny-yellow);
        transform: translateY(-2px);
        box-shadow: 4px 4px 0px var(--bright-orange);
    }}

    /* Primary Buttons */
    .stButton > button[kind="primary"] {{
        background-color: var(--deep-black);
        color: white;
        border: 1px solid var(--gray-800);
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: var(--verge-orange);
        color: white;
        box-shadow: 4px 4px 0px var(--deep-black);
        border-color: transparent;
    }}

    /* Tab Styling (Enhanced) */
    button[data-baseweb="tab"] {{
        border-radius: 0px;
        margin-right: 8px;
        border: 1px solid transparent;
        font-weight: 700;
        text-transform: uppercase;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        background-color: var(--gray-100);
        color: var(--text-color);
        padding: 0.5rem 1rem;
        border-bottom: 3px solid transparent;
    }}
    
    button[data-baseweb="tab"]:hover {{
        color: var(--verge-orange);
        background-color: var(--gray-200);
        transform: translateY(-2px);
        border-bottom: 3px solid var(--verge-orange);
    }}
    
    button[data-baseweb="tab"][aria-selected="true"] {{
        background-color: var(--neon-green);
        color: black; /* Always black text on neon green */
        border: 1px solid black;
        box-shadow: 3px 3px 0px black;
        transform: translateY(-2px);
    }}

    /* Info Boxes */
    .stAlert {{
        border-radius: 0px;
        border-left: 6px solid var(--sunny-yellow);
        background-color: var(--gray-100);
        color: var(--text-color);
    }}

    /* Dataframes */
    [data-testid="stDataFrame"] {{
        border: 1px solid var(--gray-800);
    }}

    /* Adjust the switch element itself if possible, but the container style is the main visual */
    .stToggle [data-testid="stWidgetLabel"] {{
        margin-bottom: 0; /* Align better with switch */
    }}

    /* Large Round Sidebar Button */
    /* Large Round Sidebar Button */
    [data-testid="stSidebar"] button[kind="primary"] {{
        height: 120px !important;
        border-radius: 500px !important; /* Fully round pill shape */
        font-size: 1.8rem !important;
        white-space: normal !important;
        margin-top: 2rem;
        margin-left: auto !important;
        margin-right: auto !important;
        display: block !important;
        width: 90% !important; /* Slightly less than 100% to show centering */
        box-shadow: 0 4px 14px 0 rgba(0,0,0,0.39) !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: var(--gray-100);
        border-right: 1px solid var(--gray-800);
    }}

    /* Success Message */
    .success-msg {{
        padding: 1rem;
        background-color: var(--neon-green);
        color: black;
        font-weight: bold;
        border: 2px solid black;
        margin-bottom: 1rem;
    }}
</style>
""", unsafe_allow_html=True)

# Ruta del archivo de configuración
CONFIG_FILE = 'podcast_config.json'

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# Cargar configuración inicial
config = cargar_config()

# Título
st.markdown('<div class="main-header">Podcast Control Center v0.92 </div>', unsafe_allow_html=True)

# Sidebar para acciones rápidas
with st.sidebar:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    

    # Mostrar siempre el último podcast generado
    st.markdown("### 🎧 Último Podcast")
    import glob
    try:
        # 1. Buscar directorios de podcasts (podcast_apg_*)
        # Usamos os.path.isdir para asegurar que son carpetas
        podcast_dirs = [d for d in glob.glob("podcast_apg_*") if os.path.isdir(d)]
        
        if podcast_dirs:
            # 2. Encontrar el directorio más reciente
            latest_dir = max(podcast_dirs, key=os.path.getctime)
            
            # 3. Buscar el mp3 dentro de ese directorio
            mp3_files_in_dir = glob.glob(os.path.join(latest_dir, "*.mp3"))
            
            if mp3_files_in_dir:
                latest_mp3 = mp3_files_in_dir[0] # Tomamos el primero que haya
                
                st.success(f"📁 Carpeta: {latest_dir}")
                st.audio(latest_mp3)
                
                # Buscar archivo HTML correspondiente
                html_files_in_dir = glob.glob(os.path.join(latest_dir, "*.html"))
                
                col_mp3, col_html = st.columns(2)
                
                with col_mp3:
                    # Botón de descarga explícito MP3
                    with open(latest_mp3, "rb") as file:
                        st.download_button(
                            label="⬇️ MP3",
                            data=file,
                            file_name=os.path.basename(latest_mp3),
                            mime="audio/mpeg",
                            use_container_width=True
                        )
                
                if html_files_in_dir:
                    latest_html = html_files_in_dir[0]
                    with col_html:
                        with open(latest_html, "rb") as file:
                            st.download_button(
                                label="📄 HTML",
                                data=file,
                                file_name=os.path.basename(latest_html),
                                mime="text/html",
                                use_container_width=True
                            )
            else:
                st.warning(f"Se encontró la carpeta {latest_dir} pero no contiene MP3.")
        else:
            st.text("No hay podcasts generados aún.")
    except Exception as e:
        st.error(f"Error al buscar podcasts: {e}")

    # Botón de Generar Podcast (Movido al final)
    if st.button("GENERAR PODCAST", type="primary"):
        with st.spinner("Iniciando generación del podcast... Esto puede tardar unos minutos."):
            try:
                # Ejecutar el script en un subproceso
                process = subprocess.Popen(
                    ["python3", "dorototal.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.getcwd()
                )
                
                # Mostrar logs en tiempo real (simplificado)
                log_placeholder = st.empty()
                logs = []
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        logs.append(output.strip())
                        # Mostrar solo las últimas 10 líneas
                        log_placeholder.code("\n".join(logs[-15:]))
                
                rc = process.poll()
                
                if rc == 0:
                    st.success("¡Podcast generado con éxito!")
                    st.balloons()
                    time.sleep(2) # Dar tiempo para que el sistema de archivos se actualice
                    st.rerun() # Recargar para mostrar el nuevo podcast abajo
                else:
                    stderr = process.stderr.read()
                    st.error(f"Error en la generación:\n{stderr}")
                    
            except Exception as e:
                st.error(f"Error al ejecutar el script: {e}")

# Pestañas principales
# Pestañas principales
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["⚙️ Configuración General", "🎛️ Audio y Voz", "🗣️ Pronunciación", "📝 Prompts", "📰 Lógica de Noticias", "📚 Historial de Podcasts", "📊 Fuentes", "📈 Estadísticas"])

with tab1:
    st.markdown('<div class="sub-header">Identidad del Podcast</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_presentadora = st.text_input("Nombre de la Presentadora", value=config['podcast_info'].get('presentadora', 'Dorotea'))
        new_region = st.text_input("Región", value=config['podcast_info'].get('region', 'Castilla la Mancha'))
        
    with col2:
        new_email = st.text_input("Email de Contacto", value=config['podcast_info'].get('email_contacto', ''))
        new_email_alias = st.text_input("Alias de Email (para leer)", value=config['podcast_info'].get('email_alias_ssml', ''))

    if st.button("Guardar Cambios Generales"):
        config['podcast_info']['presentadora'] = new_presentadora
        config['podcast_info']['region'] = new_region
        config['podcast_info']['email_contacto'] = new_email
        config['podcast_info']['email_alias_ssml'] = new_email_alias
        guardar_config(config)
        st.success("✅ Configuración general actualizada.")

with tab2:
    st.markdown('<div class="sub-header">Ajustes de Audio</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_voice = st.selectbox(
            "Voz de Google TTS", 
            options=["es-ES-Journey-F", "es-ES-Journey-D", "es-ES-Neural2-A", "es-ES-Neural2-B"],
            index=0 if config['audio_config'].get('voice_name') == "es-ES-Journey-F" else 0
        )
        new_lufs = st.slider("Volumen Objetivo (LUFS)", min_value=-24.0, max_value=-10.0, value=float(config['audio_config'].get('target_lufs', -16.0)), step=0.5)
        
    with col2:
        new_pausa = st.text_input("Pausa Estándar (SSML)", value=config['podcast_info'].get('pausa_estandar', '600ms'))
        new_min_words = st.number_input("Mínimo palabras por noticia", value=int(config['audio_config'].get('min_words_for_audio', 33)))

    if st.button("Guardar Ajustes de Audio"):
        config['audio_config']['voice_name'] = new_voice
        config['audio_config']['target_lufs'] = new_lufs
        config['podcast_info']['pausa_estandar'] = new_pausa
        config['audio_config']['min_words_for_audio'] = new_min_words
        guardar_config(config)
        st.success("✅ Ajustes de audio actualizados.")

with tab3:
    st.markdown('<div class="sub-header">Diccionario de Pronunciación</div>', unsafe_allow_html=True)
    st.markdown("Define cómo debe leer la IA ciertas palabras o siglas.")
    
    col_dict1, col_dict2 = st.columns(2)
    
    with col_dict1:
        st.markdown("#### 📖 Palabras y Nombres")
        correcciones = config['pronunciation'].get('correcciones', {})
        
        # Editor tipo tabla (simple)
        new_correcciones_str = st.text_area(
            "Formato: ORIGINAL : CORRECCIÓN (una por línea)",
            value="\n".join([f"{k} : {v}" for k, v in correcciones.items()]),
            height=300
        )
        
    with col_dict2:
        st.markdown("#### 🔤 Siglas (Deletreo)")
        siglas = config['pronunciation'].get('siglas', {})
        
        new_siglas_str = st.text_area(
            "Formato: SIGLA : DELETREO (una por línea)",
            value="\n".join([f"{k} : {v}" for k, v in siglas.items()]),
            height=300
        )

    if st.button("Actualizar Diccionarios"):
        # Procesar texto a diccionario
        def parse_dict_text(text):
            new_dict = {}
            for line in text.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    new_dict[key.strip()] = val.strip()
            return new_dict
            
        config['pronunciation']['correcciones'] = parse_dict_text(new_correcciones_str)
        config['pronunciation']['siglas'] = parse_dict_text(new_siglas_str)
        guardar_config(config)
        st.success("✅ Diccionarios de pronunciación actualizados.")

with tab4:
    st.markdown('<div class="sub-header">Editor de Personalidad y Prompts</div>', unsafe_allow_html=True)
    st.info("Aquí defines CÓMO habla Dorotea. Usa `{presentadora}`, `{region}`, `{email}`, `{email_alias}` y `{pausa}` como variables en los textos.")
    
    prompts_cfg = config.get('prompts', {})
    
    # 1. Personalidad Base
    st.markdown("### 🧠 Personalidad Base (Instrucción Maestra)")
    st.markdown("Esta instrucción define el estilo general de Dorotea al narrar noticias.")
    new_persona = st.text_area(
        "Prompt de Personalidad",
        value=prompts_cfg.get('persona_base', ''),
        height=150
    )
    
    st.markdown("---")
    
    # 2. Saludos
    st.markdown("### 👋 Saludos de Bienvenida")
    col_sal1, col_sal2 = st.columns(2)
    with col_sal1:
        saludo_lunes = st.text_area("Lunes", value=prompts_cfg.get('saludos', {}).get('lunes', ''), height=150)
        saludo_viernes = st.text_area("Viernes", value=prompts_cfg.get('saludos', {}).get('viernes', ''), height=150)
    with col_sal2:
        saludo_mj = st.text_area("Martes-Jueves", value=prompts_cfg.get('saludos', {}).get('martes_jueves', ''), height=150)
        saludo_finde = st.text_area("Fin de Semana", value=prompts_cfg.get('saludos', {}).get('finde', ''), height=150)

    st.markdown("---")

    # 3. Despedidas
    st.markdown("### 👋 Despedidas y Cierre")
    col_desp1, col_desp2 = st.columns(2)
    with col_desp1:
        desp_lunes = st.text_area("Cierre Lunes", value=prompts_cfg.get('despedidas', {}).get('lunes', ''), height=150)
        desp_viernes = st.text_area("Cierre Viernes", value=prompts_cfg.get('despedidas', {}).get('viernes', ''), height=150)
    with col_desp2:
        desp_mj = st.text_area("Cierre Martes-Jueves", value=prompts_cfg.get('despedidas', {}).get('martes_jueves', ''), height=150)
        desp_finde = st.text_area("Cierre Finde", value=prompts_cfg.get('despedidas', {}).get('finde', ''), height=150)

    st.markdown("---")
    
    # 4. Firmas
    st.markdown("### ✍️ Firma Final (Última frase)")
    col_firma1, col_firma2 = st.columns(2)
    with col_firma1:
        firma_lunes = st.text_area("Firma Lunes", value=prompts_cfg.get('firmas', {}).get('lunes', ''), height=100)
        firma_viernes = st.text_area("Firma Viernes", value=prompts_cfg.get('firmas', {}).get('viernes', ''), height=100)
    with col_firma2:
        firma_mj = st.text_area("Firma Martes-Jueves", value=prompts_cfg.get('firmas', {}).get('martes_jueves', ''), height=100)
        firma_finde = st.text_area("Firma Finde", value=prompts_cfg.get('firmas', {}).get('finde', ''), height=100)

    if st.button("Guardar Personalidad y Prompts"):
        # Actualizar estructura
        if 'prompts' not in config: config['prompts'] = {}
        
        config['prompts']['persona_base'] = new_persona
        
        config['prompts']['saludos'] = {
            'lunes': saludo_lunes, 'martes_jueves': saludo_mj, 'viernes': saludo_viernes, 'finde': saludo_finde
        }
        config['prompts']['despedidas'] = {
            'lunes': desp_lunes, 'martes_jueves': desp_mj, 'viernes': desp_viernes, 'finde': desp_finde
        }
        config['prompts']['firmas'] = {
            'lunes': firma_lunes, 'martes_jueves': firma_mj, 'viernes': firma_viernes, 'finde': firma_finde
        }
        
        guardar_config(config)
        st.success("✅ ¡Personalidad de Dorotea actualizada!")



# Pestaña 5: Lógica de Noticias
with tab5:
    st.markdown('<div class="sub-header">Lógica de Selección y Análisis</div>', unsafe_allow_html=True)
    
    col_logic1, col_logic2 = st.columns(2)
    
    with col_logic1:
        st.markdown("#### 🔍 Filtrado y Agrupación")
        new_dedup = st.slider("Umbral de Similitud (Deduplicación)", 0.5, 1.0, float(config['generation_config'].get('dedup_similarity_threshold', 0.9)), 0.05, help="Si dos noticias se parecen más que esto, se consideran la misma.")
        new_min_block = st.number_input("Mínimo noticias por bloque", value=int(config['generation_config'].get('min_news_per_block', 2)), help="Mínimo de noticias para formar un tema.")
        
        st.markdown("#### ⏱️ Límites de Selección")
        new_max_items = st.slider("Máximo de Noticias a Procesar", 5, 50, int(config['generation_config'].get('max_news_items', 20)), 1, help="Límite duro de noticias que entran al guion.")
        new_window_hours = st.slider("Ventana de Tiempo (Horas)", 12, 168, int(config['generation_config'].get('news_window_hours', 48)), 12, help="Solo noticias publicadas hace X horas.")
        
    with col_logic2:
        st.markdown("#### 🤖 Prompts de Análisis")
        st.info("Define las reglas para que la IA entienda las noticias.")

    analysis_prompts = config.get('prompts', {}).get('analysis_prompts', {})
    
    st.markdown("**1. Criterios de Clasificación (Informativo vs Irrelevante)**")
    prompt_clasif = st.text_area("Instrucciones para clasificar", value=analysis_prompts.get('clasificacion_criterios', ''), height=150)
    
    st.markdown("**2. Instrucciones de Resumen**")
    prompt_resumen = st.text_area("Instrucciones para resumir la noticia", value=analysis_prompts.get('resumen_instrucciones', ''), height=200)
    
    st.markdown("**3. Lógica de Agrupación**")
    prompt_agrup = st.text_area("Instrucciones para agrupar temas", value=analysis_prompts.get('agrupacion_instrucciones', ''), height=150)

    if st.button("Guardar Lógica de Noticias"):
        config['generation_config']['dedup_similarity_threshold'] = new_dedup
        config['generation_config']['min_news_per_block'] = new_min_block
        config['generation_config']['max_news_items'] = new_max_items
        config['generation_config']['news_window_hours'] = new_window_hours
        
        if 'prompts' not in config: config['prompts'] = {}
        if 'analysis_prompts' not in config['prompts']: config['prompts']['analysis_prompts'] = {}
        
        config['prompts']['analysis_prompts']['clasificacion_criterios'] = prompt_clasif
        config['prompts']['analysis_prompts']['resumen_instrucciones'] = prompt_resumen
        config['prompts']['analysis_prompts']['agrupacion_instrucciones'] = prompt_agrup
        
        guardar_config(config)
        st.success("✅ Lógica de noticias actualizada.")

with tab6:
    st.markdown('<div class="sub-header">Historial de Podcasts</div>', unsafe_allow_html=True)
    
    col_hist_header, col_hist_actions = st.columns([3, 1])
    with col_hist_header:
        st.info("Aquí podrás consultar, descargar y gestionar los episodios anteriores.")
    with col_hist_actions:
        if st.button("🛠️ Generar Datos Prueba", help="Crea 3 podcasts ficticios para probar la interfaz"):
            try:
                base_audio = "audio_assets/cortinilla_cta.mp3"
                if not os.path.exists(base_audio):
                    st.error(f"No se encuentra {base_audio} para usar como base.")
                else:
                    for i in range(3):
                        # Fecha ficticia aleatoria en los últimos 30 días
                        days_ago = random.randint(1, 30)
                        fake_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
                        folder_name = f"podcast_apg_{fake_date.strftime('%Y-%m-%d_%H-%M')}_TEST_{i}"
                        
                        os.makedirs(folder_name, exist_ok=True)
                        shutil.copy(base_audio, os.path.join(folder_name, f"podcast_test_{i}.mp3"))
                    st.success("Datos de prueba generados.")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"Error generando datos: {e}")

    # Listar todos los podcasts disponibles
    import glob
    try:
        podcast_dirs = sorted([d for d in glob.glob("podcast_apg_*") if os.path.isdir(d)], key=os.path.getctime, reverse=True)
        
        if not podcast_dirs:
            st.write("No hay podcasts generados.")
        else:
            for p_dir in podcast_dirs:
                # Extraer fecha legible del nombre si es posible
                display_name = p_dir.replace("podcast_apg_", "").replace("_", " ")
                
                with st.expander(f"🎙️ {display_name}", expanded=False):
                    col_info, col_actions = st.columns([3, 1])
                    
                    mp3s = glob.glob(os.path.join(p_dir, "*.mp3"))
                    
                    with col_info:
                        if mp3s:
                            st.audio(mp3s[0])
                            st.caption(f"Archivo: {os.path.basename(mp3s[0])}")
                        else:
                            st.warning("Carpeta vacía o sin MP3.")

                    with col_actions:
                        if mp3s:
                            with open(mp3s[0], "rb") as f:
                                st.download_button(
                                    label="⬇️ Descargar",
                                    data=f,
                                    file_name=os.path.basename(mp3s[0]),
                                    key=f"dl_{p_dir}",
                                    use_container_width=True
                                )
                        
                        st.markdown("---")
                        if st.button("🗑️ Eliminar", key=f"del_{p_dir}", type="secondary", use_container_width=True):
                            try:
                                shutil.rmtree(p_dir)
                                st.toast(f"Eliminado: {p_dir}")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error eliminando: {e}")

    except Exception as e:
        st.error(f"Error leyendo historial: {e}")

with tab7:
    st.markdown('<div class="sub-header">Informe de Actividad de Fuentes</div>', unsafe_allow_html=True)
    st.markdown("Analiza cuántas noticias ha publicado cada fuente recientemente para detectar feeds inactivos o rotos.")
    
    with st.spinner("Analizando historial de RSS..."):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        feeds_path = os.path.join(base_dir, 'feeds.txt')
        if os.path.exists(feeds_path):
            try:
                df = analizar_frecuencia_fuentes(feeds_path)
                st.dataframe(
                    df, 
                    column_config={
                        "Estado": st.column_config.TextColumn("Salud"),
                        "24h": st.column_config.ProgressColumn("Hoy", format="%d", min_value=0, max_value=10),
                        "7 días": st.column_config.ProgressColumn("Semana", format="%d", min_value=0, max_value=20),
                    },
                    use_container_width=True,
                    hide_index=True
                )
            except Exception as e:
                st.error(f"Error al analizar fuentes: {e}")
        else:
            st.error("No se encuentra el archivo feeds.txt")

with tab8:
    st.markdown('<div class="sub-header">Análisis de Contenido</div>', unsafe_allow_html=True)
    st.info("Visualiza qué temas, poblaciones y grupos GAL están dominando las noticias.")
    
    # Selector de rango de tiempo
    time_range = st.selectbox(
        "Filtrar por fecha:",
        ["Todo el historial", "Últimas 24 horas", "Última Semana", "Último Mes", "Último Año"],
        index=0
    )
    
    with st.spinner("Analizando contenido de noticias..."):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_path = os.path.join(base_dir, 'cache_noticias.json')
        
        if os.path.exists(cache_path):
            # Calcular fecha mínima
            min_date = None
            now = datetime.datetime.now()
            
            if time_range == "Últimas 24 horas":
                min_date = now - datetime.timedelta(days=1)
            elif time_range == "Última Semana":
                min_date = now - datetime.timedelta(days=7)
            elif time_range == "Último Mes":
                min_date = now - datetime.timedelta(days=30)
            elif time_range == "Último Año":
                min_date = now - datetime.timedelta(days=365)
            
            # Pasar min_date a la función de análisis
            poblaciones, gal, temas = analizar_contenido_noticias(cache_path, min_date=min_date)
            
            if not poblaciones and not gal and not temas:
                st.warning("No se encontraron datos para el periodo seleccionado.")
            else:
                col_table1, col_table2 = st.columns(2)
                
                with col_table1:
                    st.markdown("### 🏘️ Poblaciones")
                    if poblaciones:
                        df_pob = pd.DataFrame(list(poblaciones.items()), columns=['Población', 'Menciones'])
                        st.dataframe(
                            df_pob.sort_values('Menciones', ascending=False),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Menciones": st.column_config.NumberColumn("Menciones", format="%d")
                            }
                        )
                    else:
                        st.info("No se detectaron poblaciones.")
                    
                with col_table2:
                    st.markdown("### 🚜 Grupos GAL")
                    if gal:
                        df_gal = pd.DataFrame(list(gal.items()), columns=['Grupo GAL', 'Menciones'])
                        st.dataframe(
                            df_gal.sort_values('Menciones', ascending=False),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Menciones": st.column_config.NumberColumn("Menciones", format="%d")
                            }
                        )
                    else:
                        st.info("No se detectaron Grupos de Acción Local.")
                
                st.markdown("---")
                
                st.markdown("### 🗣️ Temas Recurrentes")
                if temas:
                    df_temas = pd.DataFrame(list(temas.items()), columns=['Término', 'Frecuencia'])
                    st.dataframe(
                        df_temas.sort_values('Frecuencia', ascending=False).head(50),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No se detectaron temas.")
                
        else:
            st.error("No se encuentra cache_noticias.json. Genera un podcast primero para tener datos.")

# Footer
st.markdown("---")
st.markdown("Desarrollado para Ache Podcast Generator | v1.0")
