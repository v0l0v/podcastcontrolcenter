import os
import json
from dotenv import load_dotenv

load_dotenv()

# --- CONSTANTES ---
AUDIO_CACHE_DIR = 'audio_cache'

# --- CARGA DE CONFIGURACIÓN EXTERNA ---
def cargar_configuracion():
    # Asume que el archivo de configuración está en la raíz del proyecto, dos niveles arriba de src/config
    # Pero dorototal.py estaba en raiz. Ajustamos path.
    # Si este archivo es src/config/settings.py, la raiz es ../../
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, 'podcast_config.json')
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
