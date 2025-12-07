# dorototal.py - FUSIÓN DE LO MEJOR DE 'doro.py' Y 'dorotea.py'
#
# BASE: dorotea.py (Voz Studio-C, Análisis de Sentimiento, Música Dinámica, Filtros, Clustering Temático IA)
#
# MEJORAS INTEGRADAS DE doro.py:
#  1. Prompt de Resumen Enriquecido: Usa 'extraer_entidades_clave' + 'resumen_noticia_enriquecido'.
#  2. Optimización de Memoria: Usa el método .overlay() en la FASE 4 para ensamblar el audio final.
# ---------------------------------------------------------------------------------
import gc
import io
import os
import re
import random
import html
import json
import glob
import time
import hashlib
import unicodedata
import sys
import difflib
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from time import mktime
from typing import Any, Dict, List

# --- Clientes de Google Cloud ---
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate
import vertexai
from vertexai.generative_models import GenerativeModel

import feedparser
from pydub import AudioSegment
from pydub.effects import normalize
from num2words import num2words

# --- NUEVAS DEPENDENCIAS PARA MASTERIZACIÓN ---
# Recomendado: pip install pyloudnorm pydub numpy
try:
    import pyloudnorm as pyln
    import numpy as np
    LOUDNORM_AVAILABLE = True
    print("✅ PyLoudnorm disponible para masterización a -16 LUFS")
except ImportError:
    LOUDNORM_AVAILABLE = False
    print("⚠️ PyLoudnorm no disponible. Usando normalización básica.")

# --- (Opcional) RapidFuzz para similitud más precisa si existe ---
# Recomendado: pip install rapidfuzz
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
    print("✅ RapidFuzz disponible para similitud adicional")
except Exception:
    RAPIDFUZZ_AVAILABLE = False

# --- MÓDULOS PERSONALIZADOS ---
# Asegúrate de tener un archivo mcmcn_prompts.py con los prompts necesarios.
import mcmcn_prompts

# --------------------- CONFIGURACIÓN GENERAL Y AUDIO ----------------------------

# --- CARGA DE CONFIGURACIÓN EXTERNA ---
def cargar_configuracion():
    config_path = os.path.join(os.path.dirname(__file__), 'podcast_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

CONFIG = cargar_configuracion()
AUDIO_CONFIG = CONFIG.get('audio_config', {})
GEN_CONFIG = CONFIG.get('generation_config', {})

VOICE_TARGET_PEAK_DBFS = AUDIO_CONFIG.get('voice_target_peak_dbfs', -1.5)
TARGET_LUFS = AUDIO_CONFIG.get('target_lufs', -16.0)
SAMPLE_RATE = 44100    # 44.1 kHz
BITRATE = "128k"       # 128 kbps
SILENCE_THRESHOLD_DBFS = AUDIO_CONFIG.get('silence_threshold_dbfs', -50)
VOICE_NAME = AUDIO_CONFIG.get('voice_name', "es-ES-Journey-F")
LANGUAGE_CODE = "es-ES"

# --- CONFIG AGRUPACIÓN/DEDUP ---
DEDUP_SIMILARITY_THRESHOLD = GEN_CONFIG.get('dedup_similarity_threshold', 0.90)
NGRAM_N = GEN_CONFIG.get('ngram_n', 3)
KEYPHRASE_MIN_COUNT = 2               # Mínimo de apariciones para crear un grupo dinámico.
MIN_NEWS_PER_BLOCK = GEN_CONFIG.get('min_news_per_block', 2)
MAX_DYNAMIC_KEYPHRASES = 12           # Límite de claves dinámicas a considerar.

# --- CONFIGURACIÓN DE FILTRADO DE CONTENIDO ---
# Mínimo de palabras que debe tener un resumen para generar audio.
# AJUSTA ESTE VALOR SI QUIERES CAMBIAR EL FILTRO DE NOTICIAS CORTAS.
MIN_WORDS_FOR_AUDIO = AUDIO_CONFIG.get('min_words_for_audio', 33)
AUDIENCE_QUESTIONS_FILE = "preguntas_audiencia.txt"

# --- STOPWORDS (es) ligeras para similitud/keywords ---
SPANISH_STOPWORDS = {
    'de','la','que','el','en','y','a','los','del','se','las','por','un','para','con',
    'no','una','su','al','lo','como','más','pero','sus','le','ya','o','este','sí',
    'porque','esta','entre','cuando','muy','sin','sobre','también','me','hasta',
    'hay','donde','quien','desde','todo','nos','durante','todos','uno','les',
    'ni','contra','otros','ese','eso','ante','ellos','e','esto','mí','antes',
    'algunos','qué','unos','yo','otro','otras','otra','él','tanto','esa','estos',
    'mucho','quienes','nada','muchos','cual','poco','ella','estar','estas','algunas',
    'algo','nosotros','mi','mis','tú','te','ti','tu','tus','ellas','nosotras',
    'vosotros','vosotras','os','mío','mía','míos','mías','tuyo','tuya','tuyos',
    'tuyas','suyo','suya','suyos','suyas','nuestro','nuestra','nuestros','nuestras',
    'vuestro','vuestra','vuestros','vuestras','esos','esas','estoy','estás',
    'está','estamos','estáis','están','esté','estés','estemos','estéis','estén',
    'estaré','estarás','estará','estaremos','estaréis','estarán'
}

# Diccionario ampliado para mapear localidades a provincias.
# Es crucial para el filtrado por provincia. Se puede seguir ampliando.
MUNICIPIO_A_PROVINCIA = {
    # Albacete
    "Albacete": "Albacete", "Hellín": "Albacete", "Villarrobledo": "Albacete",
    "Almansa": "Albacete", "La Roda": "Albacete", "Caudete": "Albacete",
    "Tobarra": "Albacete", "Tarazona de la Mancha": "Albacete", "Madrigueras": "Albacete",
    "Chinchilla de Monte-Aragón": "Albacete", "Yeste": "Albacete", "Elche de la Sierra": "Albacete",
    "Munera": "Albacete", "Pozo Cañada": "Albacete", "Alcaraz": "Albacete",

    # Ciudad Real
    "Ciudad Real": "Ciudad Real", "Puertollano": "Ciudad Real", "Tomelloso": "Ciudad Real",
    "Alcázar de San Juan": "Ciudad Real", "Valdepeñas": "Ciudad Real", "Manzanares": "Ciudad Real",
    "Daimiel": "Ciudad Real", "La Solana": "Ciudad Real", "Campo de Criptana": "Ciudad Real",
    "Miguelturra": "Ciudad Real", "Socuéllamos": "Ciudad Real", "Bolaños de Calatrava": "Ciudad Real",
    "Villarrubia de los Ojos": "Ciudad Real", "Herencia": "Ciudad Real", "Almagro": "Ciudad Real",
    "Malagón": "Ciudad Real", "Pedro Muñoz": "Ciudad Real", "Argamasilla de Alba": "Ciudad Real",
    "Almodóvar del Campo": "Ciudad Real", "Moral de Calatrava": "Ciudad Real",
    "Villanueva de los Infantes": "Ciudad Real",

    # Cuenca
    "Cuenca": "Cuenca", "Tarancón": "Cuenca", "Quintanar del Rey": "Cuenca",
    "San Clemente": "Cuenca", "Las Pedroñeras": "Cuenca", "Mota del Cuervo": "Cuenca",
    "Iniesta": "Cuenca", "Horcajo de Santiago": "Cuenca", "Casasimarro": "Cuenca",
    "Villamayor de Santiago": "Cuenca", "El Provencio": "Cuenca", "Motilla del Palancar": "Cuenca",
    "Honrubia": "Cuenca", "Las Mesas": "Cuenca", "Huete": "Cuenca", "Belmonte": "Cuenca",
    "Villanueva de la Jara": "Cuenca", "Priego": "Cuenca", "Landete": "Cuenca",
    "Carboneras de Guadazaón": "Cuenca", "Beteta": "Cuenca",

    # Guadalajara
    "Guadalajara": "Guadalajara", "Azuqueca de Henares": "Guadalajara", "Alovera": "Guadalajara",
    "El Casar": "Guadalajara", "Cabanillas del Campo": "Guadalajara", "Marchamalo": "Guadalajara",
    "Villanueva de la Torre": "Guadalajara", "Torrejón del Rey": "Guadalajara", "Sigüenza": "Guadalajara",
    "Molina de Aragón": "Guadalajara", "Yebes": "Guadalajara", "Chiloeches": "Guadalajara",
    "Mondéjar": "Guadalajara", "Pioz": "Guadalajara", "Brihuega": "Guadalajara",
    "Jadraque": "Guadalajara", "Cifuentes": "Guadalajara", "Pastrana": "Guadalajara",

    # Toledo
    "Toledo": "Toledo", "Talavera de la Reina": "Toledo", "Illescas": "Toledo",
    "Seseña": "Toledo", "Torrijos": "Toledo", "Ocaña": "Toledo", "Fuensalida": "Toledo",
    "Yuncos": "Toledo", "Quintanar de la Orden": "Toledo", "Sonseca": "Toledo",
    "Bargas": "Toledo", "Madridejos": "Toledo", "Consuegra": "Toledo", "Mora": "Toledo",
    "Villacañas": "Toledo", "La Puebla de Montalbán": "Toledo", "Olías del Rey": "Toledo",
    "Argés": "Toledo", "Esquivias": "Toledo", "Casarrubios del Monte": "Toledo",
    "Yepes": "Toledo", "Corral de Almaguer": "Toledo", "El Toboso": "Toledo",
    "Tembleque": "Toledo", "La Guardia": "Toledo",

    # Comarcas o zonas genéricas
    "Castilla-La Mancha": "Castilla-La Mancha",
    "Castilla la Mancha": "Castilla-La Mancha",
    "La Mancha": "Castilla-La Mancha",
    "Sierra de Alcaraz": "Albacete",
    "Campos de Montiel": "Ciudad Real",
    "La Alcarria": "Guadalajara", # También parte en Cuenca
    "Serranía de Cuenca": "Cuenca",
    "La Sagra": "Toledo"
    # (Aquí iría el diccionario completo de dorotea.py, lo omito por brevedad)
}


def obtener_provincia(localidad: str) -> str:
    """Devuelve la provincia de una localidad usando el diccionario."""
    # Búsqueda exacta primero
    provincia = MUNICIPIO_A_PROVINCIA.get(localidad)
    if provincia:
        return provincia
    
    # Si no se encuentra, buscar si la localidad es una subcadena de una clave
    # (ej. "Ayuntamiento de Cuenca" -> "Cuenca")
    for key, value in MUNICIPIO_A_PROVINCIA.items():
        if key in localidad:
            return value
            
    return "Desconocida"
# ==========================================

# --- CONFIGURACIÓN Y CLIENTES ---
gcp_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if not gcp_credentials_path:
    print("Fallo: La variable de entorno 'GOOGLE_APPLICATION_CREDENTIALS' no está configurada.")
    sys.exit(1)
gcp_project_id = os.getenv('GCP_PROJECT_ID', None)
gcp_location = os.getenv('GCP_LOCATION', 'us-central1')
if not gcp_project_id:
    print("Fallo: La variable de entorno 'GCP_PROJECT_ID' no está configurada.")
    sys.exit(1)

try:
    gcp_tts_client = texttospeech.TextToSpeechClient.from_service_account_file(gcp_credentials_path)
    translate_client = translate.Client()
    vertexai.init(project=gcp_project_id, location=gcp_location)
    print("✅ Clientes de Google Cloud (TTS, Translate, Vertex AI) inicializados correctamente.")
except Exception as e:
    print(f"Error al inicializar los clientes de Google Cloud: {e}. Revisa tus credenciales y configuración del proyecto.")
    sys.exit(1)

# =================================================================================
# DECORADOR DE REINTENTOS PARA LAS LLAMADAS A API - MOVIDO ARRIBA
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
# INICIALIZACIÓN DE GEMINI (SDK NUEVO O VIEJO) - CORREGIDO
# =================================================================================
USE_NEW_SDK = False
try:
    from google.cloud import generativelanguage as glm
    model = glm.GenerativeModel("gemini-2.5-flash-lite")
    USE_NEW_SDK = True
    print("✅ Usando SDK nuevo de Gemini (google-cloud-generativelanguage).")
except ImportError:
    try:
        from vertexai.generative_models import GenerativeModel
        model = GenerativeModel("gemini-2.5-flash-lite")
        USE_NEW_SDK = False
        print("⚠️ Usando SDK viejo de VertexAI (deprecado en 2026).")
    except ImportError:
        print("❌ No se pudo importar ningún SDK de Gemini")
        sys.exit(1)

# --- Wrapper unificado ---
@retry_on_failure(retries=3, delay=5, backoff=2)
def generar_texto_con_gemini(prompt: str) -> str:
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

# =================================================================================
# UTILIDADES DE TEXTO: NORMALIZACIÓN, TOKENS, N-GRAMS, SIMILITUD
# =================================================================================

_EMOJI_RE = re.compile(
    "["                     # rangos comunes de emojis
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002700-\U000027BF"
    "\U0001F900-\U0001F9FF"
    "\U00002600-\U000026FF"
    "]+", flags=re.UNICODE
)

URL_RE = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)
HASHTAG_RE = re.compile(r'#[\wáéíóúüñ]+', re.IGNORECASE)
MENTION_RE = re.compile(r'@\w+', re.IGNORECASE)
DATE_RE = re.compile(
    r'\b(\d{1,2}[/\-]\d{1,2}([/\-]\d{2,4})?|\d{1,2}\s+de\s+[a-záéíóú]+(\s+de\s+\d{4})?)\b',
    re.IGNORECASE
)
TIME_RE = re.compile(r'\b\d{1,2}:\d{2}(\s*h)?\b', re.IGNORECASE)
DIGITS_RE = re.compile(r'\b\d{3,}\b')

def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

def normalize_text_for_similarity(text: str) -> str:
    if not text:
        return ""
    t = html.unescape(text)
    t = URL_RE.sub(' ', t)
    t = HASHTAG_RE.sub(lambda m: m.group(0)[1:] + ' ', t)  # conserva palabra #fiesta -> 'fiesta'
    t = MENTION_RE.sub(' ', t)
    t = _EMOJI_RE.sub(' ', t)
    t = DATE_RE.sub(' ', t)
    t = TIME_RE.sub(' ', t)
    t = DIGITS_RE.sub(' ', t)
    t = strip_accents(t.lower())
    # quitar puntuación conservando espacios
    t = re.sub(r'[^a-zñáéíóúü\s]', ' ', t)
    # normaliza espacios
    t = re.sub(r'\s+', ' ', t).strip()
    # quitar stopwords básicas
    tokens = [w for w in t.split() if w not in SPANISH_STOPWORDS and len(w) > 2]
    return ' '.join(tokens)

def tokens(text: str) -> list:
    return normalize_text_for_similarity(text).split()

def ngrams(seq, n=3):
    return [' '.join(seq[i:i+n]) for i in range(0, max(len(seq)-n+1, 0))]

def jaccard_ngrams(text1: str, text2: str, n=NGRAM_N) -> float:
    t1 = tokens(text1)
    t2 = tokens(text2)
    if not t1 or not t2:
        return 0.0
    n1 = set(ngrams(t1, n))
    n2 = set(ngrams(t2, n))
    if not n1 or not n2:
        return 0.0
    inter = len(n1 & n2)
    union = len(n1 | n2)
    return inter / union if union else 0.0

