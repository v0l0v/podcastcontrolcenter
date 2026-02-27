import datetime
import holidays
import json
import os
import re
import random
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

    # 2. Inicializar lista y cargar config manual
    lista_festivos = []
    custom_festivities = CONFIG.get('festividades', {})

    # Procesar librería holidays
    for date, name in sorted(es_holidays.items()):
        lista_festivos.append(f"- {name}: {date.strftime('%d-%m-%Y')}")

    # 3. Cargar datos extendidos del JSON
    # La carpeta data está al mismo nivel que src
    ruta_json = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'efemerides_clm.json')
    datos_extra = {}
    if os.path.exists(ruta_json):
        try:
            with open(ruta_json, 'r', encoding='utf-8') as f:
                datos_extra = json.load(f)
        except Exception as e:
            print(f"Error cargando efemérides: {e}")

    # Procesar festivos fijos del JSON (si no están ya en holidays)
    for fecha_str, nombre in datos_extra.get('festivos_fijos', {}).items():
         lista_festivos.append(f"- {nombre} (Festivo): {fecha_str}-{anio}")

    # Efemérides Históricas
    if 'efemerides_historicas' in datos_extra:
        for fecha_dia_mes, descripcion in datos_extra['efemerides_historicas'].items():
            lista_festivos.append(f"- EFEMÉRIDE {fecha_dia_mes}: {descripcion}")

    # Fiestas Provinciales (Aplanamos para dar contexto general)
    if 'fiestas_por_provincia' in datos_extra:
        for provincia, fiestas in datos_extra['fiestas_por_provincia'].items():
            for fecha_dia_mes, nombre in fiestas.items():
                lista_festivos.append(f"- {nombre} ({provincia}): {fecha_dia_mes}-{anio}")
            
    # Procesar manuales de config (override final)
    for nombre, fecha_str in custom_festivities.items():
        try:
            dia, mes = map(int, fecha_str.split('-'))
            fecha_completa = datetime.date(anio, mes, dia)
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

def obtener_efemerides_hoy(fecha_dt: datetime.datetime = None) -> str:
    """
    Busca si en la fecha actual (o la dada) hay alguna efeméride, fiesta
    o evento cercano registrado en las fuentes de datos.
    Devuelve un texto descriptivo o cadena vacía.
    """
    if fecha_dt is None:
        fecha_dt = datetime.datetime.now()
        
    dia_mes = fecha_dt.strftime("%d-%m") # "19-01"
    
    # La carpeta data está al mismo nivel que src
    ruta_json = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'efemerides_clm.json')
    coincidencias = []
    
    if os.path.exists(ruta_json):
        try:
            with open(ruta_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 1. Buscar en Festivos Fijos
            if dia_mes in data.get('festivos_fijos', {}):
                coincidencias.append(f"FESTIVO: {data['festivos_fijos'][dia_mes]}")
                
            # 2. Buscar en Efemérides Históricas
            if dia_mes in data.get('efemerides_historicas', {}):
                coincidencias.append(f"EFEMÉRIDE HISTÓRICA: {data['efemerides_historicas'][dia_mes]}")
                
            # 3. Buscar en Fiestas Provinciales
            provinciales = data.get('fiestas_por_provincia', {})
            for prov, fiestas in provinciales.items():
                if dia_mes in fiestas:
                    coincidencias.append(f"FIESTA EN {prov.upper()}: {fiestas[dia_mes]}")
            
            # 4. Buscar Santoral
            if dia_mes in data.get('santoral_destacado', {}):
                coincidencias.append(f"SANTORAL: {data['santoral_destacado'][dia_mes]}")

            # 5. Refranero (Random del mes)
            mes_str = fecha_dt.strftime("%m")
            refranes = data.get('refranero_mensual', {}).get(mes_str, [])
            if refranes:
                refran = random.choice(refranes)
                coincidencias.append(f"REFRÁN DEL MES ({mes_str}): {refran}")
                    
        except Exception as e:
            print(f"Error leyendo efemérides hoy: {e}")
            
    if not coincidencias:
        return ""
        
    return "\n".join(coincidencias)

def obtener_fecha_humanizada_es(fecha_dt: datetime.datetime = None) -> str:
    """
    Devuelve la fecha en formato español.
    A veces incluye el día de la semana para dar variedad.
    Ejemplo: 'jueves, 13 de febrero' o '13 de febrero'
    """
    if fecha_dt is None:
        fecha_dt = datetime.datetime.now()
    
    meses = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
        7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    
    dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    
    dia_str = f"{fecha_dt.day} de {meses[fecha_dt.month]}"
    
    if random.choice([True, False]):
        nombre_dia = dias_semana[fecha_dt.weekday()]
        return f"{nombre_dia}, {dia_str}"
    
    return dia_str
