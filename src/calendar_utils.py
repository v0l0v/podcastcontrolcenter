
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

    # 2. Inicializar lista y cargar config manual
    lista_festivos = []
    custom_festivities = CONFIG.get('festividades', {})

    # Procesar librería holidays
    for date, name in sorted(es_holidays.items()):
        lista_festivos.append(f"- {name}: {date.strftime('%d-%m-%Y')}")

    # 3. Cargar datos extendidos del JSON
    ruta_json = os.path.join(os.path.dirname(__file__), 'data', 'efemerides_clm.json')
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

    # Procesar efemérides históricas (Solo si el mes coincide con la fecha actual aprox? 
    # NO, el prompt necesita contexto del año. Pero para no saturar, pondremos TODO 
    # y que el LLM decida. O mejor, si la lista es muy larga, solo las del mes actual?
    # El usuario pidió "que no alucine fechas", así que es mejor darle las referencias.
    # Vamos a incluir TODO pero con formato claro.
    
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

def obtener_efemerides_hoy(fecha_dt: datetime.datetime = None) -> str:
    """
    Busca si en la fecha actual (o la dada) hay alguna efeméride o fiesta
    registrada en efemerides_clm.json.
    Devuelve un texto descriptivo o cadena vacía.
    """
    if fecha_dt is None:
        fecha_dt = datetime.datetime.now()
        
    dia_mes = fecha_dt.strftime("%d-%m") # "19-01"
    
    ruta_json = os.path.join(os.path.dirname(__file__), 'data', 'efemerides_clm.json')
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
                    
        except Exception as e:
            print(f"Error leyendo efemérides hoy: {e}")
            
    if not coincidencias:
        return ""
        
    return "\n".join(coincidencias)