def composite_similarity(text1: str, text2: str) -> float:
    """Combina difflib + Jaccard n-gram + (opcional) RapidFuzz token_set_ratio."""
    if not text1 or not text2:
        return 0.0
    # base difflib sobre texto NORMALIZADO (mejor que crudo)
    d = difflib.SequenceMatcher(None, normalize_text_for_similarity(text1), normalize_text_for_similarity(text2)).ratio()
    j = jaccard_ngrams(text1, text2, n=NGRAM_N)
    if RAPIDFUZZ_AVAILABLE:
        # escalamos 0..100 a 0..1
        r = fuzz.token_set_ratio(text1, text2) / 100.0
        score = 0.45*d + 0.35*j + 0.20*r
    else:
        score = 0.60*d + 0.40*j
    return score

def stable_text_hash(text: str) -> str:
    return hashlib.md5(normalize_text_for_similarity(text).encode('utf-8')).hexdigest()


# =================================================================================
# FUNCIONES DE MASTERIZACIÓN Y AUDIO
# =================================================================================

def masterizar_a_lufs(audio_segment: AudioSegment, target_lufs: float = TARGET_LUFS) -> AudioSegment:
    if not LOUDNORM_AVAILABLE:
        print(f"      📻 Usando normalización básica (PyLoudnorm no disponible)")
        return normalize(audio_segment)
    try:
        audio_data = np.array(audio_segment.get_array_of_samples())
        if audio_segment.channels == 2:
            audio_data = audio_data.reshape((-1, 2))
        if audio_segment.sample_width == 2:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_segment.sample_width == 4:
            audio_data = audio_data.astype(np.float32) / 2147483648.0
        meter = pyln.Meter(audio_segment.frame_rate)
        loudness = meter.integrated_loudness(audio_data)
        audio_normalized = pyln.normalize.loudness(audio_data, loudness, target_lufs)
        if audio_segment.sample_width == 2:
            audio_int = (audio_normalized * 32767).astype(np.int16)
        else:
            audio_int = (audio_normalized * 2147483647).astype(np.int32)
        if audio_segment.channels == 2:
            audio_int = audio_int.flatten()
        masterized_audio = AudioSegment(
            audio_int.tobytes(),
            frame_rate=audio_segment.frame_rate,
            sample_width=audio_segment.sample_width,
            channels=audio_segment.channels
        )
        print(f"      🎛️ Audio masterizado a {target_lufs} LUFS (loudness original: {loudness:.1f} LUFS)")
        return masterized_audio
    except Exception as e:
        print(f"      ⚠️ Error en masterización LUFS: {e}. Usando normalización básica.")
        return normalize(audio_segment)

def roman_to_int(s: str) -> int:
    """Convierte un número romano a entero."""
    roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    for i in range(len(s)):
        if i > 0 and roman_map[s[i]] > roman_map[s[i-1]]:
            result += roman_map[s[i]] - 2 * roman_map[s[i-1]]
        else:
            result += roman_map[s[i]]
    return result

def numero_a_ordinal_espanol(num: int, genero: str = 'masculino') -> str:
    """
    Convierte un número a su forma ordinal en español.
    
    Args:
        num: Número entero a convertir
        genero: 'masculino' o 'femenino' para concordancia
    
    Returns:
        Forma ordinal del número en español
    """
    # Diccionario de ordinales básicos
    ordinales_masculinos = {
        1: "primer", 2: "segundo", 3: "tercer", 4: "cuarto", 5: "quinto",
        6: "sexto", 7: "séptimo", 8: "octavo", 9: "noveno", 10: "décimo",
        11: "undécimo", 12: "duodécimo", 13: "decimotercer", 14: "decimocuarto",
        15: "decimoquinto", 16: "decimosexto", 17: "decimoséptimo", 
        18: "decimoctavo", 19: "decimonoveno", 20: "vigésimo",
        21: "vigésimo primer", 22: "vigésimo segundo", 23: "vigésimo tercer",
        24: "vigésimo cuarto", 25: "vigésimo quinto", 26: "vigésimo sexto",
        27: "vigésimo séptimo", 28: "vigésimo octavo", 29: "vigésimo noveno",
        30: "trigésimo", 40: "cuadragésimo", 50: "quincuagésimo",
        60: "sexagésimo", 70: "septuagésimo", 80: "octogésimo",
        90: "nonagésimo", 100: "centésimo"
    }
    
    ordinales_femeninos = {
        1: "primera", 2: "segunda", 3: "tercera", 4: "cuarta", 5: "quinta",
        6: "sexta", 7: "séptima", 8: "octava", 9: "novena", 10: "décima",
        11: "undécima", 12: "duodécima", 13: "decimotercera", 14: "decimocuarta",
        15: "decimoquinta", 16: "decimosexta", 17: "decimoséptima", 
        18: "decimoctava", 19: "decimonovena", 20: "vigésima",
        21: "vigésima primera", 22: "vigésima segunda", 23: "vigésima tercera",
        24: "vigésima cuarta", 25: "vigésima quinta", 26: "vigésima sexta",
        27: "vigésima séptima", 28: "vigésima octava", 29: "vigésima novena",
        30: "trigésima", 40: "cuadragésima", 50: "quincuagésima",
        60: "sexagésima", 70: "septuagésima", 80: "octogésima",
        90: "nonagésima", 100: "centésima"
    }
    
    ordinales = ordinales_masculinos if genero == 'masculino' else ordinales_femeninos
    
    if num in ordinales:
        return ordinales[num]
    
    # Para números más grandes, usar el número cardinal con el sufijo º/ª
    # Pero para TTS es mejor usar la forma completa cuando sea posible
    if num > 100:
        # Retornar el número seguido de un indicador ordinal
        return f"{num}º" if genero == 'masculino' else f"{num}ª"
    
    # Para números compuestos entre decenas
    if 20 < num < 100:
        decena = (num // 10) * 10
        unidad = num % 10
        if unidad == 0:
            return ordinales.get(decena, str(num))
        
        decena_ord = ordinales.get(decena, "")
        unidad_ord = ordinales.get(unidad, "")
        
        if decena_ord and unidad_ord:
            # Ajustar para concordancia correcta
            if genero == 'masculino':
                return f"{decena_ord} {unidad_ord}"
            else:
                return f"{decena_ord} {unidad_ord}"
    
    # Fallback: devolver el número como string
    return str(num)

def detectar_contexto_ordinal(texto_antes: str, texto_despues: str) -> bool:
    """
    Detecta si el contexto sugiere uso ordinal del número romano.
    
    Args:
        texto_antes: Texto que precede al número romano
        texto_despues: Texto que sigue al número romano
    
    Returns:
        True si el contexto sugiere uso ordinal
    """
    # Palabras que típicamente preceden a ordinales
    palabras_antes_ordinal = [
        'el', 'la', 'del', 'de la', 'al', 'a la', 'en el', 'en la',
        'para el', 'para la', 'desde el', 'desde la', 'hasta el', 'hasta la'
    ]
    
    # Palabras que típicamente siguen a ordinales
    palabras_despues_ordinal = [
        'edición', 'congreso', 'conferencia', 'semana', 'mes', 'año', 'siglo',
        'jornada', 'festival', 'feria', 'exposición', 'muestra', 'encuentro',
        'reunión', 'asamblea', 'sesión', 'capítulo', 'temporada', 'episodio',
        'acto', 'escena', 'parte', 'sección', 'fase', 'etapa', 'ronda',
        'día', 'vez', 'lugar', 'puesto', 'premio', 'posición', 'aniversario'
    ]
    
    texto_antes_lower = texto_antes.lower().strip()
    texto_despues_lower = texto_despues.lower().strip()
    
    # Verificar palabras antes
    for palabra in palabras_antes_ordinal:
        if texto_antes_lower.endswith(palabra):
            return True
    
    # Verificar palabras después
    primera_palabra_despues = texto_despues_lower.split()[0] if texto_despues_lower else ""
    if primera_palabra_despues in palabras_despues_ordinal:
        return True
    return False

def detectar_genero_contexto(texto_despues: str) -> str:
    """
    Detecta el género basándose en la palabra que sigue.
    
    Args:
        texto_despues: Texto que sigue al número romano
    
    Returns:
        'masculino' o 'femenino'
    """
    palabras_femeninas = [
        'edición', 'semana', 'conferencia', 'jornada', 'feria', 'exposición',
        'muestra', 'reunión', 'asamblea', 'sesión', 'temporada', 'parte',
        'sección', 'fase', 'etapa', 'ronda', 'vez', 'posición'
    ]
    
    primera_palabra = texto_despues.lower().strip().split()[0] if texto_despues else ""
    
    if primera_palabra in palabras_femeninas:
        return 'femenino'
    
    return 'masculino'

def preprocesar_texto_para_tts(texto: str) -> str:
    """
    Preprocesa el texto para TTS, convirtiendo números romanos a su forma apropiada.
    """
    import re
    
    # Patrón mejorado para capturar números romanos con contexto
    roman_regex = r'(\S*\s*)?\b(M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))\b(\s*\S*)?'
    
    is_ssml = texto.strip().startswith('<speak>')
    
    def replacer(match):
        contexto_antes = match.group(1) if match.group(1) else ""
        roman_numeral = match.group(2)
        contexto_despues = match.group(3) if match.group(3) else ""
        
        # Si es un número romano de una sola letra, verificar si realmente es romano
        if len(roman_numeral) == 1 and roman_numeral in "IVXLCDM":
            # Verificar contexto para evitar falsos positivos
            if not detectar_contexto_ordinal(contexto_antes, contexto_despues):
                return match.group(0)  # Devolver sin cambios
        
        try:
            integer_value = roman_to_int(roman_numeral)
            
            if integer_value > 0 and integer_value <= 100:
                # Detectar si debe ser ordinal basándose en el contexto
                es_ordinal = detectar_contexto_ordinal(contexto_antes, contexto_despues)
                
                if es_ordinal:
                    # Detectar género para concordancia
                    genero = detectar_genero_contexto(contexto_despues)
                    palabra = numero_a_ordinal_espanol(integer_value, genero)
                    
                    if is_ssml:
                        # Para SSML, usar el tag sub con alias
                        return f'{contexto_antes}<sub alias="{palabra}">{roman_numeral}</sub>{contexto_despues}'
                    else:
                        return f'{contexto_antes}{palabra}{contexto_despues}'
                else:
                    # Si no es ordinal, convertir a cardinal
                    from num2words import num2words
                    palabra = num2words(integer_value, lang='es')
                    
                    if is_ssml:
                        return f'{contexto_antes}<sub alias="{palabra}">{roman_numeral}</sub>{contexto_despues}'
                    else:
                        return f'{contexto_antes}{palabra}{contexto_despues}'
                        
        except (KeyError, IndexError, ValueError):
            return match.group(0)  # Devolver sin cambios si hay error
        
        return match.group(0)
    
    if is_ssml:
        # Procesar contenido dentro de tags <speak>
        content_match = re.search(r"<speak>(.*)</speak>", texto, re.DOTALL)
        if content_match:
            content = content_match.group(1)
            processed_content = re.sub(roman_regex, replacer, content, flags=re.IGNORECASE)
            return f"<speak>{processed_content}</speak>"
        else:
            return texto
    else:
        # Procesar texto plano
        return re.sub(roman_regex, replacer, texto, flags=re.IGNORECASE)

def corregir_palabras_deletreadas_tts(texto: str) -> str:
    """
    Corrige palabras específicas que el TTS de Google tiende a deletrear 
    en lugar de pronunciar como palabras completas.
    
    Args:
        texto: El texto a procesar (puede ser SSML o texto plano)
    
    Returns:
        Texto corregido con las palabras problemáticas ajustadas
    """
    import re
    
    # Detectar si es SSML
    is_ssml = texto.strip().startswith('<speak>')
    
    # Cargar diccionarios desde la configuración global
    pronunciation_config = CONFIG.get('pronunciation', {})
    correcciones_palabras = pronunciation_config.get('correcciones', {})
    siglas_para_deletrear = pronunciation_config.get('siglas', {})
    
    # Si no hay configuración (fallback), usar valores por defecto mínimos o vacíos
    if not correcciones_palabras:
        correcciones_palabras = {
            'RECAMDER': 'Recamder',
            'LEADER': 'Leader', 
            'FEADER': 'Feader',
            'CEDER': 'Ceder',
            'AYUNTAMIENTO': 'Ayuntamiento'
        }
    
    if not siglas_para_deletrear:
        siglas_para_deletrear = {
            'UE': 'U E',
            'PP': 'P P',
            'UGT': 'U G T'
        }
    
    # Función auxiliar para aplicar correcciones
    def aplicar_correccion(texto_procesado, diccionario_correcciones):
        for palabra_problema, correccion in diccionario_correcciones.items():
            # Buscar la palabra completa (no como parte de otra palabra)
            patron = rf'\b{re.escape(palabra_problema)}\b'
            texto_procesado = re.sub(patron, correccion, texto_procesado, flags=re.IGNORECASE)
        return texto_procesado
    
    # Función para manejar texto entre paréntesis
    def corregir_parentesis(texto_procesado):
        """
        Mejora la pronunciación de texto entre paréntesis.
        """
        def parentesis_replacer(match):
            contenido = match.group(1).strip()
            
            # Verificar si es una sigla conocida
            if contenido.upper() in siglas_para_deletrear:
                espaciado = siglas_para_deletrear[contenido.upper()]
                if is_ssml:
                    return f'(<sub alias="{espaciado}">{contenido}</sub>)'
                else:
                    return f'({espaciado})'
            
            # Si está todo en mayúsculas y es corto, verificar si es palabra conocida
            if contenido.isupper():
                if contenido in correcciones_palabras:
                    corregido = correcciones_palabras[contenido]
                    if is_ssml:
                        return f'(<sub alias="{corregido}">{contenido}</sub>)'
                    else:
                        return f'({corregido})'
                # Si no está en el diccionario pero es corto, podría ser sigla
                elif len(contenido) <= 5 and contenido.isalpha():
                    # Deletrear por defecto las siglas cortas desconocidas
                    espaciado = ' '.join(contenido)
                    if is_ssml:
                        return f'(<sub alias="{espaciado}">{contenido}</sub>)'
                    else:
                        return f'({espaciado})'
            
            return match.group(0)  # No cambiar si no cumple criterios
        
        texto_procesado = re.sub(r'\(([^)]+)\)', parentesis_replacer, texto_procesado)
        return texto_procesado
    
    # Aplicar transformaciones según el tipo de texto
    if is_ssml:
        # Extraer contenido entre tags <speak>
        content_match = re.search(r"<speak>(.*)</speak>", texto, re.DOTALL)
        if content_match:
            content = content_match.group(1)
            
            # Aplicar correcciones de palabras
            content = aplicar_correccion(content, correcciones_palabras)
            content = aplicar_correccion(content, siglas_para_deletrear)
            
            # Corregir paréntesis
            content = corregir_parentesis(content)
            
            # Manejar palabras problemáticas con tags SSML
            for palabra in correcciones_palabras:
                if palabra in content and not f'<sub alias=' in content:
                    # Si la palabra está pero no tiene ya un tag sub
                    patron = rf'\b{re.escape(palabra)}\b'
                    reemplazo = f'<sub alias="{correcciones_palabras[palabra]}">{palabra}</sub>'
                    content = re.sub(patron, reemplazo, content, flags=re.IGNORECASE)
            
            return f"<speak>{content}</speak>"
        else:
            return texto
    else:
        # Texto plano
        texto_procesado = texto
        
        # Aplicar todas las correcciones
        texto_procesado = aplicar_correccion(texto_procesado, correcciones_palabras)
        texto_procesado = aplicar_correccion(texto_procesado, siglas_para_deletrear)
        texto_procesado = corregir_parentesis(texto_procesado)
        
        return texto_procesado


def corregir_numeros_con_puntos_tts(texto: str) -> str:
    """
    Corrige la lectura de números con puntos como separadores de miles para TTS.
    También maneja números grandes sin separadores (>= 10000).
    """
    import re
    from num2words import num2words

    is_ssml = texto.strip().startswith('<speak>')
    
    # 1. Patrón ESTRICTO para puntos de miles (Español). Ej: 1.234, 300.000
    # Ya NO acepta comas ni espacios para evitar conflictos con decimales o listas.
    pattern_dots = r'(?<![a-zA-Z])\b\d{1,3}(?:\.\d{3})+\b'
    
    # 2. Patrón para números grandes SIN separadores (>= 10000)
    # Evitamos 4 dígitos para no romper años (2025).
    # Añadimos (?<![\.,]) para evitar que coincida con la parte decimal de un número (ej: 3.14159)
    pattern_plain = r'(?<![\.,])\b\d{5,}\b'

    def replacer(match):
        numero_str = match.group(0)
        numero_sin_puntos = re.sub(r'\.', '', numero_str)
        try:
            numero_int = int(numero_sin_puntos)
            palabra = num2words(numero_int, lang='es')
            
            if is_ssml:
                return f'<sub alias="{palabra}">{numero_str}</sub>'
            else:
                return palabra
        except (ValueError, OverflowError):
            return numero_str

    # Procesar contenido
    if is_ssml:
        content_match = re.search(r"<speak>(.*)</speak>", texto, re.DOTALL)
        if content_match:
            content = content_match.group(1)
            # Primero puntos
            content = re.sub(pattern_dots, replacer, content)
            # Luego planos
            content = re.sub(pattern_plain, replacer, content)
            return f"<speak>{content}</speak>"
        else:
            return texto
    else:
        texto = re.sub(pattern_dots, replacer, texto)
        texto = re.sub(pattern_plain, replacer, texto)
        return texto


    # (Código de pruebas eliminado para limpieza)
    pass
    


import re

def limpiar_artefactos_ia(texto: str) -> str:
    """
    Limpia texto generado por IA eliminando marcadores de formato,
    anotaciones de voz y elementos estructurales.
    """
    # 1. Eliminar anotaciones de voz y música entre paréntesis.
    # Ej: (voz en off), (música alegre)
    texto_limpio = re.sub(
        r'\s*\([^)]*?(dicho|le[ée]|leer|voz|tono|sonido|efecto|m[úu]sica)[^)]*?\)\s*',
        ' ', texto, flags=re.IGNORECASE
    )
    # 1.1. Eliminar anotaciones entre corchetes.
    # Ej: [efecto de sonido]
    texto_limpio = re.sub(
        r'\s*\[[^\]]*?(dicho|le[ée]|leer|voz|tono|sonido|efecto|m[úu]sica)[^\]]*?\]\s*',
        ' ', texto_limpio, flags=re.IGNORECASE
    )

    # 2. Eliminar anotaciones de voz SIN paréntesis.
    # Ej: "lee con fuerza"
    patron_sin_parentesis = r'\b(lee|leer|lei|leí|leído)\s+con\s+\w+\b'
    texto_limpio = re.sub(patron_sin_parentesis, ' ', texto_limpio, flags=re.IGNORECASE)
    
    # 2.1. Eliminar instrucciones de música sin paréntesis.
    # Ej: "música de fondo que se desvanece"
    texto_limpio = re.sub(r'\b(m[úu]sica de.*?)(que se desvanece|al final|de fondo)', '', texto_limpio, flags=re.IGNORECASE)

    # 2.2. Eliminar símbolos extraños que a veces aparecen.
    texto_limpio = texto_limpio.replace('¿?¿?¿?', '')

    # 3. Conservar contenido de markdown pero quitar los asteriscos de formato.
    texto_limpio = re.sub(r'\*{1,2}([^*]+?)\*{1,2}', r'\1', texto_limpio)

    # 4. Eliminar etiquetas de sección que la IA pueda generar, como "RESUMEN:"
    texto_limpio = re.sub(r'^[A-ZÁÉÍÓÚ\s]+:$', '', texto_limpio, flags=re.MULTILINE)
    
    # Corrige la lectura de rangos de años como "2025/2026"
    texto_limpio = re.sub(r'(\d{4})/(\d{4})', r'\1 a \2', texto_limpio)

    # 5. Limpiar líneas que solo contengan numeración o viñetas.
    lineas = []
    for linea in texto_limpio.split('\n'):
        linea_limpia = linea.strip()
        # Si la línea no está vacía y no es solo una viñeta/número, la conservamos.
        if linea_limpia and not re.match(r'^\s*(\d+\.|\*+)\s*$', linea_limpia):
            lineas.append(linea_limpia)
            
    # 6. Unir las líneas limpias respetando los saltos de línea (CRUCIAL para las cortinillas).
    texto_final = '\n'.join(lineas)
    # Normalizar solo espacios horizontales (tabuladores y espacios extra), respetando el \n
    texto_final = re.sub(r'[ \t]+', ' ', texto_final).strip()
    
    return texto_final
def preprocesar_texto_para_fechas(texto: str) -> str:
    """
    Neutraliza referencias temporales relativas (como 'hoy', 'ayer') en el texto
    para evitar que la IA las repita incorrectamente en el futuro.
    """
    # Patrón para "hoy, [dd] de [mes]" o "[dd] de [mes], hoy" y variantes.
    # Captura (hoy/ayer/etc.), el espacio opcional, la fecha, y el contexto alrededor.
    patron = r'\b(hoy|ayer|mañana|esta mañana|esta tarde|anoche)\b([,.\s]+)(\d{1,2}\s+de\s+\w+)'
    
    def reemplazo_inteligente(match):
        # Simplemente eliminamos la palabra relativa ('hoy', 'ayer', etc.) y el separador.
        # Dejamos solo la fecha absoluta: "el 10 de septiembre".
        fecha_absoluta = match.group(3)
        # Devolvemos la fecha, idealmente con un artículo para que suene más natural.
        return f"el {fecha_absoluta}"

    # Aplicamos el reemplazo
    texto_procesado = re.sub(patron, reemplazo_inteligente, texto, flags=re.IGNORECASE)
    
    # Podríamos añadir más patrones aquí si detectamos otros casos
    
    return texto_procesado

def reemplazar_urls_por_mencion(texto: str) -> str:
    """
    Reemplaza URLs en el texto por una mención genérica para el podcast.
    """
    # Expresión regular para encontrar URLs.
    url_pattern = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)

    # Texto de reemplazo directo y claro.
    texto_reemplazo = " Para más detalles, puedes consultar los enlaces en la publicación original. "

    # Se busca y reemplaza cualquier URL encontrada en el texto.
    texto_modificado = url_pattern.sub(texto_reemplazo, texto)

    return texto_modificado

