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

st.set_page_config(page_title="PCC - Configuración", page_icon="⚙️", layout="wide")
inject_pcc_style()
init_session_state()
config = cargar_config()

st.markdown('<div class="pcc-page-title">⚙️ Configuración</div>', unsafe_allow_html=True)
    st.info("💡 **Sala de Máquinas.** Configura la identidad base, los enlaces de fuentes de noticias a escrapear, los modelos de voz, y personaliza las campañas publicitarias (CTAs).")
    tab_gen, tab_audio, tab_src, tab_ctas_p, tab_calendario = st.tabs(["🔧 General", "🎛️ Audio", "📡 Fuentes", "📢 CTAs", "🗓️ Calendario"])

    with tab_calendario:
        st.markdown('<div class="pcc-section-title">Calendario Anual de Oficios, Tradiciones y Costumbres</div>', unsafe_allow_html=True)
        st.info("💡 **Añade efemérides rurales.** Dorotea leerá este calendario cada mañana. Si la fecha actual coincide con un registro, lo integrará de forma educativa en su saludo inicial.")
        csv_path = "calendario_oficios.csv"
        
        if not os.path.exists(csv_path):
            st.warning("No se encontró `calendario_oficios.csv`. Se creará uno nuevo al guardar.")
            df_cal = pd.DataFrame(columns=["Fecha", "Oficio", "Explicacion"])
        else:
            df_cal = pd.read_csv(csv_path, dtype=str)
        
        # Ensure column order
        cols = ["Fecha", "Oficio", "Explicacion"]
        for c in cols:
            if c not in df_cal.columns:
                df_cal[c] = ""
        df_cal = df_cal[cols]
        
        st.caption("Formato de Fecha requerido: **DD-MM** (Ej: `06-03` para el 6 de marzo).")
        
        edited_df = st.data_editor(
            df_cal,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Fecha": st.column_config.TextColumn("Día-Mes (DD-MM)", required=True, max_chars=5),
                "Oficio": st.column_config.TextColumn("Oficio / Tradición", required=True),
                "Explicacion": st.column_config.TextColumn("Explicación Educativa", required=True)
            },
            key="calendar_editor"
        )
        
        if st.button("💾 Guardar Calendario", type="primary"):
            # Clean up empty rows
            edited_df.replace("", pd.NA, inplace=True)
            edited_df.dropna(how="all", inplace=True)
            edited_df.fillna("", inplace=True)
            
            # Simple validation
            valid_rows = []
            import re
            for idx, row in edited_df.iterrows():
                fecha_valida = re.match(r"^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])$", str(row["Fecha"]))
                if fecha_valida and row["Oficio"] and row["Explicacion"]:
                    valid_rows.append(row)
            
            final_df = pd.DataFrame(valid_rows, columns=cols)
            final_df.to_csv(csv_path, index=False)
            
            st.success(f"✅ Calendario guardado correctamente con {len(final_df)} entradas válidas.")
            time.sleep(1)
            st.rerun()

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
            new_min_block = st.number_input("Mín. noticias por bloque", value=int(config['generation_config'].get('min_news_per_block',2)))
        with c4:
            new_max_items    = st.slider("Máx. noticias", 5, 50, int(config['generation_config'].get('max_news_items',20)), 1)
            new_window_hours = st.slider("Ventana por defecto (h)", 6, 168, int(config['generation_config'].get('news_window_hours',48)), 6)

        if st.button("💾 Guardar Configuración General", type="primary"):
            config['podcast_info'].update({'presentadora':new_presentadora,'region':new_region,'email_contacto':new_email,'email_alias_ssml':new_email_alias})
            config['generation_config'].update({'feeds_file':new_feeds_file,'min_news_per_block':new_min_block,'max_news_items':new_max_items,'news_window_hours':new_window_hours})
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
        except: cur_vi = 8 # Default Laomedeia
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
                            guion = generar_texto_con_gemini(PromptsCreativos.generar_analisis_fuentes(analisis_str), model_type="pro")
                            clean = guion.replace("```txt","").replace("```","").strip()
                            ts = datetime.datetime.now().strftime("%d-%m-%y_%H-%M")
                            fname = f"EE_analisis_semanal - {ts}.txt"
                            with open(fname,"w",encoding="utf-8") as f: f.write(clean)
                            st.success(f"✅ {fname}"); st.text_area("Preview:", value=clean, height=300)
                        except Exception as e: st.error(f"Error: {e}")

    with tab_ctas_p:
        st.markdown('<div class="pcc-section-title">Opciones y Editor de CTAs</div>', unsafe_allow_html=True)
        st.info("Configura cómo Dorotea lee los anuncios o textos comerciales durante el programa.")
        
        ccta1, ccta2 = st.columns([1, 2])
        with ccta1:
            st.markdown("**Matriz: ¿Qué CTAs lee Dorotea (interpreta con IA)?**")
            st.caption("☑️ Dorotea lo reescribe e integra | ☐ Lo lee como anuncio literal (con cortinilla)")
            
            # Default matrix if not set
            default_matrix = {
                "lunes": {"inicio": True, "intermedio": True, "cierre": True},
                "martes": {"inicio": True, "intermedio": True, "cierre": True},
                "miercoles": {"inicio": True, "intermedio": True, "cierre": True},
                "jueves": {"inicio": True, "intermedio": True, "cierre": True},
                "viernes": {"inicio": True, "intermedio": True, "cierre": True},
                "fin de semana": {"inicio": True, "intermedio": True, "cierre": True},
                "generico": {"inicio": True, "intermedio": True, "cierre": True}
            }
            
            current_matrix = config['generation_config'].get('interpret_ctas_matrix', default_matrix)
            
            # Convert to Pandas DataFrame for data_editor
            df_matrix = pd.DataFrame.from_dict(current_matrix, orient='index')
            
            # Show interactive editor
            edited_df = st.data_editor(
                df_matrix,
                column_config={
                    "inicio": st.column_config.CheckboxColumn("Inicio", default=True),
                    "intermedio": st.column_config.CheckboxColumn("Intermedio", default=True),
                    "cierre": st.column_config.CheckboxColumn("Cierre", default=True)
                },
                use_container_width=True,
                hide_index=False
            )

            if st.button("💾 Guardar Matriz", type="primary"):
                # Convert back to dict and save
                config['generation_config']['interpret_ctas_matrix'] = edited_df.to_dict(orient='index')
                guardar_config(config); st.success("✅ Matriz guardada."); time.sleep(0.5); st.rerun()

        st.markdown("---")
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
                    new_c = st.text_area(f"Editando `{sel}`", value=content, height=250)
                    if st.button("💾 Sobrescribir Archivo"):
                        with open(path_f,"w",encoding="utf-8") as f: f.write(new_c)
                        st.success("✅ Guardado."); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Error: {e}")