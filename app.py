import streamlit as st
import sys
import json
import os
from dotenv import load_dotenv
load_dotenv()
import subprocess
import threading
import time
import shutil
import datetime
import random
import glob

import pandas as pd
from src.analytics import analizar_frecuencia_fuentes
from src.llm_utils import generar_texto_con_gemini, generar_texto_multimodal_audio_con_gemini
from src.engine.audio import sintetizar_ssml_a_audio, masterizar_a_lufs
from pydub import AudioSegment
from mcmcn_prompts import PromptsCreativos

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Podcast Control Center",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
#  PALETA Y CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --g-dark:    #1b5f00;
    --g-mid:     #cef89c;
    --g-light:   #e5fabd;
    --bg:        #e5fabd;
    --surface:   #cef89c;
    --border:    #cef89c;
    --text:      #1a1a1a;
    --muted:     #6b6b6b;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: var(--text);
    background-color: var(--bg);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--surface);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.95rem;
    padding: 6px 0;
    cursor: pointer;
    color: var(--muted);
}
[data-testid="stSidebar"] .stRadio label:hover {
    color: var(--g-dark);
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.875rem;
    border: 1px solid var(--border);
    transition: all 0.15s ease;
}
.stButton > button[kind="primary"] {
    background-color: var(--g-dark) !important;
    color: #fff !important;
    border-color: var(--g-dark) !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #164d00 !important;
    box-shadow: 0 2px 6px rgba(27,95,0,0.3);
}
.stButton > button:not([kind="primary"]):hover {
    border-color: var(--g-dark);
    color: var(--g-dark);
}

/* ── Cards ── */
.pcc-card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.pcc-card-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    margin-bottom: 4px;
}
.pcc-card-value {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
}

/* ── Step blocks ── */
.pcc-step {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 16px;
    background: var(--bg);
}
.pcc-step-active {
    border-color: var(--g-dark);
    background: var(--g-light);
    border-left: 4px solid var(--g-dark);
}
.pcc-step-label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin-bottom: 4px;
}
.pcc-step-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 12px;
}

/* ── Page title ── */
.pcc-page-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 24px;
}
.pcc-section-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
    margin: 20px 0 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
}

/* ── Dividers & misc ── */
hr { border-color: var(--border); }
.stAlert { border-radius: 6px; }
.stExpander { border: 1px solid var(--border) !important; border-radius: 6px !important; }
/* Remove default tab underline mess */
button[data-baseweb="tab"] { border-radius: 4px; font-size: 0.85rem; }
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: var(--g-light) !important;
    color: var(--g-dark) !important;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CONFIG HELPERS
# ─────────────────────────────────────────────
CONFIG_FILE = 'podcast_config.json'

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

config = cargar_config()

# ─────────────────────────────────────────────
#  SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;padding:8px 0 24px;">
        <span style="font-size:1.4rem;">🎙️</span>
        <span style="font-size:1.1rem;font-weight:700;color:#1b5f00;">PCC</span>
        <span style="font-size:0.7rem;color:#6b6b6b;margin-left:auto;">v0.97</span>
    </div>
    """, unsafe_allow_html=True)

    pages = {
        "🏠  Inicio": "inicio",
        "🎙️  Generar": "generar",
        "📚  Mediateca": "mediateca",
        "⚙️  Configuración": "config",
        "🧠  Cerebro": "cerebro",
        "🛠️  Extras": "extras",
    }
    page_label = st.radio("", list(pages.keys()), label_visibility="collapsed")
    page = pages[page_label]

    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("Podcast Control Center")

# ─────────────────────────────────────────────
#  SESSION STATE DEFAULTS
# ─────────────────────────────────────────────
for key, val in {
    'config_check': False,
    'news_confirmed': False,
    'window_hours_override': None,
    'noticias_editadas_finales': [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ═══════════════════════════════════════════════════════════════
#  PÁGINA: INICIO
# ═══════════════════════════════════════════════════════════════
if page == "inicio":
    st.markdown('<div class="pcc-page-title">🏠 Inicio</div>', unsafe_allow_html=True)

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
    for col, title, value in [
        (c1, "Último podcast", ultimo_podcast),
        (c2, "Fuentes configuradas", str(n_feeds)),
        (c3, "Voz activa", voz_activa.split(" [")[0] if "[" in voz_activa else voz_activa),
    ]:
        col.markdown(f"""
        <div class="pcc-card">
            <div class="pcc-card-title">{title}</div>
            <div class="pcc-card-value">{value}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="pcc-section-title">🎧 Último Podcast</div>', unsafe_allow_html=True)
    if podcast_dirs:
        latest_dir = podcast_dirs[0]
        mp3s = glob.glob(os.path.join(latest_dir, "*.mp3"))
        if mp3s:
            st.success(f"📁 {latest_dir}")
            st.audio(mp3s[0])
        else:
            st.warning(f"Carpeta {latest_dir} sin MP3.")
    else:
        st.info("No hay podcasts generados aún.")


