import streamlit as st
import json
import os
from dotenv import load_dotenv
load_dotenv() # Cargar variables de entorno desde .env
import subprocess
import threading
import threading
import time
import shutil
import datetime

import pandas as pd
# import matplotlib
# matplotlib.use('Agg') # Configurar backend no interactivo para servidor
# import matplotlib.pyplot as plt
# from wordcloud import WordCloud
from src.analytics import analizar_frecuencia_fuentes
from src.llm_utils import generar_texto_con_gemini

from mcmcn_prompts import PromptsCreativos


# Configuración de la página
st.set_page_config(
    page_title="Podcast Control Center v0.97",
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
st.markdown('<div class="main-header">Podcast Control Center v0.97</div>', unsafe_allow_html=True)

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
                

            else:
                st.warning(f"Se encontró la carpeta {latest_dir} pero no contiene MP3.")
        else:
            st.text("No hay podcasts generados aún.")
    except Exception as e:
        st.error(f"Error al buscar podcasts: {e}")

    st.markdown("---")
    
    # === ASISTENTE DE GENERACIÓN (WIZARD) ===
    st.header("🧙‍♂️ Asistente de Producción")
    
    # Estado 1: Confirmación de Configuración
    if 'config_check' not in st.session_state:
        st.session_state['config_check'] = False

    # Estado 0: Selección de Modo
    st.markdown("#### 0️⃣ Modo de Operación")
    mode_options = ["Completo (Podcast + Especiales)", "Solo Podcast (Sin Especiales)", "Solo Episodios Especiales"]
    selected_mode_label = st.radio("Selecciona qué deseas generar:", mode_options, index=0, key="gen_mode_selector")
    
    mode_only_special = "Solo Episodios Especiales" in selected_mode_label
    mode_skip_special = "Sin Especiales" in selected_mode_label
    
    if mode_only_special:
        st.info("ℹ️ Modifica o selecciona los guiones especiales antes de generar el audio.")
        
        # Buscar archivos .txt que empiecen por EE_
        ee_scripts = sorted(glob.glob("EE_*.txt"))
        
        selected_scripts = []
        
        if not ee_scripts:
            st.warning("No se han encontrado guiones (EE_*.txt).")
        else:
            st.markdown("##### 📜 Guiones disponibles:")
            for script in ee_scripts:
                col_sel, col_del = st.columns([4, 1])
                with col_sel:
                    # Checkbox marcado por defecto
                    if st.checkbox(f"{script}", value=True, key=f"sel_{script}"):
                        selected_scripts.append(script)
                with col_del:
                    if st.button("🗑️", key=f"del_script_{script}", help="Eliminar guion"):
                        try:
                            os.remove(script)
                            st.toast(f"Borrado: {script}")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error("Error")

            st.divider()
            
            # Botón de generar solo si hay seleccionados
            btn_disabled = len(selected_scripts) == 0
            
            if st.button("🚀 GENERAR SELECCIONADOS", type="primary", disabled=btn_disabled):
                with st.spinner(f"Procesando {len(selected_scripts)} episodios..."):
                    try:
                        cmd = ["python3", "dorototal.py", "--only-special", "--file-list"] + selected_scripts
                        
                        process = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            cwd=os.getcwd()
                        )
                        if process.returncode == 0:
                            st.success("✅ Proceso completado.")
                            st.code(process.stdout)
                            # Recargar para actualizar (quizas se movieron a .processed)
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Error en el proceso.")
                            st.code(process.stderr)
                    except Exception as e:
                        st.error(f"Error ejecución: {e}")
        
    st.divider()

    # Si es solo especiales, ocultamos el resto del wizard
    if not mode_only_special:
        st.markdown("#### 1️⃣ Configuración")
        st.caption("Antes de analizar, asegúrate de que en la pestaña [LÓGICA DE NOTICIAS] los Límites de Selección son correctos.Si los modificas, guardalos presionando el boton al final de la pantalla [GUARDAR LÓGICA DE NOTICIAS]")
        
        config_checked = st.checkbox("He revisado la configuración", value=st.session_state['config_check'], key='chk_config')
        st.session_state['config_check'] = config_checked

        # Estado 2: Análisis (Solo si check marcado)
        st.markdown("#### 2️⃣ Análisis de Fuentes")
        btn_analizar_disabled = not config_checked
        
        if st.button("🔎 ANALIZAR NOTICIAS", type="secondary", disabled=btn_analizar_disabled):
            with st.spinner("Conectando con feeds, filtrando y RESUMIENDO noticias con IA..."):
                try:
                    if os.path.exists("prevision_noticias_resumidas.json"):
                        os.remove("prevision_noticias_resumidas.json")
                    if os.path.exists("seleccion_usuario.json"):
                        os.remove("seleccion_usuario.json")
                        
                    # Resetear confirmación al re-analizar
                    st.session_state['news_confirmed'] = False

                    process = subprocess.run(
                        ["python3", "dorototal.py", "--preview"],
                        capture_output=True,
                        text=True,
                        cwd=os.getcwd()
                    )
                    
                    if process.returncode == 0:
                        st.success("✅ Análisis completado. Ve al panel principal para editar.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error analizando noticias:\n{process.stderr}")
                except Exception as e:
                    st.error(f"Error ejecución: {e}")

        # Lógica de Selección Manual (Edición)
        manual_selection_mode = False
        selected_news_to_process = []
        
        if os.path.exists("prevision_noticias_resumidas.json"):
            st.markdown("#### 3️⃣ Revisión y Confirmación")
            
            # Cargar datos para el formulario principal (que se muestra en el sidebar también para feedback visual)
            try:
                with open("prevision_noticias_resumidas.json", "r", encoding="utf-8") as f:
                    news_candidates = json.load(f)
                    
                manual_selection_mode = True
                st.info(f"Tienes {len(news_candidates)} noticias pendientes de revisión en el panel central.")
                
                # --- FORMULARIO DE EDICIÓN (PANEL CENTRAL REVISADO) ---
                # Mostramos el formulario en un expander AQUI en el sidebar NO, debe ir en el main, 
                # pero necesitamos la lógica de confirmación aquí.
                # Para simplificar y seguir la petición del usuario: La edición se hace abajo (main), 
                # pero el botón de CONFIRMAR lo ponemos aquí como paso del wizard.
                
                # Botón de confirmación explícita
                if 'news_confirmed' not in st.session_state:
                    st.session_state['news_confirmed'] = False
                    
                if st.button("✅ NOTICIAS REVISADAS Y CONFIRMADAS", type="secondary", disabled=False):
                    st.session_state['news_confirmed'] = True
                    st.success("¡Perfecto! Ahora puedes generar el podcast.")
                
                if st.session_state['news_confirmed']:
                    st.caption("✅ Selección confirmada.")
                else:
                    st.warning("⚠️ Debes editar (si quieres) y luego pulsar confirmar arriba.")

            except Exception as e:
                st.error("Error leyendo archivo de preview.")

        # Estado 4: Generación
        st.markdown("#### 4️⃣ Generación Final")
        
        # Solo activo si estamos en modo manual Y confirmado
        can_generate = False
        btn_type = "secondary"
        btn_text = "GENERAR PODCAST (Espera...)"
        
        if manual_selection_mode:
            if st.session_state.get('news_confirmed', False):
                can_generate = True
                btn_type = "primary"
                btn_text = "🎙️ ¡VAMOS A GENERAR EL PODCAST!"
            else:
                btn_text = "Confirma las noticias primero"
        else:
            # Caso sin preview (no debería pasar con este flujo, pero fallback)
            if config_checked: 
                 # Si no hay preview json, quizás quieran generar directo sin editar (legacy)
                 # Pero el usuario pidió guiado. Forzamos análisis primero.
                 btn_text = "Analiza las noticias primero (Paso 2)"

        if st.button(btn_text, type=btn_type, disabled=not can_generate):
            with st.spinner("Generando audios, montando bloques y finalizando podcast..."):
                try:
                    # Recopilar la selección FINAL desde el session_state si se guardó en el formulario principal
                    # OJO: La edición real ocurre en el MAIN loop.
                    # Necesitamos que el formulario principal actualice 'noticias_editadas_finales'
                    # Y que usemos eso aquí.
                    
                    # Leemos la selección del state o del archivo original si no se tocó nada
                    final_news = st.session_state.get('noticias_editadas_finales', [])
                    
                    # Si está vacío, puede ser que no hayan tocado nada y confirmado directo.
                    # En ese caso cargamos el json original de preview
                    if not final_news and os.path.exists("prevision_noticias_resumidas.json"):
                         with open("prevision_noticias_resumidas.json", "r", encoding="utf-8") as f:
                            final_news = json.load(f)

                    # Guardar selección final para el script
                    with open("seleccion_usuario.json", "w", encoding="utf-8") as f:
                        json.dump(final_news, f, ensure_ascii=False, indent=4)
                    
                    cmd = ["python3", "dorototal.py", "--from-json", "seleccion_usuario.json"]
                    
                    # Lógica para saltar especiales si el usuario lo pidió
                    if mode_skip_special:
                        cmd.append("--skip-special")

                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=os.getcwd()
                    )
                    
                    # Logs
                    log_placeholder = st.empty()
                    logs = []
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            logs.append(output.strip())
                            log_placeholder.code("\n".join(logs[-15:]))
                    
                    if process.poll() == 0:
                        st.success("¡Podcast generado con éxito!")
                        st.balloons()
                        # Resetear
                        if os.path.exists("seleccion_usuario.json"): os.remove("seleccion_usuario.json")
                        if os.path.exists("prevision_noticias_resumidas.json"): os.remove("prevision_noticias_resumidas.json")
                        st.session_state['news_confirmed'] = False # Reset
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Error generación:\n{process.stderr.read()}")
                        
                except Exception as e:
                    st.error(f"Error script: {e}")



