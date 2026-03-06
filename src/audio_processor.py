import os
import re
import json
import logging
from pydub import AudioSegment
from src.core.text_processing import limpiar_markdown_audio
from src.config.settings import VOICE_NAME, AUDIO_ASSETS_DIR
from src.engine.audio import sintetizar_ssml_a_audio

# Obtener rutas absolutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# (Eliminada función cargar_configuracion redundante)
# (Eliminada función get_voice_params redundante)
# (Eliminada función generar_audio_base_tts redundante)


from xml.sax.saxutils import escape

def text_to_ssml(text: str) -> str:
    """Envuelve texto plano en SSML básico si no lo tiene."""
    if not text.strip().startswith("<speak>"):
        return f"<speak>{escape(text)}</speak>"
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
        "SINTONIA_INICIO": "inicio.mp3",
        "CORTINILLA_TRANSICION_CORTA": "bip002.mp3",
        "CORTINILLA_TRANSICIÓN_CORTA": "bip002.mp3", # Alias con tilde
        "CORTINILLA_SINTONIA_CIERRE": "cierre.mp3",
        "SINTONIA_CIERRE": "cierre.mp3",
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

        # Limpieza robusta de la línea
        # 1. Eliminar asteriscos (bold/italic markdown)
        line = line.replace('*', '')
        
        # 2. Eliminar prefijos de hablante inline (ej: "DOROTEA: Hola") si se coló
        # Solo si está al principio de la línea
        line = re.sub(r'^[A-ZÁÉÍÓÚÑ]+\s*:\s*', '', line)
        
        # 3. Eliminar caracteres extraños
        line = line.replace('`', '').replace('#', '')
        
        if not line.strip():
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
    # Inicializar cliente TTS: YA NO ES NECESARIO, LO GESTIONA src.engine.audio
    # try:
    #      client = texttospeech.TextToSpeechClient()
    # except Exception as e:
    #     return f"Error iniciando cliente TTS: {str(e)}"

    # chunk_text logic
    def chunk_text(text: str, max_chars=4000) -> list:
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        current_chunk = []
        current_len = 0
        
        # Split by paragraphs first to preserve flow
        paragraphs = text.split('\n')
        
        for para in paragraphs:
            # If a single paragraph is huge (unlikely but possible), split by sentences
            if len(para) > max_chars:
                # Simple sentence split (can be improved)
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sent in sentences:
                    if len(sent) > max_chars:
                         # Hard chop if sentence is inexplicably long
                         for i in range(0, len(sent), max_chars):
                             chunks.append(sent[i:i+max_chars])
                    else:
                        if current_len + len(sent) + 1 > max_chars:
                            chunks.append("\n".join(current_chunk))
                            current_chunk = [sent]
                            current_len = len(sent)
                        else:
                            current_chunk.append(sent)
                            current_len += len(sent) + 1
            else:
                 if current_len + len(para) + 1 > max_chars:
                     chunks.append("\n".join(current_chunk))
                     current_chunk = [para]
                     current_len = len(para)
                 else:
                     current_chunk.append(para)
                     current_len += len(para) + 1
        
        if current_chunk:
            chunks.append("\n".join(current_chunk))
            
        return chunks

    original_segments = parse_guion(guion_text)
    
    # Pre-process segments to split long speech
    final_segments = []
    for seg in original_segments:
        if seg['type'] == 'speech':
            text_chunks = chunk_text(seg['content'])
            for chunk in text_chunks:
                if chunk.strip():
                    final_segments.append({'type': 'speech', 'content': chunk})
        else:
            final_segments.append(seg)

    final_audio = AudioSegment.empty()
    
    temp_dir = os.path.join(BASE_DIR, 'temp_audio')
    os.makedirs(temp_dir, exist_ok=True)

    for i, seg in enumerate(final_segments):
        if seg['type'] == 'speech':
            # Limpiar markdown (negritas, cursivas) antes de generar
            texto_limpio = limpiar_markdown_audio(seg['content'])
            ssml = text_to_ssml(texto_limpio)
            try:
                # Usar el motor centralizado que ya devuelve un AudioSegment con la configuración correcta
                speech_segment = sintetizar_ssml_a_audio(ssml, voz=VOICE_NAME)
                
                # (Opcional) Normalizar volumen aquí si no lo hace el motor (el motor ya lo hace)
                final_audio += speech_segment
            except Exception as e:
                print(f"Error generando segmento {i} (len={len(seg['content'])}): {e}")
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