# ═══════════════════════════════════════════════════════════════
#  PÁGINA: GENERAR
# ═══════════════════════════════════════════════════════════════
elif page == "generar":
    st.markdown('<div class="pcc-page-title">🎙️ Generar Podcast</div>', unsafe_allow_html=True)

    # ── Modo de operación ──
    mode_options = ["Completo (Podcast + Especiales)", "Solo Podcast (Sin Especiales)", "Solo Episodios Especiales"]
    selected_mode_label = st.radio("Modo de operación:", mode_options, horizontal=True, key="gen_mode_selector")
    mode_only_special = "Solo Episodios Especiales" in selected_mode_label
    mode_skip_special = "Sin Especiales" in selected_mode_label

    st.markdown("---")

    # ────────────────────────────────
    #  MODO: SOLO ESPECIALES
    # ────────────────────────────────
    if mode_only_special:
        st.info("ℹ️ Selecciona los guiones especiales (EE_*.txt) que deseas procesar.")
        ee_scripts = sorted(glob.glob("EE_*.txt"))
        selected_scripts = []
        if not ee_scripts:
            st.warning("No se han encontrado guiones (EE_*.txt).")
        else:
            for script in ee_scripts:
                col_sel, col_del = st.columns([4, 1])
                with col_sel:
                    if st.checkbox(script, value=True, key=f"sel_{script}"):
                        selected_scripts.append(script)
                with col_del:
                    if st.button("🗑️", key=f"del_script_{script}"):
                        os.remove(script)
                        st.rerun()
            st.divider()
            if st.button("🚀 GENERAR SELECCIONADOS", type="primary", disabled=len(selected_scripts) == 0):
                with st.spinner("Procesando episodios..."):
                    cmd = [sys.executable, "dorototal.py", "--only-special", "--file-list"] + selected_scripts
                    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                    if proc.returncode == 0:
                        st.success("✅ Proceso completado.")
                        st.code(proc.stdout)
                        time.sleep(2); st.rerun()
                    else:
                        st.error("Error en el proceso.")
                        st.code(proc.stderr)

    # ────────────────────────────────
    #  FLUJO NORMAL (3 pasos)
    # ────────────────────────────────
    else:
        # ── PASO 1: ANALIZAR ──
        step1_active = True
        st.markdown('<div class="pcc-step pcc-step-active">', unsafe_allow_html=True)
        st.markdown('<div class="pcc-step-label">Paso 1</div>', unsafe_allow_html=True)
        st.markdown('<div class="pcc-step-title">Analizar Noticias</div>', unsafe_allow_html=True)

        # Ventana temporal
        window_mode = st.radio(
            "Ventana temporal:",
            ["🌅 Solo hoy (desde medianoche)", "⏱️ Últimas X horas", "💾 Config guardada"],
            horizontal=True,
            key="window_mode_selector_v2"
        )
        if "Solo hoy" in window_mode:
            _ahora = datetime.datetime.now()
            horas_hoy = max(1, round(_ahora.hour + _ahora.minute / 60))
            st.caption(f"🌅 Son las {_ahora.strftime('%H:%M')} → se usarán las últimas **{horas_hoy} horas**")
            st.session_state['window_hours_override'] = horas_hoy
        elif "X horas" in window_mode:
            _saved = int(config.get('generation_config', {}).get('news_window_hours', 48))
            wh = st.slider("Horas", 6, 168, _saved, 6)
            st.session_state['window_hours_override'] = wh
        else:
            _saved = int(config.get('generation_config', {}).get('news_window_hours', 48))
            st.caption(f"Valor guardado: **{_saved} horas**")
            st.session_state['window_hours_override'] = None

        config_checked = st.checkbox("He revisado la configuración", value=st.session_state['config_check'], key='chk_config_v2')
        st.session_state['config_check'] = config_checked

        if st.button("🔎 ANALIZAR NOTICIAS", type="primary", disabled=not config_checked):
            with st.spinner("Analizando feeds y resumiendo con IA..."):
                for f in ["prevision_noticias_resumidas.json", "seleccion_usuario.json"]:
                    if os.path.exists(f): os.remove(f)
                st.session_state['news_confirmed'] = False
                _wo = st.session_state.get('window_hours_override')
                _cmd = [sys.executable, "dorototal.py", "--preview"]
                if _wo: _cmd += ["--window-hours", str(_wo)]
                
                # Use Popen to stream logs in real-time so user knows it's not hanging
                log_placeholder = st.empty()
                logs_list = []
                proc = subprocess.Popen(_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=os.getcwd())
                
                while True:
                    line = proc.stdout.readline()
                    if line == '' and proc.poll() is not None:
                        break
                    if line:
                        logs_list.append(line.strip())
                        # Mantener solo las ultimas 15 lineas de log
                        log_placeholder.code("\n".join(logs_list[-15:]), language="text")
                        
                if proc.poll() == 0 and os.path.exists("prevision_noticias_resumidas.json"):
                    st.success("✅ Análisis completado. Revisa las noticias en el Paso 2.")
                    time.sleep(1); st.rerun()
                elif proc.poll() == 0:
                    st.warning("⚠️ No se encontraron noticias con los filtros actuales.")
                else:
                    st.error(f"Error: {proc.stderr.read()}")
        st.markdown('</div>', unsafe_allow_html=True)

        # ── PASO 2: REVISAR ──
        has_preview = os.path.exists("prevision_noticias_resumidas.json")
        step2_cls = "pcc-step pcc-step-active" if has_preview else "pcc-step"
        st.markdown(f'<div class="{step2_cls}">', unsafe_allow_html=True)
        st.markdown('<div class="pcc-step-label">Paso 2</div>', unsafe_allow_html=True)
        st.markdown('<div class="pcc-step-title">Revisar y Editar</div>', unsafe_allow_html=True)

        if not has_preview:
            st.caption("Pendiente de análisis.")
        else:
            try:
                with open("prevision_noticias_resumidas.json", "r", encoding="utf-8") as f:
                    news_candidates = json.load(f)
                st.info(f"{len(news_candidates)} noticias disponibles para revisar.")

                with st.form("form_edicion_v2"):
                    edited_list = []
                    for i, news in enumerate(news_candidates):
                        titulo_raw = news.get("titulo", "")
                        sitio = news.get("sitio", "")
                        titulo_show = titulo_raw if (titulo_raw and titulo_raw != "None" and len(titulo_raw) > 3) else f"Noticia de {sitio}"
                        resumen_raw = news.get("resumen", "")
                        with st.expander(f"{i+1}. {titulo_show}", expanded=(i == 0)):
                            col_chk, col_cnt = st.columns([0.08, 0.92])
                            with col_chk:
                                incluir = st.checkbox("✓", value=True, key=f"v2_chk_{i}")
                            with col_cnt:
                                new_titulo = st.text_input("Título", value=titulo_show, key=f"v2_tit_{i}")
                                nh = max(4, len(resumen_raw) // 60)
                                new_res = st.text_area("Resumen", value=resumen_raw, height=max(150, nh * 22), key=f"v2_res_{i}")
                                st.caption(f"Fuente: {sitio} | Fecha: {news.get('fecha', '—')}")
                            if incluir:
                                n2 = news.copy()
                                n2['titulo'] = new_titulo
                                n2['resumen'] = new_res
                                edited_list.append(n2)

                    col_save, _ = st.columns([1, 2])
                    with col_save:
                        if st.form_submit_button("💾 GUARDAR CAMBIOS", type="primary", use_container_width=True):
                            st.session_state['noticias_editadas_finales'] = edited_list
                            st.toast(f"✅ {len(edited_list)} noticias guardadas.")

                # Panel de descartes
                if os.path.exists("prevision_noticias_descartadas.json"):
                    with open("prevision_noticias_descartadas.json", "r", encoding="utf-8") as f:
                        descartadas = json.load(f)
                    if descartadas:
                        with st.expander(f"🗑️ Noticias descartadas ({len(descartadas)})"):
                            motivos = {}
                            for d in descartadas:
                                m = d['motivo'].split(' (')[0]
                                motivos[m] = motivos.get(m, 0) + 1
                            for m, c in motivos.items():
                                st.markdown(f"- **{c}** por: {m}")
                            st.markdown("---")
                            for i, d in enumerate(descartadas):
                                st.markdown(f"**{i+1}. {d.get('titulo','Sin título')}**")
                                st.caption(f"Fuente: {d.get('sitio','—')} | {d.get('motivo','—')}")
                                st.divider()

                if st.button("✅ CONFIRMAR SELECCIÓN", type="primary"):
                    st.session_state['news_confirmed'] = True
                    st.success("¡Selección confirmada! Procede al Paso 3.")

            except Exception as e:
                st.error(f"Error: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

        # ── PASO 3: GENERAR ──
        confirmed = st.session_state.get('news_confirmed', False)
        step3_cls = "pcc-step pcc-step-active" if confirmed else "pcc-step"
        st.markdown(f'<div class="{step3_cls}">', unsafe_allow_html=True)
        st.markdown('<div class="pcc-step-label">Paso 3</div>', unsafe_allow_html=True)
        st.markdown('<div class="pcc-step-title">Generar Audio</div>', unsafe_allow_html=True)

        if not confirmed:
            st.caption("Pendiente de confirmar selección.")
        else:
            if st.button("🎙️ ¡GENERAR PODCAST!", type="primary", disabled=not confirmed):
                with st.spinner("Generando audios y montando el podcast..."):
                    try:
                        final_news = st.session_state.get('noticias_editadas_finales', [])
                        if not final_news and os.path.exists("prevision_noticias_resumidas.json"):
                            with open("prevision_noticias_resumidas.json", "r", encoding="utf-8") as f:
                                final_news = json.load(f)
                        with open("seleccion_usuario.json", "w", encoding="utf-8") as f:
                            json.dump(final_news, f, ensure_ascii=False, indent=4)

                        cmd = [sys.executable, "dorototal.py", "--from-json", "seleccion_usuario.json"]
                        if mode_skip_special:
                            cmd.append("--skip-special")

                        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=os.getcwd())
                        log_ph = st.empty()
                        logs = []
                        while True:
                            line = proc.stdout.readline()
                            if line == '' and proc.poll() is not None:
                                break
                            if line:
                                logs.append(line.strip())
                                log_ph.code("\n".join(logs[-15:]))
                        if proc.poll() == 0:
                            st.success("🎉 ¡Podcast generado con éxito!")
                            st.balloons()
                            for f in ["seleccion_usuario.json", "prevision_noticias_resumidas.json"]:
                                if os.path.exists(f): os.remove(f)
                            st.session_state['news_confirmed'] = False
                            time.sleep(2); st.rerun()
                        else:
                            st.error(f"Error: {proc.stderr.read()}")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  PÁGINA: MEDIATECA
# ═══════════════════════════════════════════════════════════════
elif page == "mediateca":
    st.markdown('<div class="pcc-page-title">📚 Mediateca</div>', unsafe_allow_html=True)

    tab_podcasts, tab_especiales, tab_od = st.tabs(["🎙️ Podcasts", "🎭 Episodios Especiales", "🎧 A la Carta"])

    with tab_podcasts:
        try:
            podcast_dirs = sorted([d for d in glob.glob("podcast_apg_*") if os.path.isdir(d)], key=os.path.getctime, reverse=True)
            if not podcast_dirs:
                st.info("No hay podcasts generados.")
            else:
                for p_dir in podcast_dirs:
                    display_name = p_dir.replace("podcast_apg_", "").replace("_", " ")
                    with st.expander(f"🎙️ {display_name}"):
                        mp3s = glob.glob(os.path.join(p_dir, "*.mp3"))
                        htmls = glob.glob(os.path.join(p_dir, "*.html"))
                        json_path = os.path.join(p_dir, "transcript.json")
                        col_info, col_act = st.columns([3, 1])
                        with col_info:
                            if mp3s:
                                st.audio(mp3s[0])
                                st.caption(os.path.basename(mp3s[0]))
                            else:
                                st.warning("Sin MP3.")
                            if f'social_result_{p_dir}' in st.session_state:
                                social_data = st.session_state[f'social_result_{p_dir}']
                                st_fb, st_ig = st.tabs(["Facebook", "Instagram"])
                                st_fb.text_area("Post Facebook", value=social_data.get('facebook_post', ''), height=200, key=f"fb_{p_dir}")
                                st_ig.text_area("Caption Instagram", value=social_data.get('instagram_caption', ''), height=200, key=f"ig_{p_dir}")
                                if st.button("❌ Cerrar Pack", key=f"close_{p_dir}"):
                                    del st.session_state[f'social_result_{p_dir}']; st.rerun()
                        with col_act:
                            if mp3s:
                                with open(mp3s[0], "rb") as f:
                                    st.download_button("⬇️ MP3", f, os.path.basename(mp3s[0]), key=f"dl_{p_dir}", use_container_width=True)
                            if htmls:
                                with open(htmls[0], "rb") as f:
                                    st.download_button("📄 HTML", f, os.path.basename(htmls[0]), mime="text/html", key=f"dlh_{p_dir}", use_container_width=True)
                            if os.path.exists(json_path):
                                if st.button("📱 Social Pack", key=f"sp_{p_dir}", use_container_width=True):
                                    with st.spinner("Generando..."):
                                        try:
                                            with open(json_path, 'r', encoding='utf-8') as f:
                                                transcript = json.load(f)
                                            full_text = "\n".join([i['content'] for i in transcript if i.get('type') in ['block', 'news', 'intro']])
                                            resp = generar_texto_con_gemini(PromptsCreativos.generar_social_pack(full_text))
                                            clean = resp.replace("```json", "").replace("```", "").strip()
                                            st.session_state[f'social_result_{p_dir}'] = json.loads(clean)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                            st.markdown("---")
                            if st.button("🗑️ Eliminar", key=f"del_{p_dir}", type="secondary", use_container_width=True):
                                shutil.rmtree(p_dir)
                                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_especiales:
        try:
            ee_files = sorted(glob.glob("EE_*.mp3"), key=os.path.getctime, reverse=True)
            if not ee_files:
                st.info("No hay episodios especiales.")
            else:
                for ee in ee_files:
                    with st.expander(f"📢 {os.path.basename(ee)}"):
                        col_a, col_b = st.columns([3, 1])
                        col_a.audio(ee)
                        with col_b:
                            with open(ee, "rb") as f:
                                st.download_button("⬇️ MP3", f, os.path.basename(ee), key=f"dl_ee_{ee}", use_container_width=True)
                            if st.button("🗑️ Eliminar", key=f"del_ee_{ee}", use_container_width=True):
                                os.remove(ee); st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_od:
        try:
            od_files = sorted(glob.glob("OD_*.mp3"), key=os.path.getctime, reverse=True)
            if not od_files:
                st.info("No hay grabaciones a la carta.")
            else:
                for od in od_files:
                    with st.expander(f"🎙️ {os.path.basename(od)}"):
                        col_a, col_b = st.columns([3, 1])
                        col_a.audio(od)
                        with col_b:
                            with open(od, "rb") as f:
                                st.download_button("⬇️ MP3", f, os.path.basename(od), key=f"dl_od_{od}", use_container_width=True)
                            if st.button("🗑️ Eliminar", key=f"del_od_{od}", use_container_width=True):
                                os.remove(od); st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════
#  PÁGINA: CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════
elif page == "config":
    st.markdown('<div class="pcc-page-title">⚙️ Configuración</div>', unsafe_allow_html=True)
    tab_gen, tab_audio, tab_src, tab_ctas_p = st.tabs(["🔧 General", "🎛️ Audio", "📡 Fuentes", "📢 CTAs"])

    with tab_gen:
        st.markdown('<div class="pcc-section-title">Identidad del Podcast</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            new_presentadora = st.text_input("Presentadora", value=config['podcast_info'].get('presentadora','Dorotea'))
            new_region       = st.text_input("Región",       value=config['podcast_info'].get('region',''))
        with c2:
            new_email        = st.text_input("Email",        value=config['podcast_info'].get('email_contacto',''))
            new_email_alias  = st.text_input("Alias email",  value=config['podcast_info'].get('email_alias_ssml',''))

        st.markdown('<div class="pcc-section-title">Recursos</div>', unsafe_allow_html=True)
        cur_feeds = config.get('generation_config',{}).get('feeds_file','feeds.txt')
        txt_files = sorted(set([f for f in os.listdir('.') if f.endswith('.txt') and 'feeds' in f.lower()] + [cur_feeds]))
        new_feeds_file = st.selectbox("Archivo de Feeds", txt_files, index=txt_files.index(cur_feeds) if cur_feeds in txt_files else 0)
        cur_cta = config.get('directories',{}).get('ctas','cta_texts')
        cta_dirs = sorted(set([d for d in os.listdir('.') if os.path.isdir(d) and 'cta' in d.lower()] + [cur_cta]))
        new_ctas_dir    = st.selectbox("Carpeta CTAs", cta_dirs, index=cta_dirs.index(cur_cta) if cur_cta in cta_dirs else 0)
        new_audio_dir   = st.text_input("Carpeta Audio Assets", value=config.get('directories',{}).get('audio_assets','audio_assets'))

        st.markdown('<div class="pcc-section-title">Lógica de Noticias</div>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            new_dedup     = st.slider("Umbral similitud (dedup)", 0.5, 1.0, float(config['generation_config'].get('dedup_similarity_threshold',0.9)), 0.05)
            new_min_block = st.number_input("Mín. noticias por bloque", value=int(config['generation_config'].get('min_news_per_block',2)))
        with c4:
            new_max_items    = st.slider("Máx. noticias", 5, 50, int(config['generation_config'].get('max_news_items',20)), 1)
            new_window_hours = st.slider("Ventana por defecto (h)", 6, 168, int(config['generation_config'].get('news_window_hours',48)), 6)

        if st.button("💾 Guardar Configuración General", type="primary"):
            config['podcast_info'].update({'presentadora':new_presentadora,'region':new_region,'email_contacto':new_email,'email_alias_ssml':new_email_alias})
            config['generation_config'].update({'feeds_file':new_feeds_file,'dedup_similarity_threshold':new_dedup,'min_news_per_block':new_min_block,'max_news_items':new_max_items,'news_window_hours':new_window_hours})
            config.setdefault('directories',{}).update({'ctas':new_ctas_dir,'audio_assets':new_audio_dir})
            guardar_config(config); st.success("✅ Guardado."); time.sleep(0.5); st.rerun()

    with tab_audio:
        voice_options = [
            "es-ES-Chirp3-HD-Achernar [FEMALE]","es-ES-Chirp3-HD-Aoede [FEMALE]","es-ES-Chirp3-HD-Autonoe [FEMALE]",
            "es-ES-Chirp3-HD-Callirrhoe [FEMALE]","es-ES-Chirp3-HD-Despina [FEMALE]","es-ES-Chirp3-HD-Erinome [FEMALE]",
            "es-ES-Chirp3-HD-Gacrux [FEMALE]","es-ES-Chirp3-HD-Kore [FEMALE]","es-ES-Chirp3-HD-Laomedeia [FEMALE]",
            "es-ES-Chirp3-HD-Leda [FEMALE]","es-ES-Chirp3-HD-Pulcherrima [FEMALE]","es-ES-Chirp3-HD-Sulafat [FEMALE]",
            "es-ES-Chirp3-HD-Vindemiatrix [FEMALE]","es-ES-Chirp3-HD-Zephyr [FEMALE]",
            "es-ES-Chirp3-HD-Achird [MALE]","es-ES-Chirp3-HD-Algenib [MALE]","es-ES-Chirp3-HD-Algieba [MALE]",
            "es-ES-Chirp3-HD-Alnilam [MALE]","es-ES-Chirp3-HD-Charon [MALE]","es-ES-Chirp3-HD-Enceladus [MALE]",
            "es-ES-Chirp3-HD-Fenrir [MALE]","es-ES-Chirp3-HD-Iapetus [MALE]","es-ES-Chirp3-HD-Orus [MALE]",
            "es-ES-Chirp3-HD-Puck [MALE]","es-ES-Chirp3-HD-Rasalgethi [MALE]","es-ES-Chirp3-HD-Sadachbia [MALE]",
            "es-ES-Chirp3-HD-Sadaltager [MALE]","es-ES-Chirp3-HD-Schedar [MALE]","es-ES-Chirp3-HD-Umbriel [MALE]",
            "es-ES-Chirp3-HD-Zubenelgenubi [MALE]","es-ES-Chirp-HD-F [FEMALE]","es-ES-Chirp-HD-O [FEMALE]","es-ES-Chirp-HD-D [MALE]",
            "es-ES-Neural2-A [FEMALE]","es-ES-Neural2-E [FEMALE]","es-ES-Neural2-H [FEMALE]","es-ES-Neural2-F [MALE]","es-ES-Neural2-G [MALE]",
            "es-ES-Studio-C [FEMALE]","es-ES-Studio-F [MALE]","es-ES-Journey-F [FEMALE]","es-ES-Journey-D [MALE]",
            "es-ES-Wavenet-F [FEMALE]","es-ES-Wavenet-H [FEMALE]","es-ES-Wavenet-E [MALE]","es-ES-Wavenet-G [MALE]",
            "es-ES-Standard-F [FEMALE]","es-ES-Standard-H [FEMALE]","es-ES-Standard-E [MALE]","es-ES-Standard-G [MALE]"
        ]
        try: cur_vi = voice_options.index(config['audio_config'].get('voice_name'))
        except: cur_vi = 11
        ca1, ca2 = st.columns(2)
        with ca1:
            new_voice    = st.selectbox("Voz TTS", voice_options, index=cur_vi)
            new_lufs     = st.slider("Volumen (LUFS)", -24.0, -10.0, float(config['audio_config'].get('target_lufs',-16.0)), 0.5)
        with ca2:
            new_pausa     = st.text_input("Pausa estándar (SSML)", value=config['podcast_info'].get('pausa_estandar','600ms'))
            new_min_words = st.number_input("Mín. palabras/noticia", value=int(config['audio_config'].get('min_words_for_audio',33)))
        st.markdown('<div class="pcc-section-title">Diccionario de Pronunciación</div>', unsafe_allow_html=True)
        dp1, dp2 = st.columns(2)
        correcciones = config.get('pronunciation',{}).get('correcciones',{})
        siglas       = config.get('pronunciation',{}).get('siglas',{})
        new_corr = dp1.text_area("Palabras (ORIGINAL : CORRECCIÓN)", value="\n".join([f"{k} : {v}" for k,v in correcciones.items()]), height=220)
        new_sig  = dp2.text_area("Siglas (SIGLA : DELETREO)",        value="\n".join([f"{k} : {v}" for k,v in siglas.items()]),       height=220)
        if st.button("💾 Guardar Audio y Pronunciación", type="primary"):
            config['audio_config'].update({'voice_name':new_voice,'target_lufs':new_lufs,'min_words_for_audio':new_min_words})
            config['podcast_info']['pausa_estandar'] = new_pausa
            def pd_parse(t):
                d={}
                for l in t.split('\n'):
                    if ':' in l: k,v=l.split(':',1); d[k.strip()]=v.strip()
                return d
            config.setdefault('pronunciation',{}).update({'correcciones':pd_parse(new_corr),'siglas':pd_parse(new_sig)})
            guardar_config(config); st.success("✅ Guardado."); time.sleep(0.5); st.rerun()

    with tab_src:
        st.markdown('<div class="pcc-section-title">Monitor de Fuentes RSS</div>', unsafe_allow_html=True)
        if st.button("🔄 Analizar Feeds", type="primary") or ('fuentes_analytics_df' in st.session_state and st.session_state['fuentes_analytics_df'] is not None):
            btn_src = st.session_state.get('_btn_src', False)
            if not btn_src and 'fuentes_analytics_df' in st.session_state:
                df = st.session_state['fuentes_analytics_df']
            else:
                with st.spinner("Conectando..."):
                    ff = config.get('generation_config',{}).get('feeds_file','feeds.txt')
                    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), ff)
                    df = None
                    if os.path.exists(fp):
                        try: df = analizar_frecuencia_fuentes(fp); st.session_state['fuentes_analytics_df'] = df
                        except Exception as e: st.error(f"Error: {e}")
                    else: st.error(f"No se encuentra {ff}")
            if df is not None:
                m1,m2 = st.columns(2); m1.metric("Total",len(df))
                act = len(df[df['Estado'].isin(["🟢 Muy Activo","🟡 Activo"])])
                m2.metric("Activas 30d", act, delta=f"{round(act/len(df)*100)}%")
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.markdown('<div class="pcc-section-title">Informe Semanal</div>', unsafe_allow_html=True)
                if st.button("📝 Generar Guion Informe Semanal", type="primary"):
                    with st.spinner("Redactando..."):
                        try:
                            analisis_str = "TABLA (ordenada por semana):\n" + df.sort_values('7d',ascending=False).to_string(index=False)
                            guion = generar_texto_con_gemini(PromptsCreativos.generar_analisis_fuentes(analisis_str))
                            clean = guion.replace("```txt","").replace("```","").strip()
                            ts = datetime.datetime.now().strftime("%d-%m-%y_%H-%M")
                            fname = f"EE_analisis_semanal - {ts}.txt"
                            with open(fname,"w",encoding="utf-8") as f: f.write(clean)
                            st.success(f"✅ {fname}"); st.text_area("Preview:", value=clean, height=300)
                        except Exception as e: st.error(f"Error: {e}")

    with tab_ctas_p:
        st.markdown('<div class="pcc-section-title">Editor de CTAs</div>', unsafe_allow_html=True)
        ctas_dir = config.get('directories',{}).get('ctas','cta_texts')
        if not os.path.isabs(ctas_dir): ctas_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ctas_dir)
        if not os.path.exists(ctas_dir):
            st.error(f"Directorio no encontrado: {ctas_dir}")
        else:
            files = sorted([f for f in os.listdir(ctas_dir) if f.endswith(".txt")])
            if not files: st.warning("No hay archivos .txt.")
            else:
                sel = st.selectbox("Archivo:", files)
                path_f = os.path.join(ctas_dir, sel)
                try:
                    content = open(path_f, encoding="utf-8").read()
                    new_c = st.text_area(f"Editando `{sel}`", value=content, height=300)
                    if st.button("💾 Guardar CTA", type="primary"):
                        with open(path_f,"w",encoding="utf-8") as f: f.write(new_c)
                        st.success("✅ Guardado."); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Error: {e}")


