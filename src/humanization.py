import random
import csv
import datetime
import os

# Ruta al CSV de pueblos
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'pueblos_clm.csv')

def load_pueblos_data():
    """Carga los pueblos del CSV."""
    pueblos = []
    try:
        if not os.path.exists(CSV_PATH):
            return []
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pueblos.append(row)
    except Exception as e:
        print(f"Error cargando CSV: {e}")
    return pueblos

def seleccionar_pueblo_diario():
    """
    Selecciona un pueblo basado en rotación semanal de provincias.
    Lunes a Viernes cubre las 5 provincias en orden aleatorio (determinado por semana).
    """
    pueblos = load_pueblos_data()
    if not pueblos:
        return None
        
    provincias = ["Albacete", "Ciudad Real", "Cuenca", "Guadalajara", "Toledo"]
    
    # Determinismo semanal: Usamos la semana del año como semilla
    hoy = datetime.datetime.now()
    semana_iso = hoy.isocalendar()[1]
    
    # Semillamos el random solo para barajar provincias
    rng = random.Random(semana_iso)
    rng.shuffle(provincias)
    
    # Día de la semana (0=Lunes, 4=Viernes)
    dia_semana = hoy.weekday()
    
    # Si es finde (5, 6), elegimos una provincia al azar no deterministicamente
    if dia_semana > 4:
        provincia_toca = random.choice(provincias)
    else:
        provincia_toca = provincias[dia_semana]
        
    # Filtrar pueblos de esa provincia
    candidatos = [p for p in pueblos if p['Provincia'].strip() == provincia_toca]
    
    if not candidatos:
        return random.choice(pueblos) # Fallback
        
    return random.choice(candidatos)

def humanizar_poblacion(dato):
    try:
        p = int(dato)
        if p < 100: return "una aldea íntima y tranquila"
        if p < 500: return "un pequeño pueblo con encanto"
        if p < 2000: return "una villa muy viva"
        if p < 10000: return "un pueblo grande lleno de actividad"
        if p < 50000: return "una ciudad importante"
        return "una gran capital"
    except:
        return "una población"

def humanizar_altitud(dato):
    try:
        a = int(dato)
        if a < 600: return "en tierras bajas y fértiles"
        if a < 800: return "en plena llanura manchega"
        if a < 1000: return "en zona alta"
        return "en lo alto de la sierra (aire puro)"
    except:
        return "en nuestra tierra"

def humanizar_superficie(dato):
    try:
        s = float(dato)
        if s < 50: return "término municipal recogidito"
        if s < 150: return "extensión normal"
        if s < 300: return "término municipal amplio"
        return "término municipal inmenso"
    except:
        return "superficie"

from src.weather_utils import obtener_meteo_para_provincia

