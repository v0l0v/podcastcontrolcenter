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
            if has_resumidas:
                with open("prevision_noticias_resumidas.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for n in data:
                            n['_selected_default'] = True
                            n['_is_discarded'] = False
                            n['_bloque_padre'] = None
                            news_candidates.append(n)
                    else:
                        for bloque in data.get('bloques_tematicos', []):
                            titulo_bloque = f"🎯 Bloque Temático: {bloque.get('descripcion_tema', 'Tema Varios').title()}"
                            for n in bloque.get('noticias', []):
                                n['_selected_default'] = True
                                n['_is_discarded'] = False
                                n['_bloque_padre'] = titulo_bloque
                                news_candidates.append(n)
                        for n in data.get('noticias_individuales', []):
                            n['_selected_default'] = True
                            n['_is_discarded'] = False
                            n['_bloque_padre'] = None
                            news_candidates.append(n)
            if has_descartadas:
                with open("prevision_noticias_descartadas.json", "r", encoding="utf-8") as f:
                    for n in json.load(f):
                        n['_selected_default'] = False # NO pre-seleccionar descartadas
                        n['_is_discarded'] = True
                        n['_bloque_padre'] = "🗑️ Descartadas por el Sistema"
                        if 'resumen' not in n: n['resumen'] = ""
                        if 'motivo' not in n: n['motivo'] = "Desconocido"
                        news_candidates.append(n)
                        
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
        if st.button("🎙️ ¡GENERAR PODCAST!", type="primary", disabled=not confirmed):
            with st.spinner("Generando audios y montando el podcast..."):
                try:
                    final_news = st.session_state.get('noticias_editadas_finales', [])
                    if not final_news and os.path.exists("prevision_noticias_resumidas.json"):
                        with open("prevision_noticias_resumidas.json", "r", encoding="utf-8") as f:
                            final_news = json.load(f)
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