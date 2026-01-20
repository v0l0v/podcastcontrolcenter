import requests
import datetime
import random

# Diccionario de poblaciones clave por provincia en CLM con sus coordenadas (Aprox)
# Se han añadido puntos conocidos por sus extremos térmicos (ej: Almadén, Molina) para mayor precisión.
POBLACIONES_CLM = {
    "Albacete": [
        {"nombre": "Albacete", "lat": 38.99, "lon": -1.85},
        {"nombre": "Hellín", "lat": 38.51, "lon": -1.70},
        {"nombre": "Villarrobledo", "lat": 39.26, "lon": -2.60},
        {"nombre": "Almansa", "lat": 38.86, "lon": -1.09},
        {"nombre": "La Roda", "lat": 39.20, "lon": -2.15}
    ],
    "Ciudad Real": [
        {"nombre": "Ciudad Real", "lat": 38.98, "lon": -3.92},
        {"nombre": "Puertollano", "lat": 38.68, "lon": -4.10},
        {"nombre": "Tomelloso", "lat": 39.15, "lon": -3.02},
        {"nombre": "Alcázar de San Juan", "lat": 39.39, "lon": -3.21},
        {"nombre": "Almadén", "lat": 38.78, "lon": -4.83} # Conocido por calor extremo
    ],
    "Cuenca": [
        {"nombre": "Cuenca", "lat": 40.07, "lon": -2.13},
        {"nombre": "Tarancón", "lat": 40.00, "lon": -3.00},
        {"nombre": "Quintanar del Rey", "lat": 39.34, "lon": -1.93},
        {"nombre": "Las Pedroñeras", "lat": 39.45, "lon": -2.67},
        {"nombre": "San Clemente", "lat": 39.40, "lon": -2.43}
    ],
    "Guadalajara": [
        {"nombre": "Guadalajara", "lat": 40.63, "lon": -3.16},
        {"nombre": "Azuqueca de Henares", "lat": 40.56, "lon": -3.26},
        {"nombre": "Sigüenza", "lat": 41.06, "lon": -2.64},
        {"nombre": "Molina de Aragón", "lat": 40.84, "lon": -1.88}, # Conocido por frío extremo
        {"nombre": "Cabanillas del Campo", "lat": 40.63, "lon": -3.23}
    ],
    "Toledo": [
        {"nombre": "Toledo", "lat": 39.86, "lon": -4.02},
        {"nombre": "Talavera de la Reina", "lat": 39.96, "lon": -4.83}, # Conocido por calor
        {"nombre": "Illescas", "lat": 40.12, "lon": -3.84},
        {"nombre": "Seseña", "lat": 40.10, "lon": -3.70},
        {"nombre": "Torrijos", "lat": 39.98, "lon": -4.28}
    ]
}

def obtener_descripcion_temp(temp: float) -> str:
    """Devuelve una descripción cualitativa basada en la temperatura."""
    if temp < -5: return "friísimo"
    if temp < 0: return "mucho frío"
    if temp < 10: return "frío"
    if temp < 15: return "algo de frío"
    if temp < 20: return "poco frío"
    if temp < 25: return "agradable"
    if temp < 30: return "calor"
    if temp < 35: return "mucho calor"
    return "calor extremo"

def obtener_pronostico_meteo(lat=None, lon=None) -> str:
    """
    Obtiene el pronóstico meteorológico regional para Castilla-La Mancha (Exhaustivo).
    1. Consulta TODAS las poblaciones clave para encontrar extremos reales.
    2. Devuelve descripciones cualitativas ("frio", "calor") en lugar de números exactos.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    resultados = []
    
    # Aplanar lista de poblaciones para iterar todas
    todas_poblaciones = []
    for prov, lista in POBLACIONES_CLM.items():
        for p in lista:
            p['provincia'] = prov
            todas_poblaciones.append(p)
            
    print(f"      ☁️  Consultando tiempo para TODA la región ({len(todas_poblaciones)} puntos)...")

    # Optimización: Consultar en secuencia (Open-Meteo es rápido, 25 requests ~1-2s)
    # Si fuera necesario, usar aiohttp/asyncio, pero requests simple es suficiente aquí.
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
        return ""

    # Encontrar extremos
    # 1. Máxima más alta
    max_absoluta = max(resultados, key=lambda x: x['t_max'])
    # Si hay empate, coger todos los que tengan esa temp y elegir uno al azar
    candidatos_max = [r for r in resultados if r['t_max'] == max_absoluta['t_max']]
    ganador_max = random.choice(candidatos_max)
    
    # 2. Mínima más baja
    min_absoluta = min(resultados, key=lambda x: x['t_min'])
    candidatos_min = [r for r in resultados if r['t_min'] == min_absoluta['t_min']]
    ganador_min = random.choice(candidatos_min)

    # Descripciones
    desc_max = obtener_descripcion_temp(ganador_max['t_max'])
    desc_min = obtener_descripcion_temp(ganador_min['t_min'])

    # Sensacion general (Promedio de máximas)
    promedio_max = sum(r['t_max'] for r in resultados) / len(resultados)
    desc_general = obtener_descripcion_temp(promedio_max)

    # Lluvia general
    lluvia_general = any(r['lluvia_prob'] > 60 for r in resultados)
    t_lluvia = "se esperan lluvias" if lluvia_general else "cielos mayormente despejados"

    # Construir string informativo para la IA
    # Se proporcionan datos exactos Y cualitativos para que la IA elija cómo contarlo.
    
    resumen = (
        f"DATOS METEOROLÓGICOS (CASTILLA-LA MANCHA): \n"
        f"- Sensación General: {desc_general}, cielos {t_lluvia}. \n"
        f"- MÁXIMA Regional: {ganador_max['nombre']} ({ganador_max['provincia']}) alcanza los {ganador_max['t_max']}°C ({desc_max}). \n"
        f"- MÍNIMA Regional: {ganador_min['nombre']} ({ganador_min['provincia']}) baja a {ganador_min['t_min']}°C ({desc_min})."
    )

    return resumen
