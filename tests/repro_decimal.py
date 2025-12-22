
import sys
import os
import unittest.mock

# Add project root to path
sys.path.append(os.getcwd())

# Mock src.config.settings
mock_settings = unittest.mock.Mock()
mock_settings.SPANISH_STOPWORDS = set()
mock_settings.CONFIG = {'pronunciation': {}}
mock_settings.NGRAM_N = 3
sys.modules['src.config.settings'] = mock_settings

from src.core.text_processing import preprocesar_texto_para_tts, limpiar_markdown_audio, corregir_palabras_deletreadas_tts, corregir_numeros_con_puntos_tts, corregir_mayusculas_tts, corregir_decimales_con_coma_tts

def test_pipeline(text):
    print(f"Original: '{text}'")
    
    # Simulate the pipeline in audio.py
    processed = preprocesar_texto_para_tts(text)
    processed = limpiar_markdown_audio(processed)
    processed = corregir_palabras_deletreadas_tts(processed)
    processed = corregir_mayusculas_tts(processed)
    processed = corregir_numeros_con_puntos_tts(processed)
    processed = corregir_decimales_con_coma_tts(processed)
    
    print(f"Processed: '{processed}'")
    return processed

if __name__ == "__main__":
    test_text = "supera 1,05 millones de euros"
    processed_text = test_pipeline(test_text)
    
    if "1 coma 05" in processed_text:
        print("SUCCESS: 1,05 converted to 1 coma 05")
    else:
        print("FAILURE: 1,05 NOT converted correctly")
