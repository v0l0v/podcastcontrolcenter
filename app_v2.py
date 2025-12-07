import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
from src.utils import cargar_configuracion, guardar_configuracion
from src.news_engine import procesar_feeds
from src.audio_engine import generar_tts
import subprocess

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Micomicona Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS (DARK PREMIUM) ---
st.markdown("""
<style>
    /* Importar fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Variables de color */
    :root {
        --bg-color: #0e1117;
        --card-bg: #1a1c24;
        --accent-color: #ff4b4b;
        --text-primary: #ffffff;
        --text-secondary: #a0a0a0;
    }

    /* General */
    .stApp {
        background-color: var(--bg-color);
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 {
        color: var(--text-primary) !important;
        font-weight: 800 !important;
    }

    /* Tarjetas de Noticias */
    .news-card {
        background-color: var(--card-bg);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        border: 1px solid #333;
        transition: transform 0.2s;
    }
    .news-card:hover {
        border-color: var(--accent-color);
        transform: translateY(-2px);
    }
    .news-source {
        color: var(--accent-color);
        font-size: 0.8em;
        text-transform: uppercase;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .news-title {
        font-size: 1.1em;
        font-weight: 600;
        margin-bottom: 10px;
        color: #fff;
    }
    .news-summary {
        color: var(--text-secondary);
        font-size: 0.95em;
        line-height: 1.5;
    }

    /* Botones */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        opacity: 0.9;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111;
        border-right: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if 'noticias_procesadas' not in st.session_state:
    st.session_state.noticias_procesadas = []
if 'noticias_seleccionadas' not in st.session_state:
    st.session_state.noticias_seleccionadas = set()

# --- FUNCIONES UI ---

from src.analytics import analizar_frecuencia_fuentes

def render_dashboard():
    st.title("🎙️ Micomicona Studio")
    st.markdown("### Panel de Control")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Noticias en Caché", len(st.session_state.noticias_procesadas) if st.session_state.noticias_procesadas else "0")
    with col2:
        st.metric("Seleccionadas para Podcast", len(st.session_state.noticias_seleccionadas))
    with col3:
        st.metric("Estado del Sistema", "🟢 Listo")

    st.markdown("---")
    
    with st.expander("📊 Informe de Actividad de Fuentes", expanded=False):
        st.markdown("Analiza cuántas noticias ha publicado cada fuente recientemente.")
        if st.button("Generar Informe de Fuentes"):
            with st.spinner("Analizando historial de RSS..."):
                base_dir = os.path.dirname(os.path.abspath(__file__))
                feeds_path = os.path.join(base_dir, 'feeds.txt')
                if os.path.exists(feeds_path):
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
                else:
                    st.error("No se encuentra feeds.txt")

    st.markdown("---")
    st.info("👈 Usa el menú lateral para navegar entre las fases de producción.")

def render_curacion():
    st.title("📰 Curación de Contenido")
    st.markdown("Escanea feeds, revisa las noticias y selecciona las que formarán parte del episodio de hoy.")
    
    col_acc, col_filt = st.columns([1, 3])
    with col_acc:
        col_num, col_dias = st.columns(2)
        with col_num:
            num_noticias = st.number_input("Cantidad", min_value=5, max_value=50, value=20, step=5)
        with col_dias:
            dias_atras = st.number_input("Días atrás", min_value=1, max_value=30, value=7, step=1)
            
        if st.button("🔄 Escanear Feeds Ahora", type="primary"):
            try:
                with st.spinner(f"Buscando {num_noticias} noticias de los últimos {dias_atras} días..."):
                    # Usar ruta absoluta para feeds.txt
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    feeds_path = os.path.join(base_dir, 'feeds.txt')
                    
                    if not os.path.exists(feeds_path):
                        st.error(f"No se encuentra el archivo de feeds en: {feeds_path}")
                    else:
                        noticias = procesar_feeds(feeds_path, dias_atras=dias_atras, min_items=num_noticias)
                        st.session_state.noticias_procesadas = noticias
                        # Por defecto seleccionar todas las nuevas
                        st.session_state.noticias_seleccionadas = {n['id'] for n in noticias}
                        
                        if len(noticias) < num_noticias:
                            st.warning(f"Solo se encontraron {len(noticias)} noticias en este rango de fechas.")
                        else:
                            st.success(f"¡{len(noticias)} noticias encontradas!")
                        st.rerun()
            except Exception as e:
                st.error(f"Error al procesar feeds: {e}")

        if st.button("🗑️ Limpiar Caché"):
            if os.path.exists('cache_noticias.json'):
                os.remove('cache_noticias.json')
                st.session_state.noticias_procesadas = []
                st.session_state.noticias_seleccionadas = set()
                st.toast("Caché eliminada. Vuelve a escanear.")
                st.rerun()
            
    with col_filt:
        st.text_input("🔍 Filtrar noticias...", placeholder="Escribe para buscar...")

    st.markdown("### Noticias Disponibles")
    
    if not st.session_state.noticias_procesadas:
        st.info("👆 Pulsa 'Escanear Feeds Ahora' para cargar las noticias del día.")
        return

    # Lista de noticias con checkboxes
    for noticia in st.session_state.noticias_procesadas:
        n_id = noticia['id']
        is_selected = n_id in st.session_state.noticias_seleccionadas
        
        # Contenedor visual tipo tarjeta
        cols = st.columns([0.1, 0.9])
        with cols[0]:
            # Checkbox grande
            nuevo_estado = st.checkbox("", value=is_selected, key=f"chk_{n_id}")
            if nuevo_estado != is_selected:
                if nuevo_estado:
                    st.session_state.noticias_seleccionadas.add(n_id)
                else:
                    st.session_state.noticias_seleccionadas.discard(n_id)
                st.rerun()
                
        with cols[1]:
            with st.container():
                resumen_texto = noticia.get('resumen', '') or "⚠️ No se pudo generar resumen."
                border_color = '#00ff00' if is_selected else '#333'
                
                st.markdown(f"""
                <div class="news-card" style="border-left: 4px solid {border_color};">
                    <div class="news-source">{noticia['fuente']} • {noticia['fecha']}</div>
                    <div class="news-title">{resumen_texto[:80]}...</div>
                    <div class="news-summary">{resumen_texto}</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("✏️ Editar Resumen"):
                    nuevo_resumen = st.text_area("Texto para locución", value=resumen_texto, key=f"txt_{n_id}")
                    if nuevo_resumen != noticia['resumen']:
                        noticia['resumen'] = nuevo_resumen
                        st.toast("Resumen actualizado")

def render_produccion():
    st.title("🎧 Producción y Generación")
    
    num_sel = len(st.session_state.noticias_seleccionadas)
    if num_sel == 0:
        st.error("⚠️ No has seleccionado ninguna noticia. Ve a la pestaña 'Curación' primero.")
        return
        
    st.success(f"✅ {num_sel} noticias listas para producción.")
    
    st.markdown("### Configuración del Episodio")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Título del Episodio", value=f"Noticias del {datetime.now().strftime('%d/%m/%Y')}")
    with col2:
        st.selectbox("Voz de la Presentadora", ["Dorotea (Journey)", "Dorotea (Neural)"])
        
    st.markdown("---")
    
    if st.button("🚀 GENERAR PODCAST FINAL", type="primary", use_container_width=True):
        st.balloons()
        with st.status("Generando episodio...", expanded=True) as status:
            st.write("📝 Organizando bloques temáticos...")
            # Aquí llamaremos a dorototal_v2.py o sus funciones
            # Por ahora simulamos el proceso
            import time
            time.sleep(1)
            st.write("🎤 Generando locuciones con IA...")
            time.sleep(1)
            st.write("🎛️ Mezclando música y efectos...")
            time.sleep(1)
            status.update(label="¡Podcast completado!", state="complete", expanded=False)
            
        st.success("Podcast generado correctamente.")
        st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3") # Placeholder

def main():
    with st.sidebar:
        st.image("assets/logo_ache.png", use_container_width=True)
        st.markdown("---")
        menu = st.radio("Navegación", ["Dashboard", "Curación de Noticias", "Producción", "Biblioteca"])
        st.markdown("---")
        st.caption("v2.0.0 (Beta)")

    if menu == "Dashboard":
        render_dashboard()
    elif menu == "Curación de Noticias":
        render_curacion()
    elif menu == "Producción":
        render_produccion()
    elif menu == "Biblioteca":
        st.title("📚 Biblioteca")
        st.info("Historial de podcasts generados (Próximamente)")

if __name__ == "__main__":
    main()
