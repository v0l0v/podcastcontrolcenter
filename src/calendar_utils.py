
import datetime
import holidays
import json
import os
import re
import csv
import random
from src.config.settings import CONFIG

# --- Ruta al CSV de Fiestas de Interés Turístico ---
FITR_CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'fitr.csv')

# --- Mapa de nombres de meses a números ---
_MESES_MAP = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}


def _calcular_pascua(anio: int) -> datetime.date:
    """Calcula el Domingo de Resurrección (algoritmo de Butcher/Meeus)."""
    a = anio % 19
    b = anio // 100
    c = anio % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(anio, mes, dia)


def _obtener_fechas_moviles(anio: int) -> dict:
    """
    Calcula las fechas de las fiestas móviles litúrgicas para un año dado.
    Devuelve un dict con nombre → (fecha_inicio, fecha_fin).
    """
    pascua = _calcular_pascua(anio)
    domingo_ramos = pascua - datetime.timedelta(days=7)
    miercoles_ceniza = pascua - datetime.timedelta(days=46)
    corpus_christi = pascua + datetime.timedelta(days=60)
    pentecostes = pascua + datetime.timedelta(days=49)
    lunes_pentecostes = pentecostes + datetime.timedelta(days=1)
    
    # Martes de carnaval = día anterior al miércoles de ceniza
    martes_carnaval = miercoles_ceniza - datetime.timedelta(days=1)
    # Viernes Santo
    viernes_santo = pascua - datetime.timedelta(days=2)
    # Sábado Santo / Sábado de Gloria
    sabado_santo = pascua - datetime.timedelta(days=1)
    
    return {
        "semana_santa": (domingo_ramos, pascua),
        "domingo_ramos": (domingo_ramos, domingo_ramos),
        "viernes_santo": (viernes_santo, viernes_santo),
        "sabado_santo": (sabado_santo, sabado_santo),
        "sabado_gloria": (sabado_santo, sabado_santo),
        "domingo_resurreccion": (pascua, pascua),
        "corpus_christi": (corpus_christi, corpus_christi),
        "corpus": (corpus_christi, corpus_christi),
        "pentecostes": (pentecostes, pentecostes),
        "lunes_pentecostes": (lunes_pentecostes, lunes_pentecostes),
        "carnaval": (martes_carnaval - datetime.timedelta(days=4), martes_carnaval),
        "martes_carnaval": (martes_carnaval, martes_carnaval),
        "miercoles_ceniza": (miercoles_ceniza, miercoles_ceniza),
        "navidad": (datetime.date(anio, 12, 24), datetime.date(anio, 12, 26)),
    }


