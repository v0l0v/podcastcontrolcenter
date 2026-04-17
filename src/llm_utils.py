import os
import sys
import time
import random
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# --- MONITORING ---
from src.monitoring import tracker


# =================================================================================
# DECORADOR DE REINTENTOS PARA LAS LLAMADAS A API
# =================================================================================
def retry_on_failure(retries=3, delay=5, backoff=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Wrapper for monitoring
            if 'monitor_callback' in kwargs:
                # Optional: Handle callback if needed
                pass
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

# 41. # =================================================================================
# INICIALIZACIÓN DE GEMINI
# =================================================================================
import warnings

model_flash = None
model_pro = None

MODEL_NAME_FLASH = "gemini-2.0-flash"
MODEL_NAME_PRO = "gemini-2.5-pro"

# 1. Intentar usar Google Generative AI (AI Studio) si hay API KEY
# ----------------------------------------------------------------
if os.getenv("GOOGLE_API_KEY"):
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model_flash = genai.GenerativeModel(MODEL_NAME_FLASH)
        model_pro = genai.GenerativeModel(MODEL_NAME_PRO)
        print(f"✅ [llm_utils] Usando SDK Google Generative AI. Flash: {MODEL_NAME_FLASH}, Pro: {MODEL_NAME_PRO}")
    except ImportError:
        print("❌ [llm_utils] GOOGLE_API_KEY encontrada, pero 'google-generativeai' no está instalado.")

# 2. Si no, intentar usar Vertex AI (Google Cloud)
# ----------------------------------------------------------------
if model_flash is None or model_pro is None:
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            try:
                from vertexai.generative_models import GenerativeModel
                import vertexai
            
                gcp_project_id = os.getenv('GCP_PROJECT_ID')
                gcp_location = os.getenv('GCP_LOCATION', 'us-central1')
                
                if gcp_project_id:
                    vertexai.init(project=gcp_project_id, location=gcp_location)
                    if model_flash is None: model_flash = GenerativeModel(MODEL_NAME_FLASH)
                    if model_pro is None: model_pro = GenerativeModel(MODEL_NAME_PRO)
                    print(f"⚠️ [llm_utils] Usando SDK VertexAI. Flash: {MODEL_NAME_FLASH}, Pro: {MODEL_NAME_PRO}")
                else:
                    if model_flash is None:
                        print("❌ [llm_utils] No se encontró GOOGLE_API_KEY ni GCP_PROJECT_ID. Gemini no funcionará.")
            except Exception as e:
                 print(f"❌ [llm_utils] Error crítico inicializando Vertex AI: {e}")
            
    except ImportError:
        print("❌ [llm_utils] No se pudo importar ningún SDK de Gemini (ni generativeai ni vertexai).")

# --- Wrapper unificado ---
@retry_on_failure(retries=3, delay=5, backoff=2)
def generar_texto_con_gemini(prompt: str, model_type: str = "pro") -> str:
    """
    Genera texto usando Gemini. 
    model_type: 'pro' (mejor calidad, más lento) o 'flash' (más rápido, más barato).
    """
    selected_model = model_pro if model_type == "pro" else model_flash
    
    if selected_model is None:
        # Fallback si el pro no está pero el flash sí
        selected_model = model_flash if model_flash else model_pro
        
    if selected_model is None:
        print("❌ Error: Modelos no inicializados.")
        return ""
        
    try:
        response = selected_model.generate_content(prompt)
        text = response.text.strip() if response and hasattr(response, 'text') and response.text else ""
        
        # --- TRACKING ---
        input_tokens = len(prompt) // 4 
        output_tokens = len(text) // 4
        if hasattr(response, 'usage_metadata'):
            try:
                if hasattr(response.usage_metadata, 'prompt_token_count'):
                    input_tokens = response.usage_metadata.prompt_token_count
                if hasattr(response.usage_metadata, 'candidates_token_count'):
                    output_tokens = response.usage_metadata.candidates_token_count
            except:
                pass
        
        tracker.track_gemini(input_tokens, output_tokens, model=f"gemini-1.5-{model_type}")
        return text
            
    except Exception as e:
        print(f"❌ Error en generación Gemini ({model_type}): {e}")
        return ""

@retry_on_failure(retries=3, delay=5, backoff=2)
def generar_texto_multimodal_con_gemini(prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Genera texto a partir de una imagen y un prompt usando Gemini Pro Vision (o Flash).
    """
    if model_pro is None:
        print("❌ Error: Modelo Pro no inicializado.")
        return ""
        
    try:
        from vertexai.generative_models import Part, Image

        # CASO 1: SDK google.generativeai (AI Studio)
        if 'google.generativeai' in sys.modules and hasattr(sys.modules['google.generativeai'], 'GenerativeModel'):
             try:
                 import PIL.Image
                 import io
                 img = PIL.Image.open(io.BytesIO(image_bytes))
                 response = model_pro.generate_content([prompt, img])
                 return response.text.strip() if response and hasattr(response, 'text') else ""
             except ImportError:
                 print("⚠️ PIL no instalado, no se puede procesar imagen en AI Studio mode.")
                 return ""

        # CASO 2: SDK Vertex AI
        else:
            image_part = Part.from_data(data=image_bytes, mime_type=mime_type)
            response = model_pro.generate_content([prompt, image_part])
            text = response.text.strip() if response and hasattr(response, 'text') else ""
            
            # Tracking Multimodal (Estimación básica)
            tracker.track_gemini(len(prompt)//4 + 258, len(text)//4, model="gemini-1.5-pro") # +258 tokens por imagen aprox
            return text

    except Exception as e:
        print(f"❌ Error en generación Multimodal Gemini: {e}")
        return ""

@retry_on_failure(retries=3, delay=5, backoff=2)
def generar_texto_multimodal_audio_con_gemini(prompt: str, audio_bytes: bytes, mime_type: str = "audio/mp3") -> str:
    """
    Genera texto a partir de un audio y un prompt usando Gemini Pro Vision / Flash.
    """
    if model_pro is None:
        print("❌ Error: Modelo Pro no inicializado.")
        return ""
        
    try:
        from vertexai.generative_models import Part
        
        # CASO 1: SDK google.generativeai (AI Studio)
        if 'google.generativeai' in sys.modules and hasattr(sys.modules['google.generativeai'], 'GenerativeModel'):
             # AI Studio acepta diccionarios con 'mime_type' y 'data'
             blob = {'mime_type': mime_type, 'data': audio_bytes}
             response = model_pro.generate_content([prompt, blob])
             return response.text.strip() if response and hasattr(response, 'text') else ""

        # CASO 2: SDK Vertex AI
        else:
            audio_part = Part.from_data(data=audio_bytes, mime_type=mime_type)
            response = model_pro.generate_content([prompt, audio_part])
            return response.text.strip() if response and hasattr(response, 'text') else ""

    except Exception as e:
        print(f"❌ Error en generación Multimodal Audio Gemini: {e}")
        return ""
