import sys
import os
import random
import html

# Añadir el path del proyecto para importar módulos de src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.engine.audio import sintetizar_ssml_a_audio
from src.llm_utils import generar_texto_con_gemini
from costumbrismo import obtener_saludo_aleatorio

def main():
    print("🎬 Obteniendo un saludo costumbrista aleatorio...")
    saludo_base = obtener_saludo_aleatorio(provincia="Ciudad Real", momento_dia="manana")
    print(f"Base del saludo: {saludo_base}")
    
    prompt = f"""
Eres Dorotea, una locutora de radio cálida y entrañable de Castilla-La Mancha.
Acabas de arrancar tu programa de noticias hoy. 

Aquí tienes un saludo base que debes adaptar a tu propio estilo, haciéndolo natural y conversacional:
"{saludo_base}"

Responde SOLO con el texto que vas a locutar, sin acotaciones ni introducciones. Mantenlo breve (2 o 3 frases como máximo).
"""

    print("🤖 Generando texto con Gemini...")
    texto_generado = generar_texto_con_gemini(prompt)
    
    if not texto_generado:
        print("❌ Error: No se pudo generar el texto con Gemini.")
        return
        
    print(f"Texto generado: {texto_generado}")
    
    print("🎙️ Generando audio con el motor TTS...")
    
    # Preparar SSML básico para prosodia (como se hace en dorototal.py)
    texto_escapado = html.escape(texto_generado)
    ssml = f"<speak><prosody rate='0.99'>{texto_escapado}</prosody></speak>"
    
    audio_segment = sintetizar_ssml_a_audio(ssml)
    
    if audio_segment:
        output_file = "prueba_costumbrismo.mp3"
        audio_segment.export(output_file, format="mp3")
        print(f"✅ ¡Éxito! Audio guardado en: {output_file}")
    else:
        print("❌ Error: No se pudo generar el audio.")

if __name__ == "__main__":
    main()
