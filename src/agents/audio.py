import os
import json
import random
import re
import html
import gc
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pydub import AudioSegment

from src.agents.base import BaseAgent
from src.config.settings import AUDIO_ASSETS_DIR, TARGET_LUFS, AUDIO_CACHE_DIR, VOICE_NAME
from src.utils.caching import calculate_hash, get_cached_content, cache_content
from src.core.text_processing import limpiar_artefactos_ia, convertir_ssml_a_texto_plano
from src.engine.audio import sintetizar_ssml_a_audio, masterizar_a_lufs
from src.llm_utils import generar_texto_con_gemini, generar_texto_multimodal_audio_con_gemini
from src.monitoring import logger
import mcmcn_prompts

from dorototal import (
    debe_interpretar_cta,
    _get_cta_text
)


class AudioAgent(BaseAgent):
    """
    Agente encargado de la Fase 3/4:
    Sintetizar crónicas a audio, añadir música de transición,
    procesar audios de oyentes/programados y ensamblar el podcast final.
    """
    def __init__(self, name: str = "AudioAgent"):
        super().__init__(name=name)
        self.transiciones = {'positivo': {}, 'negativo': {}, 'neutro': {}}
        self.SEGMENT_DURATION_MS = 10000
        self.FADE_DURATION_MS = 2000
        self._cargar_transiciones()

    def _cargar_transiciones(self):
        pool_universal = {}
        import glob
        patron_busqueda = "clickrozalen*.mp3"
        ruta_busqueda = os.path.join(AUDIO_ASSETS_DIR, patron_busqueda)
        files = glob.glob(ruta_busqueda)

        for f in files:
            try:
                audio = AudioSegment.from_file(f)
                if len(audio) > 0:
                    pool_universal[f] = audio
            except Exception:
                pass

        if pool_universal:
            self.transiciones['positivo'] = pool_universal
            self.transiciones['negativo'] = pool_universal
            self.transiciones['neutro'] = pool_universal

    def _agregar_transicion(self, sentimiento: str = 'neutro') -> AudioSegment:
        pool_sentimiento = self.transiciones.get(sentimiento, self.transiciones.get('neutro', {}))
        if not pool_sentimiento: return AudioSegment.silent(duration=1000)

        path = random.choice(list(pool_sentimiento.keys()))
        audio = pool_sentimiento[path]

        if len(audio) < self.SEGMENT_DURATION_MS:
            return audio.fade_in(self.FADE_DURATION_MS).fade_out(self.FADE_DURATION_MS)

        max_start = len(audio) - self.SEGMENT_DURATION_MS
        best_segment = None
        best_dbfs = -float('inf')

        for _ in range(10):
            start = random.randint(0, max_start)
            segmento = audio[start:start+self.SEGMENT_DURATION_MS]
            if segmento.dBFS > -30:
                return segmento.fade_in(self.FADE_DURATION_MS).fade_out(self.FADE_DURATION_MS)
            if segmento.dBFS > best_dbfs:
                best_dbfs = segmento.dBFS
                best_segment = segmento
        return best_segment.fade_in(self.FADE_DURATION_MS).fade_out(self.FADE_DURATION_MS)

    def _sintetizar_con_cache_estructural(self, texto: str) -> AudioSegment:
        if not texto: return None
        unique_key = f"{texto}_{VOICE_NAME}"
        key_hash = calculate_hash(unique_key)

        os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
        audio_path = os.path.join(AUDIO_CACHE_DIR, f"struct_{key_hash}.mp3")

        if os.path.exists(audio_path):
            try: return AudioSegment.from_file(audio_path)
            except Exception: pass

        audio = sintetizar_ssml_a_audio(f"<speak>{html.escape(texto)}</speak>")
        if audio:
            try: audio.export(audio_path, format="mp3")
            except Exception: pass
        return audio

    def _generar_y_cachear_audio_noticia(self, noticia: dict, fecha_actual_str: str) -> Tuple[AudioSegment | None, str]:
        noticia_id = noticia.get('id', 'unknown')
        if noticia_id == 'unknown':
            noticia_id = calculate_hash(noticia.get('resumen', ''))

        os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
        audio_file_path = os.path.join(AUDIO_CACHE_DIR, f"news_{noticia_id}.mp3")
        text_file_path = os.path.join(AUDIO_CACHE_DIR, f"news_{noticia_id}.txt")

        if os.path.exists(audio_file_path):
            try:
                audio = AudioSegment.from_file(audio_file_path, format="mp3")
                texto = ""
                if os.path.exists(text_file_path):
                    with open(text_file_path, 'r', encoding='utf-8') as f:
                        texto = f.read()
                return audio, texto
            except Exception: pass

        # fallback simple if no text generation agent used
        texto_narracion = noticia.get('resumen', '')
        texto_narracion_escapado = html.escape(texto_narracion)
        frases = re.split('([.?!])', texto_narracion_escapado)
        frases_completas = [frases[i] + (frases[i+1] if i+1 < len(frases) else '') for i in range(0, len(frases), 2)]

        texto_narracion_ssml = ""
        for frase in frases_completas:
            if frase.strip():
                rate = f"{random.uniform(0.98, 1.02):.2f}"
                texto_narracion_ssml += f'<prosody rate="{rate}">{frase.strip()}</prosody><break time="450ms"/>'

        audio_generado = sintetizar_ssml_a_audio(f"<speak>{texto_narracion_ssml}</speak>")
        if audio_generado:
            try:
                audio_generado.export(audio_file_path, format="mp3")
                with open(text_file_path, 'w', encoding='utf-8') as f:
                    f.write(texto_narracion)
                return audio_generado, texto_narracion
            except Exception: pass
        return None, ""

    def execute(self, script_data: Dict[str, Any], output_path: str, timestamp: str) -> Tuple[str, List[Dict[str, Any]]]:
        print("\n--- FASE 3: Sintetizando audios ---")
        segmentos_audio = []
        transcript_data = []

        # 1. Intro
        texto_intro = script_data.get('texto_intro', '')
        if texto_intro:
            ruta_sintonia_inicio = os.path.join(AUDIO_ASSETS_DIR, "inicio.mp3")
            if os.path.exists(ruta_sintonia_inicio):
                segmentos_audio.append(AudioSegment.from_file(ruta_sintonia_inicio))

            audio_intro = self._sintetizar_con_cache_estructural(texto_intro)
            if audio_intro:
                segmentos_audio.append(audio_intro)
                transcript_data.append({'type': 'intro', 'content': texto_intro})

            segmentos_audio.append(self._agregar_transicion())

        # 2. Bloques
        for bloque in script_data.get('bloques_narrados', []):
            texto_bloque = bloque.get('texto_narrado')
            if texto_bloque:
                audio_bloque = self._sintetizar_con_cache_estructural(texto_bloque)
                if audio_bloque:
                    segmentos_audio.append(audio_bloque)
                    segmentos_audio.append(self._agregar_transicion())
                    transcript_data.append({
                        'type': 'block',
                        'title': bloque.get('tema', 'Tema'),
                        'content': texto_bloque
                    })

        # 3. Individuales
        for noticia in script_data.get('noticias_individuales', []):
             audio_noticia, _ = self._generar_y_cachear_audio_noticia(noticia, datetime.now().strftime("%Y-%m-%d"))
             if audio_noticia:
                 segmentos_audio.append(audio_noticia)
                 segmentos_audio.append(self._agregar_transicion())
                 transcript_data.append({
                     'type': 'block',
                     'title': noticia.get('titulo', 'Noticia'),
                     'content': noticia.get('resumen', '')
                 })

        # 4. Outro (Generación Simple por ahora, en refactor futuro puede ir en Writer)
        print("\n--- FASE 4: Montaje Final ---")
        podcast_final = AudioSegment.silent(duration=500)

        duracion_total_seg = sum(len(s) for s in segmentos_audio if s) / 1000
        if duracion_total_seg < 1200:
            for segmento in segmentos_audio:
                if segmento: podcast_final += segmento
        else:
            BATCH_SIZE = 8
            for i in range(0, len(segmentos_audio), BATCH_SIZE):
                for segmento in segmentos_audio[i:i + BATCH_SIZE]:
                    if segmento: podcast_final += segmento
                if (i // BATCH_SIZE) % 3 == 0: gc.collect()

        podcast_masterizado = masterizar_a_lufs(podcast_final, TARGET_LUFS)
        podcast_masterizado.export(output_path, format="mp3")

        return output_path, transcript_data
