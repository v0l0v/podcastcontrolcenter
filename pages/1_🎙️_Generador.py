import streamlit as st
import sys
import json
import os
import subprocess
import time
import datetime
import random
import glob
import shutil
import pandas as pd
from src.utils.ui_common import inject_pcc_style, cargar_config, guardar_config, init_session_state
from src.llm_utils import generar_texto_con_gemini, generar_texto_multimodal_audio_con_gemini
from src.engine.audio import sintetizar_ssml_a_audio, masterizar_a_lufs
from pydub import AudioSegment
from mcmcn_prompts import PromptsCreativos, ConfiguracionPodcast

st.set_page_config(page_title="PCC - Generador", page_icon="🎙️", layout="wide")
inject_pcc_style()
init_session_state()
config = cargar_config()

st.markdown('<div class="pcc-page-title">🎙️ Generar Podcast</div>', unsafe_allow_html=True)
st.info("💡 **El corazón del sistema.** Este es el flujo de 3 pasos para crear el **Podcast Diario**. Extraemos noticias, las revisas/editas, y Dorotea las locuta.")

# Mostrar reporte del último podcast generado si existe
if 'last_run_stats' in st.session_state and st.session_state['last_run_stats']:
    stats = st.session_state['last_run_stats']
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #FAF3DC 0%, #FFFFFF 100%); border: 2px solid #8E701D; border-radius: 16px; padding: 22px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(142, 112, 29, 0.12);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-size: 1.1rem; font-weight: 700; color: #8E701D; font-family: 'Cinzel', serif;">🎙️ Último Podcast Generado</span>
            <span style="font-size: 0.72rem; font-weight: 700; background: #8E701D; color: #FAF3DC; padding: 4px 10px; border-radius: 30px;">REPORTE DE COSTE</span>
        </div>
        <div style="font-size: 0.88rem; line-height: 1.6; color: var(--text-color);">
            ¡Tu podcast ha sido locutado de forma impecable!<br>
            • <b>Voz Utilizada:</b> {stats['voice']}<br>
            • <b>Caracteres Sintetizados:</b> {stats['chars']:,} caracteres<br>
            • <b>Tokens Procesados (Gemini):</b> {stats['tokens']:,} tokens<br>
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px dashed rgba(142, 112, 29, 0.3); font-size: 1.05rem; font-weight: 800; color: #8E701D;">
                💰 Gasto Real de la Operación: ${stats['cost']:.4f} USD
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🗑️ Limpiar reporte de coste", key="clear_report_btn"):
        del st.session_state['last_run_stats']
        st.rerun()

# ────────────────────────────────
#  FLUJO NORMAL (3 pasos)
# ────────────────────────────────

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
    key="window_mode_selector_v2",
    index=0
)
if "Solo hoy" in window_mode:
    _ahora = datetime.datetime.now()
    horas_hoy = max(1, round(_ahora.hour + _ahora.minute / 60))
    st.caption(f"🌅 Son las {_ahora.strftime('%H:%M')} → se usarán las últimas **{horas_hoy} horas** (Máx. noticias liberado)")
    st.session_state['window_hours_override'] = horas_hoy
    st.session_state['max_items_override'] = 500
elif "X horas" in window_mode:
    _saved = int(config.get('generation_config', {}).get('news_window_hours', 48))
    wh = st.slider("Horas", 6, 168, _saved, 6)
    st.session_state['window_hours_override'] = wh
    st.session_state['max_items_override'] = None
else:
    _saved = int(config.get('generation_config', {}).get('news_window_hours', 48))
    st.caption(f"Valor guardado: **{_saved} horas**")
    st.session_state['window_hours_override'] = None
    st.session_state['max_items_override'] = None

config_checked = st.checkbox("He revisado la configuración", value=st.session_state['config_check'], key='chk_config_v2')
st.session_state['config_check'] = config_checked

