
import datetime
import holidays
import json
import os
from src.config.settings import CONFIG

def obtener_festividades_contexto(anio: int = None) -> str:
    """
    Genera un texto con las fechas de festividades clave para el año dado.
    Combina festivos nacionales/regionales (usando librería 'holidays')
    y festividades locales manuales (desde podcast_config.json).
    """
    if anio is None:
        anio = datetime.datetime.now().year

    # 1. Obtener festivos de España y Castilla-La Mancha
    es_holidays = holidays.ES(years=anio, prov='CM') # CM = Castilla-La Mancha
    
    # 2. Obtener festivos manuales de config
    custom_festivities = CONFIG.get('festividades', {})
    
    lista_festivos = []
    
    # Procesar librería holidays
    for date, name in sorted(es_holidays.items()):
        lista_festivos.append(f"- {name}: {date.strftime('%d-%m-%Y')}")
        
    # Procesar manuales
    for nombre, fecha_str in custom_festivities.items():
        # fecha_str viene como "DD-MM", le añadimos el año
        try:
            dia, mes = map(int, fecha_str.split('-'))
            fecha_completa = datetime.date(anio, mes, dia)
            # Solo añadir si no existe ya (prioridad a manual si nombre coincide, 
            # pero aquí simples añadimos a la lista, el LLM sabrá distinguir)
            lista_festivos.append(f"- {nombre}: {fecha_completa.strftime('%d-%m-%Y')}")
        except ValueError:
            continue
            
    # Formatear salida
    texto_contexto = (
        f"REFERENCIA OFICIAL DE FESTIVIDADES AÑO {anio}:\n"
        + "\n".join(lista_festivos)
        + "\n(Usa estas fechas exactas si la noticia menciona alguna de estas celebraciones)"
    )
    
    return texto_contexto