@retry_on_failure(retries=2, delay=2)
def extraer_localidad_con_ia(texto_noticia: str) -> str:
    """Usa la IA para extraer la localidad principal de un texto."""
    if not texto_noticia:
        return "Castilla la Mancha"
    
    prompt = f"""
    Analiza el siguiente texto de una noticia y devuelve ÚNICAMENTE el nombre de la localidad principal (pueblo o ciudad) mencionada.
    - Si se mencionan varias, devuelve la más relevante para la noticia.
    - No incluyas la provincia. Solo el nombre del municipio.
    - Si no puedes identificar una localidad clara, responde 'Desconocida'.

    EJEMPLOS DE RESPUESTA:
    - Hellín
    - Villanueva de los Infantes
    - Desconocida

    TEXTO:
    ---
    {texto_noticia}
    ---
    
    LOCALIDAD:
    """
    localidad = generar_texto_con_gemini(prompt).strip()
    # Pequeña limpieza por si la IA añade comillas
    localidad = localidad.replace('"', '').replace("'", "")
    
    print(f"      🌍 Localidad extraída por IA: {localidad}")
    return localidad if localidad else "Desconocida"

def es_noticia_valida(texto: str) -> bool:
    if len(texto.split()) < 16:
        print(f"      🕵️‍♂️ Ignorando por ser demasiado corto (menos de 16 palabras).")
        return False
    prompt = mcmcn_prompts.PromptsAnalisis.clasificacion_noticia(texto=texto)
    respuesta = generar_texto_con_gemini(prompt)
    if not respuesta:
        return False
    print(f"      🕵️‍♂️ IA ha clasificado el texto '{texto[:70].strip()}...' como: {respuesta.upper()}")
    return respuesta.upper() == 'INFORMATIVO'

def resumir_noticia_con_google(texto: str, idioma_destino: str, fuente_original: str = "") -> str:
    prompt = mcmcn_prompts.PromptsAnalisis.resumen_noticia(
        texto=texto,
        idioma_destino=idioma_destino,
        fuente_original=fuente_original
    )
    return generar_texto_con_gemini(prompt)

def convertir_ssml_a_texto_plano(ssml_text: str) -> str:
    """
    Convierte SSML a texto plano preservando la pronunciación definida en alias.
    Específicamente diseñado para voces 'Journey' que no soportan SSML.
    """
    # 1. Reemplazar <sub alias="pronunciación">texto</sub> por "pronunciación"
    # Captura el alias y descarta el texto original y los tags
    text = re.sub(r'<sub\s+alias=["\']([^"\']+)["\'][^>]*>.*?</sub>', r'\1', ssml_text, flags=re.IGNORECASE | re.DOTALL)
    
    # 2. Reemplazar <break> por signos de puntuación para simular pausas
    # <break time="..."/> -> " ... "
    text = re.sub(r'<break[^>]*>', '... ', text, flags=re.IGNORECASE)
    
    # 3. Eliminar cualquier otra etiqueta XML/SSML restante (<speak>, <p>, <s>, etc.)
    text = re.sub(r'<[^>]+>', '', text)
    
    # 4. Limpieza final de espacios y entidades HTML
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

@retry_on_failure(retries=3, delay=3, backoff=2)
def sintetizar_ssml_a_audio(ssml: str, voz: str = VOICE_NAME) -> AudioSegment:
    ssml_corregido = preprocesar_texto_para_tts(ssml)
    ssml_corregido = corregir_palabras_deletreadas_tts(ssml_corregido)
    ssml_corregido = corregir_numeros_con_puntos_tts(ssml_corregido)
    
    if ssml_corregido != ssml:
        print(f"      ✅ Texto preprocesado para pronunciación (números, siglas, etc.).")
    
    try:
        # Lógica específica para voces Journey (no soportan SSML)
        if "Journey" in voz:
            texto_plano = convertir_ssml_a_texto_plano(ssml_corregido)
            # print(f"      ℹ️ Voz Journey detectada. Convirtiendo SSML a texto plano: {texto_plano[:50]}...")
            input_text = texttospeech.SynthesisInput(text=texto_plano)
        else:
            input_text = texttospeech.SynthesisInput(ssml=ssml_corregido)
            
        voice = texttospeech.VoiceSelectionParams(
            language_code=LANGUAGE_CODE,
            name=voz,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            sample_rate_hertz=SAMPLE_RATE,
            speaking_rate=0.89
        )
        response = gcp_tts_client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )
        audio_segment = AudioSegment.from_file(io.BytesIO(response.audio_content), format="mp3")
        print(f"      Volumen generado ({'Texto' if 'Journey' in voz else 'SSML'}): {audio_segment.max_dBFS:.2f} dBFS")
        return audio_segment
    except Exception as e:
        raise e

def limpiar_html(texto_html: str) -> str:
    texto_limpio = re.sub(r'<[^>]+>', '', texto_html)
    return html.unescape(texto_limpio)

# (Función generar_guion_noticia eliminada por estar incompleta y sin uso)

