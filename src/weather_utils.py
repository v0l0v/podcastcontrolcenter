import requests
import datetime

def obtener_pronostico_meteo(lat=39.86, lon=-4.03) -> str:
    """
    Obtiene el pronóstico básico para hoy en la ubicación dada (Default: Toledo/CLM).
    Devuelve un string legible para pasar al prompt.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
        "timezone": "Europe/Madrid",
        "forecast_days": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get("daily", {})
        if not daily:
            return ""
            
        t_max = daily["temperature_2m_max"][0]
        t_min = daily["temperature_2m_min"][0]
        precip = daily["precipitation_sum"][0]
        prob_lluvia = daily["precipitation_probability_max"][0]
        
        # Interpretación básica para ayudar al LLM
        sensacion = "agradable"
        if t_max > 30: sensacion = "mucho calor"
        elif t_max > 25: sensacion = "calorcito"
        elif t_max < 10: sensacion = "frío"
        elif t_max < 5: sensacion = "helador"
        
        lluvia_txt = "sin lluvia"
        if precip > 0:
            if precip < 2: lluvia_txt = "quizás cuatro gotas"
            elif precip < 10: lluvia_txt = "lluvia moderada"
            else: lluvia_txt = "mucha lluvia"
            
        return (f"METEOROLOGÍA HOY: Mínima {t_min}°C, Máxima {t_max}°C. "
                f"Estado: {lluvia_txt} ({prob_lluvia}% prob.). "
                f"Sensación térmica general: {sensacion}.")
                
    except Exception as e:
        print(f"Error obteniendo meteo: {e}")
        return ""