# ═══════════════════════════════════════════════════════════════
#  PÁGINA: CEREBRO
# ═══════════════════════════════════════════════════════════════
elif page == "cerebro":
    st.markdown('<div class="pcc-page-title">🧠 Cerebro y Personalidad</div>', unsafe_allow_html=True)
    st.caption("Define CÓMO habla Dorotea. Variables disponibles: `{presentadora}`, `{region}`, `{email}`, `{pausa}`")
    prompts_cfg      = config.get('prompts',{})
    analysis_prompts = prompts_cfg.get('analysis_prompts',{})
    sub_pers, sub_logic, sub_struct = st.tabs(["🎭 Personalidad","🧠 Lógica IA","🏗️ Estructura"])

    with sub_pers:
        st.markdown('<div class="pcc-section-title">Personalidad Base</div>', unsafe_allow_html=True)
        new_persona = st.text_area("Instrucción maestra", value=prompts_cfg.get('persona_base',''), height=150)
        st.markdown('<div class="pcc-section-title">Saludos</div>', unsafe_allow_html=True)
        cs1,cs2 = st.columns(2)
        saludo_lunes   = cs1.text_area("Lunes",        value=prompts_cfg.get('saludos',{}).get('lunes',''),         height=130)
        saludo_viernes = cs1.text_area("Viernes",       value=prompts_cfg.get('saludos',{}).get('viernes',''),       height=130)
        saludo_mj      = cs2.text_area("Mar–Jue",       value=prompts_cfg.get('saludos',{}).get('martes_jueves',''), height=130)
        saludo_finde   = cs2.text_area("Fin de semana", value=prompts_cfg.get('saludos',{}).get('finde',''),         height=130)
        st.markdown('<div class="pcc-section-title">Despedidas</div>', unsafe_allow_html=True)
        cd1,cd2 = st.columns(2)
        desp_lunes   = cd1.text_area("Cierre L",  value=prompts_cfg.get('despedidas',{}).get('lunes',''),         height=110)
        desp_viernes = cd1.text_area("Cierre V",  value=prompts_cfg.get('despedidas',{}).get('viernes',''),       height=110)
        desp_mj      = cd2.text_area("Cierre MJ", value=prompts_cfg.get('despedidas',{}).get('martes_jueves',''), height=110)
        desp_finde   = cd2.text_area("Cierre F",  value=prompts_cfg.get('despedidas',{}).get('finde',''),         height=110)
        st.markdown('<div class="pcc-section-title">Firmas</div>', unsafe_allow_html=True)
        cf1,cf2 = st.columns(2)
        firma_lunes   = cf1.text_area("Firma L",  value=prompts_cfg.get('firmas',{}).get('lunes',''),         height=90)
        firma_viernes = cf1.text_area("Firma V",  value=prompts_cfg.get('firmas',{}).get('viernes',''),       height=90)
        firma_mj      = cf2.text_area("Firma MJ", value=prompts_cfg.get('firmas',{}).get('martes_jueves',''), height=90)
        firma_finde   = cf2.text_area("Firma F",  value=prompts_cfg.get('firmas',{}).get('finde',''),         height=90)
        if st.button("💾 Guardar Personalidad", type="primary", use_container_width=True):
            config.setdefault('prompts',{}).update({
                'persona_base': new_persona,
                'saludos':    {'lunes':saludo_lunes,'martes_jueves':saludo_mj,'viernes':saludo_viernes,'finde':saludo_finde},
                'despedidas': {'lunes':desp_lunes,'martes_jueves':desp_mj,'viernes':desp_viernes,'finde':desp_finde},
                'firmas':     {'lunes':firma_lunes,'martes_jueves':firma_mj,'viernes':firma_viernes,'finde':firma_finde},
            })
            guardar_config(config); st.success("✅ Personalidad guardada."); time.sleep(0.5); st.rerun()

    with sub_logic:
        st.caption("Reglas de negocio para el análisis de noticias.")
        prompt_clasif  = st.text_area("Clasificar (Relevante/Irrelevante)", value=analysis_prompts.get('clasificacion_criterios',''),  height=200)
        prompt_resumen = st.text_area("Resumir noticias",                   value=analysis_prompts.get('resumen_instrucciones',''),    height=250)
        prompt_agrup   = st.text_area("Agrupar temas",                      value=analysis_prompts.get('agrupacion_instrucciones',''), height=150)

    with sub_struct:
        st.caption("Formato de los guiones finales.")
        prompt_narracion = st.text_area("Narrar bloques",   value=analysis_prompts.get('narracion_instrucciones',''),     height=150)
        ci1,ci2 = st.columns(2)
        prompt_intro     = ci1.text_area("Intro",           value=analysis_prompts.get('intro_instrucciones',''),         height=200)
        prompt_despedida = ci2.text_area("Despedida",       value=analysis_prompts.get('despedida_instrucciones',''),     height=200)
        prompt_post      = st.text_area("Post-Créditos",    value=analysis_prompts.get('post_creditos_instrucciones',''), height=100)

    st.markdown("---")
    if st.button("💾 Guardar Lógica y Estructura", type="primary", use_container_width=True):
        config.setdefault('prompts',{}).setdefault('analysis_prompts',{}).update({
            'clasificacion_criterios': prompt_clasif, 'resumen_instrucciones': prompt_resumen,
            'narracion_instrucciones': prompt_narracion, 'agrupacion_instrucciones': prompt_agrup,
            'intro_instrucciones': prompt_intro, 'despedida_instrucciones': prompt_despedida,
            'post_creditos_instrucciones': prompt_post,
        })
        guardar_config(config); st.success("✅ Lógica actualizada."); time.sleep(0.5); st.rerun()


