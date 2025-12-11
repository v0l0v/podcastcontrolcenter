import os
import sys
import time
import random
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# =================================================================================
# DECORADOR DE REINTENTOS PARA LAS LLAMADAS A API
# =================================================================================
def retry_on_failure(retries=3, delay=5, backoff=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_delay = delay
            for i in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"      ⚠️ Fallo en '{func.__name__}' (Intento {i}/{retries}): {e}")
                    if i == retries:
                        print(f"      ❌ Se acabaron los reintentos para '{func.__name__}'. La función falló definitivamente.")
                        return None
                    sleep_time = current_delay + random.uniform(0, 1)
                    print(f"      ⏳ Esperando {sleep_time:.2f} segundos antes de reintentar...")
                    time.sleep(sleep_time)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator

# =================================================================================
# INICIALIZACIÓN DE GEMINI
# =================================================================================
USE_NEW_SDK = False
try:
    from google.cloud import generativelanguage as glm
    model = glm.GenerativeModel("gemini-2.5-flash-lite")
    USE_NEW_SDK = True
    print("✅ [llm_utils] Usando SDK nuevo de Gemini (google-cloud-generativelanguage).")
except ImportError:
    try:
        from vertexai.generative_models import GenerativeModel
        import vertexai
        
        gcp_project_id = os.getenv('GCP_PROJECT_ID')
        gcp_location = os.getenv('GCP_LOCATION', 'us-central1')
        
        if gcp_project_id:
            vertexai.init(project=gcp_project_id, location=gcp_location)
            model = GenerativeModel("gemini-2.5-flash-lite")
            USE_NEW_SDK = False
            print("⚠️ [llm_utils] Usando SDK VertexAI (deprecado en 2026).")
        else:
            print("❌ [llm_utils] No se encontró GCP_PROJECT_ID.")
            model = None
            
    except ImportError:
        print("❌ [llm_utils] No se pudo importar ningún SDK de Gemini")
        model = None

# --- Wrapper unificado ---
@retry_on_failure(retries=3, delay=5, backoff=2)
def generar_texto_con_gemini(prompt: str) -> str:
    if model is None:
        print("❌ Error: Modelo no inicializado.")
        return ""
        
    try:
        if USE_NEW_SDK:
            response = model.generate_content(prompt)
            if response and response.candidates:
                return response.candidates[0].content.parts[0].text.strip()
            return ""
        else:
            response = model.generate_content(prompt)
            return response.text.strip() if response.text else ""
    except Exception as e:
        print(f"❌ Error en generación Gemini: {e}")
        return ""
