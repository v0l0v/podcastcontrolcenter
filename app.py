
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

# Cargar estadísticas de consumo
from src.monitoring import UsageTracker
import pandas as pd
import random

tracker_usage = UsageTracker()
stats = tracker_usage.get_summary()

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

# ── SECCIÓN DE CONTROL DE CONSUMO ──
st.markdown('<div class="pcc-section-title">📊 Control de Consumo de IA y TTS</div>', unsafe_allow_html=True)

col_cons1, col_cons2 = st.columns([1, 1])

with col_cons1:
    st.markdown('<div class="pcc-card" style="height: 100%;">', unsafe_allow_html=True)
    st.markdown('<div class="pcc-card-title">Límite de Google TTS Mensual (Gratuito)</div>', unsafe_allow_html=True)
    
    tts_chars = stats.get("tts_chars", 0)
    tts_limit = 1_000_000  # Límite gratuito de 1M para Neural2/Wavenet
    tts_restante = max(0, tts_limit - tts_chars)
    tts_pct = min(100.0, (tts_chars / tts_limit) * 100.0)
    
    # Barra de progreso estilizada
    st.progress(tts_pct / 100.0)
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; font-size: 0.82rem; margin-top: 4px; color: var(--muted);'>
        <span>{tts_chars:,} caracteres usados</span>
        <span>{tts_pct:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    # Métricas secundarias
    mc1, mc2 = st.columns(2)
    with mc1:
        st.markdown(f"""
        <div style='text-align: center; border-right: 1px solid var(--border);'>
            <div style='font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em;'>Gratis Restantes</div>
            <div style='font-size: 1.25rem; font-weight: 700; color: #D4AF37; font-family: "Cinzel", serif; margin-top: 4px;'>{tts_restante:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with mc2:
        edge_chars = stats.get("tts_edge_chars", 0)
        st.markdown(f"""
        <div style='text-align: center;'>
            <div style='font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em;'>Ahorrados (Edge)</div>
            <div style='font-size: 1.25rem; font-weight: 700; color: #8fa090; font-family: "Cinzel", serif; margin-top: 4px;'>{edge_chars:,}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_cons2:
    st.markdown('<div class="pcc-card" style="height: 100%;">', unsafe_allow_html=True)
    st.markdown('<div class="pcc-card-title">Consumo de Tokens por Día (Gemini 2.5)</div>', unsafe_allow_html=True)
    
    # Cargar y formatear el DataFrame de uso diario
    daily_usage = stats.get("daily_usage", {})
    if daily_usage:
        df_data = []
        for day, metrics in daily_usage.items():
            df_data.append({
                "Fecha": day,
                "Tokens": metrics.get("tokens", 0)
            })
        df = pd.DataFrame(df_data).sort_values("Fecha")
        st.caption("📈 *Consumo real por día.*")
    else:
        # Datos simulados de demostración si el histórico está vacío
        hoy = datetime.date.today()
        df_data = []
        for i in range(6, -1, -1):
            dia = (hoy - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            # Un generador determinista para consistencia visual
            state_seed = sum(ord(c) for c in dia)
            random.seed(state_seed)
            df_data.append({
                "Fecha": dia,
                "Tokens": random.randint(1800, 9500)
            })
        df = pd.DataFrame(df_data)
        st.caption("ℹ️ *Mostrando consumo de prueba (sin consumos reales aún).*")
        
    st.bar_chart(df.set_index("Fecha")["Tokens"])
    st.markdown('</div>', unsafe_allow_html=True)

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
