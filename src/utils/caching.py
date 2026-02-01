
import os
import json
import hashlib
from typing import Optional, Dict, Tuple, Any

CACHE_FILE = "cache_structure.json"

def calculate_hash(data: Any) -> str:
    """Calcula un hash MD5 consistente para strings, dicts o listas."""
    if isinstance(data, (dict, list)):
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=True)
    else:
        serialized = str(data)
    
    return hashlib.md5(serialized.encode('utf-8')).hexdigest()

def load_structure_cache() -> Dict[str, Any]:
    """Carga el caché estructural de disco."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error cargando caché estructural: {e}")
            return {}
    return {}

def save_structure_cache(cache: Dict[str, Any]):
    """Guarda el caché estructural a disco."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error guardando caché estructural: {e}")

def get_cached_content(key_hash: str) -> Optional[Dict[str, Any]]:
    """Devuelve el contenido (texto/metadata) si existe para el hash dado."""
    cache = load_structure_cache()
    return cache.get(key_hash)

def cache_content(key_hash: str, content: Dict[str, Any]):
    """Guarda contenido bajo un hash."""
    cache = load_structure_cache()
    cache[key_hash] = content
    save_structure_cache(cache)
