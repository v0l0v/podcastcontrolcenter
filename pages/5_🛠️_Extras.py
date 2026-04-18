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

st.set_page_config(page_title="PCC - Extras", page_icon="🛠️", layout="wide")
inject_pcc_style()
init_session_state()
config = cargar_config()

st.markdown('<div class="pcc-page-title">🛠️ Extras</div>', unsafe_allow_html=True)
    tab_ee, tab_od, tab_buzon, tab_logs = st.tabs(["🧩 Episodios Especiales", "🎙️ A la Carta", "🗣️ Buzón del Oyente", "📊 Costes y Antiguos Logs"])

    with tab_ee:
        st.markdown('<div class="pcc-section-title">Creador de Episodios Especiales</div>', unsafe_allow_html=True)
        st.info("💡 **Diferencia Clave:** Aquí tú escribes literalmente qué debe decir Dorotea (palabra por palabra). En *A la carta*, la IA se inventa el guion.")
        
        with st.expander("📖 ¿Cómo formatear el guion? (Trucos y Etiquetas)"):
            st.markdown("""
            Dorotea leerá todo lo que empieces con `DOROTEA:`. Si pones solo tu texto, también lo leerá.
            
            Puedes usar **Etiquetas Sonoras** en el texto para enriquecer la locución:
            - `[ENTRE_BLOQUES]` - Pausa estándar.
            - `[CORTINILLA_TRANSICION_CORTA]` - Ráfaga sonora rápida.
            - `[CORTINILLA_TRANSICION_LARGA]` - Música de transición con más cuerpo.
            - `[CORTINILLA_CIERRE_BLOQUE]` - Ideal para terminar un tema rotundo.
            - `[CORTINILLA_PREGUNTA]` - Para dar paso al buzón del oyente.
            - `[CORTINILLA_TESTIMONIO]` - Para acompañar historias o anécdotas.
            
            *Ejemplo:*
            DOROTEA: Hola y bienvenidos a este especial sobre tecnología. [CORTINILLA_TRANSICION_CORTA] Hoy hablaremos del futuro de la IA.
            """)
            
        col_new1, col_new2 = st.columns([3, 1])
        with col_new1:
            ee_title = st.text_input("Título del Episodio (sin espacios raros)", placeholder="Ej: Especial Startups")
            ee_content = st.text_area("Cuerpo del Guion", height=200, placeholder="DOROTEA: Hola, bienvenidos a...")
        with col_new2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("🚀 Crear y Generar MP3", type="primary", use_container_width=True):
                if not ee_title or not ee_content:
                    st.error("Debes dar un título y escribir un guion.")
                else:
                    safe_title = "".join([c for c in ee_title if c.isalnum() or c in ' _-']).strip().replace(" ", "_")
                    filename = f"EE_{safe_title}.txt"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(ee_content)
                    st.success(f"Guion {filename} guardado. Empezando generación...")
                    
                    with st.spinner("Procesando episodio especial (esto puede tardar unos minutos)..."):
                        cmd = [sys.executable, "dorototal.py", "--only-special", "--file-list", filename]
                        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                        if proc.returncode == 0:
                            st.success("✅ ¡Episodio Generado Exitosamente!")
                            st.balloons()
                            with st.expander("Ver Log Interno"):
                                st.code(proc.stdout)
                            time.sleep(3); st.rerun()
                        else:
                            st.error("❌ Ocurrió un error en la generación.")
                            with st.expander("Ver Detalles Lados del Error"):
                                st.code(proc.stderr)

        st.markdown('---')
        st.markdown("### 📂 Inventario de Guiones Especiales Pendientes")
        ee_scripts = sorted(glob.glob("EE_*.txt"))
        if not ee_scripts:
            st.caption("No hay ficheros `EE_*.txt` pendientes por renderizar en esta carpeta.")
        else:
            for ev in ee_scripts:
                col_sel1, col_sel2, col_del1 = st.columns([1, 4, 1])
                with col_sel1:
                    if st.button("▶️ Renderizar MP3", key=f"ee_run_{ev}"):
                        with st.spinner(f"Renderizando {ev}..."):
                            cmd = [sys.executable, "dorototal.py", "--only-special", "--file-list", ev]
                            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                            if proc.returncode == 0:
                                st.success(f"✅ Terminado: {ev}")
                            else:
                                st.error(f"Fallo en: {ev}")
                                st.code(proc.stderr)
                with col_sel2:
                    st.write(f"📄 **{ev}**")
                with col_del1:
                    if st.button("🗑️ Borrar", key=f"ee_del_{ev}"):
                        os.remove(ev)
                        st.rerun()

    with tab_od:
        st.markdown('<div class="pcc-section-title">Generador A La Carta</div>', unsafe_allow_html=True)
        st.info("💡 **Diferencia Clave:** A diferencia de los 'Especiales', aquí tú solo le das el tema y la IA se inventa el guion entero creativamente para Dorotea.")
        col_i,col_o = st.columns([2,1])
        with col_i:
            topic_od = st.text_area("¿Sobre qué quieres que hable Dorotea?", placeholder="Ej: Explica cómo funciona un agujero negro a un niño de 5 años...", height=150)
        with col_o:
            modo_od = st.radio("Modo de Generación", ["Resumen a medida", "Guion Fiel (íntegro)"])
            dur_od = st.slider("Duración (min)", 1, 5, 2, 1, disabled=(modo_od == "Guion Fiel (íntegro)"))
            if modo_od == "Resumen a medida":
                st.caption(f"≈ {dur_od*150} palabras")
            else:
                st.caption("Sin límite de palabras.")
            style_od = st.selectbox("Tono", ["Normal (Dorotea)","Muy Alegre","Serio/Intenso","Susurro/Cómplice"])
        if st.button("🎙️ GENERAR GUION + AUDIO", type="primary"):
            if not topic_od: st.error("Escribe un tema.")
            else:
                with st.spinner("Generando creatividad y sintetizando..."):
                    try:
                        tone_map = {"Muy Alegre":"Muy enérgico y alegre.","Serio/Intenso":"Sobrio y periodístico.","Susurro/Cómplice":"Cercano, secreto."}
                        tone = tone_map.get(style_od,"")
                        
                        regla_longitud = f"{dur_od*150} palabras."
                        if modo_od == "Guion Fiel (íntegro)":
                            regla_longitud = "REGLA DE LONGITUD: NO RESUMAS. Transforma y transcribe el contenido íntegro del texto proporcionado, manteniendo todos los puntos, ideas y diálogos (en formato adaptado), sin importar la longitud final. Todo el contenido original debe estar presente."
                            
                        script = generar_texto_con_gemini(f'Eres Dorotea. Guion sobre "{topic_od}". {regla_longitud} {tone} TEXTO PLANO. REGLA OBLIGATORIA: Si el tema incluye un diálogo o entrevista, ignora TODAS las marcas de tiempo (ej. [00:00:00]) y NO leas los nombres de los interlocutores. Transforma el texto en una narración fluida o una conversación natural sin anunciar al hablante cada vez. GUION:', model_type="pro")
                        if not script: st.error("Error generando guion.")
                        else:
                            with st.expander("Revisar lo que IA ha escrito (Guion)"): st.write(script)
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
        st.markdown('<div class="pcc-section-title">Buzón del Oyente</div>', unsafe_allow_html=True)
        st.info("📥 **¿Cómo funciona esto en tu Podcast Principal?**\nEl texto plano o las transcripciones guardadas en el archivo `preguntas_audiencia.txt` (es tu buzón principal) son revisadas por Dorotea durante la **generación del Podcast Diario**. Ella automáticamente creará su respuesta en voz alta integrándola dentro del noticiero de ese día. Esto de abajo son herramientas satélite.")
        
        c_bz1, c_bz2 = st.columns([1,1])
        with c_bz1:
            st.markdown("#### 1. Gestionar Buzón de Texto")
            st.write("Mira o edita lo que Dorotea tiene pendiente de leer del público:")
            tf_path = "preguntas_audiencia.txt"
            if not os.path.exists(tf_path):
                open(tf_path, "w").close()
            with open(tf_path, "r", encoding="utf-8") as file:
                current_buzon = file.read()
            # To fix the unbound layout var issue with form submission
            with st.form("edit_buzon_form"):
                new_buzon = st.text_area("Contenido actual de reservas:", value=current_buzon, height=200)
                sub_buzon = st.form_submit_button("💾 Guardar Cambios Manuales")
                if sub_buzon:
                    with open(tf_path, "w", encoding="utf-8") as file:
                        file.write(new_buzon)
                    st.success("Buzón actualizado exitosamente.")
                    time.sleep(1); st.rerun()

        with c_bz2:
            st.markdown("#### 2. Transcripción Mágica de Audio")
            st.write("Sube el audio de un usuario, la IA lo procesará y dejará la constancia en el buzón automáticamente.")
            uploaded = st.file_uploader("Sube tú .mp3, .wav o .m4a del oyente", type=["mp3","wav","m4a","ogg"])
            # La interacción on the fly que devolvía la respuesta de forma estéril ya no es la preasignada, 
            # ahora lo manda a la db plana y un día lo saldará en bloque. (Aunque mantenemos la demo instantanea)
            demo_instant = st.checkbox("Generar ahora mismo un audio-respuesta de prueba de Dorotea", value=False)
            
            if uploaded and st.button("🎙️ Extraer y Procesar", type="primary"):
                with st.status("Analizando audio...", expanded=True) as status:
                    try:
                        temp_f = f"temp_listener_{int(time.time())}_{uploaded.name}"
                        with open(temp_f,"wb") as f: f.write(uploaded.getbuffer())
                        mime = uploaded.type
                        if mime=="audio/mpeg": mime="audio/mp3"
                        from mcmcn_prompts import ConfiguracionPodcast
                        aj = generar_texto_multimodal_audio_con_gemini(ConfiguracionPodcast.PROMPT_ANALISIS_AUDIO_OYENTE, uploaded.getvalue(), mime_type=mime)
                        aj = aj.replace("```json","").replace("```","").strip()
                        datos = {}
                        if "{" in aj:
                            try: s,e2=aj.find('{'),aj.rfind('}'); datos=json.loads(aj[s:e2+1])
                            except: pass
                        nombre=datos.get("nombre_oyente","Un oyente")
                        tema=datos.get("tema_principal","su mensaje")
                        
                        st.write(f"✅ Reconocido a: **{nombre}**")
                        
                        # Escribir en la central
                        nueva_entrada = f"\n\nMensaje escrito o de voz transcrito de:\nOyente: {nombre}\nTema Base/Mensaje Original: {tema}\n"
                        with open(tf_path, "a", encoding="utf-8") as f:
                            f.write(nueva_entrada)
                        st.toast("📧 Transcripción enrutada al buzón del oyente principal.")
                        
                        if demo_instant:
                            st.write("✍️ Redactando audio paralelo en el acto...")
                            guion = generar_texto_con_gemini(ConfiguracionPodcast.PROMPT_RESPUESTA_OYENTE.format(nombre_oyente=nombre,tema_principal=tema), model_type="pro")
                            if "INTRO:" in guion and "REACCION:" in guion:
                                partes=guion.split("REACCION:"); intro_txt=partes[0].replace("INTRO:","").strip(); reac_txt=partes[1].strip()
                            else: intro_txt=f"Escuchamos ahora a {nombre}."; reac_txt=guion
                            ai=sintetizar_ssml_a_audio(f"<speak>{intro_txt}</speak>"); ar=sintetizar_ssml_a_audio(f"<speak>{reac_txt}</speak>")
                            ls=masterizar_a_lufs(AudioSegment.from_file(temp_f),-16.0)
                            try:
                                tf=glob.glob("audio_assets/clickrozalen*.mp3"); ta=AudioSegment.silent(1000)
                                if tf: t=AudioSegment.from_file(random.choice(tf)); ta=(t[:6000].fade_out(2000) if len(t)>6000 else t)
                            except: ta=AudioSegment.silent(1000)
                            mix=AudioSegment.silent(500)
                            if ai: mix+=ai
                            mix+=ta.fade_in(500).fade_out(500)+ls+ta.fade_in(500).fade_out(500)
                            if ar: mix+=ar
                            ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); out_f=f"RESPUESTA_{nombre.replace(' ','_')}_{ts}.mp3"
                            mix.export(out_f,format="mp3",bitrate="192k")
                            st.success("¡Prueba instantánea generada!"); st.audio(out_f)
                            
                        # Limpiar y mover si existe dir original (recurso viejo)
                        if os.path.isdir("buzon_del_oyente"): shutil.copy(temp_f,os.path.join("buzon_del_oyente",uploaded.name))
                        os.remove(temp_f); status.update(label="✅ Finalizado con Éxito",state="complete",expanded=False)
                    except Exception as e: st.error(f"Error: {e}"); import traceback; st.code(traceback.format_exc())

    with tab_logs:
        st.markdown('<div class="pcc-section-title">Estimación de Costes IA / Google Cloud</div>', unsafe_allow_html=True)
        try:
            uf="logs/usage_stats.json"
            if os.path.exists(uf):
                stats=json.load(open(uf))
                colg1, colg2 = st.columns(2)
                with colg1:
                    gi=stats.get('gemini_input_tokens',0); go=stats.get('gemini_output_tokens',0); gt=gi+go; gl=1_000_000
                    st.write("**Gemini Flash (LLM)**"); st.progress(min(1.0,gt/gl)); st.caption(f"{gt:,}/{gl:,} tokens limit/m ({min(100,round(gt/gl*100))}%)")
                with colg2:
                    tts=stats.get('tts_chars',0); tl=1_000_000
                    st.write("**Google TTS (Voz)**"); st.progress(min(1.0,tts/tl)); st.caption(f"{tts:,}/{tl:,} chars limit/m ({min(100,round(tts/tl*100))}%)")
            else: st.info("No hay datos de consumo todavía.")
        except Exception as e: st.error(f"Error leyendo el tracking json: {e}")
        
        st.markdown('<br><hr><div class="pcc-section-title" style="opacity:0.6;">Vista de Log Original</div>', unsafe_allow_html=True)
        st.caption("Nota: Para monitorización amigable de errores del ciclo actual, ve a la pestaña `📋 Logs` del menú principal izquierdo.")
        if st.checkbox("Mostrar Consola antigua de Logs de Sistema JSONL"):
            try:
                lf = "logs/process_log.jsonl"
                if os.path.exists(lf):
                    lines = open(lf).readlines()
                    disp=[]
                    icon_map={"STEP":"🔹","SUCCESS":"✅","WARNING":"⚠️","ERROR":"❌","INFO":"ℹ️"}
                    for l in lines[-40:]:
                        try: e=json.loads(l); ts=e['timestamp'].split('T')[1].split('.')[0]; disp.append(f"{ts} {icon_map.get(e['level'],'')} {e['message']}")
                        except: pass
                    st.code("\n".join(disp), language="text")
                else: st.info("No hay registro puro disponible.")
            except Exception as e: st.error(f"Error parseando JSONL: {e}")