
import sys
import os
import datetime
from pydub import AudioSegment

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm_utils import generar_texto_con_gemini
from src.engine.audio import sintetizar_ssml_a_audio, masterizar_a_lufs

def test_ondemand_logic():
    print("Testing On-Demand Audio Gen Backend...")
    
    topic = "Explica qué es un fractal en 2 frases."
    duration = 1 # min
    
    print(f"Topic: {topic}")
    print(f"Duration: {duration} min")
    
    try:
        # Mocking the logic in app.py
        target_words = duration * 100 # Reduced for test speed
        
        prompt = f"""
        Eres Dorotea.
        TAREA: Escribir guion breve sobre: "{topic}"
        Longitud: {target_words} palabras.
        Formato: TEXTO PLANO.
        """
        
        print("-> Generating script...")
        script = generar_texto_con_gemini(prompt)
        print(f"-> Script generated ({len(script)} chars):\n{script}")
        
        if not script:
            print("❌ FAILURE: Empty script.")
            return

        print("-> Synthesizing audio...")
        chunks = script.split('\n')
        full_audio = AudioSegment.empty()
        
        for c in chunks:
            if not c.strip(): continue
            ssml = f"<speak>{c}<break time='200ms'/></speak>"
            seg = sintetizar_ssml_a_audio(ssml)
            if seg:
                full_audio += seg
        
        print(f"-> Audio length: {len(full_audio)} ms")
        
        print("-> Mastering...")
        final_audio = masterizar_a_lufs(full_audio, target_lufs=-16.0)
        
        output = "tests/test_ondemand_result.mp3"
        final_audio.export(output, format="mp3")
        print(f"✅ SUCCESS: Audio saved to {output}")
        
    except Exception as e:
        print(f"❌ FAILURE: Exception {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ondemand_logic()
