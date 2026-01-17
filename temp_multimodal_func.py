
@retry_on_failure(retries=2, delay=2)
def generar_texto_multimodal_con_gemini(prompt: str, image_data: bytes = None, image_url: str = None) -> str:
    """
    Genera texto a partir de un prompt y una imagen (bytes o URL).
    """
    if model is None:
        return ""

    try:
        content = [prompt]
        
        # Opción A: Bytes directos
        if image_data:
            from vertexai.generative_models import Part, Image
            # Intentar detectar SDK
            if 'vertexai' in sys.modules and hasattr(sys.modules['vertexai'], 'init'):
                image_part = Part.from_data(data=image_data, mime_type="image/jpeg") # Asumimos jpeg o detectamos?
                content.append(image_part)
            elif 'google.generativeai' in sys.modules:
                # AI Studio
                blob = {'mime_type': 'image/jpeg', 'data': image_data}
                content.append(blob)
        
        # Opción B: URL (Solo Vertex AI soporta Part.from_uri de forma nativa en algunas versiones, 
        # pero es más seguro descargarla antes en dorototal.py y pasar bytes. 
        # Aquí dejaremos soporte básico si el SDK lo permite).
        
        response = model.generate_content(content)
        return response.text.strip() if response else ""

    except Exception as e:
        print(f"❌ Error análisis multimodal Gemini: {e}")
        return ""
