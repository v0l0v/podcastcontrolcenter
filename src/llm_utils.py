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
        model = genai.GenerativeModel("gemini-2.5-pro")
        print("✅ [llm_utils] Usando SDK Google Generative AI (AI Studio) - Modelo PRO.")
    except ImportError:
        print("❌ [llm_utils] GOOGLE_API_KEY encontrada, pero 'google-generativeai' no está instalado.")

# 2. Si no, intentar usar Vertex AI (Google Cloud)
# ----------------------------------------------------------------
if model is None:
    try:
        # Suprimir advertencia de deprecación de Vertex AI SDK hasta junio 2026
        # Usamos simplefilter para asegurar que ignoramos todo lo relacionado con este bloque
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            try:
                from vertexai.generative_models import GenerativeModel
                import vertexai
            
                gcp_project_id = os.getenv('GCP_PROJECT_ID')
                gcp_location = os.getenv('GCP_LOCATION', 'us-central1')
                
                if gcp_project_id:
                    vertexai.init(project=gcp_project_id, location=gcp_location)
                    model = GenerativeModel("gemini-2.5-pro")
                    print("⚠️ [llm_utils] Usando SDK VertexAI (deprecado en 2026, advertencia silenciada) - Modelo PRO.")
                else:
                    print("❌ [llm_utils] No se encontró GOOGLE_API_KEY ni GCP_PROJECT_ID. Gemini no funcionará.")
            except Exception as e:
                 print(f"❌ [llm_utils] Error crítico inicializando Vertex AI: {e}")
                 model = None
            
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

@retry_on_failure(retries=2, delay=2)
def transcribir_audio_gemini(audio_path: str, prompt_contexto: str = "") -> str:
    """
    Sube un archivo de audio a Gemini y obtiene una transcripciÃ³n/anÃ¡lisis.
    Soporta tanto AI Studio (google.generativeai) como Vertex AI.
    """
    if model is None:
        return ""
        
    if not os.path.exists(audio_path):
        print(f"❌ Archivo de audio no encontrado: {audio_path}")
        return ""

    try:
        # Leer bytes del audio
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
            
        mime_type = "audio/mp3" # Asumimos mp3 por defecto, ojalÃ¡ baste
        if audio_path.lower().endswith(".ogg"): mime_type = "audio/ogg"
        if audio_path.lower().endswith(".wav"): mime_type = "audio/wav"
        if audio_path.lower().endswith(".m4a"): mime_type = "audio/mp4" # m4a suele mapear a audio/mp4 en estos modelos

        prompt_base = "Analiza este audio. " + prompt_contexto

        # A) DetecciÃ³n de SDK: Vertex AI
        if 'vertexai' in sys.modules and hasattr(sys.modules['vertexai'], 'init'):
             from vertexai.generative_models import Part
             audio_part = Part.from_data(data=audio_data, mime_type=mime_type)
             response = model.generate_content([audio_part, prompt_base])
             return response.text.strip() if response else ""

        # B) DetecciÃ³n de SDK: Google AI Studio
        elif 'google.generativeai' in sys.modules:
            # En AI Studio moderno se puede pasar el dict con 'data' (bytes) y 'mime_type'
            # Ojo: Requiere versiones recientes de la librerÃ­a.
            blob = {'mime_type': mime_type, 'data': audio_data}
            response = model.generate_content([prompt_base, blob])
            return response.text.strip() if response else ""
            
    except Exception as e:
        print(f"❌ Error transcribiendo audio con Gemini: {e}")
        return ""
