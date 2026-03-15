import requests
import datetime
import random
import os
import time

from dotenv import load_dotenv
load_dotenv(override=True)

# --- CÃ“DIGOS INE para AEMET ---
# Los cÃ³digos de municipio para la API de AEMET siguen el formato del INE (5 dÃ­gitos).
# Usamos 1 capital + 1 punto representativo por provincia para reducir requests (10 total).
MUNICIPIOS_AEMET = {
    "Albacete": [
        {"nombre": "Albacete", "ine": "02003", "lat": 38.99, "lon": -1.85},
        {"nombre": "HellÃ­n", "ine": "02037", "lat": 38.51, "lon": -1.70},
        {"nombre": "Villarrobledo", "ine": "02081", "lat": 39.26, "lon": -2.60},
        {"nombre": "Almansa", "ine": "02009", "lat": 38.86, "lon": -1.09},
        {"nombre": "La Roda", "ine": "02069", "lat": 39.20, "lon": -2.15}
    ],
    "Ciudad Real": [
        {"nombre": "Ciudad Real", "ine": "13034", "lat": 38.98, "lon": -3.92},
        {"nombre": "Puertollano", "ine": "13071", "lat": 38.68, "lon": -4.10},
        {"nombre": "Tomelloso", "ine": "13082", "lat": 39.15, "lon": -3.02},
        {"nombre": "AlcÃ¡zar de San Juan", "ine": "13005", "lat": 39.39, "lon": -3.21},
        {"nombre": "AlmadÃ©n", "ine": "13011", "lat": 38.78, "lon": -4.83}
    ],
    "Cuenca": [
        {"nombre": "Cuenca", "ine": "16078", "lat": 40.07, "lon": -2.13},
        {"nombre": "TarancÃ³n", "ine": "16203", "lat": 40.00, "lon": -3.00},
        {"nombre": "Quintanar del Rey", "ine": "16175", "lat": 39.34, "lon": -1.93},
        {"nombre": "Las PedroÃ±eras", "ine": "16154", "lat": 39.45, "lon": -2.67},
        {"nombre": "San Clemente", "ine": "16190", "lat": 39.40, "lon": -2.43}
    ],
    "Guadalajara": [
        {"nombre": "Guadalajara", "ine": "19130", "lat": 40.63, "lon": -3.16},
        {"nombre": "Azuqueca de Henares", "ine": "19047", "lat": 40.56, "lon": -3.26},
        {"nombre": "SigÃ¼enza", "ine": "19301", "lat": 41.06, "lon": -2.64},
        {"nombre": "Molina de AragÃ³n", "ine": "19190", "lat": 40.84, "lon": -1.88},
        {"nombre": "Cabanillas del Campo", "ine": "19059", "lat": 40.63, "lon": -3.23}
    ],
    "Toledo": [
        {"nombre": "Toledo", "ine": "45168", "lat": 39.86, "lon": -4.02},
        {"nombre": "Talavera de la Reina", "ine": "45165", "lat": 39.96, "lon": -4.83},
        {"nombre": "Illescas", "ine": "45081", "lat": 40.12, "lon": -3.84},
        {"nombre": "SeseÃ±a", "ine": "45161", "lat": 40.10, "lon": -3.70},
        {"nombre": "Torrijos", "ine": "45174", "lat": 39.98, "lon": -4.28}
    ]
}

# Alias para compatibilidad con el cÃ³digo existente que usaba POBLACIONES_CLM
POBLACIONES_CLM = MUNICIPIOS_AEMET

# --- CONSTANTES AEMET ---
AEMET_BASE_URL = "https://opendata.aemet.es/opendata/api"


def obtener_descripcion_temp(temp: float) -> str:
    """Devuelve una descripciÃ³n cualitativa basada en la temperatura."""
    if temp < -5: return "friÃ­simo"
    if temp < 0: return "mucho frÃ­o"
    if temp < 10: return "frÃ­o"
    if temp < 15: return "algo de frÃ­o"
    if temp < 20: return "poco frÃ­o"
    if temp < 25: return "agradable"
    if temp < 30: return "calor"
    if temp < 35: return "mucho calor"
    return "calor extremo"


# ============================================================
# AEMET - Fuente principal
# ============================================================