def _parsear_fecha_fiesta(texto_fecha: str, observaciones: str, anio: int) -> list:
    """
    Parsea una fecha heterogénea del CSV y devuelve una lista de tuplas (inicio, fin).
    Puede devolver [] si no se puede parsear o es imposible resolverla.
    """
    texto = texto_fecha.strip().lower()
    obs = observaciones.strip().lower() if observaciones else ""
    
    fechas_moviles = _obtener_fechas_moviles(anio)
    
    # --- CASO 1: Fecha variable (fiestas litúrgicas) ---
    if "fecha variable" in texto or texto in ("navidad",):
        texto_completo = texto + " " + obs
        
        # Prioridad 1: Si menciona "Domingo de Ramos" Y "Resurrección" → rango completo
        if "domingo de ramos" in texto_completo and "resurrección" in texto_completo:
            return [fechas_moviles["semana_santa"]]
        
        # Prioridad 2: Resolver por palabras clave (orden importa: más específicas primero)
        claves_moviles = [
            ("lunes de pentecostés", "lunes_pentecostes"),
            ("domingo de ramos", "domingo_ramos"),
            ("viernes santo", "viernes_santo"),
            ("sábado santo", "sabado_santo"),
            ("sábado de gloria", "sabado_gloria"),
            ("domingo de resurrección", "domingo_resurreccion"),
            ("corpus christi", "corpus_christi"),
            ("pentecostés", "pentecostes"),
            ("pentescostés", "pentecostes"),
            ("miércoles de ceniza", "miercoles_ceniza"),
            ("martes de carnaval", "martes_carnaval"),
            ("semana santa", "semana_santa"),
            ("corpus", "corpus"),
            ("carnaval", "carnaval"),
        ]
        
        for clave, key in claves_moviles:
            if clave in texto_completo:
                return [fechas_moviles[key]]
        
        # Si solo dice "fecha variable" sin más → no podemos resolverlo
        return []
    
    # Caso especial: solo un mes ("agosto", "febrero", "septiembre")
    if texto in _MESES_MAP:
        mes = _MESES_MAP[texto]
        return [(datetime.date(anio, mes, 1), datetime.date(anio, mes, 28))]
    
    # --- CASO 2: Rangos (evaluar ANTES de fecha simple para evitar falsos positivos) ---
    
    # Patrón: "30 de abril-6 de mayo" (rango entre 2 meses con guión)
    match_rango_2meses = re.match(
        r'(\d{1,2})\s+de\s+(\w+)\s*[-–]\s*(\d{1,2})\s+de\s+(\w+)', texto
    )
    if match_rango_2meses:
        d1 = int(match_rango_2meses.group(1))
        m1 = _MESES_MAP.get(match_rango_2meses.group(2))
        d2 = int(match_rango_2meses.group(3))
        m2 = _MESES_MAP.get(match_rango_2meses.group(4))
        if m1 and m2:
            try:
                return [(datetime.date(anio, m1, d1), datetime.date(anio, m2, d2))]
            except ValueError:
                pass
    
    # Patrón: "31 de agosto al 3 de septiembre" (rango entre 2 meses con "al")
    match_rango_al = re.match(
        r'(\d{1,2})\s+de\s+(\w+)\s+al\s+(\d{1,2})\s+de\s+(\w+)', texto
    )
    if match_rango_al:
        d1 = int(match_rango_al.group(1))
        m1 = _MESES_MAP.get(match_rango_al.group(2))
        d2 = int(match_rango_al.group(3))
        m2 = _MESES_MAP.get(match_rango_al.group(4))
        if m1 and m2:
            try:
                return [(datetime.date(anio, m1, d1), datetime.date(anio, m2, d2))]
            except ValueError:
                pass
    
    # Patrón: "del DD al DD de mes" o "del DD al DD mes"
    match_del_al = re.match(r'del\s+(\d{1,2})\s+al\s+(\d{1,2})\s+(?:de\s+)?(\w+)', texto)
    if match_del_al:
        d1 = int(match_del_al.group(1))
        d2 = int(match_del_al.group(2))
        mes_nombre = match_del_al.group(3)
        mes = _MESES_MAP.get(mes_nombre)
        if mes:
            try:
                return [(datetime.date(anio, mes, d1), datetime.date(anio, mes, d2))]
            except ValueError:
                pass
    
    # Patrón: "7-17 de septiembre" (rango dentro del mismo mes)
    match_rango = re.match(r'(\d{1,2})\s*[-–]\s*(\d{1,2})\s+de\s+(\w+)', texto)
    if match_rango:
        d1 = int(match_rango.group(1))
        d2 = int(match_rango.group(2))
        mes_nombre = match_rango.group(3)
        mes = _MESES_MAP.get(mes_nombre)
        if mes:
            try:
                return [(datetime.date(anio, mes, d1), datetime.date(anio, mes, d2))]
            except ValueError:
                pass
    
    # --- CASO 3: Fecha fija simple "DD de mes" (después de los rangos) ---
    match_simple = re.match(r'(\d{1,2})\s+de\s+(\w+)', texto)
    if match_simple:
        dia = int(match_simple.group(1))
        mes_nombre = match_simple.group(2)
        mes = _MESES_MAP.get(mes_nombre)
        if mes:
            try:
                return [(datetime.date(anio, mes, dia), datetime.date(anio, mes, dia))]
            except ValueError:
                pass
    
    # --- CASO 4: Fechas relativas con semana/fin de semana ---
    # "Primer/Segundo/Tercer/Último fin de semana/domingo de MES"
    ordinal_map = {
        "primer": 1, "primera": 1, "1er": 1, "1º": 1,
        "segundo": 2, "segunda": 2, "2º": 2, "2ª": 2,
        "tercer": 3, "tercera": 3, "3er": 3, "3º": 3,
        "cuarto": 4, "cuarta": 4, "4º": 4,
        "último": -1, "última": -1,
    }
    
    match_ordinal = re.match(
        r'(primer[ao]?|1er|1º|segund[ao]|2[ºª]|tercer[ao]?|3er|3º|cuart[ao]|4º|últim[ao])\s+'
        r'(fin de semana|domingo|sábado|lunes)\s+de\s+(\w+)',
        texto
    )
    if match_ordinal:
        ordinal_str = match_ordinal.group(1)
        tipo_dia = match_ordinal.group(2)
        mes_nombre = match_ordinal.group(3)
        
        ordinal = ordinal_map.get(ordinal_str, 0)
        mes = _MESES_MAP.get(mes_nombre)
        
        if ordinal and mes:
            # Mapear tipo de día a weekday
            dia_semana_map = {"domingo": 6, "sábado": 5, "lunes": 0, "fin de semana": 5}
            target_weekday = dia_semana_map.get(tipo_dia, 5)
            
            if ordinal == -1:  # Último
                # Ir hacia atrás desde el último día del mes
                if mes == 12:
                    ultimo_dia = datetime.date(anio, 12, 31)
                else:
                    ultimo_dia = datetime.date(anio, mes + 1, 1) - datetime.timedelta(days=1)
                
                d = ultimo_dia
                while d.weekday() != target_weekday:
                    d -= datetime.timedelta(days=1)
                
                if tipo_dia == "fin de semana":
                    return [(d, d + datetime.timedelta(days=1))]
                return [(d, d)]
            else:
                # N-ésimo día del tipo en ese mes
                count = 0
                d = datetime.date(anio, mes, 1)
                while d.month == mes:
                    if d.weekday() == target_weekday:
                        count += 1
                        if count == ordinal:
                            if tipo_dia == "fin de semana":
                                return [(d, d + datetime.timedelta(days=1))]
                            return [(d, d)]
                    d += datetime.timedelta(days=1)
    
    # --- CASO 5: "mediados de MES", "primera semana de MES" ---
    match_mediados = re.search(r'mediados\s+de\s+(\w+)', texto)
    if match_mediados:
        mes = _MESES_MAP.get(match_mediados.group(1))
        if mes:
            return [(datetime.date(anio, mes, 10), datetime.date(anio, mes, 20))]
    
    match_primera_semana = re.search(r'primera\s+semana\s+de\s+(\w+)', texto)
    if match_primera_semana:
        mes = _MESES_MAP.get(match_primera_semana.group(1))
        if mes:
            return [(datetime.date(anio, mes, 1), datetime.date(anio, mes, 7))]

    # --- CASO 6: "1,2,3 de mes" (lista de días) ---
    match_lista = re.match(r'([\d,\s]+)\s+de\s+(\w+)', texto)
    if match_lista:
        dias_str = match_lista.group(1)
        mes_nombre = match_lista.group(2)
        mes = _MESES_MAP.get(mes_nombre)
        if mes:
            dias = [int(d.strip()) for d in dias_str.split(',') if d.strip().isdigit()]
            if dias:
                try:
                    return [(datetime.date(anio, mes, min(dias)), datetime.date(anio, mes, max(dias)))]
                except ValueError:
                    pass
    
    # No pudimos parsear
    return []