if st.button("🔎 ANALIZAR NOTICIAS", type="primary", disabled=not config_checked):
    with st.spinner("Analizando feeds y resumiendo con IA..."):
        # Limpiar archivos de preview anteriores para evitar datos obsoletos si falla el nuevo análisis
        for f in ["prevision_noticias_resumidas.json", "prevision_noticias_descartadas.json", "seleccion_usuario.json"]:
            if os.path.exists(f): 
                try:
                    os.remove(f)
                    print(f"🗑️  Archivo antiguo eliminado: {f}")
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar {f}: {e}")
        st.session_state['news_confirmed'] = False
        st.session_state['noticias_editadas_finales'] = []  # Limpiar selección anterior
        _wo = st.session_state.get('window_hours_override')
        _mo = st.session_state.get('max_items_override')
        _cmd = [sys.executable, "dorototal.py", "--preview"]
        if _wo: _cmd += ["--window-hours", str(_wo)]
        if _mo: _cmd += ["--max-items", str(_mo)]
        
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
                
        if proc.poll() == 0 and (os.path.exists("prevision_noticias_resumidas.json") or os.path.exists("prevision_noticias_descartadas.json")):
            st.success("✅ Análisis completado. Revisa las noticias en el Paso 2.")
            time.sleep(1); st.rerun()
        elif proc.poll() == 0:
            st.warning("⚠️ No se encontraron noticias con los filtros actuales.")
        else:
            st.error(f"Error: {proc.stderr.read()}")
st.markdown('</div>', unsafe_allow_html=True)

# ── PASO 2: REVISAR ──
has_resumidas = os.path.exists("prevision_noticias_resumidas.json")
has_descartadas = os.path.exists("prevision_noticias_descartadas.json")
has_preview = has_resumidas or has_descartadas

step2_cls = "pcc-step pcc-step-active" if has_preview else "pcc-step"
st.markdown(f'<div class="{step2_cls}">', unsafe_allow_html=True)
st.markdown('<div class="pcc-step-label">Paso 2</div>', unsafe_allow_html=True)
st.markdown('<div class="pcc-step-title">Revisar y Editar</div>', unsafe_allow_html=True)

if not has_preview:
    st.caption("Pendiente de análisis.")
