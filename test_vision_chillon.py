
import sys
import os
import requests

# Add project root to path
sys.path.append('/home/victor/proyectos/podcastcontrolcenter')

from src.llm_utils import generar_texto_multimodal_con_gemini

def test_image():
    image_path = "/home/victor/.gemini/antigravity/brain/f65c26ac-9ec0-4a9a-b3bb-167dfa7570af/uploaded_image_1768727376976.png"
    
    print(f"Analizando imagen: {image_path}")
    
    with open(image_path, "rb") as f:
        image_data = f.read()

    prompt_vision = """
    Eres los ojos de un periodista. Analiza esta imagen (captura de Facebook) y extrae DATOS CLAVE que falten en el texto:
    1. TITULAR EXACTO: ¿Qué dice el enlace compartido?
    2. DATOS NUMÉRICOS: Cifras de población, fechas, etc.
    3. UBICACIÓN/MUNICIPIO: ¿De qué pueblo se habla?
    4. CONFIRMACIÓN DE FUENTE: ¿Quién publica y quién es la fuente original de la noticia compartida?
    """
    
    resultado = generar_texto_multimodal_con_gemini(prompt_vision, image_data=image_data)
    print("\n--- RESULTADO DE LA VISIÓN ARTIFICIAL ---")
    print(resultado)
    print("-----------------------------------------")

if __name__ == "__main__":
    test_image()