def _aemet_request(endpoint: str, timeout: int = 10) -> dict | None:
    """
    Realiza una peticiÃ³n a la API de AEMET (doble request).
    Paso 1: GET al endpoint â†’ JSON con campo 'datos' (URL temporal).
    Paso 2: GET a esa URL temporal â†’ datos reales.
    Retorna el JSON de datos o None si falla.
    """
    api_key = os.getenv("AEMET_API_KEY", "")
    if not api_key:
        print("      âš ï¸� AEMET: AEMET_API_KEY no encontrada en el entorno.")
        return None

    headers = {
        "api_key": api_key,
        "Accept": "application/json"
    }
    
    try:
        # Paso 1: Obtener URL de datos
        url = f"{AEMET_BASE_URL}{endpoint}"
        resp1 = requests.get(url, headers=headers, timeout=timeout)
        
        if resp1.status_code != 200:
            print(f"      âš ï¸� AEMET Paso 1 fallÃ³ (HTTP {resp1.status_code}): {endpoint}")
            if resp1.status_code == 401:
                print("      ðŸ”‘ Error de autenticaciÃ³n: Verifica que la AEMET_API_KEY sea vÃ¡lida.")
            elif resp1.status_code == 429:
                print("      â�³ LÃ­mite de peticiones (Rate Limit) alcanzado.")
            return None
        
        meta = resp1.json()
        estado = meta.get("estado")
        if estado == 401:
             print("      ðŸ”‘ AEMET reporta Error 401 en el cuerpo del JSON (API Key invÃ¡lida).")
             return None

        url_datos = meta.get("datos")
        if not url_datos:
            print(f"      âš ï¸� AEMET no devolviÃ³ URL de datos para: {endpoint}. Respuesta: {meta}")
            return None
        
        # Paso 2: Descargar datos reales
        resp2 = requests.get(url_datos, timeout=timeout)
        
        if resp2.status_code != 200:
            print(f"      ⚠️ AEMET Paso 2 falló (HTTP {resp2.status_code}) al descargar de {url_datos}")
            return None
        
        return resp2.json()
    
    except Exception as e:
        print(f"      ⚠️ Error de conexión con AEMET: {e}")
        return None


def _parsear_prediccion_aemet(datos_json: list) -> dict | None:
    """
    Parsea la respuesta de predicciÃ³n diaria de AEMET.
    Extrae: temp_max, temp_min, prob_precipitaciÃ³n, estado_cielo para HOY.
    """
    if not datos_json or not isinstance(datos_json, list):
        return None

    try:
        prediccion = datos_json[0]  # Primer municipio
        dias = prediccion.get("prediccion", {}).get("dia", [])
        
        if not dias:
            return None
        
        # Hoy es el primer dÃ­a
        hoy = dias[0]
        
        # Temperaturas
        temp_data = hoy.get("temperatura", {})
        t_max = temp_data.get("maxima")
        t_min = temp_data.get("minima")
        
        if t_max is None or t_min is None:
            return None
        
        t_max = float(t_max)
        t_min = float(t_min)
        
        # Probabilidad de precipitaciÃ³n (mÃ¡xima del dÃ­a)
        prob_precip = 0
        periodos_precip = hoy.get("probPrecipitacion", [])
        for periodo in periodos_precip:
            valor = periodo.get("value") or periodo.get("valor", 0)
            try:
                prob_precip = max(prob_precip, int(valor))
            except (ValueError, TypeError):
                pass
        
        # Estado del cielo (descripciÃ³n del perÃ­odo mÃ¡s representativo)
        estado_cielo = ""
        periodos_cielo = hoy.get("estadoCielo", [])
        for periodo in periodos_cielo:
            desc = periodo.get("descripcion", "")
            if desc:
                estado_cielo = desc
                break  # Tomamos la primera descripciÃ³n disponible
        
        return {
            "t_max": t_max,
            "t_min": t_min,
            "prob_precip": prob_precip,
            "estado_cielo": estado_cielo
        }
    
    except Exception as e:
        print(f"      âš ï¸� Error parseando AEMET: {e}")
        return None


