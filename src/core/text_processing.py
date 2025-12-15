import re
import html
import unicodedata
import hashlib
import difflib
import numpy as np
from num2words import num2words
from src.config.settings import SPANISH_STOPWORDS, CONFIG, NGRAM_N

# --- (Opcional) RapidFuzz ---
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except Exception:
    RAPIDFUZZ_AVAILABLE = False

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

def reparar_codificacion(texto: str) -> str:
    """Intenta arreglar texto decodificado incorrectamente (mojibake)."""
    if not texto: return ""
    try:
        fixed = texto.encode('cp1252').decode('utf-8')
        return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
        
    try:
        fixed = texto.encode('latin-1').decode('utf-8')
        return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    return texto

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
# UTILIDADES DE TEXTO PARA TTS
# =================================================================================

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
    
    if num > 100:
        return f"{num}º" if genero == 'masculino' else f"{num}ª"
    
    if 20 < num < 100:
        decena = (num // 10) * 10
        unidad = num % 10
        if unidad == 0:
            return ordinales.get(decena, str(num))
        
        decena_ord = ordinales.get(decena, "")
        unidad_ord = ordinales.get(unidad, "")
        
        if decena_ord and unidad_ord:
            return f"{decena_ord} {unidad_ord}"
    
    return str(num)

def detectar_contexto_ordinal(texto_antes: str, texto_despues: str) -> bool:
    palabras_antes_ordinal = [
        'el', 'la', 'del', 'de la', 'al', 'a la', 'en el', 'en la',
        'para el', 'para la', 'desde el', 'desde la', 'hasta el', 'hasta la'
    ]
    palabras_despues_ordinal = [
        'edición', 'congreso', 'conferencia', 'semana', 'mes', 'año', 'siglo',
        'jornada', 'festival', 'feria', 'exposición', 'muestra', 'encuentro',
        'reunión', 'asamblea', 'sesión', 'capítulo', 'temporada', 'episodio',
        'acto', 'escena', 'parte', 'sección', 'fase', 'etapa', 'ronda',
        'día', 'vez', 'lugar', 'puesto', 'premio', 'posición', 'aniversario'
    ]
    
    texto_antes_lower = texto_antes.lower().strip()
    texto_despues_lower = texto_despues.lower().strip()
    
    for palabra in palabras_antes_ordinal:
        if texto_antes_lower.endswith(palabra):
            return True
    
    primera_palabra_despues = texto_despues_lower.split()[0] if texto_despues_lower else ""
    if primera_palabra_despues in palabras_despues_ordinal:
        return True
    return False

def detectar_genero_contexto(texto_despues: str) -> str:
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
    roman_regex = r'(\S*\s*)?\b(M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))\b(\s*\S*)?'
    is_ssml = texto.strip().startswith('<speak>')
    
    def replacer(match):
        contexto_antes = match.group(1) if match.group(1) else ""
        roman_numeral = match.group(2)
        contexto_despues = match.group(3) if match.group(3) else ""
        
        if len(roman_numeral) == 1 and roman_numeral in "IVXLCDM":
            if not detectar_contexto_ordinal(contexto_antes, contexto_despues):
                return match.group(0)
        
        try:
            integer_value = roman_to_int(roman_numeral)
            if integer_value > 0 and integer_value <= 100:
                es_ordinal = detectar_contexto_ordinal(contexto_antes, contexto_despues)
                if es_ordinal:
                    genero = detectar_genero_contexto(contexto_despues)
                    palabra = numero_a_ordinal_espanol(integer_value, genero)
                    if is_ssml:
                        return f'{contexto_antes}<sub alias="{palabra}">{roman_numeral}</sub>{contexto_despues}'
                    else:
                        return f'{contexto_antes}{palabra}{contexto_despues}'
                else:
                    palabra = num2words(integer_value, lang='es')
                    if is_ssml:
                        return f'{contexto_antes}<sub alias="{palabra}">{roman_numeral}</sub>{contexto_despues}'
                    else:
                        return f'{contexto_antes}{palabra}{contexto_despues}'
        except (KeyError, IndexError, ValueError):
            return match.group(0)
        return match.group(0)
    
    if is_ssml:
        content_match = re.search(r"<speak>(.*)</speak>", texto, re.DOTALL)
        if content_match:
            content = content_match.group(1)
            processed_content = re.sub(roman_regex, replacer, content, flags=re.IGNORECASE)
            return f"<speak>{processed_content}</speak>"
        else:
            return texto
    else:
        return re.sub(roman_regex, replacer, texto, flags=re.IGNORECASE)

def corregir_palabras_deletreadas_tts(texto: str) -> str:
    is_ssml = texto.strip().startswith('<speak>')
    pronunciation_config = CONFIG.get('pronunciation', {})
    correcciones_palabras = pronunciation_config.get('correcciones', {})
    siglas_para_deletrear = pronunciation_config.get('siglas', {})
    
    if not correcciones_palabras:
        correcciones_palabras = {
            'RECAMDER': 'Recamder', 'LEADER': 'Leader', 'FEADER': 'Feader',
            'CEDER': 'Ceder', 'AYUNTAMIENTO': 'Ayuntamiento'
        }
    if not siglas_para_deletrear:
        siglas_para_deletrear = {'UE': 'U E', 'PP': 'P P', 'UGT': 'U G T'}
    
    def aplicar_correccion(texto_procesado, diccionario_correcciones):
        for palabra_problema, correccion in diccionario_correcciones.items():
            patron = rf'\b{re.escape(palabra_problema)}\b'
            texto_procesado = re.sub(patron, correccion, texto_procesado, flags=re.IGNORECASE)
        return texto_procesado
    
    def corregir_parentesis(texto_procesado):
        def parentesis_replacer(match):
            contenido = match.group(1).strip()
            if contenido.upper() in siglas_para_deletrear:
                espaciado = siglas_para_deletrear[contenido.upper()]
                if is_ssml: return f'(<sub alias="{espaciado}">{contenido}</sub>)'
                else: return f'({espaciado})'
            if contenido.isupper():
                if contenido in correcciones_palabras:
                    corregido = correcciones_palabras[contenido]
                    if is_ssml: return f'(<sub alias="{corregido}">{contenido}</sub>)'
                    else: return f'({corregido})'
                elif len(contenido) <= 5 and contenido.isalpha():
                    espaciado = ' '.join(contenido)
                    if is_ssml: return f'(<sub alias="{espaciado}">{contenido}</sub>)'
                    else: return f'({espaciado})'
            return match.group(0)
        return re.sub(r'\(([^)]+)\)', parentesis_replacer, texto_procesado)
    
    if is_ssml:
        content_match = re.search(r"<speak>(.*)</speak>", texto, re.DOTALL)
        if content_match:
            content = content_match.group(1)
            content = aplicar_correccion(content, correcciones_palabras)
            content = aplicar_correccion(content, siglas_para_deletrear)
            content = corregir_parentesis(content)
            for palabra in correcciones_palabras:
                if palabra in content and not f'<sub alias=' in content:
                    patron = rf'\b{re.escape(palabra)}\b'
                    reemplazo = f'<sub alias="{correcciones_palabras[palabra]}">{palabra}</sub>'
                    content = re.sub(patron, reemplazo, content, flags=re.IGNORECASE)
            return f"<speak>{content}</speak>"
        else:
            return texto
    else:
        texto_procesado = texto
        texto_procesado = aplicar_correccion(texto_procesado, correcciones_palabras)
        texto_procesado = aplicar_correccion(texto_procesado, siglas_para_deletrear)
        texto_procesado = corregir_parentesis(texto_procesado)
        return texto_procesado

def corregir_numeros_con_puntos_tts(texto: str) -> str:
    is_ssml = texto.strip().startswith('<speak>')
    pattern_dots = r'(?<![a-zA-Z])\b\d{1,3}(?:\.\d{3})+\b'
    pattern_plain = r'(?<![\.,])\b\d{5,}\b'

    def replacer(match):
        numero_str = match.group(0)
        numero_sin_puntos = re.sub(r'\.', '', numero_str)
        try:
            numero_int = int(numero_sin_puntos)
            palabra = num2words(numero_int, lang='es')
            if is_ssml: return f'<sub alias="{palabra}">{numero_str}</sub>'
            else: return palabra
        except (ValueError, OverflowError):
            return numero_str

    if is_ssml:
        content_match = re.search(r"<speak>(.*)</speak>", texto, re.DOTALL)
        if content_match:
            content = content_match.group(1)
            content = re.sub(pattern_dots, replacer, content)
            content = re.sub(pattern_plain, replacer, content)
            return f"<speak>{content}</speak>"
        else:
            return texto
    else:
        texto = re.sub(pattern_dots, replacer, texto)
        texto = re.sub(pattern_plain, replacer, texto)
        return texto

def limpiar_artefactos_ia(texto: str) -> str:
    texto_limpio = re.sub(
        r'\s*\([^)]*?(dicho|le[ée]|leer|voz|tono|sonido|efecto|m[úu]sica)[^)]*?\)\s*',
        ' ', texto, flags=re.IGNORECASE
    )
    texto_limpio = re.sub(
        r'\s*\[[^\]]*?(dicho|le[ée]|leer|voz|tono|sonido|efecto|m[úu]sica)[^\]]*?\]\s*',
        ' ', texto_limpio, flags=re.IGNORECASE
    )
    patron_sin_parentesis = r'\b(lee|leer|lei|leí|leído)\s+con\s+\w+\b'
    texto_limpio = re.sub(patron_sin_parentesis, ' ', texto_limpio, flags=re.IGNORECASE)
    texto_limpio = re.sub(r'\b(m[úu]sica de.*?)(que se desvanece|al final|de fondo)', '', texto_limpio, flags=re.IGNORECASE)
    texto_limpio = texto_limpio.replace('¿?¿?¿?', '')
    texto_limpio = texto_limpio.replace('*', '')
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

def convertir_ssml_a_texto_plano(ssml_text: str) -> str:
    text = re.sub(r'<sub\s+alias=["\']([^"\']+)["\'][^>]*>.*?</sub>', r'\1', ssml_text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<break[^>]*>', '... ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def limpiar_markdown_audio(texto: str) -> str:
    texto = re.sub(r'\*{1,2}([^*]+?)\*{1,2}', r'\1', texto)
    texto = re.sub(r'_{1,2}([^_]+?)_{1,2}', r'\1', texto)
    return texto

def limpiar_html(texto_html: str) -> str:
    texto_limpio = re.sub(r'<[^>]+>', '', texto_html)
    return html.unescape(texto_limpio)

# =================================================================================
# UTILIDADES DE EXTRACCIÓN (CLUSTERING)
# =================================================================================

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
    # secuencias de nombres propios
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
    if isinstance(n, int): n = (n,)
    for k in n:
        keys += ngrams(toks, k)
    # filtra solo los que no son puro stopword
    keys = [k for k in keys if any(w not in SPANISH_STOPWORDS for w in k.split())]
    return keys

def match_stem(text_norm: str, stems: list) -> bool:
    return any(st in text_norm for st in stems)