# ═══════════════════════════════════════════════════════════════
#  PÁGINA: EXTRAS
# ═══════════════════════════════════════════════════════════════
elif page == "extras":
    st.markdown('<div class="pcc-page-title">🛠️ Extras</div>', unsafe_allow_html=True)
    tab_od, tab_buzon, tab_logs = st.tabs(["🎙️ A la Carta","🗣️ Buzón del Oyente","📊 Logs y Costes"])

    with tab_od:
        st.info("Genera un audio con la voz de Dorotea sobre cualquier tema.")
        col_i,col_o = st.columns([2,1])
        with col_i:
            topic_od = st.text_area("¿Sobre qué quieres que hable Dorotea?", placeholder="Ej: Explica cómo funciona un agujero negro...", height=150)
        with col_o:
            dur_od = st.slider("Duración (min)", 1, 5, 2, 1)
            st.caption(f"≈ {dur_od*150} palabras")
            style_od = st.selectbox("Tono", ["Normal (Dorotea)","Muy Alegre","Serio/Intenso","Susurro/Cómplice"])
        if st.button("🎙️ GENERAR AUDIO A LA CARTA", type="primary"):
            if not topic_od: st.error("Escribe un tema.")
            else:
                with st.spinner("Generando..."):
                    try:
                        tone_map = {"Muy Alegre":"Muy enérgico y alegre.","Serio/Intenso":"Sobrio y periodístico.","Susurro/Cómplice":"Cercano, secreto."}
                        tone = tone_map.get(style_od,"")
                        script = generar_texto_con_gemini(f'Eres Dorotea. Guion sobre "{topic_od}". {dur_od*150} palabras. {tone} TEXTO PLANO. GUION:')
                        if not script: st.error("Error generando guion.")
                        else:
                            with st.expander("Ver guion"): st.write(script)
                            chunks = [c for c in script.split('\n') if c.strip()]
                            full_audio = AudioSegment.empty()
                            pb = st.progress(0)
                            for i,chunk in enumerate(chunks):
                                safe = chunk.replace('&','y').replace('<','').replace('>','')
                                seg = sintetizar_ssml_a_audio(f"<speak>{safe}<break time='500ms'/></speak>")
                                if seg: full_audio += seg
                                pb.progress((i+1)/len(chunks))
                            final = masterizar_a_lufs(full_audio,-16.0)
                            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            safe_t = "".join([c for c in topic_od if c.isalnum() or c in ' _-']).strip().replace(" ","_")[:30]
                            fname = f"OD_{ts}_{safe_t}.mp3"
                            final.export(fname, format="mp3", bitrate="192k")
                            st.audio(fname); st.success(f"Audio listo: {fname}")
                            with open(fname,"rb") as f: st.download_button("⬇️ Descargar MP3", f, fname, mime="audio/mpeg")
                    except Exception as e: st.error(f"Error: {e}")

    with tab_buzon:
        st.info("Sube un audio de un oyente para generar una respuesta de Dorotea.")
        col_up,col_op = st.columns([1,1])
        with col_up: uploaded = st.file_uploader("Audio del oyente", type=["mp3","wav","m4a","ogg"])
        with col_op:
            mover = st.checkbox("Mover al buzón del podcast", value=True)
            if uploaded: st.audio(uploaded, format="audio/mp3")
        if uploaded and st.button("🎙️ Generar Interacción", type="primary"):
            with st.status("Procesando...", expanded=True) as status:
                try:
                    temp_f = f"temp_listener_{int(time.time())}_{uploaded.name}"
                    with open(temp_f,"wb") as f: f.write(uploaded.getbuffer())
                    st.write("🧠 Analizando audio...")
                    mime = uploaded.type
                    if mime=="audio/mpeg": mime="audio/mp3"
                    from mcmcn_prompts import ConfiguracionPodcast
                    aj = generar_texto_multimodal_audio_con_gemini(ConfiguracionPodcast.PROMPT_ANALISIS_AUDIO_OYENTE, uploaded.getvalue(), mime_type=mime)
                    aj = aj.replace("```json","").replace("```","").strip()
                    datos = {}
                    if "{" in aj:
                        try: s,e2=aj.find('{'),aj.rfind('}'); datos=json.loads(aj[s:e2+1])
                        except: pass
                    nombre=datos.get("nombre_oyente","Un oyente"); tema=datos.get("tema_principal","su mensaje")
                    st.write(f"✅ Detectado: **{nombre}** sobre *{tema}*")
                    st.write("✍️ Redactando respuesta...")
                    guion = generar_texto_con_gemini(ConfiguracionPodcast.PROMPT_RESPUESTA_OYENTE.format(nombre_oyente=nombre,tema_principal=tema))
                    if "INTRO:" in guion and "REACCION:" in guion:
                        partes=guion.split("REACCION:"); intro_txt=partes[0].replace("INTRO:","").strip(); reac_txt=partes[1].strip()
                    else: intro_txt=f"Escuchamos ahora a {nombre}."; reac_txt=guion
                    st.write("🗣️ Sintetizando voz...")
                    ai=sintetizar_ssml_a_audio(f"<speak>{intro_txt}</speak>"); ar=sintetizar_ssml_a_audio(f"<speak>{reac_txt}</speak>")
                    ls=masterizar_a_lufs(AudioSegment.from_file(temp_f),-16.0)
                    tf=glob.glob("audio_assets/clickrozalen*.mp3"); ta=AudioSegment.silent(1000)
                    if tf:
                        t=AudioSegment.from_file(random.choice(tf)); ta=(t[:6000].fade_out(2000) if len(t)>6000 else t)
                    mix=AudioSegment.silent(500)
                    if ai: mix+=ai
                    mix+=ta.fade_in(500).fade_out(500)+ls+ta.fade_in(500).fade_out(500)
                    if ar: mix+=ar
                    ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); out_f=f"RESPUESTA_{nombre.replace(' ','_')}_{ts}.mp3"
                    mix.export(out_f,format="mp3",bitrate="192k")
                    st.success("¡Interacción generada!"); st.audio(out_f)
                    with open(out_f,"rb") as f: st.download_button("⬇️ Descargar",f,out_f,mime="audio/mpeg")
                    if mover: shutil.copy(temp_f,os.path.join("buzon_del_oyente",uploaded.name)); st.toast("📧 Copiado al buzón.")
                    os.remove(temp_f); status.update(label="✅ Completado",state="complete",expanded=False)
                except Exception as e: st.error(f"Error: {e}"); import traceback; st.code(traceback.format_exc())

    with tab_logs:
        cola,colb = st.columns([2,1])
        with cola:
            st.markdown('<div class="pcc-section-title">Registro de Ejecución</div>', unsafe_allow_html=True)
            if st.button("🔄 Refrescar"): st.rerun()
            try:
                lf = "logs/process_log.jsonl"
                if os.path.exists(lf):
                    lines = open(lf).readlines()
                    disp=[]
                    icon_map={"STEP":"🔹","SUCCESS":"✅","WARNING":"⚠️","ERROR":"❌","INFO":"ℹ️"}
                    for l in lines[-50:]:
                        try: e=json.loads(l); ts=e['timestamp'].split('T')[1].split('.')[0]; disp.append(f"{ts} {icon_map.get(e['level'],'')} {e['message']}")
                        except: pass
                    st.code("\n".join(disp), language="text")
                else: st.info("No hay logs disponibles.")
            except Exception as e: st.error(f"Error: {e}")
        with colb:
            st.markdown('<div class="pcc-section-title">Estimación de Costes</div>', unsafe_allow_html=True)
            try:
                uf="logs/usage_stats.json"
                if os.path.exists(uf):
                    stats=json.load(open(uf))
                    gi=stats.get('gemini_input_tokens',0); go=stats.get('gemini_output_tokens',0); gt=gi+go; gl=1_000_000
                    st.write("**Gemini Flash**"); st.progress(min(1.0,gt/gl)); st.caption(f"{gt:,}/{gl:,} tokens ({min(100,round(gt/gl*100))}%)")
                    st.divider()
                    tts=stats.get('tts_chars',0); tl=1_000_000
                    st.write("**Google TTS**"); st.progress(min(1.0,tts/tl)); st.caption(f"{tts:,}/{tl:,} chars ({min(100,round(tts/tl*100))}%)")
                else: st.info("Sin datos de consumo.")
            except Exception as e: st.error(f"Error: {e}")

# ── Footer ──
st.markdown("---")
st.markdown('<span style="font-size:0.75rem;color:#6b6b6b;">Podcast Control Center v0.97</span>', unsafe_allow_html=True)
