
import streamlit as st
import sys
import os
import json
import datetime
import glob
from src.utils.ui_common import inject_pcc_style, cargar_config, init_session_state

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Podcast Control Center",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_pcc_style()
init_session_state()
config = cargar_config()

# ─────────────────────────────────────────────
#  SIDEBAR (Branding only, navigation is native)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;padding:8px 0 24px;">
        <span style="font-size:1.4rem;">🎙️</span>
        <span style="font-size:1.1rem;font-weight:700;color:#1b5f00;">PCC</span>
        <span style="font-size:0.7rem;color:#6b6b6b;margin-left:auto;">v1.0-MOD</span>
    </div>
    """, unsafe_allow_html=True)
    st.info("💡 Navega usando el menú superior para configurar o generar tu podcast.")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("Micomicona Podcast System")

# ─────────────────────────────────────────────
#  DASHBOARD (PÁGINA PRINCIPAL)
# ─────────────────────────────────────────────
st.markdown('<div class="pcc-page-title">🏠 Dashboard Principal</div>', unsafe_allow_html=True)
st.markdown("### Bienvenido al Centro de Control de Dorotea")

# Status cards
voz_activa = config.get('audio_config', {}).get('voice_name', '—')
feeds_file = config.get('generation_config', {}).get('feeds_file', 'feeds.txt')
n_feeds = 0
if os.path.exists(feeds_file):
    with open(feeds_file) as f:
        n_feeds = sum(1 for l in f if l.strip() and not l.startswith('#'))

podcast_dirs = sorted([d for d in glob.glob("podcast_apg_*") if os.path.isdir(d)], key=os.path.getctime, reverse=True)
ultimo_podcast = "—"
if podcast_dirs:
    mtime = os.path.getmtime(podcast_dirs[0])
    delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(mtime)
    h = int(delta.total_seconds() // 3600)
    ultimo_podcast = f"Hace {h}h" if h < 48 else f"Hace {delta.days}d"

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="pcc-card"><div class="pcc-card-title">Último podcast</div><div class="pcc-card-value">{ultimo_podcast}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="pcc-card"><div class="pcc-card-title">Fuentes activas</div><div class="pcc-card-value">{n_feeds}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="pcc-card"><div class="pcc-card-title">Locutora</div><div class="pcc-card-value">{voz_activa.split(" [")[0] if "[" in voz_activa else voz_activa}</div></div>', unsafe_allow_html=True)

st.divider()

col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("#### 🚀 Acciones Rápidas")
    st.info("Utiliza el menú lateral para acceder a las herramientas:")
    st.markdown("""
    - **🎙️ Generador**: Inicia el flujo de 3 pasos para crear el episodio de hoy.
    - **📚 Mediateca**: Descarga o comparte episodios anteriores.
    - **⚙️ Configuración**: Ajusta la voz, el calendario de tradiciones o las fuentes RSS.
    """)

with col_right:
    st.markdown("#### 📜 Último Registro")
    try:
        lf = "logs/process_log.jsonl"
        if os.path.exists(lf):
            lines = open(lf).readlines()
            last_lines = lines[-5:]
            for l in last_lines:
                e = json.loads(l)
                st.caption(f"{e['timestamp'].split('T')[1][:5]} | {e['message']}")
    except:
        st.write("Sin logs recientes.")

st.markdown("---")
st.markdown('<span style="font-size:0.75rem;color:#6b6b6b;">Podcast Control Center Modular v1.0</span>', unsafe_allow_html=True)