# Pestañas principales
# Pestañas principales
# Pestañas principales
tab_rev, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📝 Revisión", "⚙️ Configuración General", "🎛️ Audio y Voz", "🗣️ Pronunciación", "📝 Prompts", "📰 Lógica de Noticias", "📚 Historial de Podcasts", "📊 Fuentes"])

with tab_rev:
    st.markdown('<div class="sub-header">Revisión de Noticias</div>', unsafe_allow_html=True)
    # --- ZONA PRINCIPAL DE EDICIÓN (VISUALIZACIÓN) ---
    # Si hay noticias para revisar, mostramos el editor AQUI
    if 'manual_selection_mode' in locals() and manual_selection_mode:
        
        st.info("Revisa los resúmenes generados por la IA. Edita lo que quieras y pulsa 'Guardar Cambios' al final.")
        
        # Intentar recuperar candidates si no están en local (por si acaso)
        if 'news_candidates' not in locals():
             try:
                with open("prevision_noticias_resumidas.json", "r", encoding="utf-8") as f:
                    news_candidates = json.load(f)
             except:
                news_candidates = []

        if news_candidates:
            with st.form("seleccion_noticias_main"):
                 edited_news_list_main = []
                 
                 for i, news in enumerate(news_candidates):
                     # Título robusto
                     titulo_original = news.get("titulo") or news.get("sitio")
                     resumen_original = news.get("resumen", "")
                     
                     # Usar expander para el detalle - expandido por defecto el primero? no, mejor colapsado para limpieza
                     with st.expander(f"Noticia {i+1}: {titulo_original}", expanded=(i==0)):
                         
                         col_check, col_content = st.columns([0.1, 0.9])
                         
                         with col_check:
                             # Checkbox de inclusión
                             incluir = st.checkbox("Incluir", value=True, key=f"main_chk_{i}")
                         
                         with col_content:
                             # Campos editables
                             new_titulo = st.text_input("Título", value=titulo_original, key=f"main_title_{i}")
                             new_resumen = st.text_area("Resumen (Texto para el locutor)", value=resumen_original, height=150, key=f"main_res_{i}")
                             st.caption(f"Fuente: {news.get('sitio', 'Desconocida')} | Fecha: {news.get('fecha', '---')}")
                         
                         if incluir:
                             # Crear copia de la noticia con los datos editados
                             news_edited = news.copy()
                             news_edited['titulo'] = new_titulo
                             news_edited['resumen'] = new_resumen
                             edited_news_list_main.append(news_edited)

                 st.markdown("---")
                 col_save, col_info = st.columns([1, 2])
                 with col_save:
                     update_selection = st.form_submit_button("💾 GUARDAR CAMBIOS", type="primary", use_container_width=True)
                 
                 if update_selection:
                     st.session_state['noticias_editadas_finales'] = edited_news_list_main
                     st.toast(f"✅ Se han guardado {len(edited_news_list_main)} noticias. Ahora confirma en la barra lateral.")
    else:
        st.write("No hay análisis pendiente. Pulsa '🔎 ANALIZAR NOTICIAS' en la barra lateral para comenzar.")

