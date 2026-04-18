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

st.set_page_config(page_title="PCC - Mediateca", page_icon="📚", layout="wide")
inject_pcc_style()
init_session_state()
config = cargar_config()

st.markdown('<div class="pcc-page-title">📚 Mediateca</div>', unsafe_allow_html=True)
    st.info("💡 **Tu archivo histórico.** Aquí se guardan listos para descarga todos los audios generados por el sistema, clasificados por tipología.")

    tab_podcasts, tab_especiales, tab_od = st.tabs(["🎙️ Podcasts", "🎭 Episodios Especiales", "🎧 A la Carta"])

    with tab_podcasts:
        try:
            podcast_dirs = sorted([d for d in glob.glob("podcast_apg_*") if os.path.isdir(d)], key=os.path.getctime, reverse=True)
            if not podcast_dirs:
                st.info("No hay podcasts generados.")
            else:
                col_all, col_del = st.columns([4, 1])
                sel_all_pd = col_all.checkbox("Seleccionar todos (Podcasts)", key="sel_all_pd")
                pd_to_delete = []
                
                for p_dir in podcast_dirs:
                    display_name = p_dir.replace("podcast_apg_", "").replace("_", " ")
                    col_chk, col_exp = st.columns([0.05, 0.95])
                    with col_chk:
                        # Un pequeño margen top para alinear con el expander
                        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                        if st.checkbox(" ", value=sel_all_pd, key=f"del_chk_{p_dir}"):
                            pd_to_delete.append(p_dir)
                    
                    with col_exp:
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
                                                resp = generar_texto_con_gemini(PromptsCreativos.generar_social_pack(full_text), model_type="pro")
                                                clean = resp.replace("```json", "").replace("```", "").strip()
                                                st.session_state[f'social_result_{p_dir}'] = json.loads(clean)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error: {e}")
                
                with col_del:
                    if st.button(f"🗑️ Eliminar ({len(pd_to_delete)})", type="primary", disabled=len(pd_to_delete)==0, key="btn_del_pd"):
                        for p in pd_to_delete:
                            shutil.rmtree(p)
                        st.toast(f"✅ {len(pd_to_delete)} podcasts eliminados.")
                        time.sleep(1); st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_especiales:
        try:
            ee_files = sorted(glob.glob("EE_*.mp3"), key=os.path.getctime, reverse=True)
            if not ee_files:
                st.info("No hay episodios especiales.")
            else:
                col_all, col_del = st.columns([4, 1])
                sel_all_ee = col_all.checkbox("Seleccionar todos (Especiales)", key="sel_all_ee")
                ee_to_delete = []

                for ee in ee_files:
                    col_chk, col_exp = st.columns([0.05, 0.95])
                    with col_chk:
                        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                        if st.checkbox(" ", value=sel_all_ee, key=f"del_chk_ee_{ee}"):
                            ee_to_delete.append(ee)
                    
                    with col_exp:
                        with st.expander(f"📢 {os.path.basename(ee)}"):
                            col_a, col_b = st.columns([3, 1])
                            col_a.audio(ee)
                            with col_b:
                                with open(ee, "rb") as f:
                                    st.download_button("⬇️ MP3", f, os.path.basename(ee), key=f"dl_ee_{ee}", use_container_width=True)

                with col_del:
                    if st.button(f"🗑️ Eliminar ({len(ee_to_delete)})", type="primary", disabled=len(ee_to_delete)==0, key="btn_del_ee"):
                        for ee in ee_to_delete:
                            os.remove(ee)
                        st.toast(f"✅ {len(ee_to_delete)} especiales eliminados.")
                        time.sleep(1); st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_od:
        try:
            od_files = sorted(glob.glob("OD_*.mp3"), key=os.path.getctime, reverse=True)
            if not od_files:
                st.info("No hay grabaciones a la carta.")
            else:
                col_all, col_del = st.columns([4, 1])
                sel_all_od = col_all.checkbox("Seleccionar todos (A la Carta)", key="sel_all_od")
                od_to_delete = []

                for od in od_files:
                    col_chk, col_exp = st.columns([0.05, 0.95])
                    with col_chk:
                        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                        if st.checkbox(" ", value=sel_all_od, key=f"del_chk_od_{od}"):
                            od_to_delete.append(od)

                    with col_exp:
                        with st.expander(f"🎙️ {os.path.basename(od)}"):
                            col_a, col_b = st.columns([3, 1])
                            col_a.audio(od)
                            with col_b:
                                with open(od, "rb") as f:
                                    st.download_button("⬇️ MP3", f, os.path.basename(od), key=f"dl_od_{od}", use_container_width=True)
                
                with col_del:
                    if st.button(f"🗑️ Eliminar ({len(od_to_delete)})", type="primary", disabled=len(od_to_delete)==0, key="btn_del_od"):
                        for od in od_to_delete:
                            os.remove(od)
                        st.toast(f"✅ {len(od_to_delete)} audios eliminados.")
                        time.sleep(1); st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")