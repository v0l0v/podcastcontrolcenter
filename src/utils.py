import os
import json
import time
import random
import re
import hashlib
import unicodedata
import html
import difflib
from typing import Any, Dict, List

# --- CONFIGURACIÓN ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'settings.json')

def cargar_configuracion() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_configuracion(config: Dict[str, Any]):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# --- DECORADORES ---
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

# --- TEXTO Y NORMALIZACIÓN ---
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

_EMOJI_RE = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U0001F900-\U0001F9FF\U00002600-\U000026FF]+", flags=re.UNICODE)
URL_RE = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)
HASHTAG_RE = re.compile(r'#[\wáéíóúüñ]+', re.IGNORECASE)
MENTION_RE = re.compile(r'@\w+', re.IGNORECASE)
DATE_RE = re.compile(r'\b(\d{1,2}[/\-]\d{1,2}([/\-]\d{2,4})?|\d{1,2}\s+de\s+[a-záéíóú]+(\s+de\s+\d{4})?)\b', re.IGNORECASE)
TIME_RE = re.compile(r'\b\d{1,2}:\d{2}(\s*h)?\b', re.IGNORECASE)
DIGITS_RE = re.compile(r'\b\d{3,}\b')

def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

def normalize_text_for_similarity(text: str) -> str:
    if not text:
        return ""
    t = html.unescape(text)
    t = URL_RE.sub(' ', t)
    t = HASHTAG_RE.sub(lambda m: m.group(0)[1:] + ' ', t)
    t = MENTION_RE.sub(' ', t)
    t = _EMOJI_RE.sub(' ', t)
    t = DATE_RE.sub(' ', t)
    t = TIME_RE.sub(' ', t)
    t = DIGITS_RE.sub(' ', t)
    t = strip_accents(t.lower())
    t = re.sub(r'[^a-zñáéíóúü\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    tokens = [w for w in t.split() if w not in SPANISH_STOPWORDS and len(w) > 2]
    return ' '.join(tokens)

def stable_text_hash(text: str) -> str:
    return hashlib.md5(normalize_text_for_similarity(text).encode('utf-8')).hexdigest()

def limpiar_artefactos_ia(texto: str) -> str:
    texto_limpio = re.sub(r'\s*\([^)]*?(dicho|le[ée]|leer|voz|tono|sonido|efecto|m[úu]sica)[^)]*?\)\s*', ' ', texto, flags=re.IGNORECASE)
    texto_limpio = re.sub(r'\s*\[[^\]]*?(dicho|le[ée]|leer|voz|tono|sonido|efecto|m[úu]sica)[^\]]*?\]\s*', ' ', texto_limpio, flags=re.IGNORECASE)
    patron_sin_parentesis = r'\b(lee|leer|lei|leí|leído)\s+con\s+\w+\b'
    texto_limpio = re.sub(patron_sin_parentesis, ' ', texto_limpio, flags=re.IGNORECASE)
    texto_limpio = re.sub(r'\b(m[úu]sica de.*?)(que se desvanece|al final|de fondo)', '', texto_limpio, flags=re.IGNORECASE)
    texto_limpio = texto_limpio.replace('¿?¿?¿?', '')
    texto_limpio = re.sub(r'\*{1,2}([^*]+?)\*{1,2}', r'\1', texto_limpio)
    texto_limpio = re.sub(r'^[A-ZÁÉÍÓÚ\s]+:$', '', texto_limpio, flags=re.MULTILINE)
    texto_limpio = re.sub(r'(\d{4})/(\d{4})', r'\1 a \2', texto_limpio)
    lineas = []
    for linea in texto_limpio.split('\n'):
        linea_limpia = linea.strip()
        if linea_limpia and not re.match(r'^\s*(\d+\.|\*+)\s*$', linea_limpia):
            lineas.append(linea_limpia)
    texto_final = '\n'.join(lineas)
    texto_final = re.sub(r'[ \t]+', ' ', texto_final).strip()
    return texto_final

def preprocesar_texto_para_fechas(texto: str) -> str:
    patron = r'\b(hoy|ayer|mañana|esta mañana|esta tarde|anoche)\b([,.\s]+)(\d{1,2}\s+de\s+\w+)'
    def reemplazo_inteligente(match):
        fecha_absoluta = match.group(3)
        return f"el {fecha_absoluta}"
    return re.sub(patron, reemplazo_inteligente, texto, flags=re.IGNORECASE)

def reemplazar_urls_por_mencion(texto: str) -> str:
    url_pattern = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)
    texto_reemplazo = " Para más detalles, puedes consultar los enlaces en la publicación original. "
    return url_pattern.sub(texto_reemplazo, texto)

def limpiar_html(texto_html: str) -> str:
    texto_limpio = re.sub(r'<[^>]+>', '', texto_html)
    return html.unescape(texto_limpio)

# --- LOCALIDADES ---
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
    # Comarcas
    "Castilla-La Mancha": "Castilla-La Mancha", "Castilla la Mancha": "Castilla-La Mancha",
    "La Mancha": "Castilla-La Mancha", "Sierra de Alcaraz": "Albacete",
    "Campos de Montiel": "Ciudad Real", "La Alcarria": "Guadalajara",
    "Serranía de Cuenca": "Cuenca", "La Sagra": "Toledo"
}

def obtener_provincia(localidad: str) -> str:
    provincia = MUNICIPIO_A_PROVINCIA.get(localidad)
    if provincia:
        return provincia
    for key, value in MUNICIPIO_A_PROVINCIA.items():
        if key in localidad:
            return value
    return "Desconocida"
