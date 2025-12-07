import os
import sys
import json
from src.utils import retry_on_failure, cargar_configuracion
import src.prompts as prompts

# --- CONFIGURACIÓN ---
CONFIG = cargar_configuracion()

# --- INICIALIZACIÓN GEMINI ---
USE_NEW_SDK = False
model = None

try:
    from google.cloud import generativelanguage as glm
    # Nota: Ajustar el nombre del modelo según disponibilidad
    # model = glm.GenerativeModel("gemini-2.0-flash-exp") # Ejemplo
    # Por ahora mantenemos la lógica de dorototal.py de intentar importar
    pass 
except ImportError:
    pass

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    
    gcp_project_id = os.getenv('GCP_PROJECT_ID')
    gcp_location = os.getenv('GCP_LOCATION', 'us-central1')
    
    if gcp_project_id:
        vertexai.init(project=gcp_project_id, location=gcp_location)
        model = GenerativeModel("gemini-2.0-flash-exp") # Usando modelo flash
        print("✅ Cliente Vertex AI inicializado.")
    else:
        print("⚠️ GCP_PROJECT_ID no configurado. Gemini no funcionará.")

except ImportError:
    print("❌ No se pudo importar Vertex AI SDK.")

@retry_on_failure(retries=3, delay=5, backoff=2)
def generar_texto_con_gemini(prompt: str) -> str:
    if not model:
        return ""
    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else ""
    except Exception as e:
        print(f"❌ Error en generación Gemini: {e}")
        return ""

# --- FUNCIONES DE ALTO NIVEL ---

def identificar_fuente_original(texto: str) -> str:
    prompt = f"""
    Analiza el siguiente texto. Identifica si menciona un organismo, ayuntamiento o institución como fuente.
    Si lo encuentras, devuelve solo el nombre. Si no, devuelve "Desconocida".
    TEXTO:
    ---
    {texto}
    ---
    RESPUESTA:"""
    respuesta = generar_texto_con_gemini(prompt)
    if respuesta and "Desconocida" not in respuesta:
        return respuesta.strip()
    return ""

def extraer_localidad_con_ia(texto_noticia: str) -> str:
    if not texto_noticia: return "Castilla la Mancha"
    prompt = f"""
    Analiza el texto y devuelve ÚNICAMENTE el nombre de la localidad principal mencionada.
    TEXTO: {texto_noticia}
    LOCALIDAD:
    """
    localidad = generar_texto_con_gemini(prompt).strip()
    return localidad.replace('"', '').replace("'", "") if localidad else "Desconocida"

def analizar_sentimiento(texto: str) -> str:
    prompt = prompts.PromptsAnalisis.analizar_sentimiento_texto(texto)
    return generar_texto_con_gemini(prompt).lower().strip()

def resumir_noticia(texto: str, fuente_original: str = "", entidades_clave: list = None, es_breve: bool = False) -> str:
    if es_breve:
        prompt = prompts.PromptsAnalisis.resumen_muy_breve(texto, fuente_original)
    else:
        prompt = prompts.PromptsAnalisis.resumen_noticia_enriquecido(texto, fuente_original, entidades_clave)
    return generar_texto_con_gemini(prompt)

def extraer_entidades(texto: str) -> list:
    prompt = prompts.PromptsAnalisis.extraer_entidades_clave(texto)
    resp = generar_texto_con_gemini(prompt)
    try:
        if "```" in resp:
            resp = resp.split("```")[1].replace("json", "").strip()
        return json.loads(resp)
    except:
        return []

def agrupar_noticias_logica(noticias_simplificadas_json: str) -> dict:
    prompt = prompts.PromptsAnalisis.agrupacion_logica_temas(noticias_simplificadas_json)
    resp = generar_texto_con_gemini(prompt)
    try:
        if "```" in resp:
            resp = resp.split("```")[1].replace("json", "").strip()
        return json.loads(resp)
    except:
        return {}

def enriquecer_tema(tema: str, resumenes_json: str) -> dict:
    prompt = prompts.PromptsCreativos.enriquecimiento_creativo_tema(tema, resumenes_json)
    resp = generar_texto_con_gemini(prompt)
    try:
        if "```" in resp:
            resp = resp.split("```")[1].replace("json", "").strip()
        return json.loads(resp)
    except:
        return {}

def generar_cronica_bloque(tema: str, transicion: str, noticias: list) -> str:
    # Reconstrucción de la lógica de generar_narracion_fluida_bloque
    resumenes = "\n".join([f"- {n.get('resumen')}" for n in noticias])
    prompt = f"""
    Eres un editor de radio. Crea una crónica consolidada sobre "{tema}".
    Transición de entrada: "{transicion}"
    Noticias:
    {resumenes}
    Instrucciones: Fusiona en una historia coherente. Usa fechas absolutas.
    """
    return generar_texto_con_gemini(prompt)