else:
    try:
        news_candidates = []
        def clean_html(text):
            if not text:
                return ""
            import html
            import re
            clean = html.unescape(text)
            clean = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', clean)
            clean = re.sub(r'<[^>]*>', '', clean)
            clean = clean.replace("<![CDATA[", "").replace("]]>", "")
            return clean.strip()

        if has_resumidas:
            with open("prevision_noticias_resumidas.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for n in data:
                        n['titulo'] = clean_html(n.get('titulo', ''))
                        n['resumen'] = clean_html(n.get('resumen', ''))
                        n['_selected_default'] = True
                        n['_is_discarded'] = False
                        n['_bloque_padre'] = None
                        news_candidates.append(n)
                else:
                    for bloque in data.get('bloques_tematicos', []):
                        titulo_bloque = f"🎯 Bloque Temático: {bloque.get('descripcion_tema', 'Tema Varios').title()}"
                        for n in bloque.get('noticias', []):
                            n['titulo'] = clean_html(n.get('titulo', ''))
                            n['resumen'] = clean_html(n.get('resumen', ''))
                            n['_selected_default'] = True
                            n['_is_discarded'] = False
                            n['_bloque_padre'] = titulo_bloque
                            news_candidates.append(n)
                    for n in data.get('noticias_individuales', []):
                        n['titulo'] = clean_html(n.get('titulo', ''))
                        n['resumen'] = clean_html(n.get('resumen', ''))
                        n['_selected_default'] = True
                        n['_is_discarded'] = False
                        n['_bloque_padre'] = None
                        news_candidates.append(n)
        if has_descartadas:
            with open("prevision_noticias_descartadas.json", "r", encoding="utf-8") as f:
                for n in json.load(f):
                    n['titulo'] = clean_html(n.get('titulo', ''))
                    n['resumen'] = clean_html(n.get('resumen', ''))
                    n['_selected_default'] = False # NO pre-seleccionar descartadas
                    n['_is_discarded'] = True
                    n['_bloque_padre'] = "🗑️ Descartadas por el Sistema"
                    if 'resumen' not in n: n['resumen'] = ""
                    if 'motivo' not in n: n['motivo'] = "Desconocido"
                    news_candidates.append(n)
                    
        col_cover, col_msg = st.columns([1, 2.5])
        with col_cover:
            if os.path.exists("prevision_portada.png"):
                st.image("prevision_portada.png", caption="🎨 Portada Autogenerada de la Edición", use_container_width=True)
        with col_msg:
            st.info(f"✅ Hay {len(news_candidates)} noticias listas para revisar (todas pre-seleccionadas).")

        with st.form("form_edicion_v2"):
            edited_list = []
            ultimo_bloque = "XYZ_NONE"
            for i, news in enumerate(news_candidates):
                current_block = news.get('_bloque_padre')
                if current_block != ultimo_bloque:
                    ultimo_bloque = current_block
                    title_str = current_block if current_block else "📄 Noticias Individuales"
                    st.markdown(f"<div class='pcc-section-title' style='color:var(--g-dark); margin-top:15px; border-bottom:2px solid var(--g-dark); padding-bottom:5px;'>{title_str}</div>", unsafe_allow_html=True)

                titulo_raw = news.get("titulo", "")
                sitio = news.get("sitio", "")
                titulo_show = titulo_raw if (titulo_raw and titulo_raw != "None" and len(titulo_raw) > 3) else f"Noticia de {sitio}"
                resumen_raw = news.get("resumen", "")
                
                # Decorador para descartadas
                if news['_is_discarded']:
                    exp_title = f"{i+1}. 🗑️ [DESCARTADA: {news['motivo'].split(' (')[0]}] {titulo_show}"
                else:
                    exp_title = f"{i+1}. ✅ {titulo_show}"
                    
                with st.expander(exp_title, expanded=(i == 0)):
                    col_chk, col_cnt = st.columns([0.08, 0.92])
                    nid = news.get("id", i)
                    with col_chk:
                        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
                        incluir = st.checkbox("Incluir", value=news['_selected_default'], key=f"v2_chk_{nid}")
                    with col_cnt:
                        new_titulo = st.text_input("Título", value=titulo_show, key=f"v2_tit_{nid}")
                        nh = max(4, len(resumen_raw) // 60)
                        if news['_is_discarded'] and not resumen_raw:
                            st.info("ℹ️ El resumen no se ha generado para ahorrar costes (Pipeline Zero-Cost). Si marcas 'Incluir' y lo dejas en blanco, la IA lo generará en el Paso 3, o puedes escribirlo tú mismo.")
                            placeholder_txt = "Déjalo en blanco para generación automática por IA, o escribe tu propio resumen..."
                        else:
                            placeholder_txt = "Escribe el resumen de la noticia..."
                            
                        new_res = st.text_area("Resumen", value=resumen_raw, height=max(150, nh * 22), key=f"v2_res_{nid}", placeholder=placeholder_txt)
                        if news['_is_discarded']:
                            st.warning(f"Motivo descarte original: {news['motivo']}")
                        st.caption(f"Fuente: {sitio} | Fecha: {news.get('fecha', '—')}")
                    
                    if incluir:
                        n2 = {k: v for k, v in news.items() if not k.startswith('_')} # clean internal flags
                        n2['titulo'] = new_titulo
                        n2['resumen'] = new_res
                        # If missing essential fields, fill them
                        if 'url' not in n2: n2['url'] = ""
                        if 'fecha' not in n2: n2['fecha'] = datetime.datetime.now().isoformat()
                        edited_list.append(n2)

            col_save, _ = st.columns([1, 2])
            with col_save:
                if st.form_submit_button("💾 GUARDAR CAMBIOS", type="primary", use_container_width=True):
                    st.session_state['noticias_editadas_finales'] = edited_list
                    st.toast(f"✅ {len(edited_list)} noticias guardadas en selección.")


        if st.button("✅ CONFIRMAR SELECCIÓN", type="primary"):
            # Si el usuario no pulsó GUARDAR CAMBIOS, usamos todas las
            # noticias del JSON de preview (las pre-seleccionadas por defecto)
            if not st.session_state.get('noticias_editadas_finales'):
                try:
                    if os.path.exists("prevision_noticias_resumidas.json"):
                        with open("prevision_noticias_resumidas.json", "r", encoding="utf-8") as f:
                            st.session_state['noticias_editadas_finales'] = json.load(f)
                except Exception:
                    pass
            st.session_state['news_confirmed'] = True
            n_confirmadas = len(st.session_state.get('noticias_editadas_finales', []))
            st.success(f"¡Selección confirmada ({n_confirmadas} noticias)! Procede al Paso 3.")


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
    # Obtener noticias seleccionadas para la estimación
    final_news = st.session_state.get('noticias_editadas_finales', [])
    if not final_news and os.path.exists("prevision_noticias_resumidas.json"):
        try:
            with open("prevision_noticias_resumidas.json", "r", encoding="utf-8") as f:
                final_news = json.load(f)
        except:
            pass

    # Obtener voz actual configurada
    voz_actual = config.get('audio_config', {}).get('voice_name', 'es-ES-Chirp3-HD-Laomedeia [FEMALE]')
    
    voice_options = [
        # --- EDGE-TTS (Free) ---
        "es-ES-ElviraNeural [Edge-TTS - FEMALE - Gratis]",
        "es-ES-AlvaroNeural [Edge-TTS - MALE - Gratis]",
        "es-CL-ElianaNeural [Edge-TTS - FEMALE (CL) - Gratis]",
        "es-CL-LorenzoNeural [Edge-TTS - MALE (CL) - Gratis]",
        "es-MX-DaliaNeural [Edge-TTS - FEMALE (MX) - Gratis]",
        "es-MX-JorgeNeural [Edge-TTS - MALE (MX) - Gratis]",
        
        # --- NEURAL2 (High Quality) ---
        "es-ES-Neural2-A [FEMALE]","es-ES-Neural2-E [FEMALE]","es-ES-Neural2-H [FEMALE]","es-ES-Neural2-F [MALE]","es-ES-Neural2-G [MALE]",
        
        # --- CHIRP 3 HD (Generative, Ultra-Realistic) ---
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
        
        # --- OTHER GOOGLE TTS ---
        "es-ES-Studio-C [FEMALE]","es-ES-Studio-F [MALE]","es-ES-Journey-F [FEMALE]","es-ES-Journey-D [MALE]",
        "es-ES-Wavenet-F [FEMALE]","es-ES-Wavenet-H [FEMALE]","es-ES-Wavenet-E [MALE]","es-ES-Wavenet-G [MALE]",
        "es-ES-Standard-F [FEMALE]","es-ES-Standard-H [FEMALE]","es-ES-Standard-E [MALE]","es-ES-Standard-G [MALE]"
    ]
    
    try: cur_idx = voice_options.index(voz_actual)
    except: cur_idx = 14 # Por defecto si no está

    st.markdown("<div style='margin-bottom:10px; font-weight:600;'>🎙️ Configuración rápida de Voz:</div>", unsafe_allow_html=True)
    voz_elegida = st.selectbox("Selecciona la voz para este podcast:", voice_options, index=cur_idx, key="voice_generator_override")

    if voz_elegida != voz_actual:
        config['audio_config']['voice_name'] = voz_elegida
        guardar_config(config)
        st.toast(f"🗣️ Voz actualizada a: {voz_elegida}")
        time.sleep(0.5)
        st.rerun()

    # Estimar costes
    total_estimado_chars = 3200 # Base fija para intros, outro, clima, fútbol y transiciones
    for n in final_news:
        total_estimado_chars += len(n.get("resumen", "") or "") + len(n.get("titulo", "") or "") + 300
        
    is_edge_voice = "edge" in voz_elegida.lower() or ("neural" in voz_elegida.lower() and "neural2" not in voz_elegida.lower())
    
    if is_edge_voice:
        tts_tarifa = 0.0
        tts_tipo = "Edge-TTS (Gratuito y Sencillo)"
    elif "Standard" in voz_elegida:
        tts_tarifa = 4.0 / 1_000_000
        tts_tipo = "Google TTS Standard (Bajo coste)"
    elif "Wavenet" in voz_elegida or "Neural2" in voz_elegida:
        tts_tarifa = 16.0 / 1_000_000
        tts_tipo = "Google TTS Neural2 (Alta fidelidad)"
    elif "Chirp" in voz_elegida or "Journey" in voz_elegida or "Studio" in voz_elegida:
        tts_tarifa = 30.0 / 1_000_000
        tts_tipo = "Google TTS Chirp 3 HD / Journey (Premium Ultra-Realista)"
    else:
        tts_tarifa = 4.0 / 1_000_000
        tts_tipo = "Estándar"
        
    coste_tts_estimado = total_estimado_chars * tts_tarifa
    
    # Coste LLM aproximado (15K tokens de input base + noticias, 1.5K tokens output)
    input_tokens_est = 15000 + sum([len(n.get("resumen", "") or "") // 3 for n in final_news])
    output_tokens_est = 1500
    coste_llm_estimado = (input_tokens_est * (0.075 / 1_000_000)) + (output_tokens_est * (0.30 / 1_000_000))
    
    coste_total_estimado = coste_tts_estimado + coste_llm_estimado
    
    st.markdown(f"""
    <div style="background: rgba(142, 112, 29, 0.05); border: 1px solid rgba(142, 112, 29, 0.2); border-radius: 12px; padding: 16px; margin: 15px 0 25px 0;">
        <div style="font-size: 0.95rem; font-weight: 700; color: #8E701D; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
            💰 Estimación Económica Previa
        </div>
        <div style="font-size: 0.85rem; line-height: 1.6; color: var(--muted);">
            • <b>Modelo de Voz:</b> {voz_elegida.split(" [")[0]} (<i>{tts_tipo}</i>)<br>
            • <b>Longitud de Guion Estimada:</b> ~{total_estimado_chars:,} caracteres (basado en {len(final_news)} noticias)<br>
            • <b>Coste Síntesis Vocal (TTS):</b> ${coste_tts_estimado:.4f} USD<br>
            • <b>Coste Redacción Inteligente (Gemini):</b> ${coste_llm_estimado:.4f} USD (aprox.)<br>
            <div style="border-top: 1px dashed rgba(142, 112, 29, 0.15); margin: 8px 0; padding-top: 8px; font-size: 0.95rem; font-weight: 700; color: #8E701D;">
                💸 Coste de Generación Estimado: <b>${coste_total_estimado:.4f} USD</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🎙️ ¡GENERAR PODCAST!", type="primary", disabled=not confirmed, use_container_width=True):
        with st.spinner("Generando audios y montando el podcast..."):
            try:
                # Cargar el tracking antes de la ejecución para comparar
                from src.monitoring import tracker
                tracker.load_stats()
                start_cost = tracker.stats.get("estimated_cost", 0.0)
                start_chars = tracker.stats.get("tts_chars", 0) + tracker.stats.get("tts_edge_chars", 0)
                start_tokens = tracker.stats.get("gemini_input_tokens", 0) + tracker.stats.get("gemini_output_tokens", 0)

                with open("seleccion_usuario.json", "w", encoding="utf-8") as f:
                    json.dump(final_news, f, ensure_ascii=False, indent=4)

                cmd = [sys.executable, "dorototal.py", "--from-json", "seleccion_usuario.json", "--skip-special"]

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
                    # Recargar el tracking al finalizar para comparar
                    tracker.load_stats()
                    end_cost = tracker.stats.get("estimated_cost", 0.0)
                    end_chars = tracker.stats.get("tts_chars", 0) + tracker.stats.get("tts_edge_chars", 0)
                    end_tokens = tracker.stats.get("gemini_input_tokens", 0) + tracker.stats.get("gemini_output_tokens", 0)

                    run_cost = max(0.0, end_cost - start_cost)
                    run_chars = max(0, end_chars - start_chars)
                    run_tokens = max(0, end_tokens - start_tokens)

                    # Registrar en session state para el banner tras el rerun
                    st.session_state['last_run_stats'] = {
                        "voice": voz_elegida,
                        "chars": run_chars,
                        "tokens": run_tokens,
                        "cost": run_cost
                    }

                    st.success("🎉 ¡Podcast generado con éxito!")
                    st.balloons()
                    
                    for f in ["seleccion_usuario.json", "prevision_noticias_resumidas.json"]:
                        if os.path.exists(f): 
                            try: os.remove(f)
                            except: pass
                    
                    st.session_state['news_confirmed'] = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"Error: {proc.stderr.read()}")
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown('</div>', unsafe_allow_html=True)