def leer_pregunta_del_dia() -> Dict[str, str] | None:
    """
    Lee los mensajes de la audiencia y devuelve solo el que corresponde al día actual.
    Formato esperado por mensaje:
    fecha: DD-MM-YYYY
    autor: Nombre del Oyente
    texto: Mensaje del oyente...
    """
    if not os.path.exists(AUDIENCE_QUESTIONS_FILE):
        print(f"      ℹ️ No se encontró el archivo '{AUDIENCE_QUESTIONS_FILE}'. Se omitirá la sección de audiencia.")
        return None

    try:
        with open(AUDIENCE_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            bloques = f.read().split('---')
        
        fecha_hoy = datetime.now().date()

        for bloque in bloques:
            if not bloque.strip():
                continue

            mensaje = {}
            for linea in bloque.strip().split('\n'):
                if ':' in linea:
                    clave, valor = linea.split(':', 1)
                    mensaje[clave.strip().lower()] = valor.strip()
            
            if 'fecha' in mensaje:
                try:
                    fecha_mensaje = datetime.strptime(mensaje['fecha'], '%d-%m-%Y').date()
                    if fecha_mensaje == fecha_hoy:
                        if 'autor' in mensaje and 'texto' in mensaje:
                            print(f"      ✅ Mensaje de la audiencia encontrado para hoy ({fecha_hoy.strftime('%d-%m-%Y')}) de '{mensaje['autor']}'.")
                            return {'autor': mensaje['autor'], 'texto': mensaje['texto']}
                except ValueError:
                    print(f"      ⚠️ Fecha en formato incorrecto en el bloque: {mensaje.get('fecha')}. Se ignora.")
                    continue
        
        print(f"      ℹ️ No se encontró ningún mensaje de la audiencia para la fecha de hoy ({fecha_hoy.strftime('%d-%m-%Y')}).")
        return None
        
    except Exception as e:
        print(f"      ❌ Error al leer el archivo de preguntas de la audiencia: {e}")
        return None

# =================================================================================
# GESTIÓN DE CACHE HÍBRIDO PARA OPTIMIZAR LLAMADAS A API
# =================================================================================

PROCESSED_NEWS_FILE = 'cache_noticias.json'
AUDIO_CACHE_DIR = 'audio_cache'
# AUDIENCE_QUESTIONS_FILE movido al inicio
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

def cargar_cache_noticias() -> Dict[str, Any]:
    if os.path.exists(PROCESSED_NEWS_FILE):
        try:
            with open(PROCESSED_NEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print("⚠️ Archivo de caché corrupto o no encontrado. Se creará uno nuevo.")
            return {}
    return {}

def guardar_cache_noticias(cache_completo: Dict[str, Any]):
    with open(PROCESSED_NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_completo, f, indent=4, ensure_ascii=False)
    print(f"✅ Caché de noticias actualizado. Total de noticias en caché: {len(cache_completo)}")

# =================================================================================
# AGRUPACIÓN Y DEDUP: NUEVAS FUNCIONES
# =================================================================================

def identificar_fuente_original(texto: str) -> str:
    print("      🔍 Identificando la fuente original con IA...")
    prompt = f"""
    Analiza el siguiente texto de una publicación de redes sociales. Identifica si menciona un organismo, ayuntamiento o institución como la fuente original de la noticia. Si lo encuentras, devuelve solo el nombre del organismo. Si no lo encuentras, devuelve "Desconocida".

    TEXTO:
    ---
    {texto}
    ---

    EJEMPLOS DE RESPUESTA:
    Ayuntamiento de Ontígola
    Mancomunidad de La Sagra Baja
    Desconocida

    RESPUESTA:"""
    respuesta = generar_texto_con_gemini(prompt)
    if respuesta and respuesta.strip() != "Desconocida":
        print(f"      ✅ Fuente original identificada: {respuesta.strip()}")
        return respuesta.strip()
    return ""

def calcular_similitud_texto(texto1: str, texto2: str) -> float:
    return composite_similarity(texto1, texto2)

def detectar_duplicados_y_similares(resumenes: list, umbral_similitud: float = DEDUP_SIMILARITY_THRESHOLD) -> list:
    print(f"\n🔍 Detectando duplicados (umbral comp.: {umbral_similitud:.2f})")
    noticias_unicas = []
    hashes_vistos = set()
    eliminados = 0

    for noticia in resumenes:
        resumen_actual = (noticia.get('resumen') or "").strip()
        if not resumen_actual:
            continue

        # ID estable por hash del texto normalizado
        h = stable_text_hash(resumen_actual)
        if h in hashes_vistos:
            eliminados += 1
            continue

        es_duplicado = False
        for existente in noticias_unicas:
            sim = calcular_similitud_texto(resumen_actual, existente.get('resumen', ''))
            if sim >= umbral_similitud:
                # combinar fuentes
                f1 = existente.get('fuente', '')
                f2 = noticia.get('fuente', '')
                if f2 and f2 not in f1:
                    existente['fuente'] = f"{f1} · {f2}" if f1 else f2
                # combinar fechas si no hay
                if 'fecha' not in existente and 'fecha' in noticia:
                    existente['fecha'] = noticia['fecha']
                es_duplicado = True
                eliminados += 1
                break

        if not es_duplicado:
            noticia_copia = noticia.copy()
            noticia_copia['id'] = h
            noticias_unicas.append(noticia_copia)
            hashes_vistos.add(h)

    print(f"    ✅ Eliminados {eliminados} duplicados. Quedan {len(noticias_unicas)} noticias únicas.")
    return noticias_unicas

# --------- EXTRACCIÓN DE ENTIDADES/KEYWORDS DINÁMICAS ---------

PROPER_NOUN_PHRASE_RE = re.compile(r'\b([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚñáéíóú\-]+(?:\s+de\s+|[\s\-])[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚñáéíóú\-]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚñáéíóú\-]+)*)\b')
QUOTED_PHRASE_RE = re.compile(r'“([^”]+)”|"([^"]+)"|\‘([^\’]+)\’|\’([^\’]+)\’')

def extract_candidate_phrases(text: str) -> list:
    phrases = []
    # hashtags como frases
    phrases += [m.group(0)[1:] for m in HASHTAG_RE.finditer(text or "")]
    # entrecomilladas
    for m in QUOTED_PHRASE_RE.finditer(text or ""):
        for g in m.groups():
            if g:
                phrases.append(g)
    # secuencias de nombres propios (Aaaa Bbbb ...)
    for m in PROPER_NOUN_PHRASE_RE.finditer(text or ""):
        phrases.append(m.group(0))
    # limpieza ligera
    cleaned = []
    for p in phrases:
        p2 = normalize_text_for_similarity(p)
        if p2 and len(p2.split()) >= 2:  # prioriza 2+ palabras
            cleaned.append(p2)
    return cleaned

def extract_ngrams_keyphrases(text: str, n=(2,3)) -> list:
    toks = tokens(text)
    keys = []
    for k in n:
        keys += ngrams(toks, k)
    # filtra solo los que no son puro stopword
    keys = [k for k in keys if any(w not in SPANISH_STOPWORDS for w in k.split())]
    return keys

def build_dynamic_key_index(resumenes: list):
    key_to_items = defaultdict(list)
    for item in resumenes:
        txt = item.get('resumen', '')
        keys = []
        keys += extract_candidate_phrases(txt)
        keys += extract_ngrams_keyphrases(txt, n=(2,3))
        # normaliza claves
        keys = [normalize_text_for_similarity(k) for k in keys]
        keys = [k for k in keys if len(k) > 3]
        for k in set(keys):  # set para no duplicar misma clave por noticia
            if k:
                key_to_items[k].append(item)
    # filtra por mínimo de apariciones
    key_to_items = {k:v for k,v in key_to_items.items() if len(v) >= KEYPHRASE_MIN_COUNT}
    # ordena por frecuencia
    sorted_keys = sorted(key_to_items.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    return sorted_keys[:MAX_DYNAMIC_KEYPHRASES]

def cluster_by_dynamic_keyphrases(resumenes: list) -> dict:
    """Devuelve bloques por claves dinámicas + noticias individuales restantes."""
    keys = build_dynamic_key_index(resumenes)
    used_ids = set()
    bloques = []
    for key, items in keys:
        bundle = []
        for it in items:
            if it.get('id') not in used_ids:
                bundle.append(it)
        if len(bundle) >= MIN_NEWS_PER_BLOCK:
            # marca usados
            for it in bundle:
                used_ids.add(it.get('id'))
            bloques.append({
                'tema': f'clave:{key}',
                'descripcion_tema': key,
                'transicion_elegante': f"En torno a «{key}», varias noticias coinciden",
                'noticias': bundle
            })
    # restantes
    restantes = [it for it in resumenes if it.get('id') not in used_ids]
    return {'bloques_tematicos': bloques, 'noticias_individuales': restantes}

# --------- FALLBACK DETERMINISTA POR PALABRAS CLAVE (AMPLIADO) ---------

STEM_GROUPS = {
    'jovenes_rural': [
        'joven','juvent','raiz','formacion','emple','emprend','talent'
    ],
    'deportes': [
        'cicl','futbol','deport','compet','torne','atlet','carrer','baloncest','nataci'
    ],
    'cultura_eventos': [
        'festival','fiest','cultur','event','celebr','tradic','music','teatr','exposic','conciert','feri'
    ],
    'astronomia': [
        'perseid','estrella','astronom','observ','cielo','meteor'
    ],
    'agricultura': [
        'agric','agricol','campo','cultiv','cosech','ganad','agro'
    ],
    'turismo': [
        'turism','turist','visit','ruta','patrimoni','monument','itinerar','sender'
    ],
    'naturaleza_escapadas': [
        'natural','rio','paisaj','valle','escap','recorr','parque','reserva','entorno'
    ]
}

def match_stem(text_norm: str, stems: list) -> bool:
    return any(st in text_norm for st in stems)

def agrupacion_simple_por_palabras_clave(resumenes: list) -> dict:
    print("\n🎯 Ejecutando agrupación simple por palabras clave (stems)...")
    grupos_detectados = defaultdict(list)
    sin_grupo = []
    for noticia in resumenes:
        resumen_norm = normalize_text_for_similarity(noticia.get('resumen',''))
        asignada = False
        for tema, stems in STEM_GROUPS.items():
            if match_stem(resumen_norm, stems):
                grupos_detectados[tema].append(noticia)
                asignada = True
                break
        if not asignada:
            sin_grupo.append(noticia)

    bloques = []
    tema_desc = {
        'jovenes_rural': 'iniciativas para jóvenes rurales',
        'deportes': 'competiciones y eventos deportivos',
        'cultura_eventos': 'eventos culturales y festividades',
        'astronomia': 'observación astronómica',
        'agricultura': 'sector agrícola y ganadero',
        'turismo': 'turismo y patrimonio',
        'naturaleza_escapadas': 'naturaleza y escapadas'
    }
    tema_trans = {
        'jovenes_rural': 'En el ámbito de las iniciativas para jóvenes rurales',
        'deportes': 'En el mundo del deporte comarcal',
        'cultura_eventos': 'En la agenda cultural de la región',
        'astronomia': 'En las noticias de astronomía',
        'agricultura': 'En el sector agrícola',
        'turismo': 'En materia de turismo y patrimonio',
        'naturaleza_escapadas': 'Para quienes buscan naturaleza y escapadas'
    }
    for tema, noticias in grupos_detectados.items():
        if len(noticias) >= MIN_NEWS_PER_BLOCK:
            bloques.append({
                'tema': tema,
                'descripcion_tema': tema_desc.get(tema, tema.replace('_',' ')) ,
                'transicion_elegante': tema_trans.get(tema, f'En {tema_desc.get(tema, tema)}'),
                'noticias': noticias
            })
            print(f"    📚 Bloque '{tema_desc.get(tema, tema)}': {len(noticias)} noticias")
        else:
            sin_grupo.extend(noticias)

    return {'bloques_tematicos': bloques, 'noticias_individuales': sin_grupo}

# --------- DEBUG ---------

def debug_noticias_antes_agrupacion(resumenes: list):
    print("\n🔍 DEBUG: Análisis de noticias antes de agrupar")
    print("=" * 60)
    for i, noticia in enumerate(resumenes):
        fuente = noticia.get('fuente', 'Sin fuente')
        resumen = noticia.get('resumen', 'Sin resumen')
        norm = normalize_text_for_similarity(resumen)[:150]
        ents = extract_candidate_phrases(resumen)
        print(f"\n📰 Noticia {i+1}: {fuente}")
        print(f"    Resumen: {resumen[:150]}{'...' if len(resumen) > 150 else ''}")
        print(f"    Norm: {norm}{'...' if len(norm)==150 else ''}")
        if ents:
            print(f"    🔎 Entidades/hashtags: {', '.join(ents[:6])}{'...' if len(ents)>6 else ''}")
    print("\n" + "=" * 60)

# --------- AGRUPACIÓN PRINCIPAL (IA + din. + fallback) ---------

def _enforce_unique_assignment(agrupado: dict) -> dict:
    """Evita que una noticia aparezca en varios bloques; prioriza primer bloque."""
    seen = set()
    nuevos_bloques = []
    for bloque in agrupado.get('bloques_tematicos', []):
        nuevas = []
        for n in bloque.get('noticias', []):
            nid = n.get('id') or stable_text_hash(n.get('resumen',''))
            if nid not in seen:
                nuevas.append(n)
                seen.add(nid)
        if len(nuevas) >= MIN_NEWS_PER_BLOCK:
            b2 = bloque.copy()
            b2['noticias'] = nuevas
            nuevos_bloques.append(b2)
    restantes = []
    for n in agrupado.get('noticias_individuales', []):
        nid = n.get('id') or stable_text_hash(n.get('resumen',''))
        if nid not in seen:
            restantes.append(n); seen.add(nid)
    return {'bloques_tematicos': nuevos_bloques, 'noticias_individuales': restantes}

def agrupar_noticias_por_temas_mejorado(resumenes: list) -> dict:
    print("\n🎯 Iniciando agrupación mejorada de noticias (Estrategia de 2 Pasos)...")
    
    # PASO 0: DEDUP (Esto no cambia)
    noticias_unicas = detectar_duplicados_y_similares(resumenes, umbral_similitud=DEDUP_SIMILARITY_THRESHOLD)

    if len(noticias_unicas) < MIN_NEWS_PER_BLOCK:
        print("    ℹ️ Muy pocas noticias para agrupar. Procesando individualmente.")
        return {"bloques_tematicos": [], "noticias_individuales": noticias_unicas}

    try:
        # --- NUEVA LÓGICA ---
        
        # PASO 1: Agrupación Lógica con IA (Obteniendo temas y IDs)
        print("\n🤖 PASO 1: Agrupación Lógica con IA (Obteniendo temas y IDs)...")
        noticias_simplificadas = json.dumps(
            [{"id": n.get("id"), "resumen": n.get("resumen")} for n in noticias_unicas],
            ensure_ascii=False, indent=2
        )
        prompt_agrupacion = mcmcn_prompts.PromptsAnalisis.agrupacion_logica_temas(noticias_simplificadas)
        respuesta_grupos = generar_texto_con_gemini(prompt_agrupacion)
        
        # Limpiar y parsear la respuesta del paso 1
        start_idx = respuesta_grupos.find('{')
        end_idx = respuesta_grupos.rfind('}')
        if start_idx == -1 or end_idx == -1:
            raise ValueError("La respuesta de la IA para agrupar no es un JSON válido.")
        json_limpio = respuesta_grupos[start_idx:end_idx+1]
        grupos_logicos = json.loads(json_limpio)
        print(f"    ✅ IA ha identificado {len(grupos_logicos)} temas.")

        # PASO 2: Enriquecimiento Creativo por cada tema
        print("\n🤖 PASO 2: Enriquecimiento Creativo con IA (Generando descripciones)...")
        bloques_tematicos = []
        used_ids = set()
        noticias_por_id = {n.get("id"): n for n in noticias_unicas}
        ids_ya_en_bloques = set() # <-- NUEVO: Para evitar duplicados entre bloques

        for tema, ids_noticias in grupos_logicos.items():
            if len(ids_noticias) < MIN_NEWS_PER_BLOCK:
                continue

            print(f"  -> Enriqueciendo tema: '{tema}'...")
            
            # --- NUEVO: Filtrar noticias que ya han sido asignadas a otro bloque ---
            ids_noticias_unicas = [nid for nid in ids_noticias if nid not in ids_ya_en_bloques]
            if len(ids_noticias_unicas) < MIN_NEWS_PER_BLOCK:
                continue

            lista_resumenes = [noticias_por_id[nid]["resumen"] for nid in ids_noticias_unicas if nid in noticias_por_id]
            resumenes_json = json.dumps(lista_resumenes, indent=2, ensure_ascii=False)

            prompt_enriquecimiento = mcmcn_prompts.PromptsCreativos.enriquecimiento_creativo_tema(tema, resumenes_json)
            respuesta_creativa = generar_texto_con_gemini(prompt_enriquecimiento)
            # --- NUEVA LÓGICA DE LIMPIEZA ---
            # Elimina el bloque de código Markdown si la IA lo añade
            json_limpio = respuesta_creativa
            if "```" in respuesta_creativa:
                # Extrae el contenido entre el primer '{' y el último '}'
                start_idx = respuesta_creativa.find('{')
                end_idx = respuesta_creativa.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_limpio = respuesta_creativa[start_idx:end_idx+1]
                else:
                    json_limpio = "" # No se encontró JSON válido
            try:
                # Usamos la variable 'json_limpio' en lugar de la original
                info_creativa = json.loads(json_limpio)
                
                # Construir el bloque temático final
                noticias_del_bloque = [noticias_por_id[nid] for nid in ids_noticias_unicas if nid in noticias_por_id]
                bloques_tematicos.append({
                    'tema': tema,
                    'descripcion_tema': info_creativa.get("descripcion", "Noticias sobre " + tema.replace("_", " ")),
                    'transicion_elegante': info_creativa.get("transicion", "A continuación, hablamos de " + tema.replace("_", " ")),
                    'noticias': noticias_del_bloque
                })
                used_ids.update(ids_noticias_unicas)
                ids_ya_en_bloques.update(ids_noticias_unicas) # <-- NUEVO: Marcar como usados
            except (json.JSONDecodeError, TypeError) as e:
                print(f"    ⚠️ Fallo al enriquecer el tema '{tema}'. Se omitirá.")
                print(f"      Respuesta recibida de la IA que causó el error: {respuesta_creativa}")
                print(f"      Error de decodificación: {e}")
                continue
        
        # PASO 3: Ensamblaje final
        print("\n🤖 PASO 3: Ensamblaje final...")
        noticias_individuales = [n for n in noticias_unicas if n.get("id") not in used_ids]
        
        print("    🎉 Agrupación en dos pasos completada con éxito.")
        return {'bloques_tematicos': bloques_tematicos, 'noticias_individuales': noticias_individuales}

    except Exception as e:
        print(f"    ❌ Fallo en el proceso de agrupación con IA de 2 pasos: {e}")
        print("    🔧 Usando agrupación por claves dinámicas como fallback...")
        agrupado_dyn = cluster_by_dynamic_keyphrases(noticias_unicas)
        if agrupado_dyn['bloques_tematicos']:
             print("    ✅ Agrupación dinámica exitosa.")
             return _enforce_unique_assignment(agrupado_dyn)
        
        print("    🔧 Usando agrupación simple como último recurso...")
        return _enforce_unique_assignment(agrupacion_simple_por_palabras_clave(noticias_unicas))



def fusionar_bloques_similares(bloques: list, umbral_similitud: float = 0.75) -> list:
    """
    Fusiona bloques temáticos que son muy similares entre sí para evitar redundancia.
    Compara el contenido de los bloques y, si superan un umbral de similitud,
    los une en un único bloque más grande.
    """
    if not bloques:
        return []

    print(f"\n🔗 Iniciando fusión de bloques temáticos similares (umbral: {umbral_similitud:.2f})...")

    # 1. Crear una "firma" de texto para cada bloque para poder compararlos
    for bloque in bloques:
        bloque['firma_texto'] = " ".join([normalize_text_for_similarity(n.get('resumen', '')) for n in bloque['noticias']])

    bloques_procesados = list(bloques)
    
    i = 0
    while i < len(bloques_procesados):
        bloque_a = bloques_procesados[i]
        j = i + 1
        while j < len(bloques_procesados):
            bloque_b = bloques_procesados[j]
            
            similitud = composite_similarity(bloque_a.get('firma_texto', ''), bloque_b.get('firma_texto', ''))
            
            if similitud >= umbral_similitud:
                print(f"    🤝 FUSIONANDO: Bloque '{bloque_b.get('descripcion_tema', 'N/A')}' ({similitud:.2f}) en '{bloque_a.get('descripcion_tema', 'N/A')}'")
                
                # 2. Añadir noticias del bloque B al A, evitando duplicados por ID
                ids_existentes = {n.get('id') for n in bloque_a['noticias']}
                for noticia_nueva in bloque_b['noticias']:
                    if noticia_nueva.get('id') not in ids_existentes:
                        bloque_a['noticias'].append(noticia_nueva)
                
                # 3. Actualizar la firma del bloque A para que sea más representativo
                bloque_a['firma_texto'] += " " + bloque_b.get('firma_texto', '')
                
                # 4. Eliminar el bloque B que ya ha sido fusionado
                bloques_procesados.pop(j)
            else:
                j += 1
        i += 1

    # 5. Limpiar las firmas de texto temporales
    for bloque in bloques_procesados:
        if 'firma_texto' in bloque:
            del bloque['firma_texto']

    if len(bloques_procesados) < len(bloques):
        print(f"    ✅ Fusión completada. Se redujeron {len(bloques) - len(bloques_procesados)} bloques.")
        # Reordenar bloques por número de noticias, de mayor a menor
        bloques_procesados.sort(key=lambda b: len(b.get('noticias', [])), reverse=True)
    else:
        print("    ✅ No se encontraron bloques similares para fusionar.")
        
    return bloques_procesados

# =================================================================================
# FUNCIÓN: GENERACIÓN DE NARRACIONES FLUIDAS POR BLOQUE
# ** LÓGICA MEJORADA PARA PRIORIZAR NOTICIAS RECIENTES **
# =================================================================================

def generar_narracion_fluida_bloque(bloque_tematico: dict, fecha_actual_str: str) -> str:
    """
    **NUEVA LÓGICA MEJORADA**
    Genera una única crónica consolidada para un bloque temático, en lugar de
    leer las noticias una por una. La longitud es proporcional al número de noticias.
    """
    tema = bloque_tematico.get("descripcion_tema", "varios temas")
    transicion = bloque_tematico.get("transicion_elegante", f"Y ahora, un bloque de noticias sobre {tema}.")
    noticias = bloque_tematico.get("noticias", [])

    if not noticias:
        return ""

    # Si solo hay una noticia en el "bloque", tratarla como individual para evitar sobre-ingeniería.
    if len(noticias) < 2:
        noticia = noticias[0]
        resumen_simple = f"{transicion}. {noticia.get('resumen', '')}"
        return resumen_simple

    # Ordenar noticias por fecha, por si acaso
    noticias_ordenadas = sorted(noticias, key=lambda x: x.get('fecha', '0000-00-00'), reverse=True)

    # 1. Preparar la lista de resúmenes y fuentes
    resumenes_para_prompt = []
    fuentes = []
    for i, n in enumerate(noticias_ordenadas):
        resumenes_para_prompt.append(f"Noticia {i+1} (Fuente: {n.get('fuente', 'desconocida')}): \"{n.get('resumen', '')}\"")
        fuentes.append(n.get('fuente', ''))
    
    lista_de_noticias_str = "\n".join(resumenes_para_prompt)
    
    # Limpiar y obtener fuentes únicas
    fuentes_unicas = sorted(list(set(f for f in fuentes if f)))

    # 2. Calcular longitud deseada
    num_noticias = len(noticias)
    # Lógica de longitud: base de 70 palabras, +40 por cada noticia.
    # Esto da un buen balance para que no sea ni muy corto ni excesivamente largo.
    longitud_deseada = 70 + (num_noticias * 40)

    # 3. Construir el prompt para la IA
    prompt = f"""Eres un editor y guionista de radio experto en sintetizar múltiples noticias sobre un mismo tema para crear una única crónica consolidada, coherente y fluida para un podcast.

**Tema principal:** "{tema}"

**Noticias a combinar (pueden ser muy similares o repetitivas):**
---
{lista_de_noticias_str}
---

**Instrucciones para tu crónica:**

1.  **SÍNTESIS EDITORIAL, NO UNA LISTA:** Tu tarea principal es actuar como un editor. Identifica la información clave y los datos únicos de cada noticia. **Elimina activamente la información redundante y las frases repetidas** entre las distintas fuentes.
2.  **CONSTRUYE UNA ÚNICA HISTORIA:** No leas las noticias una por una. Fusiona los datos relevantes en una sola narración cohesionada. Usa el evento más importante como hilo conductor y enriquécelo con detalles complementarios de las otras noticias.
3.  **LONGITUD PROPORCIONAL Y NATURAL:** La crónica debe sonar completa y natural. Al combinar {num_noticias} noticias, el texto final debería tener una longitud aproximada de **{longitud_deseada} palabras**.
4.  **INTEGRACIÓN NATURAL DE FUENTES:** Es crucial dar crédito, pero hazlo de forma fluida y agradable al oído.
    - **NO hagas una lista pesada al final.**
    - Si son pocas fuentes, menciónalas intercaladas en el texto (ej: "Según informa el Ayuntamiento de...").
    - Si son muchas fuentes (como aquí, que hay {len(fuentes_unicas)}), **AGRÚPALAS** de forma inteligente o cítalas de forma general durante la narración (ej: "Diversas asociaciones como RECAMDER y varios ayuntamientos de la región coinciden en...", "Fuentes locales destacan...").
    - El objetivo es que el oyente sepa de dónde viene la info sin aburrirse con un listado.
5.  **REGLA DE ORO SOBRE FECHAS:**
    - **PROHIBIDO** usar términos relativos como "hoy", "mañana", "ayer", "este lunes", "el próximo viernes". El podcast puede escucharse cualquier día.
    - **PROHIBIDO** intentar adivinar qué día de la semana cae una fecha (ej: NO digas "el lunes 25", di solo "el 25 de noviembre"). A menudo te equivocas con los días de la semana.
    - **USA SIEMPRE FECHAS ABSOLUTAS:** Di "el 25 de noviembre", "el 3 de diciembre".
    - Si la fecha no es relevante o es confusa, omítela o usa términos genéricos como "recientemente" o "próximamente".

**Importante:** La crónica debe empezar directamente con la frase de transición que te proporciono. No añadas introducciones adicionales.

**ESTRUCTURA VISUAL OBLIGATORIA:**
- Aunque la narración debe sonar fluida y conectada, **DEBES separar cada noticia o tema distinto en un PÁRRAFO NUEVO**.
- Usa un salto de línea doble entre cada noticia.
- Esto es vital para que podamos insertar una pequeña cortinilla musical entre ellas.

**Frase de transición de entrada (úsala para empezar):**
"{transicion}"

**CRÓNICA DE RADIO:**
"""

    # 4. Generar el texto con Gemini
    cronica_generada = generar_texto_con_gemini(prompt)

    # 5. Fallback por si la IA falla
    if not cronica_generada:
        print("      ⚠️ Fallo en la generación de crónica consolidada. Usando concatenación simple como fallback.")
        resumenes_fallback = ' '.join([n.get('resumen', '') for n in noticias_ordenadas])
        fuentes_fallback = ", ".join(fuentes_unicas)
        return f"{transicion}. {resumenes_fallback}. Esta información proviene de {fuentes_fallback}."

    # La IA ya debería incluir la transición, así que devolvemos el texto tal cual.
    return cronica_generada

# (Función normalizar_voz_a_pico eliminada por falta de uso)

# =================================================================================
# NUEVA FUNCIÓN REFRACTORIZADA PARA GESTIONAR AUDIO Y CTAs
# =================================================================================

def _generar_audio_noticia(datos: dict, fecha_actual_str: str) -> tuple[AudioSegment | None, str]:
    """Genera un segmento de audio para una noticia individual. Devuelve (audio, texto)."""
    
    texto_narracion = "" 
    
    fuente = datos.get('fuente', 'Fuente desconocida')
    resumen = datos.get('resumen', '')
    es_breve = datos.get('es_breve', False)
    fecha_noticia = datos.get('fecha', 'Desconocida')
    print(f"  📰 Generando narración para noticia individual: {fuente}")
    
    if es_breve:
        print("      -> Noticia breve: manteniendo concisión")
        texto_narracion = f"Desde {fuente}: {resumen}"
    else:
        texto_narracion_generado = generar_texto_con_gemini(
            mcmcn_prompts.PromptsCreativos.narracion_profesional(
                fuentes=fuente, 
                resumen=resumen, 
                fecha_noticia_str=fecha_noticia,
                fecha_actual_str=fecha_actual_str,
                contexto_tematico=None
            )
        )        
        if not texto_narracion_generado:
            print("      ⚠️ Error generando narración individual. Usando formato simple.")
            texto_narracion = f"Desde {fuente}, nos llega la noticia de que: {resumen}"
        else:
            texto_narracion = texto_narracion_generado
    
    if not texto_narracion:
        print("      ❌ No se pudo generar ninguna narración. Devolviendo silencio.")
        return AudioSegment.silent(duration=100), ""
    
    texto_narracion = limpiar_artefactos_ia(texto_narracion)
    
    # --- GENERACIÓN ESTÁNDAR ---
    # Escapar el texto ANTES de añadir las etiquetas SSML
    texto_narracion_escapado = html.escape(texto_narracion)

    # Dividir el texto en frases para aplicar prosodia variable
    frases = re.split('([.?!])', texto_narracion_escapado)
    
    # Reconstruir las frases con su puntuación
    frases_completas = [frases[i] + (frases[i+1] if i+1 < len(frases) else '') for i in range(0, len(frases), 2)]

    texto_narracion_ssml = ""
    for frase in frases_completas:
        if frase.strip():
            # Aplicar una ligera variación aleatoria al ritmo de cada frase
            rate = f"{random.uniform(0.98, 1.02):.2f}"
            texto_narracion_ssml += f'<prosody rate="{rate}">{frase.strip()}</prosody><break time="450ms"/>'
    
    print(f"      ✅ Narración generada: '{texto_narracion[:80]}...' ")
    
    audio_segment = sintetizar_ssml_a_audio(f"<speak>{texto_narracion_ssml}</speak>")
    if audio_segment:
        return audio_segment, texto_narracion
    return None, texto_narracion

def _generar_resumen_final(noticias_agrupadas: dict) -> str:
    """Genera un resumen final conciso de todos los temas y noticias cubiertas."""
    noticias_individuales = noticias_agrupadas.get('noticias_individuales', [])
    bloques_tematicos = noticias_agrupadas.get('bloques_tematicos', [])
    
    contexto = []
    if bloques_tematicos:
        contexto.append("Temas tratados:")
        for bloque in bloques_tematicos:
            temas = bloque.get('descripcion_tema', 'varios temas')
            noticias_por_bloque = [n.get('resumen') for n in bloque.get('noticias', [])]
            contexto.append(f"- {temas}: " + " y ".join(noticias_por_bloque[:2]))
    if noticias_individuales:
        contexto.append("También cubrimos noticias individuales sobre:")
        for noticia in noticias_individuales:
            contexto.append(f"- {noticia.get('resumen')[:100]}...")
            
    prompt = mcmcn_prompts.PromptsCreativos.resumen_final(
        contexto='\n'.join(contexto)
    )
    
    texto_resumen_ia = generar_texto_con_gemini(prompt)
    
    # <-- LÍNEA AÑADIDA: Limpiamos la salida de la IA antes de devolverla
    texto_resumen = limpiar_artefactos_ia(texto_resumen_ia) if texto_resumen_ia else ""

    if not texto_resumen:
        print("      ⚠️ No se pudo generar el resumen final con IA. Usando un resumen simple.")
        temas_desc = [b.get('descripcion_tema') for b in bloques_tematicos]
        resumenes_ind = [n.get('resumen') for n in noticias_individuales]
        texto_resumen = "En resumen, hoy hablamos sobre " + ", ".join(temas_desc)
        if resumenes_ind:
            texto_resumen += " y otras noticias como " + ", ".join(resumenes_ind[:2]) + "..."
    
    return texto_resumen

def analizar_sentimiento_general_noticias(resumenes: List[Dict[str, Any]]) -> str:
    """
    Analiza el sentimiento general de una lista de noticias y devuelve el más común.
    Para optimizar, solo analiza un máximo de 5 noticias.
    """
    if not resumenes:
        return "neutro"

    sentimientos = []
    # Para no hacer demasiadas llamadas a la API, analizamos un máximo de 5 noticias
    # representativas para obtener el tono general.
    for noticia in resumenes[:5]:
        texto_resumen = noticia.get('resumen', '')
        if texto_resumen:
            prompt = mcmcn_prompts.PromptsAnalisis.analizar_sentimiento_texto(texto=texto_resumen)
            sentimiento = generar_texto_con_gemini(prompt).lower().strip()
            if sentimiento in ['positivo', 'negativo', 'neutro']:
                sentimientos.append(sentimiento)

    if not sentimientos:
        return "neutro"

    # Devolver el sentimiento más común
    return Counter(sentimientos).most_common(1)[0][0]

# =================================================================================
# FUNCIONES AUXILIARES MEJORADAS
# =================================================================================

def parsear_fecha_segura(entry):
    """Maneja fechas de forma segura con múltiples intentos."""
    for field in ['published_parsed', 'updated_parsed']:
        if hasattr(entry, field) and entry[field]:
            try:
                return datetime.fromtimestamp(mktime(entry[field]))
            except (ValueError, TypeError):
                continue
    return datetime.now()  # Valor por defecto

def audio_cache_valido(audio_path):
    """Verifica la integridad de un archivo de audio en caché."""
    if not os.path.exists(audio_path):
        return False
    try:
        audio = AudioSegment.from_file(audio_path)
        return len(audio) > 0 and audio.max_dBFS > SILENCE_THRESHOLD_DBFS
    except:
        return False

def _get_cta_text(tipo: str, dia_semana: str, base_dir: str) -> str:
    """
    Carga el texto de un CTA, buscando primero el específico del día y luego un genérico.
    Ej: busca 'viernes_cta_inicio.txt' y si no, 'cta_inicio.txt'.
    """
    import unicodedata

    # Normalizar día de la semana para quitar tildes (miércoles -> miercoles)
    # ya que los archivos no suelen tener tildes.
    dia_normalizado = ''.join(c for c in unicodedata.normalize('NFD', dia_semana)
                              if unicodedata.category(c) != 'Mn')

    # 1. Probar el archivo específico del día
    nombre_fichero_dia = f"{dia_normalizado}_cta_{tipo}.txt"
    ruta_fichero_dia = os.path.join(base_dir, nombre_fichero_dia)
    if os.path.exists(ruta_fichero_dia):
        try:
            with open(ruta_fichero_dia, 'r', encoding='utf-8') as f:
                print(f"      ✅ CTA específico encontrado: {nombre_fichero_dia}")
                return f.read().strip()
        except Exception as e:
            print(f"      ⚠️ Error leyendo {nombre_fichero_dia}: {e}")

    # 2. Fallback al archivo genérico
    nombre_fichero_generico = f"cta_{tipo}.txt"
    ruta_fichero_generico = os.path.join(base_dir, nombre_fichero_generico)
    if os.path.exists(ruta_fichero_generico):
        try:
            with open(ruta_fichero_generico, 'r', encoding='utf-8') as f:
                print(f"      ℹ️ Usando CTA genérico: {nombre_fichero_generico}")
                return f.read().strip()
        except Exception as e:
            print(f"      ⚠️ Error leyendo {nombre_fichero_generico}: {e}")
    
    # 3. Si no se encuentra nada
    print(f"      ❌ No se encontró ningún archivo de CTA para '{tipo}'.")
    return ""

def _generar_y_cachear_audio_noticia(noticia: dict, fecha_actual_str: str) -> tuple[AudioSegment | None, str]:
    """
    Genera (o carga desde caché) el audio para una única noticia.
    Devuelve (audio_segment, texto_narracion) o (None, "") si falla.
    """
    noticia_id = noticia.get('id')
    if not noticia_id:
        return None, ""

    audio_file_path = os.path.join(AUDIO_CACHE_DIR, f"{noticia_id}.mp3")
    text_file_path = os.path.join(AUDIO_CACHE_DIR, f"{noticia_id}.txt")

    if audio_cache_valido(audio_file_path):
        print(f"  🎧 Cargando audio desde caché para noticia: {noticia.get('fuente')}")
        audio = AudioSegment.from_file(audio_file_path)
        
        # Intentar cargar el texto asociado
        texto = ""
        if os.path.exists(text_file_path):
            try:
                with open(text_file_path, 'r', encoding='utf-8') as f:
                    texto = f.read()
            except Exception as e:
                print(f"      ⚠️ Error leyendo caché de texto: {e}")
        
        # Si no hay texto en caché, usar el resumen como fallback
        if not texto:
            texto = noticia.get('resumen', '')
            
        return audio, texto
    
    print(f"  🎤 Generando nuevo audio para noticia: {noticia.get('fuente')}")
    audio_generado, texto_generado = _generar_audio_noticia(noticia, fecha_actual_str)
    
    if audio_generado:
        try:
            audio_generado.export(audio_file_path, format="mp3")
            # Guardar también el texto generado
            if texto_generado:
                with open(text_file_path, 'w', encoding='utf-8') as f:
                    f.write(texto_generado)
            return audio_generado, texto_generado
        except Exception as e:
            print(f"      ❌ Error al guardar audio/texto en caché: {e}")
    
    return None, ""

def generar_html_transcripcion(transcript_data: list, output_dir: str, timestamp: str):
    """
    Genera un archivo HTML con la transcripción/resumen del podcast.
    Estilo: Dark Mode, High Contrast (Inspirado en The Verge).
    Colores: Blanco, Negro, Naranja, Amarillo, Verde.
    Incluye reproductor de audio personalizado.
    """
    print("\n📝 Generando archivo de transcripción HTML con estilo y reproductor...")
    
    # Calcular año y mes desde el timestamp (formato esperado: YYYYMMDD_HHMMSS)
    try:
        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        year = dt.strftime("%Y")
        month = dt.strftime("%m")
        fecha_emision = dt.strftime("%d/%m/%Y")
    except ValueError:
        # Fallback si el timestamp no tiene el formato esperado
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        fecha_emision = now.strftime("%d/%m/%Y")

    # URL dinámica del audio
    audio_url = f"https://micomicona.com/wp-content/uploads/{year}/{month}/podcast_completo_{timestamp}.mp3"
    
    css_styles = """
    <style>
        .podcast-transcript {
            background-color: #000000;
            color: #ffffff;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            padding: 40px;
            line-height: 1.6;
            border: 1px solid #333;
        }
        .podcast-transcript h2 {
            font-family: 'Impact', 'Arial Black', sans-serif;
            text-transform: uppercase;
            font-size: 3em;
            letter-spacing: -1px;
            margin-bottom: 10px;
            color: #ffffff;
            line-height: 1;
        }
        .podcast-transcript .meta {
            font-family: 'Courier New', monospace;
            color: #ffff00; /* Amarillo */
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 40px;
            border-bottom: 4px solid #ffffff;
            padding-bottom: 20px;
            display: block;
        }
        
        /* --- CUSTOM AUDIO PLAYER STYLES --- */
        .audio-player-container {
            background-color: #111;
            border: 2px solid #00ff00; /* Verde */
            padding: 20px;
            margin-bottom: 40px;
            display: flex;
            align-items: center;
            gap: 20px;
            box-shadow: 5px 5px 0px #00ff00;
        }
        
        .play-btn {
            background-color: #ff4d00; /* Naranja */
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.1s;
        }
        .play-btn:active {
            transform: scale(0.95);
        }
        .play-btn svg {
            fill: #000;
            width: 20px;
            height: 20px;
            margin-left: 2px; /* Ajuste visual para el icono de play */
        }
        .play-btn.playing svg {
            margin-left: 0;
        }
        
        .progress-container {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .player-label {
            font-family: 'Arial Black', sans-serif;
            text-transform: uppercase;
            color: #00ff00;
            font-size: 0.8em;
            margin-bottom: 5px;
        }

        .progress-bar-bg {
            background-color: #333;
            height: 8px;
            width: 100%;
            cursor: pointer;
            position: relative;
        }
        
        .progress-bar-fill {
            background-color: #ffff00; /* Amarillo */
            height: 100%;
            width: 0%;
            transition: width 0.1s linear;
        }
        
        .time-display {
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #ffffff;
            font-size: 0.9em;
            min-width: 100px;
            text-align: right;
        }
        
        /* ---------------------------------- */

        .transcript-section {
            margin-bottom: 40px;
            padding-left: 20px;
            border-left: 6px solid #333;
        }
        .transcript-section h3, .transcript-section h4 {
            font-family: 'Arial Black', sans-serif;
            text-transform: uppercase;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.5em;
            letter-spacing: -0.5px;
        }
        .transcript-section p {
            font-size: 1.1em;
            color: #e0e0e0;
            margin: 0;
        }
        
        /* Estilos específicos por sección */
        .transcript-intro {
            border-left-color: #ffff00; /* Amarillo */
        }
        .transcript-intro h3 {
            color: #ffff00;
        }

        .transcript-block {
            border-left-color: #00ff00; /* Verde */
        }
        .transcript-block h3 {
            color: #00ff00;
            background: #000;
            display: inline-block;
        }

        .transcript-news {
            border-left-color: #00ff00; /* Verde */
            margin-left: 20px; /* Indentar noticias dentro de bloques si se quiere */
        }
        .transcript-news h4 {
            color: #ffffff;
            background-color: #000000;
            border-bottom: 2px solid #00ff00;
            display: inline;
            padding-right: 10px;
        }

        .transcript-audience {
            border-left-color: #ff4d00; /* Naranja */
            background-color: #111;
            padding: 20px;
            border-left-width: 10px;
        }
        .transcript-audience h3 {
            color: #ff4d00;
        }

        .transcript-outro {
            border-left-color: #ffffff;
            border-bottom: 4px solid #ffffff;
            padding-bottom: 20px;
        }
        .transcript-outro h3 {
            color: #ffffff;
        }

        .footer-note {
            font-family: 'Courier New', monospace;
            color: #666;
            font-size: 0.8em;
            text-align: right;
            margin-top: 20px;
        }
        
        a {
            color: #ff4d00;
            text-decoration: none;
            border-bottom: 2px solid #ff4d00;
            font-weight: bold;
        }
        a:hover {
            background-color: #ff4d00;
            color: #000;
        }
    </style>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const audio = document.getElementById('podcast-audio');
            const playBtn = document.getElementById('play-btn');
            const playIcon = document.getElementById('play-icon');
            const pauseIcon = document.getElementById('pause-icon');
            const progressBarBg = document.getElementById('progress-bar-bg');
            const progressBarFill = document.getElementById('progress-bar-fill');
            const timeDisplay = document.getElementById('time-display');
            
            // Toggle Play/Pause
            playBtn.addEventListener('click', function() {
                if (audio.paused) {
                    audio.play();
                    playBtn.classList.add('playing');
                    playIcon.style.display = 'none';
                    pauseIcon.style.display = 'block';
                } else {
                    audio.pause();
                    playBtn.classList.remove('playing');
                    playIcon.style.display = 'block';
                    pauseIcon.style.display = 'none';
                }
            });
            
            // Update Progress Bar
            audio.addEventListener('timeupdate', function() {
                const percent = (audio.currentTime / audio.duration) * 100;
                progressBarFill.style.width = percent + '%';
                
                // Update Time
                const current = formatTime(audio.currentTime);
                const duration = formatTime(audio.duration || 0);
                timeDisplay.textContent = `${current} / ${duration}`;
            });
            
            // Click on Progress Bar
            progressBarBg.addEventListener('click', function(e) {
                const rect = progressBarBg.getBoundingClientRect();
                const pos = (e.clientX - rect.left) / rect.width;
                audio.currentTime = pos * audio.duration;
            });
            
            function formatTime(seconds) {
                if (isNaN(seconds)) return "0:00";
                const m = Math.floor(seconds / 60);
                const s = Math.floor(seconds % 60);
                return `${m}:${s.toString().padStart(2, '0')}`;
            }
        });
    </script>
    """
    
    # SVG Icons
    icon_play = '<svg id="play-icon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>'
    icon_pause = '<svg id="pause-icon" viewBox="0 0 24 24" style="display:none;"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>'
    
    html_content = f"""
    {css_styles}
    <div class="podcast-transcript">
        <h2>Podcast Micomicona</h2>
        <span class="meta">Emitido el {fecha_emision} </span>
        
        <!-- CUSTOM AUDIO PLAYER -->
        <div class="audio-player-container">
            <audio id="podcast-audio" src="{audio_url}"></audio>
            
            <button id="play-btn" class="play-btn">
                {icon_play}
                {icon_pause}
            </button>
            
            <div class="progress-container">
                <div class="player-label">ESCUCHAR PODCAST</div>
                <div id="progress-bar-bg" class="progress-bar-bg">
                    <div id="progress-bar-fill" class="progress-bar-fill"></div>
                </div>
            </div>
            
            <div id="time-display" class="time-display">0:00 / --:--</div>
        </div>
        <!-- END PLAYER -->
        
        <hr style="border-color: #333; margin-bottom: 40px;">
    """
    
    for item in transcript_data:
        tipo = item.get('type')
        titulo = item.get('title', '')
        contenido = item.get('content', '')
        
        # Limpieza básica de HTML en el contenido
        contenido_html = html.escape(contenido).replace('\n', '<br>')
        
        if tipo == 'intro':
            html_content += f"""
            <div class="transcript-section transcript-intro">
                <h3>🎙️ Introducción</h3>
                <p>{contenido_html}</p>
            </div>
            """
        elif item.get('type') == 'block':
            html_content += f"""
            <div class="transcript-section transcript-block">
                <h3>{html.escape(titulo)}</h3>
                <p>{contenido_html}</p>
            </div>
            """
        elif item.get('type') == 'news':
            html_content += f"""
            <div class="transcript-section transcript-news">
                <h4>📰 {html.escape(titulo)}</h4>
                <p>{contenido_html}</p>
            </div>
            """
        elif item.get('type') == 'audience':
            html_content += f"""
            <div class="transcript-section transcript-audience">
                <h3>💬 La Voz de la Audiencia</h3>
                <p>{contenido_html}</p>
            </div>
            """
        elif item.get('type') == 'outro':
            html_content += f"""
            <div class="transcript-section transcript-outro">
                <h3>👋 Despedida</h3>
                <p>{contenido_html}</p>
            </div>
            """
            
    html_content += """
        <div class="footer-note">
            <p>Generado automáticamente por Dorotea • con mucho amor</p>
        </div>
    </div>
    """
    
    filename = f"podcast_summary_{timestamp}.html"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Transcripción estilizada con reproductor guardada en: {filepath}")
    except Exception as e:
        print(f"❌ Error al guardar transcripción: {e}")

# =================================================================================
# FUNCIÓN PRINCIPAL MEJORADA
# =================================================================================

def procesar_feeds_google(nombre_archivo_feeds: str, idioma_destino: str = 'es', min_items: int = 5):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"podcast_apg_{timestamp}"
        
        # Verificar y crear directorios necesarios
        required_dirs = ["audio_assets", "cta_texts", "audio_cache", output_dir]
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)
            if not os.path.exists(dir_path):
                print(f"❌ No se pudo crear directorio: {dir_path}")
                sys.exit(1)
                
        print(f"Directorio de salida creado: {output_dir}")

        print("\n--- FASE 1: Recopilando, filtrando y resumiendo noticias ---")
        
        cache_noticias = cargar_cache_noticias()
        with open(nombre_archivo_feeds, 'r', encoding='utf-8') as f:
            feeds_urls = [url.strip() for url in f.read().replace(',', '\n').splitlines() if url.strip()]

        if not feeds_urls:
            print(f"Advertencia: El archivo de feeds '{nombre_archivo_feeds}' está vacío.")
            sys.exit(1)

        # Configuración de límites (con valores por defecto si no existen)
        gen_config = CONFIG.get('generation_config', {})
        window_hours = int(gen_config.get('news_window_hours', 48))
        max_items = int(gen_config.get('max_news_items', 20))
        
        print(f"      ⚙️ Configuración: Ventana={window_hours}h, Máx. Noticias={max_items}")

        limite_dias = datetime.now() - timedelta(hours=window_hours)
        noticias_candidatas_totales = []

        for url in feeds_urls:
            try:
                feed = feedparser.parse(url)
                sitio = feed.feed.get('title', 'Fuente desconocida').replace(" on Facebook", "").strip()
                for entry in feed.entries:
                    fecha_pub = parsear_fecha_segura(entry)
                    if fecha_pub < limite_dias:
                        continue
                    contenido = entry.get('summary', entry.get('description', ''))
                    if not contenido:
                        continue

                    noticia_hash = stable_text_hash(contenido)
                    texto_crudo = limpiar_html(contenido)

                    noticias_candidatas_totales.append({
                        'sitio': sitio, 'texto': texto_crudo, 'fecha': fecha_pub, 'hash': noticia_hash
                    })
            except Exception as e:
                print(f"Advertencia: No se pudo procesar el feed '{url}'. Error: {e}")

        if not noticias_candidatas_totales:
            print("No se encontraron noticias válidas para procesar. Abortando.")
            sys.exit(0)

        noticias_candidatas_totales.sort(key=lambda x: x['fecha'], reverse=True)
        # Usar el límite configurado en lugar del argumento min_items (que era un nombre confuso para un max limit)
        noticias_seleccionadas = noticias_candidatas_totales[:max_items]

        resumenes_finales = []
        nuevas_noticias_para_cache = {}

        for noticia in noticias_seleccionadas:
            noticia_hash = noticia['hash']
            if noticia_hash in cache_noticias:
                noticia_cacheada = cache_noticias[noticia_hash]
                resumenes_finales.append(noticia_cacheada)
                print(f"      ⏩ Usando caché para '{noticia_cacheada['resumen'][:50]}...'")

            else:
                print(f"  Resumiendo y generando audio para noticia nueva: {noticia['sitio'][:50]}...")
                fuente_original = identificar_fuente_original(noticia['texto'])
                
                # APLICAMOS LA NUEVA FUNCIÓN DE LIMPIEZA DE FECHAS
                texto_crudo = preprocesar_texto_para_fechas(noticia['texto'])

                es_noticia_breve = len(texto_crudo) < 150
                prompt_para_ia = ""

                # ============================================================
                # === INICIO DE LA MEJORA (FUSIÓN 'doro.py') ===
                # ============================================================
                
                print("      -> Fase 1/3: Extrayendo entidades clave con IA...")
                prompt_entidades = mcmcn_prompts.PromptsAnalisis.extraer_entidades_clave(texto_crudo)
                respuesta_entidades_json = generar_texto_con_gemini(prompt_entidades)
                
                entidades_clave = []
                if respuesta_entidades_json:
                    try:
                        json_limpio = respuesta_entidades_json
                        # Limpiar posible markdown de la IA
                        if "```" in json_limpio:
                            start_idx = json_limpio.find('[')
                            end_idx = json_limpio.rfind(']')
                            if start_idx != -1 and end_idx != -1:
                                json_limpio = json_limpio[start_idx:end_idx+1]
                        
                        entidades_clave = json.loads(json_limpio)
                        print(f"      ✅ Entidades extraídas: {', '.join(entidades_clave)}")
                    except json.JSONDecodeError:
                        print("      ⚠️ No se pudieron decodificar las entidades clave (JSON inválido).")
                        entidades_clave = []

                if es_noticia_breve:
                    print("      -> Fase 2/3: Usando el prompt de resumen MUY BREVE (texto corto).")
                    prompt_para_ia = mcmcn_prompts.PromptsAnalisis.resumen_muy_breve(
                        texto=texto_crudo,
                        fuente_original=fuente_original
                    )
                else:
                    print("      -> Fase 2/3: Generando resumen enriquecido con IA (texto largo).")
                    # Usamos el prompt 'enriquecido' de doro.py
                    prompt_para_ia = mcmcn_prompts.PromptsAnalisis.resumen_noticia_enriquecido(
                        texto=texto_crudo,
                        fuente_original=fuente_original,
                        entidades_clave=entidades_clave, # <-- Usamos las entidades
                        idioma_destino=idioma_destino
                    )
                
                # ============================================================
                # === FIN DE LA MEJORA (FUSIÓN 'doro.py') ===
                # ============================================================

                # Llamamos a la IA con el prompt que hemos elegido
                resumen = generar_texto_con_gemini(prompt_para_ia)

                if resumen:
                    fuente_final = f"{noticia['sitio']} ({fuente_original})" if fuente_original else noticia['sitio']
                    audio_file_path = os.path.join(AUDIO_CACHE_DIR, f"{noticia_hash}.mp3")
                    
                    texto_limpio = limpiar_artefactos_ia(resumen)

                    # NUEVO: Reemplazar URLs por una mención genérica DESPUÉS de resumir.
                    texto_limpio = reemplazar_urls_por_mencion(texto_limpio)

                    # Filtrar noticias demasiado cortas después de resumir
                    if len(texto_limpio.split()) < MIN_WORDS_FOR_AUDIO:
                        print(f"      🗑️  Ignorando noticia por tener menos de {MIN_WORDS_FOR_AUDIO} palabras: '{texto_limpio[:60]}...'")
                        continue

                    # === ANÁLISIS DE SENTIMIENTO INDIVIDUAL ===
                    print(f"      -> Fase 3/3: Analizando sentimiento de la noticia...")
                    prompt_sentimiento = mcmcn_prompts.PromptsAnalisis.analizar_sentimiento_texto(texto=texto_limpio)
                    sentimiento_noticia = generar_texto_con_gemini(prompt_sentimiento).lower().strip()
                    if sentimiento_noticia not in ['positivo', 'negativo', 'neutro']:
                        sentimiento_noticia = 'neutro' # Fallback
                    print(f"      ✅ Sentimiento detectado: {sentimiento_noticia.upper()}")
                    # =========================================

                    # === AÑADIR ESTAS LÍNEAS ===
                    # Usamos el texto original para una mejor extracción de la localidad
                    localidad_extraida = extraer_localidad_con_ia(noticia['texto'])
                    # ==========================

                    audio_segment = sintetizar_ssml_a_audio(f"<speak>{html.escape(texto_limpio)}</speak>")

                    if audio_segment:
                        audio_segment.export(audio_file_path, format="mp3")
                        nueva_noticia_procesada = {
                            'fuente': fuente_final,
                            'resumen': resumen,
                            'fecha': noticia['fecha'].strftime("%Y-%m-%d"),
                            'id': noticia_hash,
                            'audio_path': audio_file_path,
                            'es_breve': es_noticia_breve,
                            'localidad': localidad_extraida,
                            'sentimiento': sentimiento_noticia,
                            'entidades_clave': entidades_clave # <-- AÑADIDO DE 'doro.py'
                        }
                        resumenes_finales.append(nueva_noticia_procesada)
                        nuevas_noticias_para_cache[noticia_hash] = nueva_noticia_procesada

        if not resumenes_finales:
            print("No se pudieron generar resúmenes válidos. Abortando.")
            sys.exit(0)

        # Guardamos el caché actualizado (incluyendo las nuevas entidades)
        cache_noticias.update(nuevas_noticias_para_cache)
        guardar_cache_noticias(cache_noticias)

        debug_noticias_antes_agrupacion(resumenes_finales)
        noticias_agrupadas = agrupar_noticias_por_temas_mejorado(resumenes_finales)
        
        # --- NUEVO PASO: Fusión de bloques temáticos similares ---
        bloques_originales = noticias_agrupadas.get('bloques_tematicos', [])
        if bloques_originales:
            noticias_agrupadas['bloques_tematicos'] = fusionar_bloques_similares(bloques_originales)
        # --- FIN DEL NUEVO PASO ---

        # INICIO DE LOS CAMBIOS DE NORMALIZACIÓN
        print("\n--- FASE 2: Generando audio con la nueva introducción estructurada ---")

        dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        dia_semana_str = dias_semana[datetime.now().weekday()]

        print(f"\n--- Obteniendo textos de CTA para el {dia_semana_str} ---")
        
        cta_texts_dir = "cta_texts"
        cta_inicio_text = _get_cta_text("inicio", dia_semana_str, cta_texts_dir)
        cta_intermedio_text = _get_cta_text("intermedio", dia_semana_str, cta_texts_dir)
        cta_cierre_text = _get_cta_text("cierre", dia_semana_str, cta_texts_dir)
        
        segmentos_audio = []
        transcript_data = [] # <-- Inicializar lista para transcripción
        audio_assets_dir = "audio_assets"

        # --- Cargar la cortinilla para los CTAs ---
        cortinilla_cta_audio = None
        ruta_cortinilla_cta = os.path.join(audio_assets_dir, "cortinilla_cta.mp3")
        if os.path.exists(ruta_cortinilla_cta):
            try:
                cortinilla_cta_audio = AudioSegment.from_file(ruta_cortinilla_cta)
                print("✅ Cortinilla CTA cargada correctamente.")
            except Exception as e:
                print(f"⚠️ Advertencia: No se pudo cargar 'cortinilla_cta.mp3'. Error: {e}")
        # ------------------------------------------

        # --- NUEVO: Cargar la sintonía específica para los bloques temáticos ---
        sinto_bloque_audio = None
        ruta_sinto_bloque = os.path.join(audio_assets_dir, "sinto_bloque.mp3")
        if os.path.exists(ruta_sinto_bloque):
            try:
                sinto_bloque_audio = AudioSegment.from_file(ruta_sinto_bloque)
                print("✅ Sintonía de bloque ('sinto_bloque.mp3') cargada correctamente.")
            except Exception as e:
                print(f"⚠️ Advertencia: No se pudo cargar 'sinto_bloque.mp3'. Error: {e}")
        # --------------------------------------------------------------------
# --- LÓGICA DE CARGA DE TRANSICIONES MODIFICADA (clickrozalen) ---
        print("\n🎵 Cargando músicas de transición universales (clickrozalen)...")
        transiciones = {
            'positivo': {},
            'negativo': {},
            'neutro': {}
        }
        # Mantenemos las constantes de duración, la función agregar_transicion las usará
        SEGMENT_DURATION_MS, FADE_DURATION_MS = 10000, 2000 

        # Pool universal para todos los archivos 'clickrozalen'
        pool_universal = {}
        
        # 1. Definir el patrón de búsqueda específico para tus archivos
        patron_busqueda = "clickrozalen*.mp3"
        ruta_busqueda = os.path.join(audio_assets_dir, patron_busqueda)
        print(f"    -> Buscando archivos que coincidan con '{patron_busqueda}' en '{audio_assets_dir}'...")
        
        files = glob.glob(ruta_busqueda)

        if not files:
            print(f"    ⚠️ ADVERTENCIA: No se encontró ningún archivo de transición con el patrón '{patron_busqueda}'.")
            print(f"    -> Asegúrate de que los archivos están en '{audio_assets_dir}' y se llaman 'clickrozalen...mp3'.")
        
        # 2. Cargar los archivos encontrados
        for f in files:
            try:
                audio = AudioSegment.from_file(f)
            except Exception as e:
                print(f"    ⚠️ Error cargando transición '{f}': {e}")
                continue
            
            # Comprobar si el audio es válido (no está vacío)
            if len(audio) > 0:
                pool_universal[f] = audio
            else:
                print(f"    -> Aviso: Archivo '{f}' está vacío o corrupto. Omitiendo.")

        print(f"    -> {len(pool_universal)} transiciones 'clickrozalen' cargadas en el pool universal.")

        # 3. Asignar el pool universal a todos los sentimientos
        if pool_universal:
            transiciones['positivo'] = pool_universal
            transiciones['negativo'] = pool_universal
            transiciones['neutro'] = pool_universal
            print("    ✅ Pool universal 'clickrozalen' asignado a todos los sentimientos.")
        else:
            print("    -> No se cargaron transiciones. La función 'agregar_transicion' usará silencios.")
        # --- FIN DE LA MODIFICACIÓN ---
        # --------------------------------------------------------------------
        def agregar_transicion(sentimiento: str = 'neutro') -> AudioSegment:
            pool_sentimiento = transiciones.get(sentimiento)
            # Fallback a neutro si no hay transiciones para el sentimiento específico
            if not pool_sentimiento:
                pool_sentimiento = transiciones['neutro']
            
            if not pool_sentimiento: return AudioSegment.silent(duration=1000)
            
            path = random.choice(list(pool_sentimiento.keys()))
            audio = pool_sentimiento[path]
            
            if len(audio) < SEGMENT_DURATION_MS: 
                return audio.fade_in(FADE_DURATION_MS).fade_out(FADE_DURATION_MS)
                
            max_start = len(audio) - SEGMENT_DURATION_MS
            
            # Intentar encontrar un segmento con volumen decente (evitar silencios)
            best_segment = None
            best_dbfs = -float('inf')
            
            for _ in range(10): # 10 intentos
                start = random.randint(0, max_start)
                segmento = audio[start:start+SEGMENT_DURATION_MS]
                
                # Si encontramos un segmento con buen volumen, lo usamos
                if segmento.dBFS > -30: 
                    return segmento.fade_in(FADE_DURATION_MS).fade_out(FADE_DURATION_MS)
                
                # Si no, guardamos el "menos malo" por si acaso
                if segmento.dBFS > best_dbfs:
                    best_dbfs = segmento.dBFS
                    best_segment = segmento
                    
            # Si fallan todos los intentos, devolvemos el mejor encontrado
            return best_segment.fade_in(FADE_DURATION_MS).fade_out(FADE_DURATION_MS)

        print("\n🎤 Ensamblando introducción profesional por segmentos...")
        todos_los_resumenes = [n['resumen'] for n in resumenes_finales]
        contenido_completo_texto = "\n\n- ".join(todos_los_resumenes)

        # Obtener el mensaje de la audiencia antes de generar la introducción,
        # para que la IA pueda tenerlo en cuenta si es necesario para el tono.
        mensaje_del_dia = leer_pregunta_del_dia()

        # NUEVO: Analizar sentimiento general de las noticias
        sentimiento_general = analizar_sentimiento_general_noticias(resumenes_finales)
        print(f"  ✨ Sentimiento general de las noticias del día: {sentimiento_general.upper()}")

        # --- INICIO DE LA NUEVA LÓGICA DE INTRODUCCIÓN UNIFICADA ---
        print("  -> Generando monólogo de inicio unificado con IA...")
        
        # NUEVO: Extraer dato curioso para "El Chisme Culto" (DESACTIVADO POR PETICIÓN DE USUARIO)
        # print("  🕵️‍♀️ Buscando dato curioso para 'El Chisme Culto'...")
        # dato_curioso_json = generar_texto_con_gemini(
        #     mcmcn_prompts.PromptsAnalisis.extraer_dato_curioso(contenido_completo_texto)
        # )
        dato_curioso_gancho = ""
        dato_curioso_resolucion = ""
        
        # try:
        #     if dato_curioso_json:
        #         # Limpiar json por si acaso
        #         dato_curioso_json = dato_curioso_json.replace("```json", "").replace("```", "").strip()
        #         dato_obj = json.loads(dato_curioso_json)
        #         dato_curioso_gancho = dato_obj.get("gancho", "")
        #         dato_curioso_resolucion = dato_obj.get("resolucion", "")
        #         print(f"    ✅ Dato curioso encontrado: {dato_curioso_gancho[:50]}...")
        # except Exception as e:
        #     print(f"    ⚠️ No se pudo extraer dato curioso: {e}")

        # 1. Obtener plantilla base del día para REINTERPRETACIÓN
        print("      🗣️ Obteniendo plantilla base para reinterpretación...")
        dia_semana = datetime.now().weekday()
        saludo_base = mcmcn_prompts.obtener_plantilla_por_dia(dia_semana, mcmcn_prompts.PlantillasSSML.FRASES_SALUDO_POR_DIA)
        
        # 2. Generar MONÓLOGO UNIFICADO (Saludo reinterpretado + Sumario)
        print("      🧠 Generando monólogo de inicio unificado (reinterpretado)...")
        prompt_inicio_unificado = mcmcn_prompts.PromptsCreativos.generar_monologo_inicio_unificado(
            contenido_noticias=contenido_completo_texto,
            texto_cta=cta_inicio_text,
            texto_base_saludo=saludo_base,
            # dato_curioso_gancho=dato_curioso_gancho, # Reactivar si se usa
            sentimiento_general=sentimiento_general
        )
        
        texto_monologo_inicio = generar_texto_con_gemini(prompt_inicio_unificado)
        
        # 3. Añadir la sintonía de inicio ANTES del monólogo.
        ruta_sintonia_inicio = os.path.join("audio_assets", "inicio.mp3")
        if os.path.exists(ruta_sintonia_inicio):
            segmentos_audio.append(AudioSegment.from_file(ruta_sintonia_inicio))
        
        # 4. Limpiar, sintetizar y añadir el monólogo de inicio.
        if texto_monologo_inicio:
            texto_limpio = limpiar_artefactos_ia(texto_monologo_inicio)
            print(f"      ✅ Monólogo de inicio generado: '{texto_limpio[:100]}...'")
            transcript_data.append({'type': 'intro', 'content': texto_limpio})
            
            # Lógica para insertar cortinilla si existe el marcador
            if "[CORTINILLA]" in texto_limpio:
                print("      ✂️ Marcador [CORTINILLA] detectado. Dividiendo audio...")
                partes = texto_limpio.split("[CORTINILLA]")
                
                # Parte 1: Saludo + Resumen
                if partes[0].strip():
                    audio_p1 = sintetizar_ssml_a_audio(f"<speak>{html.escape(partes[0].strip())}</speak>")
                    if audio_p1:
                        segmentos_audio.append(audio_p1)
                
                # Insertar Cortinilla (Clickrozalen)
                print("      🎵 Insertando cortinilla 'clickrozalen'...")
                segmentos_audio.append(agregar_transicion())
                
                # Parte 2: CTA + Adivinanza + Cierre
                if len(partes) > 1 and partes[1].strip():
                    audio_p2 = sintetizar_ssml_a_audio(f"<speak>{html.escape(partes[1].strip())}</speak>")
                    if audio_p2:
                        segmentos_audio.append(audio_p2)
            else:
                # Comportamiento normal si no hay marcador
                monologo_inicio_audio = sintetizar_ssml_a_audio(f"<speak>{html.escape(texto_limpio)}</speak>")
                if monologo_inicio_audio:
                    segmentos_audio.append(monologo_inicio_audio)
        else:
            # Fallback por si la IA falla.
            print("      ⚠️ Fallo en la generación del monólogo. Usando saludo estático.")
            if saludo_base:
                saludo_audio_fallback = sintetizar_ssml_a_audio(saludo_base)
                if saludo_audio_fallback:
                    segmentos_audio.append(saludo_audio_fallback)
        
        # 5. Añadir la primera transición para dar paso a las noticias.
        segmentos_audio.append(agregar_transicion())

        print("\n🎯 Procesando bloques temáticos y noticias para narración...")
        bloques_tematicos = noticias_agrupadas.get('bloques_tematicos', [])
        noticias_individuales = noticias_agrupadas.get('noticias_individuales', [])

        # --- INICIO DE LA NUEVA LÓGICA DE PROCESAMIENTO DE AUDIO ---
        # Se crea una lista plana de tareas para tener control total sobre las transiciones.
        tareas_audio = []
        for bloque in bloques_tematicos:
            # 1. Añadir la introducción del bloque como una tarea.
            if bloque.get('transicion_elegante'):
                tareas_audio.append({'tipo': 'intro_bloque', 'data': bloque})
            # 2. Añadir cada noticia del bloque como una tarea individual.
            for noticia in bloque.get('noticias', []):
                tareas_audio.append({'tipo': 'noticia', 'data': noticia})
        
        # 3. Añadir las noticias individuales.
        for noticia in noticias_individuales:
            tareas_audio.append({'tipo': 'noticia', 'data': noticia})

        # Contar solo las noticias para la inserción del CTA intermedio.
        num_noticias = sum(1 for t in tareas_audio if t['tipo'] == 'noticia')
        punto_insercion_cta = num_noticias // 2 if num_noticias > 0 else -1
        noticias_procesadas = 0

        fecha_actual_str = datetime.now().strftime("%A, %d de %B de %Y")

        # --- INICIO DE LA NUEVA LÓGICA DE PROCESAMIENTO DE AUDIO (MODIFICADA: UNIFICACIÓN TOTAL) ---
        # 1. Procesar TODOS los bloques temáticos como crónicas unificadas
        for bloque in bloques_tematicos:
            print(f"  🎪 Generando crónica unificada para el bloque: '{bloque.get('descripcion_tema')}'")
            
            # Guardamos el número de noticias procesadas ANTES de empezar el bloque
            noticias_antes_del_bloque = noticias_procesadas
            
            # Generar narración unificada
            cronica_unificada_texto = generar_narracion_fluida_bloque(bloque, fecha_actual_str)
            
            if cronica_unificada_texto:
                transcript_data.append({
                    'type': 'block',
                    'title': bloque.get('descripcion_tema', 'Bloque Temático'),
                    'content': cronica_unificada_texto
                }) # <-- Capturar bloque
                
                # --- MODIFICACIÓN: Insertar cortinillas entre noticias del bloque ---
                audio_cronica = AudioSegment.empty()
                # Separamos por párrafos (que la IA ha generado con doble salto de línea)
                parrafos = [p.strip() for p in cronica_unificada_texto.split('\n') if p.strip()]
                
                if len(parrafos) > 1:
                    print(f"      🎵 Insertando cortinillas (clickrozalen) entre {len(parrafos)} noticias del bloque...")
                    for i, parrafo in enumerate(parrafos):
                        # Generamos audio para este párrafo/noticia
                        audio_parrafo = sintetizar_ssml_a_audio(f"<speak>{html.escape(parrafo)}</speak>")
                        if audio_parrafo:
                            audio_cronica += audio_parrafo
                            # Si NO es el último párrafo, añadimos la cortinilla
                            if i < len(parrafos) - 1:
                                audio_cronica += agregar_transicion()
                                audio_cronica += AudioSegment.silent(duration=600) # Pequeña pausa tras la cortinilla
                else:
                    # Fallback: Si solo hay 1 párrafo, lo hacemos todo junto
                    audio_cronica = sintetizar_ssml_a_audio(f"<speak>{html.escape(cronica_unificada_texto)}</speak>")
                # ------------------------------------------------------------------
                sentimiento_bloque = analizar_sentimiento_general_noticias(bloque.get('noticias', []))
                
                if audio_cronica:
                    segmentos_audio.append(audio_cronica)
                    segmentos_audio.append(agregar_transicion(sentimiento_bloque))
                    
                    # Sumamos todas las noticias del bloque al contador
                    noticias_en_bloque = len(bloque.get('noticias', []))
                    noticias_procesadas += noticias_en_bloque

                    # Comprobamos si debemos insertar el CTA intermedio
                    # Lo insertamos DESPUÉS del bloque si cruzamos el umbral
                    if noticias_antes_del_bloque < punto_insercion_cta <= noticias_procesadas and cta_intermedio_text:
                        print("\n🎯 Insertando CTA intermedio (tras bloque temático)...")
                        prompt_cta_intermedio = mcmcn_prompts.PromptsCreativos.reescritura_cta_creativa(
                            cta_intermedio_text,
                            tono_actual="informativo y sugerente"
                        )
                        texto_cta_reescrito = generar_texto_con_gemini(prompt_cta_intermedio)
                        if texto_cta_reescrito:
                            cta_intermedio_audio = sintetizar_ssml_a_audio(f"<speak>{html.escape(texto_cta_reescrito)}</speak>")
                            if cta_intermedio_audio:
                                # Insertamos: [Cortinilla] -> [CTA] -> [Transición existente]
                                # 1. Insertamos el CTA antes de la última transición (index -1)
                                segmentos_audio.insert(-1, cta_intermedio_audio)
                                
                                # 2. Insertamos la cortinilla ANTES del CTA (index -2 ahora)
                                if cortinilla_cta_audio:
                                    segmentos_audio.insert(-2, cortinilla_cta_audio)
                                else:
                                    # Si no hay cortinilla específica, usamos una transición del pool
                                    segmentos_audio.insert(-2, agregar_transicion())
                                    
                        print("    ✅ CTA intermedio procesado e insertado (con cortinilla previa).")
            else:
                print("      ⚠️ Fallo al generar crónica unificada. Saltando bloque.")

        # 2. Procesar noticias individuales restantes
        for noticia in noticias_individuales:
            audio_noticia, texto_noticia = _generar_y_cachear_audio_noticia(noticia, fecha_actual_str) # <-- Unpack tuple
            if audio_noticia:
                transcript_data.append({
                    'type': 'news',
                    'title': noticia.get('fuente', 'Noticia'),
                    'content': texto_noticia
                }) # <-- Capturar noticia
                sentimiento_noticia = noticia.get('sentimiento', 'neutro')
                segmentos_audio.append(audio_noticia)
                segmentos_audio.append(agregar_transicion(sentimiento_noticia))

        # --- FASE 2.5: Procesando sección de la audiencia ---
        print("\n--- FASE 2.5: Procesando sección de la audiencia ---")
        # mensaje_del_dia ya se obtuvo al inicio de la FASE 2

        if mensaje_del_dia:
            autor = mensaje_del_dia.get('autor', 'un oyente')
            texto_mensaje = mensaje_del_dia.get('texto', '')
            
            print(f"  -> Generando segmento integrado para el mensaje de: {autor}")

            # 1. Llamamos al NUEVO prompt unificado que genera TODO el segmento, pasando el sentimiento general
            prompt_segmento = mcmcn_prompts.PromptsCreativos.generar_segmento_audiencia_integrado(
                autor, texto_mensaje,
                sentimiento_general=sentimiento_general # <-- PASAMOS SENTIMIENTO
            )
            texto_segmento_completo = generar_texto_con_gemini(prompt_segmento)
            
            if texto_segmento_completo:
                # 2. Limpiamos y sintetizamos el segmento completo en un único paso
                segmento_limpio = limpiar_artefactos_ia(texto_segmento_completo)
                print(f"      ✅ Segmento de audiencia generado: '{segmento_limpio[:90]}...'")
                transcript_data.append({'type': 'audience', 'content': segmento_limpio}) # <-- Capturar audiencia
                
                segmento_ssml = f"<speak>{html.escape(segmento_limpio)}</speak>"
                segmento_audio = sintetizar_ssml_a_audio(segmento_ssml)
                
                if segmento_audio:
                    # 3. Añadimos el audio del segmento y una transición DESPUÉS
                    segmentos_audio.append(segmento_audio)
                    segmentos_audio.append(agregar_transicion())
            else:
                print("      ⚠️ No se pudo generar el segmento de la audiencia.")
        else:
            print("  -> No hay mensaje de la audiencia programado para hoy.")


        print("\n--- FASE 3: Generando cierre del podcast ---")

        # --- INICIO DE LA NUEVA LÓGICA DE CIERRE UNIFICADO ---
        print("  -> Generando monólogo de cierre unificado (resumen + despedida)...")
        
        # 1. Preparar el contexto con los temas tratados para la IA.
        contexto_cierre = []
        for bloque in noticias_agrupadas.get('bloques_tematicos', []):
            contexto_cierre.append(bloque.get('descripcion_tema', 'varios temas'))
        for noticia in noticias_agrupadas.get('noticias_individuales', []):
            contexto_cierre.append(noticia.get('resumen')[:80] + "...")
        
        # 2. Obtener plantilla base de despedida y firma para REINTERPRETACIÓN
        print("      🗣️ Obteniendo plantilla base de despedida y firma...")
        dia_semana = datetime.now().weekday()
        despedida_base = mcmcn_prompts.obtener_plantilla_por_dia(dia_semana, mcmcn_prompts.PlantillasSSML.FRASES_CIERRE_POR_DIA)
        firma_base = mcmcn_prompts.obtener_plantilla_por_dia(dia_semana, mcmcn_prompts.PlantillasSSML.FRASES_FIRMA_FINAL_POR_DIA)

        # 3. Llamar al nuevo prompt unificado que genera todo el monólogo de cierre.
        # SELECCIONAMOS 3 temas/noticias ALEATORIOS para dar variedad y brevedad.
        if len(contexto_cierre) > 3:
            contexto_seleccionado = random.sample(contexto_cierre, 3)
        else:
            contexto_seleccionado = contexto_cierre
            
        contexto_cierre_str = "\n".join(contexto_seleccionado) 
        
        prompt_cierre_unificado = mcmcn_prompts.PromptsCreativos.generar_monologo_cierre_unificado(
            contexto=contexto_cierre_str,
            texto_cta=cta_cierre_text,
            texto_base_despedida=despedida_base,
            texto_firma=firma_base,
            # dato_curioso_resolucion=dato_curioso_resolucion, # DESACTIVADO
            sentimiento_general=sentimiento_general
        )
        
        texto_monologo_cierre = generar_texto_con_gemini(prompt_cierre_unificado)
        
        # 4. Limpiar, sintetizar y añadir el monólogo de cierre.
        if texto_monologo_cierre:
            texto_limpio = limpiar_artefactos_ia(texto_monologo_cierre)
            print(f"      ✅ Monólogo final generado: '{texto_limpio[:100]}...'")
            transcript_data.append({'type': 'outro', 'content': texto_limpio}) # <-- Capturar cierre
            monologo_cierre_audio = sintetizar_ssml_a_audio(f"<speak>{html.escape(texto_limpio)}</speak>")
            if monologo_cierre_audio:
                segmentos_audio.append(monologo_cierre_audio)
        else:
            # Fallback por si la IA falla.
            print("      ⚠️ Fallo en la generación del monólogo. Usando despedida estática.")
            if despedida_base:
                despedida_audio_fallback = sintetizar_ssml_a_audio(despedida_base)
                if despedida_audio_fallback:
                    segmentos_audio.append(despedida_audio_fallback)

        # 4. Añadir la sintonía de cierre DESPUÉS del monólogo.
        ruta_sintonia_cierre = os.path.join("audio_assets", "cierre.mp3")
        if os.path.exists(ruta_sintonia_cierre):
            segmentos_audio.append(AudioSegment.from_file(ruta_sintonia_cierre))
        

        # FASE 4: ENSAMBLAJE INTELIGENTE (BASADO EN TAMAÑO)
        # ============================================================
        print("\n--- FASE 4: Ensamblando y masterizando el podcast final ---")

        # Calcular duración total para decidir método
        duracion_total_seg = sum(len(s) for s in segmentos_audio if s) / 1000
        print(f"  📊 Duración total estimada: {duracion_total_seg / 60:.1f} minutos")

        # Silencio inicial
        podcast_final = AudioSegment.silent(duration=500)

        # Método adaptativo según duración
        if duracion_total_seg < 1200:  # Menos de 20 minutos
            print("  ⚡ Usando ensamblaje directo (podcast corto)")
            for segmento in segmentos_audio:
                if segmento:
                    podcast_final += segmento
        else:
            print("  🔧 Usando ensamblaje por lotes (podcast largo)")
            BATCH_SIZE = 8
            
            for i in range(0, len(segmentos_audio), BATCH_SIZE):
                batch = segmentos_audio[i:i + BATCH_SIZE]
                for segmento in batch:
                    if segmento:
                        podcast_final += segmento
                
                # Liberar memoria cada 3 lotes
                if (i // BATCH_SIZE) % 3 == 0:
                    gc.collect()
                
                print(f"     Progreso: {min(i + BATCH_SIZE, len(segmentos_audio))}/{len(segmentos_audio)} segmentos")

        print(f"  ✅ Ensamblaje completado")

        # Masterizar
        podcast_masterizado = masterizar_a_lufs(podcast_final, TARGET_LUFS)

        # Exportar
        nombre_podcast_final = os.path.join(output_dir, f"podcast_completo_{timestamp}.mp3")
        podcast_masterizado.export(nombre_podcast_final, format="mp3", bitrate=BITRATE)
        
        # Generar transcripción HTML
        generar_html_transcripcion(transcript_data, output_dir, timestamp) # <-- Generar HTML

        print(f"\n🎉 ¡Podcast generado con éxito! Archivo: {nombre_podcast_final}")


    except FileNotFoundError as e:
        print(f"Error: Archivo no encontrado - {e}.")
        sys.exit(1)
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Asegúrate de crear una carpeta 'audio_assets' y 'cta_texts'
    # y de tener un archivo 'feeds.txt' con URLs de RSS/Facebook.
    
    # Este script requiere variables de entorno:
    # GOOGLE_APPLICATION_CREDENTIALS=/ruta/a/tu/credencial.json
    # GCP_PROJECT_ID=tu-proyecto-id
    
    procesar_feeds_google('feeds.txt', min_items=20)