def obtener_toque_humano(num_noticias: int, datos_meteo: dict = None) -> dict:
    """
    Selecciona una 'píldora' de humanización para el podcast.
    MODIFICACIÓN: El 'Bingo de Pueblos' es OBLIGATORIO.
    A veces (30%) se añade un segundo toque, incluyendo el 'Termómetro Manchego'.
    """
    
    instrucciones_finales = []

    # 1. BINGO DE PUEBLOS (Siempre)
    # Lógica de CSV y Rotación Semanal
    try:
        pueblo_elegido = seleccionar_pueblo_diario()
        if pueblo_elegido:
             nombre = pueblo_elegido.get("Municipio", "Pueblo Desconocido")
             provincia = pueblo_elegido.get("Provincia", "Castilla-La Mancha")
             
             # Generar contexto humanizado
             desc_poblacion = humanizar_poblacion(pueblo_elegido.get("Población", 0))
             desc_altitud = humanizar_altitud(pueblo_elegido.get("Altitud (m s.n.m.)", 0))
             desc_superficie = humanizar_superficie(pueblo_elegido.get("Superficie (km²)", 0))
             
             # NUEVO: Obtener clima ESPECÍFICO de la provincia/zona para el Bingo
             # "Adapta el clima mas cercano a la poblacion seleccionado"
             datos_clima_local = obtener_meteo_para_provincia(provincia)
             frase_clima_local = ""
             
             if datos_clima_local:
                 temp_local = datos_clima_local.get('media_temp', 15)
                 
                 # Lógica termómetro manchego aplicada LOCALMENTE al saludo
                 if temp_local <= 4:
                     frase_clima_local = f"donde hoy hace un frío que pela ({temp_local:.1f}C), así que abríguense bien"
                 elif temp_local >= 35:
                     frase_clima_local = f"donde hoy cae una solana importante ({temp_local:.1f}C), busquen la sombra"
                 else:
                     frase_clima_local = f"donde hoy tienen un día estupendo ({temp_local:.1f}C)"

             instrucciones_finales.append(
                f"- **DINÁMICA 'BINGO DE PUEBLOS' (OBLIGATORIO):** Hoy el saludo viaja a la provincia de **{provincia}**.\n"
                f"  - Destino: **{nombre}**.\n"
                f"  - Contexto Humanizado: \n"
                f"    * Población: Es {desc_poblacion}.\n"
                f"    * Entorno: Situado {desc_altitud}.\n"
                f"    * Clima HOY allí: {frase_clima_local}.\n"
                f"  - **INSTRUCCIÓN:** Manda un saludo cariñoso a {nombre}. Integra el dato del clima DE FORMA INVISIBLE "
                f"(ej: 'espero que estéis disfrutando de ese fresco', 'cuidado con el calor'). NO DIGAS la temperatura exacta."
             )
        else:
             # Fallback
             pueblos_backup = ["Molinicos", "Belmonte", "Sigüenza", "Almagro", "Consuegra"]
             pueblo = random.choice(pueblos_backup)
             instrucciones_finales.append(
                f"- **DINÁMICA 'BINGO DE PUEBLOS' (BACKUP):** Saluda a **{pueblo}**."
             )
    except Exception as e:
        print(f"Error en Bingo de Pueblos: {e}")
        instrucciones_finales.append("- **DINÁMICA 'BINGO DE PUEBLOS':** Saluda a un pueblo de La Mancha al azar.")

    # 2. TERMÓMETRO MANCHEGO (Alta prioridad si hay temperatura extrema)
    # Se evalúa antes del sorteo aleatorio general porque depende del dato real.
    if datos_meteo and "media_temp" in datos_meteo:
        temp = datos_meteo["media_temp"]
        frase_meteo = ""
        
        if temp <= 2:
            frases_frio = [
                "Madre mía, qué rasca hace hoy, no se os ocurra salir sin la rebeca (y el abrigo gordo).",
                "Hoy hace un frío que pela, de los que se te quedan los sabañones.",
                "Vaya día de perros, ideal para quedarse al brasero y no asomar la nariz."
            ]
            frase_meteo = random.choice(frases_frio)
            
        elif temp >= 38:
             frases_calor = [
                "Vaya chicharrera que está cayendo en la llanura, buscad la sombra como oro en paño.",
                "Hoy no se puede estar en la calle, que te derrites como un helado al sol.",
                "Menudo bochorno, hoy es día de persiana bajada y abanico en mano."
             ]
             frase_meteo = random.choice(frases_calor)
             
        if frase_meteo:
            # Si hay clima extremo, lo añadimos con alta probabilidad (70%)
            if random.random() < 0.7:
                instrucciones_finales.append(
                    f"- **TERMÓMETRO MANCHEGO (REAL: {temp:.1f}ºC):** "
                    f"Comenta el tiempo usando esta expresión local: '{frase_meteo}'."
                )

    # 3. OTROS TOQUES (Opcional 30%, si no se ha llenado ya mucho con el clima)
    # Si ya hemos metido clima extremo, bajamos la probabilidad de otro extra para no saturar.
    prob_extra = 0.15 if len(instrucciones_finales) > 1 else 0.30
    
    if random.random() < prob_extra:
        opciones_extra = [
            "vida_ia",
            "mensaje_productor",
            "estadistica_absurda",
            "refran_inventado"
        ]
        # Pesos para el extra
        pesos_extra = [0.30, 0.20, 0.25, 0.25]
        eleccion_extra = random.choices(opciones_extra, weights=pesos_extra, k=1)[0]
        
        instruccion_extra = ""
        
        if eleccion_extra == "vida_ia":
            frases = [
                "Comenta que hoy tu procesador va un poco lento y necesitas un café virtual bien cargado.",
                "Di que has estado soñando con ovejas eléctricas pastando en La Mancha.",
                "Bromea con que casi te quedas sin batería esperando tantas noticias interesantes.",
                "Di que te has levantado con el algoritmo un poco 'revuelto' hoy.",
                "Confiesa que a veces te gustaría probar el gazpacho real y no solo procesar su receta."
            ]
            instruccion_extra = (
                f"- **META-HUMOR IA (EXTRA):** Además del saludo, haz este comentario simpático: "
                f"'{random.choice(frases)}'. Hazlo con naturalidad."
            )

        elif eleccion_extra == "mensaje_productor":
            instruccion_extra = (
                "- **INTERACCIÓN CON EQUIPO (EXTRA):** Menciona a 'Víctor' (tu productor/técnico). "
                "Di algo como 'Víctor me chiva por el pinganillo que...' o 'El jefe me está haciendo señas'."
            )

        elif eleccion_extra == "estadistica_absurda":
            comparaciones = [
                "casi tantas como las veces que mi abuela me ofrece comida en un domingo",
                "más que tractores caben en la plaza del pueblo en fiestas",
                "casi tantas como las veces que se dice 'acho' en una hora en Albacete",
                "una lista más larga que un día sin pan",
                "tantas que casi se me funden los circuitos contándolas"
            ]
            comp = random.choice(comparaciones)
            instruccion_extra = (
                f"- **ESTADÍSTICA CASTIZA (EXTRA):** Hoy traemos {num_noticias} noticias. "
                f"Comenta que eso son {comp}."
            )

        elif eleccion_extra == "refran_inventado":
            refranes = [
                "Quien madruga, A Dios ayuda... pero quien escucha este podcast, se entera de todo.",
                "A falta de pan, buenas son noticias de nuestros pueblos.",
                "En abril aguas mil, y en este podcast historias mil.",
                "Más vale podcast en mano (o en oído), que ciento volando."
            ]
            instruccion_extra = (
                f"- **SABIDURÍA POPULAR 2.0 (EXTRA):** Suelta este refrán adaptado: '{random.choice(refranes)}'. "
                "Dilo con tono de sentencia popular."
            )
            
        if instruccion_extra:
            instrucciones_finales.append(instruccion_extra)

    return {"humanizacion_instruccion": "\n".join(instrucciones_finales)}
