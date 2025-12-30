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
import warnings

model = None
USE_NEW_SDK = False # Flag para diferenciar comportamientos sutiles si fuera necesario

# 1. Intentar usar Google Generative AI (AI Studio) si hay API KEY
# ----------------------------------------------------------------
if os.getenv("GOOGLE_API_KEY"):
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        print("✅ [llm_utils] Usando SDK Google Generative AI (AI Studio).")
    except ImportError:
        print("❌ [llm_utils] GOOGLE_API_KEY encontrada, pero 'google-generativeai' no está instalado.")

# 2. Si no, intentar usar Vertex AI (Google Cloud)
# ----------------------------------------------------------------
if model is None:
    try:
        # Suprimir advertencia de deprecación de Vertex AI SDK hasta junio 2026
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, message=".*deprecated.*")
            from vertexai.generative_models import GenerativeModel
            import vertexai
        
            gcp_project_id = os.getenv('GCP_PROJECT_ID')
            gcp_location = os.getenv('GCP_LOCATION', 'us-central1')
            
            if gcp_project_id:
                vertexai.init(project=gcp_project_id, location=gcp_location)
                model = GenerativeModel("gemini-2.5-flash-lite")
                print("⚠️ [llm_utils] Usando SDK VertexAI (deprecado en 2026, advertencia silenciada).")
            else:
                print("❌ [llm_utils] No se encontró GOOGLE_API_KEY ni GCP_PROJECT_ID. Gemini no funcionará.")
            
    except ImportError:
        print("❌ [llm_utils] No se pudo importar ningún SDK de Gemini (ni generativeai ni vertexai).")
        model = None

# --- Wrapper unificado ---
@retry_on_failure(retries=3, delay=5, backoff=2)
def generar_texto_con_gemini(prompt: str) -> str:
    if model is None:
        print("❌ Error: Modelo no inicializado.")
        return ""
        
    try:
        # Tanto vertexai como google.generativeai soportan .generate_content() y .text
        response = model.generate_content(prompt)
        return response.text.strip() if response and hasattr(response, 'text') and response.text else ""
            
    except Exception as e:
        # Fallback para estructuras antiguas o errores de bloqueos
        print(f"❌ Error en generación Gemini: {e}")
        return ""