def _cargar_fiestas_csv() -> list:
    """Carga y parsea el CSV de Fiestas de Interés Turístico."""
    if not os.path.exists(FITR_CSV_PATH):
        return []
    
    fiestas = []
    try:
        with open(FITR_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nombre = row.get('DENOMINACIÓN', '').strip()
                localidad = row.get('LOCALIDAD', '').strip()
                provincia = row.get('PROVINCIA', '').strip()
                fecha_texto = row.get('FECHA DE CELEBRACIÓN DE LA FIESTA ', '').strip()
                observaciones = row.get('OBSERVACIONES', '').strip()
                
                if not nombre:
                    continue
                
                fiestas.append({
                    "nombre": nombre,
                    "localidad": localidad,
                    "provincia": provincia,
                    "fecha_texto": fecha_texto,
                    "observaciones": observaciones
                })
    except Exception as e:
        print(f"Error cargando CSV de fiestas: {e}")
    
    return fiestas


def obtener_fiestas_cercanas(fecha_dt: datetime.datetime = None, margen_dias: int = 5) -> str:
    """
    Busca fiestas de interés turístico cercanas a la fecha actual.
    Devuelve un texto para inyectar en el prompt o cadena vacía.
    
    - Si hay fiestas EN CURSO hoy → las anuncia como actuales.
    - Si hay fiestas en los próximos `margen_dias` días → las anuncia como próximas.
    """
    if fecha_dt is None:
        fecha_dt = datetime.datetime.now()
    
    hoy = fecha_dt.date() if isinstance(fecha_dt, datetime.datetime) else fecha_dt
    anio = hoy.year
    limite = hoy + datetime.timedelta(days=margen_dias)
    
    fiestas_csv = _cargar_fiestas_csv()
    
    en_curso = []
    proximas = []
    
    for fiesta in fiestas_csv:
        rangos = _parsear_fecha_fiesta(fiesta['fecha_texto'], fiesta['observaciones'], anio)
        
        for inicio, fin in rangos:
            if inicio <= hoy <= fin:
                # Fiesta EN CURSO
                en_curso.append(fiesta)
                break
            elif hoy < inicio <= limite:
                # Fiesta PRÓXIMA
                dias_faltan = (inicio - hoy).days
                fiesta_copy = fiesta.copy()
                fiesta_copy['_dias_faltan'] = dias_faltan
                fiesta_copy['_fecha_inicio'] = inicio.strftime("%d de %B").lstrip("0")
                proximas.append(fiesta_copy)
                break
    
    if not en_curso and not proximas:
        return ""
    
    bloques = []
    
    if en_curso:
        textos = []
        for f in en_curso[:3]:  # Max 3 para no saturar
            textos.append(
                f'  - "{f["nombre"]}" en {f["localidad"]} ({f["provincia"]}). '
                f'Fechas: {f["fecha_texto"]}.'
            )
        bloques.append(
            "🎉 FIESTAS DE INTERÉS TURÍSTICO EN CURSO HOY:\n" + "\n".join(textos)
        )
    
    if proximas:
        # Ordenar por cercanía
        proximas.sort(key=lambda x: x['_dias_faltan'])
        textos = []
        for f in proximas[:3]:  # Max 3
            textos.append(
                f'  - "{f["nombre"]}" en {f["localidad"]} ({f["provincia"]}) '
                f'— en {f["_dias_faltan"]} día{"s" if f["_dias_faltan"] > 1 else ""}.'
            )
        bloques.append(
            "📅 FIESTAS DE INTERÉS TURÍSTICO PRÓXIMAS:\n" + "\n".join(textos) +
            "\n  (Puedes mencionarlas brevemente si encaja con el tono.)"
        )
    
    return "\n".join(bloques)


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
    
    # 6. Buscar Fiestas de Interés Turístico cercanas (CSV)
    try:
        fiestas_cercanas = obtener_fiestas_cercanas(fecha_dt)
        if fiestas_cercanas:
            coincidencias.append(fiestas_cercanas)
    except Exception as e:
        print(f"Error buscando fiestas de interés turístico: {e}")
            
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