def _obtener_meteo_aemet_regional() -> dict | None:
    """
    Obtiene datos meteorolÃ³gicos de AEMET para toda Castilla-La Mancha.
    Consulta 1 municipio representativo por provincia (5 requests).
    """
    # Solo consultamos las capitales para no saturar la API
    capitales = {
        "Albacete": "02003",
        "Ciudad Real": "13034",
        "Cuenca": "16078",
        "Guadalajara": "19130",
        "Toledo": "45168"
    }
    
    resultados = []
    
    print(f"      â˜�ï¸�  [AEMET] Consultando predicciÃ³n para {len(capitales)} capitales de provincia...")
    
    for i, (prov, ine) in enumerate(capitales.items()):
        if i > 0:
            time.sleep(0.3)  # Evitar rate limiting de AEMET (429)
        datos = _aemet_request(f"/prediccion/especifica/municipio/diaria/{ine}")
        if datos:
            parsed = _parsear_prediccion_aemet(datos)
            if parsed:
                parsed["provincia"] = prov
                resultados.append(parsed)
    
    if not resultados:
        return None
    
    # Calcular medias y extremos
    promedio_max = sum(r['t_max'] for r in resultados) / len(resultados)
    promedio_min = sum(r['t_min'] for r in resultados) / len(resultados)
    media_total = (promedio_max + promedio_min) / 2
    
    desc_general = obtener_descripcion_temp(media_total)
    
    # Lluvia: si alguna capital tiene >60% prob
    lluvia_general = any(r['prob_precip'] > 60 for r in resultados)
    t_lluvia = "se esperan lluvias" if lluvia_general else "cielos mayormente despejados"
    
    # Estado del cielo (tomar el mÃ¡s comÃºn o el primero disponible)
    estados_cielo = [r.get('estado_cielo', '') for r in resultados if r.get('estado_cielo')]
    cielo_desc = estados_cielo[0] if estados_cielo else ""
    
    resumen_texto = (
        f"DATOS METEOROLÃ“GICOS REGIONALES (AEMET - media): \n"
        f"- SensaciÃ³n TÃ©rmica General: {desc_general}. \n"
        f"- Estado del cielo: {t_lluvia}"
        + (f" ({cielo_desc})" if cielo_desc else "") + ". \n"
        f"- Temperatura Media Regional: {media_total:.1f}Â°C."
    )
    
    return {
        "texto": resumen_texto,
        "media_temp": media_total,
        "lluvia": lluvia_general,
        "fuente": "AEMET"
    }


def _obtener_meteo_aemet_provincia(provincia: str) -> dict | None:
    """
    Obtiene el clima de AEMET para una provincia concreta.
    Consulta la capital de esa provincia.
    """
    municipios = MUNICIPIOS_AEMET.get(provincia, [])
    if not municipios:
        return None
    
    # Usar la capital (primer municipio de la lista)
    mun = municipios[0]
    ine = mun.get("ine")
    
    if not ine:
        return None
    
    datos = _aemet_request(f"/prediccion/especifica/municipio/diaria/{ine}")
    if not datos:
        return None
    
    parsed = _parsear_prediccion_aemet(datos)
    if not parsed:
        return None
    
    media = (parsed['t_max'] + parsed['t_min']) / 2
    
    return {
        "provincia": provincia,
        "ciudad_ref": mun['nombre'],
        "media_temp": media,
        "t_max": parsed['t_max'],
        "t_min": parsed['t_min'],
        "fuente": "AEMET"
    }


# ============================================================
# Open-Meteo - Fallback de seguridad
# ============================================================

