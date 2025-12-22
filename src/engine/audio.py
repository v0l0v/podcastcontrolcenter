import os
import io
import sys
import json
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize
from google.cloud import texttospeech
from src.config.settings import TARGET_LUFS, LANGUAGE_CODE, SAMPLE_RATE, VOICE_NAME
from src.core.text_processing import (
    preprocesar_texto_para_tts, 
    limpiar_markdown_audio, 
    corregir_palabras_deletreadas_tts, 
    corregir_numeros_con_puntos_tts, 
    convertir_ssml_a_texto_plano,
    corregir_mayusculas_tts,
    corregir_decimales_con_coma_tts
)
from src.llm_utils import retry_on_failure

# --- LIBRARIES OPCIONALES ---
try:
    import pyloudnorm as pyln
    LOUDNORM_AVAILABLE = True
except ImportError:
    LOUDNORM_AVAILABLE = False
    print("⚠️ PyLoudnorm no disponible. Usando normalización básica.")

# --- CLIENTE TTS ---
_tts_client = None

def get_tts_client():
    global _tts_client
    if _tts_client:
        return _tts_client
    
    gcp_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not gcp_credentials_path:
        print("Fallo: La variable de entorno 'GOOGLE_APPLICATION_CREDENTIALS' no está configurada.")
        # No salimos aquí para no romper import, pero fallará al usar
        return None
        
    try:
        _tts_client = texttospeech.TextToSpeechClient.from_service_account_file(gcp_credentials_path)
        return _tts_client
    except Exception as e:
        print(f"Error al inicializar cliente TTS: {e}")
        return None

# =================================================================================
# MASTERIZACIÓN Y AUDIO
# =================================================================================

def masterizar_a_lufs(audio_segment: AudioSegment, target_lufs: float = TARGET_LUFS) -> AudioSegment:
    if not LOUDNORM_AVAILABLE:
        print(f"      📻 Usando normalización básica (PyLoudnorm no disponible)")
        return normalize(audio_segment)
    try:
        audio_data = np.array(audio_segment.get_array_of_samples())
        if audio_segment.channels == 2:
            audio_data = audio_data.reshape((-1, 2))
        if audio_segment.sample_width == 2:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_segment.sample_width == 4:
            audio_data = audio_data.astype(np.float32) / 2147483648.0
        
        meter = pyln.Meter(audio_segment.frame_rate)
        loudness = meter.integrated_loudness(audio_data)
        audio_normalized = pyln.normalize.loudness(audio_data, loudness, target_lufs)
        
        # --- PEAK LIMITER (Seguridad anti-distorsión) ---
        max_peak = np.max(np.abs(audio_normalized))
        target_peak_linear = 0.9  # -1.0 dBFS aprox de seguridad
        
        if max_peak > target_peak_linear:
            normalization_factor = target_peak_linear / max_peak
            audio_normalized = audio_normalized * normalization_factor
            print(f"      🛡️ Limiter activado: Reduciendo ganancia en {(20 * np.log10(normalization_factor)):.2f} dB para evitar clipping.")

        if audio_segment.sample_width == 2:
            audio_int = (audio_normalized * 32767).astype(np.int16)
        else:
            audio_int = (audio_normalized * 2147483647).astype(np.int32)
        if audio_segment.channels == 2:
            audio_int = audio_int.flatten()
            
        masterized_audio = AudioSegment(
            audio_int.tobytes(),
            frame_rate=audio_segment.frame_rate,
            sample_width=audio_segment.sample_width,
            channels=audio_segment.channels
        )
        print(f"      🎛️ Audio masterizado a {target_lufs} LUFS (loudness original: {loudness:.1f} LUFS)")
        return masterized_audio
    except Exception as e:
        print(f"      ⚠️ Error en masterización LUFS: {e}. Usando normalización básica.")
        return normalize(audio_segment)

@retry_on_failure(retries=3, delay=3, backoff=2)
def sintetizar_ssml_a_audio(ssml: str, voz: str = VOICE_NAME) -> AudioSegment:
    client = get_tts_client()
    if not client:
        raise RuntimeError("Cliente TTS no inicializado.")

    ssml_corregido = preprocesar_texto_para_tts(ssml)
    ssml_corregido = limpiar_markdown_audio(ssml_corregido)
    ssml_corregido = corregir_palabras_deletreadas_tts(ssml_corregido)
    ssml_corregido = corregir_mayusculas_tts(ssml_corregido)
    ssml_corregido = corregir_numeros_con_puntos_tts(ssml_corregido)
    ssml_corregido = corregir_decimales_con_coma_tts(ssml_corregido)
    
    if ssml_corregido != ssml:
        # print(f"      ✅ Texto preprocesado para pronunciación.") # Verbose off? 
        pass
    
    try:
        if "Journey" in voz or "Chirp" in voz:
            texto_plano = convertir_ssml_a_texto_plano(ssml_corregido)
            print(f"      ℹ️ Voz Generativa ({voz}) detectada. Limpiando SSML a texto plano...")
            input_text = texttospeech.SynthesisInput(text=texto_plano)
        else:
            input_text = texttospeech.SynthesisInput(ssml=ssml_corregido)
            
        nombre_voz_limpio = voz.split(" [")[0].strip()

        voice = texttospeech.VoiceSelectionParams(
            language_code=LANGUAGE_CODE,
            name=nombre_voz_limpio,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            sample_rate_hertz=SAMPLE_RATE,
            speaking_rate=0.89
        )
        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )
        audio_segment = AudioSegment.from_file(io.BytesIO(response.audio_content), format="mp3")
        print(f"      Volumen generado ({'Texto' if 'Journey' in voz else 'SSML'}): {audio_segment.max_dBFS:.2f} dBFS")
        return audio_segment
    except Exception as e:
        raise e
