from src.core.regional_data import MUNICIPIO_A_PROVINCIA, MUNICIPIO_A_GAL
from src.core.text_processing import normalize_text_for_similarity

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

def obtener_info_gal(municipio: str, nombre_fuente: str = "") -> str:
    """
    Devuelve el nombre del GAL si el municipio pertenece a uno.
    Devuelve cadena vacía si:
    - El municipio no tiene GAL asignado.
    - El nombre del GAL ya aparece en el nombre de la fuente (para evitar redundancia).
    """
    if not municipio: return ""
    
    gal = MUNICIPIO_A_GAL.get(municipio)
    if not gal or "Comarca de" in gal: # Ignorar los genéricos de capitales si se prefiere
        return ""
        
    # Chequeo de redundancia
    # Normalizamos para comparar
    gal_norm = normalize_text_for_similarity(gal)
    fuente_norm = normalize_text_for_similarity(nombre_fuente)
    
    # Si el nombre del GAL es muy similar o está contenido en la fuente, no lo devolvemos
    if gal_norm in fuente_norm or fuente_norm in gal_norm:
        # Check adicional: si la fuente es MUY corta ("ADIMAN") y el GAL es largo ("ADIMAN (Manchuela...)")
        # igual es redundante.
        return ""
        
    return gal