with tab1:
    st.markdown('<div class="sub-header">Identidad de Podcast</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_presentadora = st.text_input("Nombre de la Presentadora", value=config['podcast_info'].get('presentadora', 'Dorotea'))
        new_region = st.text_input("Región", value=config['podcast_info'].get('region', 'Castilla la Mancha'))
        
    with col2:
        new_email = st.text_input("Email de Contacto", value=config['podcast_info'].get('email_contacto', ''))
        new_email_alias = st.text_input("Alias de Email (para leer)", value=config['podcast_info'].get('email_alias_ssml', ''))
        
        # Selector de archivo de feeds
        txt_files = [f for f in os.listdir('.') if f.endswith('.txt')]
        if 'feeds.txt' not in txt_files and os.path.exists('feeds.txt'):
            txt_files.append('feeds.txt')
        
        current_feeds_file = config.get('generation_config', {}).get('feeds_file', 'feeds.txt')
        if current_feeds_file not in txt_files:
            txt_files.append(current_feeds_file)
            
        new_feeds_file = st.selectbox(
            "Archivo de Feeds",
            options=sorted(list(set(txt_files))),
            index=txt_files.index(current_feeds_file) if current_feeds_file in txt_files else 0
        )

    if st.button("Guardar Cambios Generales"):
        config['podcast_info']['presentadora'] = new_presentadora
        config['podcast_info']['region'] = new_region
        config['podcast_info']['email_contacto'] = new_email
        config['podcast_info']['email_alias_ssml'] = new_email_alias
        
        if 'generation_config' not in config: config['generation_config'] = {}
        config['generation_config']['feeds_file'] = new_feeds_file
        
        guardar_config(config)
        st.success("✅ Configuración general actualizada.")

with tab2:
    st.markdown('<div class="sub-header">Ajustes de Audio</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_voice = st.selectbox(
            "Voz de Google TTS", 
            options=[
                # --- CHIRP 3 HD (Generative, Ultra-Realistic) ---
                "es-ES-Chirp3-HD-Achernar [FEMALE]", "es-ES-Chirp3-HD-Aoede [FEMALE]", 
                "es-ES-Chirp3-HD-Autonoe [FEMALE]", "es-ES-Chirp3-HD-Callirrhoe [FEMALE]", 
                "es-ES-Chirp3-HD-Despina [FEMALE]", "es-ES-Chirp3-HD-Erinome [FEMALE]", 
                "es-ES-Chirp3-HD-Gacrux [FEMALE]", "es-ES-Chirp3-HD-Kore [FEMALE]", 
                "es-ES-Chirp3-HD-Laomedeia [FEMALE]", "es-ES-Chirp3-HD-Leda [FEMALE]", 
                "es-ES-Chirp3-HD-Pulcherrima [FEMALE]", "es-ES-Chirp3-HD-Sulafat [FEMALE]", 
                "es-ES-Chirp3-HD-Vindemiatrix [FEMALE]", "es-ES-Chirp3-HD-Zephyr [FEMALE]",
                
                "es-ES-Chirp3-HD-Achird [MALE]", "es-ES-Chirp3-HD-Algenib [MALE]", 
                "es-ES-Chirp3-HD-Algieba [MALE]", "es-ES-Chirp3-HD-Alnilam [MALE]", 
                "es-ES-Chirp3-HD-Charon [MALE]", "es-ES-Chirp3-HD-Enceladus [MALE]", 
                "es-ES-Chirp3-HD-Fenrir [MALE]", "es-ES-Chirp3-HD-Iapetus [MALE]", 
                "es-ES-Chirp3-HD-Orus [MALE]", "es-ES-Chirp3-HD-Puck [MALE]", 
                "es-ES-Chirp3-HD-Rasalgethi [MALE]", "es-ES-Chirp3-HD-Sadachbia [MALE]", 
                "es-ES-Chirp3-HD-Sadaltager [MALE]", "es-ES-Chirp3-HD-Schedar [MALE]", 
                "es-ES-Chirp3-HD-Umbriel [MALE]", "es-ES-Chirp3-HD-Zubenelgenubi [MALE]",

                # --- CHIRP HD (Previous Gen) ---
                "es-ES-Chirp-HD-F [FEMALE]", "es-ES-Chirp-HD-O [FEMALE]", 
                "es-ES-Chirp-HD-D [MALE]",

                # --- NEURAL2 (High Quality) ---
                "es-ES-Neural2-A [FEMALE]", "es-ES-Neural2-E [FEMALE]", "es-ES-Neural2-H [FEMALE]",
                "es-ES-Neural2-F [MALE]", "es-ES-Neural2-G [MALE]",

                # --- STUDIO (Professional) ---
                "es-ES-Studio-C [FEMALE]", "es-ES-Studio-F [MALE]",

                # --- JOURNEY (Experimental) ---
                "es-ES-Journey-F [FEMALE]", "es-ES-Journey-D [MALE]",
                
                # --- WAVENET (Legacy) ---
                "es-ES-Wavenet-F [FEMALE]", "es-ES-Wavenet-H [FEMALE]",
                "es-ES-Wavenet-E [MALE]", "es-ES-Wavenet-G [MALE]",
                
                # --- STANDARD (Basic) ---
                "es-ES-Standard-F [FEMALE]", "es-ES-Standard-H [FEMALE]",
                "es-ES-Standard-E [MALE]", "es-ES-Standard-G [MALE]"
            ],
            index=0
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
    
    st.info("Aquí podrás consultar, descargar y gestionar los episodios anteriores.")


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
                    htmls = glob.glob(os.path.join(p_dir, "*.html"))
                    json_path = os.path.join(p_dir, "transcript.json")
                    
                    with col_info:
                        if mp3s:
                            st.audio(mp3s[0])
                            st.caption(f"Archivo: {os.path.basename(mp3s[0])}")
                        else:
                            st.warning("Carpeta vacía o sin MP3.")
                        
                        # Social Pack Result Display
                        if f'social_result_{p_dir}' in st.session_state:
                            st.markdown("### 📱 Social Pack Generado")
                            social_data = st.session_state[f'social_result_{p_dir}']
                            
                            subtab1, subtab2 = st.tabs(["Facebook", "Instagram"])
                            with subtab1:
                                st.text_area("Post Facebook", value=social_data.get('facebook_post', ''), height=250, key=f"fb_area_{p_dir}")
                            with subtab2:
                                st.text_area("Caption Instagram", value=social_data.get('instagram_caption', ''), height=250, key=f"ig_area_{p_dir}")
                            
                            if st.button("❌ Cerrar Pack", key=f"close_sp_{p_dir}"):
                                del st.session_state[f'social_result_{p_dir}']
                                st.rerun()

                    with col_actions:
                        if mp3s:
                            with open(mp3s[0], "rb") as f:
                                st.download_button(
                                    label="⬇️ MP3",
                                    data=f,
                                    file_name=os.path.basename(mp3s[0]),
                                    key=f"dl_mp3_{p_dir}",
                                    use_container_width=True
                                )
                        
                        if htmls:
                            with open(htmls[0], "rb") as f:
                                st.download_button(
                                    label="📄 HTML",
                                    data=f,
                                    file_name=os.path.basename(htmls[0]),
                                    mime="text/html",
                                    key=f"dl_html_{p_dir}",
                                    use_container_width=True
                                )
                        
                        # Botón Social Pack
                        if os.path.exists(json_path):
                            if st.button("📱 Social Pack", key=f"btn_sp_{p_dir}", use_container_width=True):
                                with st.spinner("Generando contenidos con IA..."):
                                    try:
                                        with open(json_path, 'r', encoding='utf-8') as f:
                                            transcript = json.load(f)
                                        
                                        # Combinar texto de noticias
                                        full_text = "\n".join([item['content'] for item in transcript if item.get('type') in ['block', 'news', 'intro']])
                                        
                                        # Generar con IA
                                        prompt = PromptsCreativos.generar_social_pack(full_text)
                                        resp_json = generar_texto_con_gemini(prompt)
                                        
                                        # Limpiar y parsear
                                        clean_json = resp_json.replace("```json", "").replace("```", "").strip()
                                        social_dict = json.loads(clean_json)
                                        
                                        st.session_state[f'social_result_{p_dir}'] = social_dict
                                        st.rerun()
                                        
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        
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

    st.markdown("---")
    st.markdown('<div class="sub-header">🎭 Historial de Episodios Especiales</div>', unsafe_allow_html=True)
    
    try:
        ee_files = sorted(glob.glob("EE_*.mp3"), key=os.path.getctime, reverse=True)
        
        if not ee_files:
            st.info("No hay episodios especiales generados.")
        else:
            for ee_file in ee_files:
                # Nombre limpio
                display_name_ee = os.path.basename(ee_file)
                
                with st.expander(f"📢 {display_name_ee}", expanded=False):
                    col_ee_info, col_ee_actions = st.columns([3, 1])
                    
                    with col_ee_info:
                        st.audio(ee_file)
                        st.caption(f"Archivo: {display_name_ee}")
                        
                    with col_ee_actions:
                         with open(ee_file, "rb") as f:
                                st.download_button(
                                    label="⬇️ MP3",
                                    data=f,
                                    file_name=display_name_ee,
                                    key=f"dl_ee_{ee_file}",
                                    use_container_width=True
                                )
                         
                         if st.button("🗑️ Eliminar", key=f"del_ee_{ee_file}", type="secondary", use_container_width=True):
                            try:
                                os.remove(ee_file)
                                # Buscar si existe también el .txt.processed y borrarlo para limpiar
                                txt_processed = ee_file.split("_1")[0] + ".txt.processed" # Aproximacion simple, mejor regex si fuera critico
                                # Intentamos buscar el original basado en nombre
                                # EE_nombre_timestamp.mp3 -> EE_nombre.txt.processed
                                # Esto es dificil deducir exacto sin timestamp. Borramos solo mp3 por seguridad.
                                
                                st.toast(f"Eliminado: {display_name_ee}")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error eliminando: {e}")
    except Exception as e:
        st.error(f"Error leyendo especiales: {e}")

with tab7:
    st.markdown('<div class="sub-header">Informe de Actividad de Fuentes</div>', unsafe_allow_html=True)
    st.markdown("Monitoriza la salud de tus fuentes RSS con métricas de actividad en tiempo real.")
    
    
    col_analizar, col_espacio = st.columns([1,3])
    with col_analizar:
        btn_check_feeds = st.button("🔄 Analizar Estado de Feeds", type="primary", use_container_width=True)

    # Lógica de carga: Botón O Caché existe
    should_load = btn_check_feeds or ('fuentes_analytics_df' in st.session_state and st.session_state['fuentes_analytics_df'] is not None)

    if should_load:
        # Si fue por botón, o si no hay caché (aunque la lógica de should_load ya cubre parte, forzamos recarga si es botón)
        if btn_check_feeds:
            with st.spinner("Conectando con servidores RSS y calculando estadísticas..."):
                base_dir = os.path.dirname(os.path.abspath(__file__))
                feeds_path = os.path.join(base_dir, 'feeds.txt')
                if os.path.exists(feeds_path):
                    try:
                        df = analizar_frecuencia_fuentes(feeds_path)
                        st.session_state['fuentes_analytics_df'] = df
                    except Exception as e:
                        st.error(f"Error al analizar fuentes: {e}")
                        df = None
                else:
                    st.error("No se encuentra el archivo feeds.txt")
                    df = None
        else:
            # Recuperar de caché
            df = st.session_state['fuentes_analytics_df']

        # Renderizar si tenemos datos
        if df is not None:
            try:
                # Métricas Globales
                total_fuentes = len(df)
                fuentes_activas = len(df[df['Estado'].isin(["🟢 Muy Activo", "🟡 Activo"])])
                
                m1, m2 = st.columns(2)
                m1.metric("Total Fuentes", total_fuentes)
                m2.metric("Fuentes Activas (30d)", fuentes_activas, delta=f"{round(fuentes_activas/total_fuentes*100)}%")
                
                st.dataframe(
                    df, 
                    column_config={
                        "Estado": st.column_config.TextColumn("Salud"),
                        "24h": st.column_config.NumberColumn("Hoy", format="%d"),
                        "7d": st.column_config.NumberColumn("7 Días", format="%d"),
                        "30d": st.column_config.NumberColumn("30 Días", format="%d"),
                        "1 año": st.column_config.NumberColumn("Año", format="%d"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
            except Exception as e:
                 st.error(f"Error renderizando tabla: {e}")

        # === GENERACIÓN DE EPISODIO ESPECIAL DE ANÁLISIS ===
        st.markdown("---")
        st.markdown("### 🎙️ Episodio Especial: Informe Semanal")
        st.info("Genera un guion humorístico analizando quién ha trabajado más y quién menos esta semana.")
        
        if st.button("📝 Redactar Guion de Agradecimiento (Semanal)", type="primary"):
            if df is not None and not df.empty:
                with st.spinner("Analizando datos y redactando con gracia..."):
                    try:
                        # 1. Preparar datos (Enfasis en '7d' como pidió el usuario)
                        # Ordenar por 7 días
                        df_sorted = df.sort_values(by="7d", ascending=False)
                        
                        top_3 = df_sorted.head(3)
                        bottom_3 = df_sorted[df_sorted['7d'] == 0].head(3) # Los que tienen 0 esta semana
                        if bottom_3.empty:
                             bottom_3 = df_sorted.tail(3) # Si todos tienen algo, los ultimos
                        
                        # Construir string de análisis y EXTRAER INFO REAL
                        analisis_str = "TOP 3 FUENTES MÁS ACTIVAS (ÚLTIMA SEMANA):\n"
                        
                        import feedparser # Aseguramos import aquí o arriba
                        
                        # Buscamos la URL original en el archivo feeds.txt para poder parsearlo
                        # El DF solo tiene el Nombre (Titulo). Es un poco ineficiente pero necesario si el DF no guarda la URL.
                        # Mejor si src.analytics devolviera tambien la URL.
                        # ASUMIMOS QUE df TIENE NOMBRE PERO NO URL. 
                        # VAMOS A LEER FEEDS.TXT Y MAPEAR RAPIDO.
                        base_dir = os.path.dirname(os.path.abspath(__file__))
                        feeds_filepath_local = os.path.join(base_dir, 'feeds.txt')
                        mapa_nombre_url = {}
                        if os.path.exists(feeds_filepath_local):
                            with open(feeds_filepath_local, 'r') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and not line.startswith('#'):
                                         # Parseamos ligero para sacar titulo y mapear
                                         try:
                                             fd = feedparser.parse(line)
                                             tit = fd.feed.get('title', line) # Aproximacion
                                             # Normalizar titulos seria ideal
                                             # Para simplificar, iteramos sobre los top3 y buscamos match 'parecido' o usamos lo que src.analytics haya usado.
                                             # src.analytics devuelve el título del feed.
                                         except: pass
                        
                        # ESTRATEGIA: src.analytics NO devuelve URL. Es un fallo de diseño previo, pero work around:
                        # Re-instanciar src.analytics.analizar_frecuencia_fuentes devuelve DF.
                        # Modificaremos src.analytics es mejor opcion? NO, usuario pidio tocar app.py y dorototal.
                        # Haremos un best-effort re-leyendo feeds.txt y buscando coincidencias.
                        
                        # O MEJOR: modificar src.analytics rapido para incluir URL oculta? No, keep simple.
                        # Vamos a iterar feeds.txt y si el titulo coincide con uno del Top 3, sacamos noticias.
                        
                        urls_top_3 = []
                        nombres_top_3 = top_3['Fuente'].tolist()
                        
                        if os.path.exists(feeds_filepath_local):
                             with open(feeds_filepath_local, 'r') as f:
                                urls_candidatas = [l.strip() for l in f if l.strip() and not l.startswith('#')]
                                
                             for url in urls_candidatas:
                                 try:
                                     fd = feedparser.parse(url)
                                     tit = fd.feed.get('title', url)
                                     # Comprobamos si este titulo esta en nuestro top 3
                                     # OJO: src.analytics hace encoding fix. Hacemos igual?
                                     # Simplemente si contain o exact match.
                                     
                                     for nombre_top in nombres_top_3:
                                         if nombre_top in tit or tit in nombre_top: # Aproximación laxa
                                             # Es uno de los top!
                                             # Sacamos 1 noticia reciente
                                             if fd.entries:
                                                 entry = fd.entries[0]
                                                 tit_noticia = entry.get('title', 'Sin titulo')
                                                 analisis_str += f"- {nombre_top}: {row['7d']} noticias. Destacada: '{tit_noticia}'\n"
                                                 # Lo sacamos de la lista para no repetir
                                                 nombres_top_3.remove(nombre_top)
                                                 break 
                                 except: pass
                        
                        # Si quedó alguno sin matchear (por encoding o lo que sea), lo ponemos simple
                        for nombre_restante in nombres_top_3:
                             row_data = top_3[top_3['Fuente'] == nombre_restante].iloc[0]
                             analisis_str += f"- {nombre_restante}: {row_data['7d']} noticias.\n"
                        
                        # CALCULO DE ESTADISTICAS GLOBALES (BINS)
                        count_hyper = len(df_sorted[df_sorted['7d'] > 10])
                        count_high = len(df_sorted[(df_sorted['7d'] >= 5) & (df_sorted['7d'] <= 10)])
                        count_mod = len(df_sorted[(df_sorted['7d'] >= 1) & (df_sorted['7d'] < 5)])
                        count_zero = len(df_sorted[df_sorted['7d'] == 0])
                        
                        analisis_str += "\nRESUMEN GLOBAL DE ACTIVIDAD (SEMÁFORO):\n"
                        analisis_str += f"- Muy Activos (>10 noticias): {count_hyper} fuentes.\n"
                        analisis_str += f"- Activos (5-10 noticias): {count_high} fuentes.\n"
                        analisis_str += f"- Tranquilos (1-4 noticias): {count_mod} fuentes.\n"
                        analisis_str += f"- Inactivos (0 noticias): {count_zero} fuentes.\n"

                        analisis_str += "\nFUENTES MENOS ACTIVAS (ÚLTIMA SEMANA):\n"
                        for _, row in bottom_3.iterrows():
                            analisis_str += f"- {row['Fuente']}: {row['7d']} noticias.\n"
                            
                        # 2. Llamar a la IA
                        prompt = PromptsCreativos.generar_analisis_fuentes(analisis_str)
                        guion_generado = generar_texto_con_gemini(prompt)
                        
                        # 3. Limpiar y Guardar
                        clean_script = guion_generado.replace("```txt", "").replace("```", "").strip()
                        
                        timestamp_str = datetime.now().strftime("%d-%m-%y_%H-%M")
                        filename = f"EE_analisis_semanal - {timestamp_str}.txt"
                        
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(clean_script)
                            
                        st.success(f"✅ ¡Guion generado con éxito! ({filename})")
                        st.balloons()
                        st.write("Puedes revisarlo en la pestaña de 'Episodios Especiales' (automático) o abrirlo aquí:")
                        st.text_area("Previsualización:", value=clean_script, height=300)
                        
                    except Exception as e:
                        st.error(f"Error generando guion: {e}")
            else:
                st.warning("Primero debes analizar el estado de los feeds (botón arriba).")




# Footer
st.markdown("---")
st.markdown("Desarrollado por Podcast control center | v1.0")
