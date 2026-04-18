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

st.set_page_config(page_title="PCC - Cerebro", page_icon="🧠", layout="wide")
inject_pcc_style()
init_session_state()
config = cargar_config()

st.markdown('<div class="pcc-page-title">🧠 Cerebro y Personalidad</div>', unsafe_allow_html=True)
    st.info("💡 **El Alma de Dorotea.** Construye detalladamente y mediante prompts en lenguaje natural cómo se debe comportar, saludar, redactar o filtrar noticias tu Inteligencia Artificial.")
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