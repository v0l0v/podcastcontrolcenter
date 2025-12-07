import os
import io
import re
import html
import random
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize
from google.cloud import texttospeech
from src.utils import cargar_configuracion, retry_on_failure, limpiar_artefactos_ia

# --- CONFIGURACIÓN ---
CONFIG = cargar_configuracion()
AUDIO_CONFIG = CONFIG.get('audio_config', {})
VOICE_NAME = AUDIO_CONFIG.get('voice_name', "es-ES-Journey-F")
SAMPLE_RATE = 44100

# PyLoudnorm opcional
try:
    import pyloudnorm as pyln
    LOUDNORM_AVAILABLE = True
except ImportError:
    LOUDNORM_AVAILABLE = False

# Cliente TTS
try:
    tts_client = texttospeech.TextToSpeechClient()
except:
    tts_client = None
    print("⚠️ Cliente TTS no inicializado. Verifica credenciales.")

def masterizar_audio(segment: AudioSegment, target_lufs: float = -16.0) -> AudioSegment:
    if not LOUDNORM_AVAILABLE:
        return normalize(segment)
    
    try:
        # Conversión a numpy para pyloudnorm
        samples = np.array(segment.get_array_of_samples())
        if segment.channels == 2:
            samples = samples.reshape((-1, 2))
        
        # Normalizar a float -1..1
        if segment.sample_width == 2: # 16-bit
            samples = samples.astype(np.float32) / 32768.0
        elif segment.sample_width == 4: # 32-bit
            samples = samples.astype(np.float32) / 2147483648.0
            
        meter = pyln.Meter(segment.frame_rate)
        loudness = meter.integrated_loudness(samples)
        
        normalized = pyln.normalize.loudness(samples, loudness, target_lufs)
        
        # Volver a PCM
        if segment.sample_width == 2:
            audio_int = (normalized * 32767).astype(np.int16)
        else:
            audio_int = (normalized * 2147483647).astype(np.int32)
            
        if segment.channels == 2:
            audio_int = audio_int.flatten()
            
        return AudioSegment(
            audio_int.tobytes(),
            frame_rate=segment.frame_rate,
            sample_width=segment.sample_width,
            channels=segment.channels
        )
    except Exception as e:
        print(f"⚠️ Error masterizando: {e}")
        return normalize(segment)

@retry_on_failure()
def generar_tts(texto: str, voz: str = VOICE_NAME) -> AudioSegment:
    if not tts_client: return None
    
    # Preprocesamiento básico
    texto = limpiar_artefactos_ia(texto)
    
    # Lógica Journey (No SSML) vs Standard (SSML)
    is_journey = "Journey" in voz
    
    if is_journey:
        # Eliminar tags SSML si existen
        texto_plano = re.sub(r'<[^>]+>', '', texto)
        input_text = texttospeech.SynthesisInput(text=texto_plano)
    else:
        # Envolver en speak si no lo está
        if not texto.strip().startswith("<speak>"):
            texto = f"<speak>{html.escape(texto)}</speak>"
        input_text = texttospeech.SynthesisInput(ssml=texto)
        
    voice_params = texttospeech.VoiceSelectionParams(
        language_code="es-ES",
        name=voz
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        sample_rate_hertz=SAMPLE_RATE
    )
    
    response = tts_client.synthesize_speech(
        request={"input": input_text, "voice": voice_params, "audio_config": audio_config}
    )
    
    return AudioSegment.from_file(io.BytesIO(response.audio_content), format="mp3")

def mezclar_con_fondo(voz: AudioSegment, fondo_path: str, ducking_db: int = -10) -> AudioSegment:
    if not os.path.exists(fondo_path):
        return voz
    
    fondo = AudioSegment.from_file(fondo_path)
    # Loop fondo si es más corto
    while len(fondo) < len(voz) + 2000:
        fondo += fondo
        
    # Recortar fondo
    fondo = fondo[:len(voz) + 2000]
    
    # Aplicar ducking (bajar volumen del fondo)
    fondo = fondo - abs(ducking_db)
    
    # Mezclar (overlay)
    mezcla = fondo.overlay(voz, position=1000) # Voz empieza al segundo 1
    
    return mezcla