def _obtener_meteo_openmeteo_regional() -> dict | None:
    """
    Fallback: Obtiene el pronÃ³stico meteorolÃ³gico regional usando Open-Meteo.
    LÃ³gica original intacta.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    resultados = []
    
    todas_poblaciones = []
    for prov, lista in MUNICIPIOS_AEMET.items():
        for p in lista:
            p_copy = p.copy()
            p_copy['provincia'] = prov
            todas_poblaciones.append(p_copy)
            
    print(f"      â˜�ï¸�  [Open-Meteo Fallback] Consultando tiempo para TODA la regiÃ³n ({len(todas_poblaciones)} puntos)...")

    for pob in todas_poblaciones:
        params = {
            "latitude": pob['lat'],
            "longitude": pob['lon'],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
            "timezone": "Europe/Madrid",
            "forecast_days": 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=1) 
            if response.status_code == 200:
                data = response.json()
                daily = data.get("daily", {})
                if daily:
                    resultados.append({
                        "nombre": pob['nombre'],
                        "provincia": pob['provincia'],
                        "t_max": daily["temperature_2m_max"][0],
                        "t_min": daily["temperature_2m_min"][0],
                        "lluvia_prob": daily["precipitation_probability_max"][0]
                    })
        except Exception:
            continue

    if not resultados:
        return None

    # Promedios
    promedio_max = sum(r['t_max'] for r in resultados) / len(resultados)
    promedio_min = sum(r['t_min'] for r in resultados) / len(resultados)
    media_total = (promedio_max + promedio_min) / 2
    
    desc_general = obtener_descripcion_temp(media_total)

    lluvia_general = any(r['lluvia_prob'] > 60 for r in resultados)
    t_lluvia = "se esperan lluvias" if lluvia_general else "cielos mayormente despejados"

    resumen_texto = (
        f"DATOS METEOROLÃ“GICOS REGIONALES (media): \n"
        f"- SensaciÃ³n TÃ©rmica General: {desc_general}. \n"
        f"- Estado del cielo: {t_lluvia}. \n"
        f"- Temperatura Media Regional: {media_total:.1f}Â°C."
    )
    return {
        "texto": resumen_texto,
        "media_temp": media_total,
        "lluvia": lluvia_general,
        "fuente": "Open-Meteo"
    }


def _obtener_meteo_openmeteo_provincia(provincia: str) -> dict:
    """
    Fallback: Obtiene el clima de Open-Meteo para una provincia.
    LÃ³gica original intacta.
    """
    poblaciones = MUNICIPIOS_AEMET.get(provincia, [])
    if not poblaciones:
        poblaciones = MUNICIPIOS_AEMET.get("Albacete")
    
    pob = random.choice(poblaciones)
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": pob['lat'],
        "longitude": pob['lon'],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Europe/Madrid",
        "forecast_days": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=2)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            if daily:
                t_max = daily["temperature_2m_max"][0]
                t_min = daily["temperature_2m_min"][0]
                media = (t_max + t_min) / 2
                return {
                    "provincia": provincia,
                    "ciudad_ref": pob['nombre'],
                    "media_temp": media,
                    "t_max": t_max,
                    "t_min": t_min,
                    "fuente": "Open-Meteo"
                }
    except Exception as e:
        print(f"Error meteo provincia {provincia}: {e}")
        
    return {}


# ============================================================
# Funciones pÃºblicas (interfaz que usan dorototal.py y humanization.py)
# ============================================================

def obtener_pronostico_meteo(lat=None, lon=None) -> dict:
    """
    Obtiene el pronÃ³stico meteorolÃ³gico regional para Castilla-La Mancha.
    Intenta primero con AEMET (oficial). Si falla, usa Open-Meteo como fallback.
    """
    # Intento 1: AEMET (fuente oficial)
    resultado = _obtener_meteo_aemet_regional()
    
    if resultado:
        print(f"      âœ… Meteo obtenida desde AEMET (temp media {resultado.get('media_temp', '?'):.1f}ÂºC)")
        return resultado
    
    # Intento 2: Open-Meteo (fallback)
    print("      âš ï¸� AEMET fallÃ³, usando Open-Meteo como fallback...")
    resultado = _obtener_meteo_openmeteo_regional()
    
    if resultado:
        print(f"      âœ… Meteo obtenida desde Open-Meteo (temp media {resultado.get('media_temp', '?'):.1f}ÂºC)")
        return resultado
    
    return ""


def obtener_meteo_para_provincia(provincia: str) -> dict:
    """
    Obtiene el clima de una poblaciÃ³n representativa de la provincia indicada.
    Intenta primero con AEMET. Si falla, usa Open-Meteo como fallback.
    """
    # Intento 1: AEMET
    resultado = _obtener_meteo_aemet_provincia(provincia)
    
    if resultado:
        return resultado
    
    # Intento 2: Open-Meteo (fallback)
    return _obtener_meteo_openmeteo_provincia(provincia)
