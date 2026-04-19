import sys
import os

# Añadir el path del proyecto
sys.path.append(os.getcwd())

from src.engine.audio import sintetizar_ssml_a_audio
from src.config.settings import VOICE_NAME

def test_voice():
    print(f"Probando la nueva voz configurada: {VOICE_NAME}")
    
    texto = """
    <speak>
        Hola, soy Dorotea. He cambiado mi voz a una versión más eficiente para ahorrar unos eurillos, 
        que la cosa no está para ir tirando la casa por la ventana. 
        ¿Qué te parece cómo sueno ahora? Sigo siendo la misma de siempre, con el corazón en La Mancha.
    </speak>
    """
    
    try:
        audio = sintetizar_ssml_a_audio(texto, voz=VOICE_NAME)
        output_file = "scratch/test_dorotea_voice.mp3"
        audio.export(output_file, format="mp3")
        print(f"✅ Audio generado con éxito en: {output_file}")
    except Exception as e:
        print(f"❌ Error al generar el audio: {e}")

if __name__ == "__main__":
    test_voice()
