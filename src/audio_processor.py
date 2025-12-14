
import os
import re
from google.cloud import texttospeech
import json
import logging
from pydub import AudioSegment


# Obtener rutas absolutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'podcast_config.json')
AUDIO_ASSETS_DIR = os.path.join(BASE_DIR, 'audio_assets')

# Cargar configuración
def cargar_configuracion():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Eliminar constantes globales que cachean la configuración
# CONFIG = cargar_configuracion()
# AUDIO_CONFIG = CONFIG.get('audio_config', {})
# VOICE_NAME = AUDIO_CONFIG.get('voice_name', "es-ES-Studio-C")
# VOICE_PARAMS = {"language_code": "es-ES", "name": VOICE_NAME}
# AUDIO_ENCODING = texttospeech.AudioEncoding.MP3

def get_voice_params():
    """Carga la configuración actual de voz."""
    config = cargar_configuracion()
    audio_config = config.get('audio_config', {})
    voice_name = audio_config.get('voice_name', "es-ES-Chirp3-HD-Sulafat")
    return {"language_code": "es-ES", "name": voice_name}

def generar_audio_base_tts(texto_ssml: str, client: texttospeech.TextToSpeechClient) -> bytes:
    """Genera audio crudo desde SSML usando GCP TTS."""
    synthesis_input = texttospeech.SynthesisInput(ssml=texto_ssml)
    
    # Cargar parámetros frescos
    voice_params = get_voice_params()
    voice = texttospeech.VoiceSelectionParams(**voice_params)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content

def text_to_ssml(text: str) -> str:
    """Envuelve texto plano en SSML básico si no lo tiene."""
    if not text.strip().startswith("<speak>"):
        return f"<speak>{text}</speak>"
    return text

def parse_guion(guion_text: str) -> list:
    """
    Parsea el guion en una lista de segmentos.
    Tipos de segmentos:
    - {'type': 'speech', 'content': 'Texto a leer...'}
    - {'type': 'sound', 'file': 'nombre_archivo.mp3'}
    - {'type': 'transition', 'file': '...'}
    """
    segments = []
    lines = guion_text.splitlines()
    buffer_text = []

    # Mapa de etiquetas a archivos reales (basado en lo que vi en audio_assets)
    # Como no sé exactamente qué es cada 'clickrozalen...', usaré algunos genéricos o los mapearé
    # a archivos concretos si el usuario los define. 
    # Por ahora usaré 'cortinilla_cta.mp3' como comodín para cortinillas desconocidas
    # e 'inicio.mp3' para inicio. 'cierre.mp3' para cierre.
    
    SOUND_MAP = {
        "CORTINILLA_SINTONIA_INICIO": "inicio.mp3",
        "CORTINILLA_TRANSICION_CORTA": "bip002.mp3",
        "CORTINILLA_TRANSICIÓN_CORTA": "bip002.mp3", # Alias con tilde
        "CORTINILLA_SINTONIA_CIERRE": "cierre.mp3",
        "CORTINILLA_CIERRE": "cierre.mp3", # Alias
    }

    current_speaker = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detectar etiquetas de sonido [TAG]
        # Regex más permisiva: acepta CUALQUIER COSA entre corchetes
        tag_match = re.match(r'^\s*\[([^]]+)\]\s*$', line)
        if tag_match:
            # Si había texto acumulado, guardarlo como segmento de habla
            if buffer_text:
                segments.append({'type': 'speech', 'content': "\n".join(buffer_text)})
                buffer_text = []
            
            tag_name = tag_match.group(1)
            # Buscar archivo mapeado o usar default
            filename = SOUND_MAP.get(tag_name, "cortinilla_cta.mp3") 
            segments.append({'type': 'sound', 'file': filename})
            continue

        # Detectar narrador (DOROTEA:)
        # Permisivo con espacios al final
        speaker_match = re.match(r'^\s*([A-ZÁÉÍÓÚÑ]+)\s*:\s*$', line)
        if speaker_match:
            # Solo informativo por ahora, no cambia la voz
            continue
            
        # Saltarse anotaciones de dirección (Texto entre paréntesis)
        # Regex: Empieza por (, tiene algo, termina por ) y puede tener cualquier basura después.
        # Esto cubre casos como "(Risas)." o "(Música) ..." 
        # Evita falsos positivos como "(1) Primero..." si nos aseguramos que cierra cerca del final?
        # Para direcciones de guion, solemos asumir que TODA la línea es la dirección.
        if re.match(r'^\s*\(.+\)[^a-zA-Z0-9]*$', line):
            # Si la línea entera es un paréntesis (ignorando puntuación final), lo saltamos.
            continue
        
        # Fallback simple: si empieza y acaba con parentesis (tras limpiar)
        clean_line = line.strip().rstrip(".,; ")
        if clean_line.startswith("(") and clean_line.endswith(")"):
            continue

        buffer_text.append(line)

    if buffer_text:
        segments.append({'type': 'speech', 'content': "\n".join(buffer_text)})

    return segments

def generar_episodio_especial(guion_text: str, output_path: str):
    """
    Orquesta la generación del episodio especial.
    1. Parsea el guion.
    2. Genera audio TTS para bloques de texto.
    3. Carga y mezcla efectos de sonido.
    4. Exporta el archivo final.
    """
    # Inicializar cliente TTS
    # Nota: Asume credenciales en entorno, configurar en app.py si es necesario
    try:
         client = texttospeech.TextToSpeechClient()
    except Exception as e:
        return f"Error iniciando cliente TTS: {str(e)}"

    segments = parse_guion(guion_text)
    final_audio = AudioSegment.empty()
    
    temp_dir = os.path.join(BASE_DIR, 'temp_audio')
    os.makedirs(temp_dir, exist_ok=True)

    for i, seg in enumerate(segments):
        if seg['type'] == 'speech':
            # Generar voz
            ssml = text_to_ssml(seg['content'])
            try:
                raw_audio = generar_audio_base_tts(ssml, client)
                temp_file = os.path.join(temp_dir, f"seg_{i}.mp3")
                with open(temp_file, "wb") as f:
                    f.write(raw_audio)
                
                speech_segment = AudioSegment.from_mp3(temp_file)
                final_audio += speech_segment
            except Exception as e:
                print(f"Error generando segmento {i}: {e}")
                # Si falla, añadir silencio o continuar
                final_audio += AudioSegment.silent(duration=1000)

        elif seg['type'] == 'sound':
            # Cargar sonido
            file_path = os.path.join(AUDIO_ASSETS_DIR, seg['file'])
            if os.path.exists(file_path):
                sound = AudioSegment.from_mp3(file_path)
                # Normalizar volumen?
                final_audio += sound
            else:
                print(f"Advertencia: Archivo de sonido no encontrado {file_path}")
                final_audio += AudioSegment.silent(duration=500)

    # Exportar
    final_audio.export(output_path, format="mp3")
    return output_path
