# dorototal.py - Refactorizado a Arquitectura Modular

import gc
import io
import os
import re
import random
import html
import json
import time
import sys
import hashlib
import glob
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
from pydub import AudioSegment
import feedparser
from dateutil import parser as date_parser

# --- IMPORTACIONES MODULARES ---
from src.config.settings import (
    CONFIG, AUDIO_CONFIG, GEN_CONFIG, VOICE_TARGET_PEAK_DBFS, TARGET_LUFS, 
    SAMPLE_RATE, BITRATE, SILENCE_THRESHOLD_DBFS, VOICE_NAME, LANGUAGE_CODE,
    DEDUP_SIMILARITY_THRESHOLD, NGRAM_N, KEYPHRASE_MIN_COUNT, MIN_NEWS_PER_BLOCK, 
    MAX_DYNAMIC_KEYPHRASES, MIN_WORDS_FOR_AUDIO, AUDIENCE_QUESTIONS_FILE, 
    AUDIO_CACHE_DIR, SPANISH_STOPWORDS, AUDIO_ASSETS_DIR, CTA_TEXTS_DIR
)
from src.core.text_processing import (
    strip_accents, reparar_codificacion, normalize_text_for_similarity, tokens, 
    ngrams, jaccard_ngrams, composite_similarity, stable_text_hash, 
    roman_to_int, numero_a_ordinal_espanol, detectar_contexto_ordinal, 
    detectar_genero_contexto, preprocesar_texto_para_tts, corregir_palabras_deletreadas_tts,
    corregir_numeros_con_puntos_tts, limpiar_artefactos_ia, preprocesar_texto_para_fechas,
    reemplazar_urls_por_mencion, convertir_ssml_a_texto_plano, limpiar_markdown_audio, 
    limpiar_html, extract_candidate_phrases, extract_ngrams_keyphrases, match_stem
)
from src.core.geography import obtener_provincia, obtener_info_gal
from src.engine.audio import masterizar_a_lufs, sintetizar_ssml_a_audio
from src.web_scraper import extract_first_external_link, fetch_article_text, extract_image_url, download_image_as_bytes
from src.llm_utils import generar_texto_con_gemini, retry_on_failure, generar_texto_multimodal_con_gemini, generar_texto_multimodal_audio_con_gemini
from src.calendar_utils import obtener_festividades_contexto, obtener_efemerides_hoy
from src.weather_utils import obtener_pronostico_meteo
from src.sports_utils import obtener_resultados_futbol
import mcmcn_prompts 

# --- CONFIGURACIÓN Y CLIENTES ---
# Los clientes se manejan en los módulos (src.engine.audio, src.llm_utils).
# Translate client se eliminó por desuso.
# Vertex AI se inicializa en src.llm_utils.



@retry_on_failure(retries=2, delay=2)
def extraer_localidad_con_ia(texto_noticia: str) -> str:
    """Usa la IA para extraer la localidad principal de un texto."""
    if not texto_noticia:
        return "Castilla la Mancha"
    
    prompt = f"""
    Analiza el siguiente texto de una noticia y devuelve ÚNICAMENTE el nombre de la localidad principal (pueblo o ciudad) mencionada.
    - Si se mencionan varias, devuelve la más relevante para la noticia.
    - No incluyas la provincia. Solo el nombre del municipio.
    - Si no puedes identificar una localidad clara, responde 'Desconocida'.

    EJEMPLOS DE RESPUESTA:
    - Hellín
    - Villanueva de los Infantes
    - Desconocida

    TEXTO:
    ---
    {texto_noticia}
    ---
    
    LOCALIDAD:
    """
    localidad = generar_texto_con_gemini(prompt).strip()
    # Pequeña limpieza por si la IA añade comillas
    localidad = localidad.replace('"', '').replace("'", "")
    
    print(f"      🌍 Localidad extraída por IA: {localidad}")
    return localidad if localidad else "Desconocida"

def es_noticia_valida(texto: str) -> bool:
    if len(texto.split()) < 16:
        print(f"      🕵️‍♂️ Ignorando por ser demasiado corto (menos de 16 palabras).")
        return False
    prompt = mcmcn_prompts.PromptsAnalisis.clasificacion_noticia(texto=texto)
    respuesta = generar_texto_con_gemini(prompt)
    if not respuesta:
        return False
    print(f"      🕵️‍♂️ IA ha clasificado el texto '{texto[:70].strip()}...' como: {respuesta.upper()}")
    return respuesta.upper() == 'INFORMATIVO'

def resumir_noticia_con_google(texto: str, idioma_destino: str, fuente_original: str = "") -> str:
    # Intentar extraer localidad para enriquecer contexto
    localidad = extraer_localidad_con_ia(texto)
    gal_info = obtener_info_gal(localidad, fuente_original)
    
    contexto_extra = ""
    if localidad and localidad != "Desconocida":
        contexto_extra = f"Localidad: {localidad}."
        if gal_info:
            contexto_extra += f" Zona/Comarca: {gal_info}."
    
    # Inyectamos este contexto al principio del texto para que el modelo lo tenga en cuenta
    texto_con_contexto = f"[{contexto_extra}] {texto}" if contexto_extra else texto

    prompt = mcmcn_prompts.PromptsAnalisis.resumen_noticia(
        texto=texto_con_contexto,
        idioma_destino=idioma_destino,
        fuente_original=fuente_original,
        contexto_calendario=obtener_festividades_contexto()
    )
    return generar_texto_con_gemini(prompt)

def leer_pregunta_del_dia() -> Dict[str, str] | None:
    """
    Lee los mensajes de la audiencia y devuelve solo el que corresponde al día actual.
    Formato esperado por mensaje:
    fecha: DD-MM-YYYY
    autor: Nombre del Oyente
    texto: Mensaje del oyente...
    """
    if not os.path.exists(AUDIENCE_QUESTIONS_FILE):
        print(f"      ℹ️ No se encontró el archivo '{AUDIENCE_QUESTIONS_FILE}'. Se omitirá la sección de audiencia.")
        return None

    try:
        with open(AUDIENCE_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            bloques = f.read().split('---')
        
        fecha_hoy = datetime.now().date()

        for bloque in bloques:
            if not bloque.strip():
                continue

            mensaje = {}
            for linea in bloque.strip().split('\n'):
                if ':' in linea:
                    clave, valor = linea.split(':', 1)
                    mensaje[clave.strip().lower()] = valor.strip()
            
            if 'fecha' in mensaje:
                try:
                    fecha_mensaje = datetime.strptime(mensaje['fecha'], '%d-%m-%Y').date()
                    if fecha_mensaje == fecha_hoy:
                        if 'autor' in mensaje and 'texto' in mensaje:
                            print(f"      ✅ Mensaje de la audiencia encontrado para hoy ({fecha_hoy.strftime('%d-%m-%Y')}) de '{mensaje['autor']}'.")
                            return {'autor': mensaje['autor'], 'texto': mensaje['texto']}
                except ValueError:
                    print(f"      ⚠️ Fecha en formato incorrecto en el bloque: {mensaje.get('fecha')}. Se ignora.")
                    continue
        
        print(f"      ℹ️ No se encontró ningún mensaje de la audiencia para la fecha de hoy ({fecha_hoy.strftime('%d-%m-%Y')}).")
        return None
        
    except Exception as e:
        print(f"      ❌ Error al leer el archivo de preguntas de la audiencia: {e}")
        return None

# =================================================================================
# GESTIÓN DE CACHE HÍBRIDO PARA OPTIMIZAR LLAMADAS A API
# =================================================================================

PROCESSED_NEWS_FILE = 'cache_noticias.json'
AUDIO_CACHE_DIR = 'audio_cache'
# AUDIENCE_QUESTIONS_FILE movido al inicio
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

def cargar_cache_noticias() -> Dict[str, Any]:
    if os.path.exists(PROCESSED_NEWS_FILE):
        try:
            with open(PROCESSED_NEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print("⚠️ Archivo de caché corrupto o no encontrado. Se creará uno nuevo.")
            return {}
    return {}

def guardar_cache_noticias(cache_completo: Dict[str, Any]):
    with open(PROCESSED_NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_completo, f, indent=4, ensure_ascii=False)
    print(f"✅ Caché de noticias actualizado. Total de noticias en caché: {len(cache_completo)}")

# =================================================================================
# AGRUPACIÓN Y DEDUP: NUEVAS FUNCIONES
# =================================================================================

def identificar_fuente_original(texto: str) -> str:
    print("      🔍 Identificando la fuente original con IA...")
    prompt = f"""
    Analiza el siguiente texto. Tu misión es identificar quién es la FUENTE ORIGINAL de la información.

    CONTEXTO:
    Este texto ha sido publicado por un Grupo de Desarrollo Rural (el "reposter"). 
    Buscamos saber si la noticia es PROPIA del grupo o si están citando a otra entidad (Ayuntamiento, Gobierno, Asociación, etc.).

    INSTRUCCIONES:
    1. Si el texto dice explícitamente "Compartimos noticia de...", "Según informa...", "Publicado por...", devuelve EL NOMBRE DE esa tercera entidad.
    2. Si el contenido habla como "Nosotros", "Nuestro pueblo", "Desde el Grupo...", entonces la fuente es el propio emisor (devuelve "PROPIA").
    3. Si no hay pistas claras, intenta inferir la institución responsable (ej: si habla de "El Ayuntamiento abre plazo...", la fuente es "Ayuntamiento").
    4. Si es imposible determinarlo, devuelve "Desconocida".

    TEXTO:
    ---
    {texto}
    ---

    RESPUESTA (Solo el nombre o "PROPIA" o "Desconocida"):"""
    respuesta = generar_texto_con_gemini(prompt)
    if respuesta and respuesta.strip() != "Desconocida":
        print(f"      ✅ Fuente original identificada: {respuesta.strip()}")
        return respuesta.strip()
    return ""

def calcular_similitud_texto(texto1: str, texto2: str) -> float:
    return composite_similarity(texto1, texto2)

def detectar_duplicados_y_similares(resumenes: list, umbral_similitud: float = DEDUP_SIMILARITY_THRESHOLD) -> list:
    print(f"\n🔍 Detectando duplicados (umbral comp.: {umbral_similitud:.2f})")
    noticias_unicas = []
    hashes_vistos = set()
    eliminados = 0

    for noticia in resumenes:
        resumen_actual = (noticia.get('resumen') or "").strip()
        if not resumen_actual:
            continue

        # ID estable por hash del texto normalizado
        h = stable_text_hash(resumen_actual)
        if h in hashes_vistos:
            eliminados += 1
            continue

        es_duplicado = False
        for existente in noticias_unicas:
            sim = calcular_similitud_texto(resumen_actual, existente.get('resumen', ''))
            if sim >= umbral_similitud:
                # combinar fuentes
                f1 = existente.get('fuente', '')
                f2 = noticia.get('fuente', '')
                if f2 and f2 not in f1:
                    existente['fuente'] = f"{f1} · {f2}" if f1 else f2
                # combinar fechas si no hay
                if 'fecha' not in existente and 'fecha' in noticia:
                    existente['fecha'] = noticia['fecha']
                es_duplicado = True
                eliminados += 1
                break

        if not es_duplicado:
            noticia_copia = noticia.copy()
            noticia_copia['id'] = h
            noticias_unicas.append(noticia_copia)
            hashes_vistos.add(h)

    print(f"    ✅ Eliminados {eliminados} duplicados. Quedan {len(noticias_unicas)} noticias únicas.")
    return noticias_unicas

# --------- EXTRACCIÓN DE ENTIDADES/KEYWORDS DINÁMICAS ---------

PROPER_NOUN_PHRASE_RE = re.compile(r'\b([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚñáéíóú\-]+(?:\s+de\s+|[\s\-])[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚñáéíóú\-]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚñáéíóú\-]+)*)\b')
QUOTED_PHRASE_RE = re.compile(r'“([^”]+)”|"([^"]+)"|\‘([^\’]+)\’|\’([^\’]+)\’')

def build_dynamic_key_index(resumenes: list):
    key_to_items = defaultdict(list)
    for item in resumenes:
        txt = item.get('resumen', '')
        keys = []
        keys += extract_candidate_phrases(txt)
        keys += extract_ngrams_keyphrases(txt, n=(2,3))
        # normaliza claves
        keys = [normalize_text_for_similarity(k) for k in keys]
        keys = [k for k in keys if len(k) > 3]
        for k in set(keys):  # set para no duplicar misma clave por noticia
            if k:
                key_to_items[k].append(item)
    # filtra por mínimo de apariciones
    key_to_items = {k:v for k,v in key_to_items.items() if len(v) >= KEYPHRASE_MIN_COUNT}
    # ordena por frecuencia
    sorted_keys = sorted(key_to_items.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    return sorted_keys[:MAX_DYNAMIC_KEYPHRASES]

def cluster_by_dynamic_keyphrases(resumenes: list) -> dict:
    """Devuelve bloques por claves dinámicas + noticias individuales restantes."""
    keys = build_dynamic_key_index(resumenes)
    used_ids = set()
    bloques = []
    for key, items in keys:
        bundle = []
        for it in items:
            if it.get('id') not in used_ids:
                bundle.append(it)
        if len(bundle) >= MIN_NEWS_PER_BLOCK:
            # marca usados
            for it in bundle:
                used_ids.add(it.get('id'))
            bloques.append({
                'tema': f'clave:{key}',
                'descripcion_tema': key,
                'transicion_elegante': f"En torno a «{key}», varias noticias coinciden",
                'noticias': bundle
            })
    # restantes
    restantes = [it for it in resumenes if it.get('id') not in used_ids]
    return {'bloques_tematicos': bloques, 'noticias_individuales': restantes}

# --------- FALLBACK DETERMINISTA POR PALABRAS CLAVE (AMPLIADO) ---------

STEM_GROUPS = {
    'jovenes_rural': [
        'joven','juvent','raiz','formacion','emple','emprend','talent'
    ],
    'deportes': [
        'cicl','futbol','deport','compet','torne','atlet','carrer','baloncest','nataci'
    ],
    'cultura_eventos': [
        'festival','fiest','cultur','event','celebr','tradic','music','teatr','exposic','conciert','feri'
    ],
    'astronomia': [
        'perseid','estrella','astronom','observ','cielo','meteor'
    ],
    'agricultura': [
        'agric','agricol','campo','cultiv','cosech','ganad','agro'
    ],
    'turismo': [
        'turism','turist','visit','ruta','patrimoni','monument','itinerar','sender'
    ],
    'naturaleza_escapadas': [
        'natural','rio','paisaj','valle','escap','recorr','parque','reserva','entorno'
    ]
}


def agrupacion_simple_por_palabras_clave(resumenes: list) -> dict:
    print("\n🎯 Ejecutando agrupación simple por palabras clave (stems)...")
    grupos_detectados = defaultdict(list)
    sin_grupo = []
    for noticia in resumenes:
        resumen_norm = normalize_text_for_similarity(noticia.get('resumen',''))
        asignada = False
        for tema, stems in STEM_GROUPS.items():
            if match_stem(resumen_norm, stems):
                grupos_detectados[tema].append(noticia)
                asignada = True
                break
        if not asignada:
            sin_grupo.append(noticia)

    bloques = []
    tema_desc = {
        'jovenes_rural': 'iniciativas para jóvenes rurales',
        'deportes': 'competiciones y eventos deportivos',
        'cultura_eventos': 'eventos culturales y festividades',
        'astronomia': 'observación astronómica',
        'agricultura': 'sector agrícola y ganadero',
        'turismo': 'turismo y patrimonio',
        'naturaleza_escapadas': 'naturaleza y escapadas'
    }
    tema_trans = {
        'jovenes_rural': 'En el ámbito de las iniciativas para jóvenes rurales',
        'deportes': 'En el mundo del deporte comarcal',
        'cultura_eventos': 'En la agenda cultural de la región',
        'astronomia': 'En las noticias de astronomía',
        'agricultura': 'En el sector agrícola',
        'turismo': 'En materia de turismo y patrimonio',
        'naturaleza_escapadas': 'Para quienes buscan naturaleza y escapadas'
    }
    for tema, noticias in grupos_detectados.items():
        if len(noticias) >= MIN_NEWS_PER_BLOCK:
            bloques.append({
                'tema': tema,
                'descripcion_tema': tema_desc.get(tema, tema.replace('_',' ')) ,
                'transicion_elegante': tema_trans.get(tema, f'En {tema_desc.get(tema, tema)}'),
                'noticias': noticias
            })
            print(f"    📚 Bloque '{tema_desc.get(tema, tema)}': {len(noticias)} noticias")
        else:
            sin_grupo.extend(noticias)

    return {'bloques_tematicos': bloques, 'noticias_individuales': sin_grupo}

# --------- DEBUG ---------

def debug_noticias_antes_agrupacion(resumenes: list):
    print("\n🔍 DEBUG: Análisis de noticias antes de agrupar")
    print("=" * 60)
    for i, noticia in enumerate(resumenes):
        fuente = noticia.get('fuente', 'Sin fuente')
        resumen = noticia.get('resumen', 'Sin resumen')
        norm = normalize_text_for_similarity(resumen)[:150]
        ents = extract_candidate_phrases(resumen)
        print(f"\n📰 Noticia {i+1}: {fuente}")
        print(f"    Resumen: {resumen[:150]}{'...' if len(resumen) > 150 else ''}")
        print(f"    Norm: {norm}{'...' if len(norm)==150 else ''}")
        if ents:
            print(f"    🔎 Entidades/hashtags: {', '.join(ents[:6])}{'...' if len(ents)>6 else ''}")
    print("\n" + "=" * 60)

# --------- AGRUPACIÓN PRINCIPAL (IA + din. + fallback) ---------

def _enforce_unique_assignment(agrupado: dict) -> dict:
    """Evita que una noticia aparezca en varios bloques; prioriza primer bloque."""
    seen = set()
    nuevos_bloques = []
    for bloque in agrupado.get('bloques_tematicos', []):
        nuevas = []
        for n in bloque.get('noticias', []):
            nid = n.get('id') or stable_text_hash(n.get('resumen',''))
            if nid not in seen:
                nuevas.append(n)
                seen.add(nid)
        if len(nuevas) >= MIN_NEWS_PER_BLOCK:
            b2 = bloque.copy()
            b2['noticias'] = nuevas
            nuevos_bloques.append(b2)
    restantes = []
    for n in agrupado.get('noticias_individuales', []):
        nid = n.get('id') or stable_text_hash(n.get('resumen',''))
        if nid not in seen:
            restantes.append(n); seen.add(nid)
    return {'bloques_tematicos': nuevos_bloques, 'noticias_individuales': restantes}

def agrupar_noticias_por_temas_mejorado(resumenes: list) -> dict:
    print("\n🎯 Iniciando agrupación mejorada de noticias (Estrategia de 2 Pasos)...")
    
    # PASO 0: DEDUP (Esto no cambia)
    noticias_unicas = detectar_duplicados_y_similares(resumenes, umbral_similitud=DEDUP_SIMILARITY_THRESHOLD)

    if len(noticias_unicas) < MIN_NEWS_PER_BLOCK:
        print("    ℹ️ Muy pocas noticias para agrupar. Procesando individualmente.")
        return {"bloques_tematicos": [], "noticias_individuales": noticias_unicas}

    try:
        # --- NUEVA LÓGICA ---
        
        # PASO 1: Agrupación Lógica con IA (Obteniendo temas y IDs)
        print("\n🤖 PASO 1: Agrupación Lógica con IA (Obteniendo temas y IDs)...")
        noticias_simplificadas = json.dumps(
            [{"id": n.get("id"), "resumen": n.get("resumen")} for n in noticias_unicas],
            ensure_ascii=False, indent=2
        )
        prompt_agrupacion = mcmcn_prompts.PromptsAnalisis.agrupacion_logica_temas(noticias_simplificadas)
        respuesta_grupos = generar_texto_con_gemini(prompt_agrupacion)
        
        # Limpiar y parsear la respuesta del paso 1
        start_idx = respuesta_grupos.find('{')
        end_idx = respuesta_grupos.rfind('}')
        if start_idx == -1 or end_idx == -1:
            raise ValueError("La respuesta de la IA para agrupar no es un JSON válido.")
        json_limpio = respuesta_grupos[start_idx:end_idx+1]
        grupos_logicos = json.loads(json_limpio)
        print(f"    ✅ IA ha identificado {len(grupos_logicos)} temas.")

        # PASO 2: Enriquecimiento Creativo por cada tema
        print("\n🤖 PASO 2: Enriquecimiento Creativo con IA (Generando descripciones)...")
        bloques_tematicos = []
        used_ids = set()
        noticias_por_id = {n.get("id"): n for n in noticias_unicas}
        ids_ya_en_bloques = set() # <-- NUEVO: Para evitar duplicados entre bloques

        for tema, ids_noticias in grupos_logicos.items():
            if len(ids_noticias) < MIN_NEWS_PER_BLOCK:
                continue

            print(f"  -> Enriqueciendo tema: '{tema}'...")
            
            # --- NUEVO: Filtrar noticias que ya han sido asignadas a otro bloque ---
            ids_noticias_unicas = [nid for nid in ids_noticias if nid not in ids_ya_en_bloques]
            if len(ids_noticias_unicas) < MIN_NEWS_PER_BLOCK:
                continue

            lista_resumenes = [noticias_por_id[nid]["resumen"] for nid in ids_noticias_unicas if nid in noticias_por_id]
            resumenes_json = json.dumps(lista_resumenes, indent=2, ensure_ascii=False)

            prompt_enriquecimiento = mcmcn_prompts.PromptsCreativos.enriquecimiento_creativo_tema(tema, resumenes_json)
            respuesta_creativa = generar_texto_con_gemini(prompt_enriquecimiento)
            # --- NUEVA LÓGICA DE LIMPIEZA ---
            # Elimina el bloque de código Markdown si la IA lo añade
            json_limpio = respuesta_creativa
            if "```" in respuesta_creativa:
                # Extrae el contenido entre el primer '{' y el último '}'
                start_idx = respuesta_creativa.find('{')
                end_idx = respuesta_creativa.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_limpio = respuesta_creativa[start_idx:end_idx+1]
                else:
                    json_limpio = "" # No se encontró JSON válido
            try:
                # Usamos la variable 'json_limpio' en lugar de la original
                info_creativa = json.loads(json_limpio)
                
                # Construir el bloque temático final
                noticias_del_bloque = [noticias_por_id[nid] for nid in ids_noticias_unicas if nid in noticias_por_id]
                bloques_tematicos.append({
                    'tema': tema,
                    'descripcion_tema': info_creativa.get("descripcion", "Noticias sobre " + tema.replace("_", " ")),
                    'transicion_elegante': info_creativa.get("transicion", "A continuación, hablamos de " + tema.replace("_", " ")),
                    'noticias': noticias_del_bloque
                })
                used_ids.update(ids_noticias_unicas)
                ids_ya_en_bloques.update(ids_noticias_unicas) # <-- NUEVO: Marcar como usados
            except (json.JSONDecodeError, TypeError) as e:
                print(f"    ⚠️ Fallo al enriquecer el tema '{tema}'. Se omitirá.")
                print(f"      Respuesta recibida de la IA que causó el error: {respuesta_creativa}")
                print(f"      Error de decodificación: {e}")
                continue
        
        # PASO 3: Ensamblaje final
        print("\n🤖 PASO 3: Ensamblaje final...")
        noticias_individuales = [n for n in noticias_unicas if n.get("id") not in used_ids]
        
        print("    🎉 Agrupación en dos pasos completada con éxito.")
        return {'bloques_tematicos': bloques_tematicos, 'noticias_individuales': noticias_individuales}

    except Exception as e:
        print(f"    ❌ Fallo en el proceso de agrupación con IA de 2 pasos: {e}")
        print("    🔧 Usando agrupación por claves dinámicas como fallback...")
        agrupado_dyn = cluster_by_dynamic_keyphrases(noticias_unicas)
        if agrupado_dyn['bloques_tematicos']:
             print("    ✅ Agrupación dinámica exitosa.")
             return _enforce_unique_assignment(agrupado_dyn)
        
        print("    🔧 Usando agrupación simple como último recurso...")
        return _enforce_unique_assignment(agrupacion_simple_por_palabras_clave(noticias_unicas))



def fusionar_bloques_similares(bloques: list, umbral_similitud: float = 0.75) -> list:
    """
    Fusiona bloques temáticos que son muy similares entre sí para evitar redundancia.
    Compara el contenido de los bloques y, si superan un umbral de similitud,
    los une en un único bloque más grande.
    """
    if not bloques:
        return []

    print(f"\n🔗 Iniciando fusión de bloques temáticos similares (umbral: {umbral_similitud:.2f})...")

    # 1. Crear una "firma" de texto para cada bloque para poder compararlos
    for bloque in bloques:
        bloque['firma_texto'] = " ".join([normalize_text_for_similarity(n.get('resumen', '')) for n in bloque['noticias']])

    bloques_procesados = list(bloques)
    
    i = 0
    while i < len(bloques_procesados):
        bloque_a = bloques_procesados[i]
        j = i + 1
        while j < len(bloques_procesados):
            bloque_b = bloques_procesados[j]
            
            similitud = composite_similarity(bloque_a.get('firma_texto', ''), bloque_b.get('firma_texto', ''))
            
            if similitud >= umbral_similitud:
                print(f"    🤝 FUSIONANDO: Bloque '{bloque_b.get('descripcion_tema', 'N/A')}' ({similitud:.2f}) en '{bloque_a.get('descripcion_tema', 'N/A')}'")
                
                # 2. Añadir noticias del bloque B al A, evitando duplicados por ID
                ids_existentes = {n.get('id') for n in bloque_a['noticias']}
                for noticia_nueva in bloque_b['noticias']:
                    if noticia_nueva.get('id') not in ids_existentes:
                        bloque_a['noticias'].append(noticia_nueva)
                
                # 3. Actualizar la firma del bloque A para que sea más representativo
                bloque_a['firma_texto'] += " " + bloque_b.get('firma_texto', '')
                
                # 4. Eliminar el bloque B que ya ha sido fusionado
                bloques_procesados.pop(j)
            else:
                j += 1
        i += 1

    # 5. Limpiar las firmas de texto temporales
    for bloque in bloques_procesados:
        if 'firma_texto' in bloque:
            del bloque['firma_texto']

    if len(bloques_procesados) < len(bloques):
        print(f"    ✅ Fusión completada. Se redujeron {len(bloques) - len(bloques_procesados)} bloques.")
        # Reordenar bloques por número de noticias, de mayor a menor
        bloques_procesados.sort(key=lambda b: len(b.get('noticias', [])), reverse=True)
    else:
        print("    ✅ No se encontraron bloques similares para fusionar.")
        
    return bloques_procesados

# =================================================================================
# FUNCIÓN: GENERACIÓN DE NARRACIONES FLUIDAS POR BLOQUE
# ** LÓGICA MEJORADA PARA PRIORIZAR NOTICIAS RECIENTES **
# =================================================================================

def generar_narracion_fluida_bloque(bloque_tematico: dict, fecha_actual_str: str) -> str:
    """
    **NUEVA LÓGICA MEJORADA**
    Genera una única crónica consolidada para un bloque temático, en lugar de
    leer las noticias una por una. La longitud es proporcional al número de noticias.
    """
    tema = bloque_tematico.get("descripcion_tema", "varios temas")
    transicion = bloque_tematico.get("transicion_elegante", f"Y ahora, un bloque de noticias sobre {tema}.")
    noticias = bloque_tematico.get("noticias", [])

    if not noticias:
        return ""

    # Si solo hay una noticia en el "bloque", tratarla como individual para evitar sobre-ingeniería.
    if len(noticias) < 2:
        noticia = noticias[0]
        resumen_simple = f"{transicion}. {noticia.get('resumen', '')}"
        return resumen_simple

    # Ordenar noticias por fecha, por si acaso
    noticias_ordenadas = sorted(noticias, key=lambda x: x.get('fecha', '0000-00-00'), reverse=True)

    # 1. Preparar la lista de resúmenes y fuentes
    resumenes_para_prompt = []
    fuentes = []
    for i, n in enumerate(noticias_ordenadas):
        resumenes_para_prompt.append(f"Noticia {i+1} (Fuente: {n.get('fuente', 'desconocida')}): \"{n.get('resumen', '')}\"")
        fuentes.append(n.get('fuente', ''))
    
    lista_de_noticias_str = "\n".join(resumenes_para_prompt)
    
    # Limpiar y obtener fuentes únicas
    fuentes_unicas = sorted(list(set(f for f in fuentes if f)))

    # 2. Calcular longitud deseada
    num_noticias = len(noticias)
    # Lógica de longitud: base de 70 palabras, +80 por cada noticia.
    # Esto da un buen balance para que no sea ni muy corto ni excesivamente largo.
    longitud_deseada = 70 + (num_noticias * 80)

    # 3. Construir el prompt para la IA
    prompt = f"""Eres un editor y guionista de radio experto en sintetizar múltiples noticias sobre un mismo tema para crear una única crónica consolidada, coherente y fluida para un podcast.

**Tema principal:** "{tema}"

**Noticias a combinar (pueden ser muy similares o repetitivas):**
---
{lista_de_noticias_str}
---

**Instrucciones para tu crónica:**

1.  **SÍNTESIS EDITORIAL, NO UNA LISTA:** Tu tarea principal es actuar como un editor. Identifica la información clave y los datos únicos de cada noticia. **Elimina activamente la información redundante y las frases repetidas** entre las distintas fuentes.
2.  **CONSTRUYE UNA ÚNICA HISTORIA:** No leas las noticias una por una. Fusiona los datos relevantes en una sola narración cohesionada. Usa el evento más importante como hilo conductor y enriquécelo con detalles complementarios de las otras noticias.
3.  **LONGITUD PROPORCIONAL Y NATURAL:** La crónica debe sonar completa y natural. Al combinar {num_noticias} noticias, el texto final debería tener una longitud aproximada de **{longitud_deseada} palabras**.
4.  **CITACIÓN EXPLÍCITA DE FUENTES:**
    - Es **OBLIGATORIO** mencionar las fuentes originales de cada noticia integrada. El oyente debe saber quién lo dice.
    - Úsalas como parte de la narración: "Según informa el Ayuntamiento de X...", "La Asociación Y ha comunicado que...", "Desde Z nos cuentan que...".
    - Si son muchas fuentes (más de 3 o 4), intenta agruparlas pero **mencionando los nombres clave** (ej: "Municipios como A, B y C han lanzado...").
    - SOLO usa generalizaciones ("varios ayuntamientos") si nombrarlos todos rompiera totalmente el ritmo, pero prioriza siempre la atribución específica.
5.  **REGLA DE ORO SOBRE FECHAS:**
    - **PROHIBIDO** usar términos relativos como "hoy", "mañana", "ayer", "este lunes", "el próximo viernes". El podcast puede escucharse cualquier día.
    - **PROHIBIDO** intentar adivinar qué día de la semana cae una fecha (ej: NO digas "el lunes 25", di solo "el 25 de noviembre"). A menudo te equivocas con los días de la semana.
    - **USA SIEMPRE FECHAS ABSOLUTAS:** Di "el 25 de noviembre", "el 3 de diciembre".
    - Si la fecha no es relevante o es confusa, omítela o usa términos genéricos como "recientemente" o "próximamente".

**Importante:** La crónica debe empezar directamente con la frase de transición que te proporciono. No añadas introducciones adicionales.

**ESTRUCTURA VISUAL OBLIGATORIA:**
- Aunque la narración debe sonar fluida y conectada, **DEBES separar cada noticia o tema distinto en un PÁRRAFO NUEVO**.
- Usa un salto de línea doble entre cada noticia.
- Esto es vital para que podamos insertar una pequeña cortinilla musical entre ellas.

**Frase de transición de entrada (úsala para empezar):**
"{transicion}"

**CRÓNICA DE RADIO:**
"""

    # 4. Generar el texto con Gemini
    cronica_generada = generar_texto_con_gemini(prompt)

    # 5. Fallback por si la IA falla
    if not cronica_generada:
        print("      ⚠️ Fallo en la generación de crónica consolidada. Usando concatenación simple como fallback.")
        resumenes_fallback = ' '.join([n.get('resumen', '') for n in noticias_ordenadas])
        fuentes_fallback = ", ".join(fuentes_unicas)
        return f"{transicion}. {resumenes_fallback}. Esta información proviene de {fuentes_fallback}."

    # La IA ya debería incluir la transición, así que devolvemos el texto tal cual.
    return cronica_generada

def extraer_nombre_de_url(url: str) -> str:
    """Intenta extraer un nombre legible de la URL del feed o link."""
    try:
        if "facebook.com" in url:
            # Intentar sacar el último segmento válida
            parts = url.strip('/').split('/')
            for part in reversed(parts):
                if part and part not in ['facebook.com', 'www.facebook.com', 'groups', 'pages', 'profile.php']:
                    # Limpiar ID si viene formato Name-123456
                    if '-' in part and part.split('-')[-1].isdigit():
                        return part.rsplit('-', 1)[0].replace('-', ' ').title()
                    return part.replace('.', ' ').replace('-', ' ').title()
        
        # Fallback genérico para otros dominios
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        if domain:
             return domain.replace('www.', '').split('.')[0].title()
             
    except:
        pass
    return ""

# (Función normalizar_voz_a_pico eliminada por falta de uso)

# =================================================================================
# NUEVA FUNCIÓN REFRACTORIZADA PARA GESTIONAR AUDIO Y CTAs
# =================================================================================

def _generar_audio_noticia(datos: dict, fecha_actual_str: str) -> tuple[AudioSegment | None, str]:
    """Genera un segmento de audio para una noticia individual. Devuelve (audio, texto)."""
    
    texto_narracion = "" 
    
    fuente = datos.get('fuente', '')
    resumen = datos.get('resumen', '')
    es_breve = datos.get('es_breve', False)
    fecha_noticia = datos.get('fecha', 'Desconocida')
    print(f"  📰 Generando narración para noticia individual: {fuente}")
    
    if es_breve:
        print("      -> Noticia breve: manteniendo concisión")
        texto_narracion = f"Desde {fuente}: {resumen}"
    else:
        texto_narracion_generado = generar_texto_con_gemini(
            mcmcn_prompts.PromptsCreativos.narracion_profesional(
                fuentes=fuente, 
                resumen=resumen, 
                fecha_noticia_str=fecha_noticia,
                fecha_actual_str=fecha_actual_str,
                contexto_tematico=None
            )
        )        
        if not texto_narracion_generado:
            print("      ⚠️ Error generando narración individual. Usando formato simple.")
            texto_narracion = f"Desde {fuente}, nos llega la noticia de que: {resumen}"
        else:
            texto_narracion = texto_narracion_generado
    
    if not texto_narracion:
        print("      ❌ No se pudo generar ninguna narración. Devolviendo silencio.")
        return AudioSegment.silent(duration=100), ""
    
    texto_narracion = limpiar_artefactos_ia(texto_narracion)
    
    # --- GENERACIÓN ESTÁNDAR ---
    # Escapar el texto ANTES de añadir las etiquetas SSML
    texto_narracion_escapado = html.escape(texto_narracion)

    # Dividir el texto en frases para aplicar prosodia variable
    frases = re.split('([.?!])', texto_narracion_escapado)
    
    # Reconstruir las frases con su puntuación
    frases_completas = [frases[i] + (frases[i+1] if i+1 < len(frases) else '') for i in range(0, len(frases), 2)]

    texto_narracion_ssml = ""
    for frase in frases_completas:
        if frase.strip():
            # Aplicar una ligera variación aleatoria al ritmo de cada frase
            rate = f"{random.uniform(0.98, 1.02):.2f}"
            texto_narracion_ssml += f'<prosody rate="{rate}">{frase.strip()}</prosody><break time="450ms"/>'
    
    print(f"      ✅ Narración generada: '{texto_narracion[:80]}...' ")
    
    audio_segment = sintetizar_ssml_a_audio(f"<speak>{texto_narracion_ssml}</speak>")
    if audio_segment:
        return audio_segment, texto_narracion
    return None, texto_narracion

def _generar_resumen_final(noticias_agrupadas: dict) -> str:
    """Genera un resumen final conciso de todos los temas y noticias cubiertas."""
    noticias_individuales = noticias_agrupadas.get('noticias_individuales', [])
    bloques_tematicos = noticias_agrupadas.get('bloques_tematicos', [])
    
    contexto = []
    if bloques_tematicos:
        contexto.append("Temas tratados:")
        for bloque in bloques_tematicos:
            temas = bloque.get('descripcion_tema', 'varios temas')
            noticias_por_bloque = [n.get('resumen') for n in bloque.get('noticias', [])]
            contexto.append(f"- {temas}: " + " y ".join(noticias_por_bloque[:2]))
    if noticias_individuales:
        contexto.append("También cubrimos noticias individuales sobre:")
        for noticia in noticias_individuales:
            contexto.append(f"- {noticia.get('resumen')[:100]}...")
            
    prompt = mcmcn_prompts.PromptsCreativos.resumen_final(
        contexto='\n'.join(contexto)
    )
    
    texto_resumen_ia = generar_texto_con_gemini(prompt)
    
    # <-- LÍNEA AÑADIDA: Limpiamos la salida de la IA antes de devolverla
    texto_resumen = limpiar_artefactos_ia(texto_resumen_ia) if texto_resumen_ia else ""

    if not texto_resumen:
        print("      ⚠️ No se pudo generar el resumen final con IA. Usando un resumen simple.")
        temas_desc = [b.get('descripcion_tema') for b in bloques_tematicos]
        resumenes_ind = [n.get('resumen') for n in noticias_individuales]
        texto_resumen = "En resumen, hoy hablamos sobre " + ", ".join(temas_desc)
        if resumenes_ind:
            texto_resumen += " y otras noticias como " + ", ".join(resumenes_ind[:2]) + "..."
    
    return texto_resumen

def analizar_sentimiento_general_noticias(resumenes: List[Dict[str, Any]]) -> str:
    """
    Analiza el sentimiento general de una lista de noticias y devuelve el más común.
    Para optimizar, solo analiza un máximo de 5 noticias.
    """
    if not resumenes:
        return "neutro"

    sentimientos = []
    # Para no hacer demasiadas llamadas a la API, analizamos un máximo de 5 noticias
    # representativas para obtener el tono general.
    for noticia in resumenes[:5]:
        texto_resumen = noticia.get('resumen', '')
        if texto_resumen:
            prompt = mcmcn_prompts.PromptsAnalisis.analizar_sentimiento_texto(texto=texto_resumen)
            sentimiento = generar_texto_con_gemini(prompt).lower().strip()
            if sentimiento in ['positivo', 'negativo', 'neutro']:
                sentimientos.append(sentimiento)

    if not sentimientos:
        return "neutro"

    # Devolver el sentimiento más común
    return Counter(sentimientos).most_common(1)[0][0]

# =================================================================================
# FUNCIONES AUXILIARES MEJORADAS
# =================================================================================

def parsear_fecha_segura(entry):
    """Maneja fechas de forma segura con múltiples intentos."""
    for field in ['published_parsed', 'updated_parsed']:
        if hasattr(entry, field) and entry[field]:
            try:
                return datetime.fromtimestamp(time.mktime(entry[field]))
            except (ValueError, TypeError):
                continue
    return datetime(2000, 1, 1)  # Valor por defecto: antigua para ser filtrada si no tiene fecha

def audio_cache_valido(audio_path):
    """Verifica la integridad de un archivo de audio en caché."""
    if not os.path.exists(audio_path):
        return False
    try:
        audio = AudioSegment.from_file(audio_path)
        return len(audio) > 0 and audio.max_dBFS > SILENCE_THRESHOLD_DBFS
    except:
        return False

def _get_cta_text(tipo: str, dia_semana: str, base_dir: str) -> str:
    """
    Carga el texto de un CTA, buscando primero el específico del día y luego un genérico.
    Ej: busca 'viernes_cta_inicio.txt' y si no, 'cta_inicio.txt'.
    """
    import unicodedata

    # Normalizar día de la semana para quitar tildes (miércoles -> miercoles)
    # ya que los archivos no suelen tener tildes.
    dia_normalizado = ''.join(c for c in unicodedata.normalize('NFD', dia_semana)
                              if unicodedata.category(c) != 'Mn')

    # 1. Probar el archivo específico del día
    nombre_fichero_dia = f"{dia_normalizado}_cta_{tipo}.txt"
    ruta_fichero_dia = os.path.join(base_dir, nombre_fichero_dia)
    if os.path.exists(ruta_fichero_dia):
        try:
            with open(ruta_fichero_dia, 'r', encoding='utf-8') as f:
                print(f"      ✅ CTA específico encontrado: {nombre_fichero_dia}")
                return f.read().strip()
        except Exception as e:
            print(f"      ⚠️ Error leyendo {nombre_fichero_dia}: {e}")

    # 2. Fallback al archivo genérico
    nombre_fichero_generico = f"cta_{tipo}.txt"
    ruta_fichero_generico = os.path.join(base_dir, nombre_fichero_generico)
    if os.path.exists(ruta_fichero_generico):
        try:
            with open(ruta_fichero_generico, 'r', encoding='utf-8') as f:
                print(f"      ℹ️ Usando CTA genérico: {nombre_fichero_generico}")
                return f.read().strip()
        except Exception as e:
            print(f"      ⚠️ Error leyendo {nombre_fichero_generico}: {e}")
    
    # 3. Si no se encuentra nada
    print(f"      ❌ No se encontró ningún archivo de CTA para '{tipo}'.")
    return ""

def limpiar_cache_antiguo(cache_completo: Dict[str, Any], horas_retencion: int = 72):
    """
    Elimina entradas del caché y archivos de audio que sean más antiguos que el periodo de retención.
    """
    print(f"\n🧹 Limpiando caché (entradas anteriores a {horas_retencion} horas)...")
    limite = datetime.now() - timedelta(hours=horas_retencion)
    eliminar = []

    for hash_id, datos in cache_completo.items():
        fecha_str = datos.get('fecha')
        if not fecha_str:
            continue
        
        try:
            # La fecha en cache suele guardarse como YYYY-MM-DD
            # Asumimos fin del día para no borrar demasiado pronto si solo hay fecha
            # O mejor, usamos la fecha tal cual (00:00:00)
            fecha_dato = datetime.strptime(fecha_str, "%Y-%m-%d")
            
            # Si es más vieja que el límite...
            if fecha_dato < limite:
                eliminar.append(hash_id)
        except ValueError:
            pass # Fecha mal formada, la dejamos por seguridad (o borrarla, a gusto)

    count = 0
    for hash_id in eliminar:
        datos = cache_completo.pop(hash_id)
        audio_path = datos.get('audio_path')
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError:
                pass
        count += 1

    if count > 0:
        print(f"   🗑️  Se han eliminado {count} noticias antiguas y sus audios.")
    else:
        print("   ✅ El caché está limpio.")

def _generar_y_cachear_audio_noticia(noticia: dict, fecha_actual_str: str) -> tuple[AudioSegment | None, str]:
    """
    Genera (o carga desde caché) el audio para una única noticia.
    Devuelve (audio_segment, texto_narracion) o (None, "") si falla.
    """
    noticia_id = noticia.get('id')
    if not noticia_id:
        return None, ""

    audio_file_path = os.path.join(AUDIO_CACHE_DIR, f"{noticia_id}.mp3")
    text_file_path = os.path.join(AUDIO_CACHE_DIR, f"{noticia_id}.txt")

    if audio_cache_valido(audio_file_path):
        print(f"  🎧 Cargando audio desde caché para noticia: {noticia.get('fuente')}")
        audio = AudioSegment.from_file(audio_file_path)
        
        # Intentar cargar el texto asociado
        texto = ""
        if os.path.exists(text_file_path):
            try:
                with open(text_file_path, 'r', encoding='utf-8') as f:
                    texto = f.read()
            except Exception as e:
                print(f"      ⚠️ Error leyendo caché de texto: {e}")
        
        # Si no hay texto en caché, usar el resumen como fallback
        if not texto:
            texto = noticia.get('resumen', '')
            
        return audio, texto
    
    print(f"  🎤 Generando nuevo audio para noticia: {noticia.get('fuente')}")
    audio_generado, texto_generado = _generar_audio_noticia(noticia, fecha_actual_str)
    
    if audio_generado:
        try:
            audio_generado.export(audio_file_path, format="mp3")
            # Guardar también el texto generado
            if texto_generado:
                with open(text_file_path, 'w', encoding='utf-8') as f:
                    f.write(texto_generado)
            return audio_generado, texto_generado
        except Exception as e:
            print(f"      ❌ Error al guardar audio/texto en caché: {e}")
    
    return None, ""

def generar_html_transcripcion(transcript_data: list, output_dir: str, timestamp: str):
    """
    Genera un archivo HTML con la transcripción/resumen del podcast.
    Estilo: Dark Mode, High Contrast (Inspirado en The Verge).
    Colores: Blanco, Negro, Naranja, Amarillo, Verde.
    Incluye reproductor de audio personalizado.
    """
    print("\n📝 Generando archivo de transcripción HTML con estilo y reproductor...")
    
    # Calcular año y mes desde el timestamp (formato esperado: YYYYMMDD_HHMMSS)
    try:
        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        year = dt.strftime("%Y")
        month = dt.strftime("%m")
        fecha_emision = dt.strftime("%d/%m/%Y")
    except ValueError:
        # Fallback si el timestamp no tiene el formato esperado
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        fecha_emision = now.strftime("%d/%m/%Y")

    # URL dinámica del audio
    audio_url = f"https://micomicona.com/wp-content/uploads/{year}/{month}/podcast_completo_{timestamp}.mp3"
    
    css_styles = """
    <style>
        .podcast-transcript {
            background-color: #000000;
            color: #ffffff;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            padding: 40px;
            line-height: 1.6;
            border: 1px solid #333;
        }
        .podcast-transcript h2 {
            font-family: 'Impact', 'Arial Black', sans-serif;
            text-transform: uppercase;
            font-size: 3em;
            letter-spacing: -1px;
            margin-bottom: 10px;
            color: #ffffff;
            line-height: 1;
        }
        .podcast-transcript .meta {
            font-family: 'Courier New', monospace;
            color: #ffff00; /* Amarillo */
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 40px;
            border-bottom: 4px solid #ffffff;
            padding-bottom: 20px;
            display: block;
        }
        
        /* --- CUSTOM AUDIO PLAYER STYLES --- */
        .audio-player-container {
            background-color: #111;
            border: 2px solid #00ff00; /* Verde */
            padding: 20px;
            margin-bottom: 40px;
            display: flex;
            align-items: center;
            gap: 20px;
            box-shadow: 5px 5px 0px #00ff00;
        }
        
        .play-btn {
            background-color: #ff4d00; /* Naranja */
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.1s;
        }
        .play-btn:active {
            transform: scale(0.95);
        }
        .play-btn svg {
            fill: #000;
            width: 20px;
            height: 20px;
            margin-left: 2px; /* Ajuste visual para el icono de play */
        }
        .play-btn.playing svg {
            margin-left: 0;
        }
        
        .progress-container {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .player-label {
            font-family: 'Arial Black', sans-serif;
            text-transform: uppercase;
            color: #00ff00;
            font-size: 0.8em;
            margin-bottom: 5px;
        }

        .progress-bar-bg {
            background-color: #333;
            height: 8px;
            width: 100%;
            cursor: pointer;
            position: relative;
        }
        
        .progress-bar-fill {
            background-color: #ffff00; /* Amarillo */
            height: 100%;
            width: 0%;
            transition: width 0.1s linear;
        }
        
        .time-display {
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #ffffff;
            font-size: 0.9em;
            min-width: 100px;
            text-align: right;
        }
        
        /* ---------------------------------- */

        .transcript-section {
            margin-bottom: 40px;
            padding-left: 20px;
            border-left: 6px solid #333;
        }
        .transcript-section h3, .transcript-section h4 {
            font-family: 'Arial Black', sans-serif;
            text-transform: uppercase;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.5em;
            letter-spacing: -0.5px;
        }
        .transcript-section p {
            font-size: 1.1em;
            color: #e0e0e0;
            margin: 0;
        }
        
        /* Estilos específicos por sección */
        .transcript-intro {
            border-left-color: #ffff00; /* Amarillo */
        }
        .transcript-intro h3 {
            color: #ffff00;
        }

        .transcript-block {
            border-left-color: #00ff00; /* Verde */
        }
        .transcript-block h3 {
            color: #00ff00;
            background: #000;
            display: inline-block;
        }

        .transcript-news {
            border-left-color: #00ff00; /* Verde */
            margin-left: 20px; /* Indentar noticias dentro de bloques si se quiere */
        }
        .transcript-news h4 {
            color: #ffffff;
            background-color: #000000;
            border-bottom: 2px solid #00ff00;
            display: inline;
            padding-right: 10px;
        }

        .transcript-audience {
            border-left-color: #ff4d00; /* Naranja */
            background-color: #111;
            padding: 20px;
            border-left-width: 10px;
        }
        .transcript-audience h3 {
            color: #ff4d00;
        }

        .transcript-outro {
            border-left-color: #ffffff;
            border-bottom: 4px solid #ffffff;
            padding-bottom: 20px;
        }
        .transcript-outro h3 {
            color: #ffffff;
        }

        .footer-note {
            font-family: 'Courier New', monospace;
            color: #666;
            font-size: 0.8em;
            text-align: right;
            margin-top: 20px;
        }
        

    </style>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const audio = document.getElementById('podcast-audio');
            const playBtn = document.getElementById('play-btn');
            const playIcon = document.getElementById('play-icon');
            const pauseIcon = document.getElementById('pause-icon');
            const progressBarBg = document.getElementById('progress-bar-bg');
            const progressBarFill = document.getElementById('progress-bar-fill');
            const timeDisplay = document.getElementById('time-display');
            
            // Toggle Play/Pause
            playBtn.addEventListener('click', function() {
                if (audio.paused) {
                    audio.play();
                    playBtn.classList.add('playing');
                    playIcon.style.display = 'none';
                    pauseIcon.style.display = 'block';
                } else {
                    audio.pause();
                    playBtn.classList.remove('playing');
                    playIcon.style.display = 'block';
                    pauseIcon.style.display = 'none';
                }
            });
            
            // Update Progress Bar
            audio.addEventListener('timeupdate', function() {
                const percent = (audio.currentTime / audio.duration) * 100;
                progressBarFill.style.width = percent + '%';
                
                // Update Time
                const current = formatTime(audio.currentTime);
                const duration = formatTime(audio.duration || 0);
                timeDisplay.textContent = `${current} / ${duration}`;
            });
            
            // Click on Progress Bar
            progressBarBg.addEventListener('click', function(e) {
                const rect = progressBarBg.getBoundingClientRect();
                const pos = (e.clientX - rect.left) / rect.width;
                audio.currentTime = pos * audio.duration;
            });
            
            function formatTime(seconds) {
                if (isNaN(seconds)) return "0:00";
                const m = Math.floor(seconds / 60);
                const s = Math.floor(seconds % 60);
                return `${m}:${s.toString().padStart(2, '0')}`;
            }
        });
    </script>
    """
    
    # SVG Icons
    icon_play = '<svg id="play-icon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>'
    icon_pause = '<svg id="pause-icon" viewBox="0 0 24 24" style="display:none;"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>'
    
    html_content = f"""
    {css_styles}
    <div class="podcast-transcript">
        <h2>Podcast Micomicona</h2>
        <span class="meta">Emitido el {fecha_emision} </span>
        
        <!-- CUSTOM AUDIO PLAYER -->
        <div class="audio-player-container">
            <audio id="podcast-audio" src="{audio_url}"></audio>
            
            <button id="play-btn" class="play-btn">
                {icon_play}
                {icon_pause}
            </button>
            
            <div class="progress-container">
                <div class="player-label">ESCUCHAR PODCAST</div>
                <div id="progress-bar-bg" class="progress-bar-bg">
                    <div id="progress-bar-fill" class="progress-bar-fill"></div>
                </div>
            </div>
            
            <div id="time-display" class="time-display">0:00 / --:--</div>
        </div>
        <!-- END PLAYER -->
        
        <hr style="border-color: #333; margin-bottom: 40px;">
    """
    
    for item in transcript_data:
        tipo = item.get('type')
        titulo = item.get('title', '')
        contenido = item.get('content', '')
        
        # Limpieza básica de HTML en el contenido
        contenido_html = html.escape(contenido).replace('\n', '<br>')
        
        if tipo == 'intro':
            html_content += f"""
            <div class="transcript-section transcript-intro">
                <h3>🎙️ Introducción</h3>
                <p>{contenido_html}</p>
            </div>
            """
        elif item.get('type') == 'block':
            html_content += f"""
            <div class="transcript-section transcript-block">
                <h3>{html.escape(titulo)}</h3>
                <p>{contenido_html}</p>
            </div>
            """
        elif item.get('type') == 'news':
            html_content += f"""
            <div class="transcript-section transcript-news">
                <h4>📰 {html.escape(titulo)}</h4>
                <p>{contenido_html}</p>
            </div>
            """
        elif item.get('type') == 'audience':
            html_content += f"""
            <div class="transcript-section transcript-audience">
                <h3>💬 La Voz de la Audiencia</h3>
                <p>{contenido_html}</p>
            </div>
            """
        elif item.get('type') == 'outro':
            html_content += f"""
            <div class="transcript-section transcript-outro">
                <h3>👋 Despedida</h3>
                <p>{contenido_html}</p>
            </div>
            """
            
    html_content += """
        <div class="footer-note">
            <p>Generado automáticamente por Dorotea • con mucho amor</p>
        </div>
    </div>
    """
    
    # Guardar transcripción en JSON para usos futuros (Social Pack, etc)
    json_filename = f"transcript.json"
    json_filepath = os.path.join(output_dir, json_filename)
    try:
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=4, ensure_ascii=False)
        print(f"✅ Transcripción JSON guardada en: {json_filepath}")
    except Exception as e:
        print(f"❌ Error al guardar transcripción JSON: {e}")

    filename = f"podcast_summary_{timestamp}.html"

    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Transcripción estilizada con reproductor guardada en: {filepath}")
    except Exception as e:
        print(f"❌ Error al guardar transcripción: {e}")

# =================================================================================
# FUNCIÓN PRINCIPAL MEJORADA
# =================================================================================

def procesar_feeds_google(nombre_archivo_feeds: str, idioma_destino: str = 'es', min_items: int = 5, solo_preview: bool = False, archivo_entrada_json: str = None):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"podcast_apg_{timestamp}"
        
        # Verificar y crear directorios necesarios
        required_dirs = [AUDIO_ASSETS_DIR, CTA_TEXTS_DIR, AUDIO_CACHE_DIR, output_dir]
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)
            if not os.path.exists(dir_path):
                print(f"❌ No se pudo crear directorio: {dir_path}")
                sys.exit(1)
                
        print(f"Directorio de salida creado: {output_dir}")

        print("\n--- FASE 1: Recopilando, filtrando y resumiendo noticias ---")
        
        cache_noticias = cargar_cache_noticias()
        noticias_candidatas_totales = []

        # --- MODO 1: CARGAR DESDE JSON (Selección de usuario) ---
        if archivo_entrada_json:
            print(f"📂 Cargando noticias seleccionadas desde: {archivo_entrada_json}")
            try:
                with open(archivo_entrada_json, 'r', encoding='utf-8') as f:
                    # Se asume que el JSON contiene una lista de objetos noticia completos
                    noticias_candidatas_totales = json.load(f)
                    # Convertir fechas string de vuelta a datetime si es necesario
                    for n in noticias_candidatas_totales:
                        if isinstance(n['fecha'], str):
                            try:
                                n['fecha'] = datetime.fromisoformat(n['fecha'])
                            except:
                                n['fecha'] = datetime.now() # Fallback
            except Exception as e:
                print(f"❌ Error leyendo JSON de entrada: {e}")
                sys.exit(1)

        # --- MODO 2: PROCESAMIENTO NORMAL (O PREVIEW) DESDE RSS ---
        else:
            with open(nombre_archivo_feeds, 'r', encoding='utf-8') as f:
                feeds_urls = [url.strip() for url in f.read().replace(',', '\n').splitlines() if url.strip()]

            if not feeds_urls:
                print(f"Advertencia: El archivo de feeds '{nombre_archivo_feeds}' está vacío.")
                sys.exit(1)

            # Configuración de límites (con valores por defecto si no existen)
            gen_config = CONFIG.get('generation_config', {})
            window_hours = int(gen_config.get('news_window_hours', 48))
            max_items = int(gen_config.get('max_news_items', 20))
            
            print(f"      ⚙️ Configuración: Ventana={window_hours}h, Máx. Noticias={max_items}")

            limite_dias = datetime.now() - timedelta(hours=window_hours)

            for url in feeds_urls:
                try:
                    feed = feedparser.parse(url)
                    sitio = feed.feed.get('title', '').replace(" on Facebook", "").strip()
                    if not sitio:
                         link_feed = feed.feed.get('link', '') or url
                         sitio = extraer_nombre_de_url(link_feed)
                    for entry in feed.entries:
                        fecha_pub = parsear_fecha_segura(entry)
                        if fecha_pub < limite_dias:
                            continue
                        contenido = entry.get('summary', entry.get('description', ''))
                        if not contenido:
                            continue

                        # Reparar posible codificación rota
                        contenido = reparar_codificacion(contenido)
                        titulo_reparado = reparar_codificacion(entry.get('title', ''))

                        # --- NUEVO: Intentar seguir encadenamiento de noticias (republicaciones) ---
                        texto_externo = ""
                        enlace_externo = extract_first_external_link(contenido)
                        if enlace_externo:
                            print(f"      🔗 Detectado enlace externo en noticia: {enlace_externo}")
                            scraped_text = fetch_article_text(enlace_externo)
                            if scraped_text:
                                # Limitamos el texto extraído para no saturar el prompt (ej: 3000 chars)
                                texto_externo = f"\n\n[INFORMACIÓN DE FUENTE ENLAZADA ({enlace_externo})]:\n{scraped_text[:3000]}"
                                print(f"      ✅ Contenido externo añadido ({len(scraped_text)} caracteres).")

                        # --- DEFINIR CONTEXTO BASE (Para uso en visión y texto final) ---
                        texto_contexto = limpiar_html(contenido) + texto_externo

                        # --- NUEVO: Multimodalidad (Análisis de imágenes) ---
                        texto_imagen = ""
                        url_imagen = extract_image_url(contenido)
                        if url_imagen:
                             print(f"      🖼️ Detectada imagen en la noticia: {url_imagen[:60]}...")
                             img_bytes = download_image_as_bytes(url_imagen)
                             if img_bytes:
                                  print("      👁️ Analizando imagen con Gemini Vision...")
                                  # USA texto_contexto AHORA QUE EXISTE
                                  prompt_vision = mcmcn_prompts.PromptsAnalisis.analizar_imagen(texto_contexto[:500])
                                  analisis_img = generar_texto_multimodal_con_gemini(prompt_vision, img_bytes)
                                  if analisis_img and "IMAGEN_SIN_DATOS" not in analisis_img:
                                       texto_imagen = f"\n\n[DATOS EXTRAÍDOS DE LA IMAGEN ADJUNTA]:\n{analisis_img}"
                                       print(f"      ✅ Datos visuales extraídos: {analisis_img[:100].replace(chr(10), ' ')}...")
                                  else:
                                       print("      ℹ️ La imagen no contenía datos relevantes o legibles.")

                        noticia_hash = stable_text_hash(contenido)
                        texto_crudo = texto_contexto + texto_imagen

                        noticias_candidatas_totales.append({
                            'sitio': sitio, 
                            'texto': texto_crudo, 
                            'fecha': fecha_pub, 
                            'hash': noticia_hash,
                            'titulo': titulo_reparado,
                            'link': entry.get('link', '')
                        })
                except Exception as e:
                    print(f"Advertencia: No se pudo procesar el feed '{url}'. Error: {e}")

        if not noticias_candidatas_totales:
            print("No se encontraron noticias válidas para procesar. Abortando.")
            sys.exit(0)
            
        # Si venimos de JSON, quizás ya estén ordenadas, pero no está de más
        noticias_candidatas_totales.sort(key=lambda x: x['fecha'], reverse=True)
        


        # Continuar con el flujo normal...
        # Usar el límite configurado solo si no venimos de un JSON manual (que manda el usuario)
        if not archivo_entrada_json:
            noticias_seleccionadas = noticias_candidatas_totales[:max_items]
        else:
            noticias_seleccionadas = noticias_candidatas_totales

        resumenes_finales = []
        nuevas_noticias_para_cache = {}

        for noticia in noticias_seleccionadas:
            # Soporte para ambas claves: 'hash' (raw) o 'id' (processed/edited)
            noticia_hash = noticia.get('hash') or noticia.get('id')
            
            if not noticia_hash:
                 # Fallback de emergencia si no hay ni hash ni id
                 noticia_hash = stable_text_hash(noticia.get('texto', '') or noticia.get('resumen', ''))

            # Determinar si necesitamos procesar (generar audio) o usar caché
            necesita_procesamiento = True

            if noticia_hash in cache_noticias:
                noticia_cacheada = cache_noticias[noticia_hash]
                
                # VERIFICACIÓN INTELIGENTE DE CACHÉ
                # Si tenemos un resumen manual (input), SOLO usamos el caché si el texto coincide.
                usar_cache = True
                if 'resumen' in noticia and noticia.get('resumen'):
                    resumen_input = noticia.get('resumen', '').strip()
                    resumen_cache = noticia_cacheada.get('resumen', '').strip()
                    if resumen_input != resumen_cache:
                        print(f"      ✏️ DETECTADO CAMBIO EN EL RESUMEN: Ignorando caché para regenerar audio.")
                        usar_cache = False
                
                if usar_cache:
                    resumenes_finales.append(noticia_cacheada)
                    print(f"      ⏩ Usando caché para '{noticia_cacheada['resumen'][:50]}...'")
                    necesita_procesamiento = False # Ya lo tenemos, no procesar más

            if necesita_procesamiento:
                # ----------------------------------------------------------------
                # LÓGICA UNIFICADA: Si ya tiene resumen (edición manual), lo usamos.
                # Si no, lo generamos con IA. LUEGO, siempre hacemos el resto.
                # ----------------------------------------------------------------
                
                resumen = None
                entidades_clave = []
                es_noticia_breve = False # Valor inicial
                
                # APLICAMOS LA PRE-LIMPIEZA SIEMPRE (para tener texto_crudo disponible)
                texto_origen = noticia.get('texto', '')
                if texto_origen:
                    texto_crudo = preprocesar_texto_para_fechas(texto_origen)
                    es_noticia_breve = len(texto_crudo) < 150
                    fuente_original = identificar_fuente_original(texto_origen)
                    # FIX: Si es propia, usar el nombre del sitio (feed) en su lugar para evitar "Desde PROPIA..."
                    if fuente_original == "PROPIA":
                        fuente_original = noticia.get('sitio', '') or "la organización"
                else:
                    texto_crudo = ""
                    es_noticia_breve = noticia.get('es_breve', False)
                    fuente_original = ""

                # CASO 1: RESUMEN YA EXISTENTE (Manual)
                if 'resumen' in noticia and noticia.get('resumen'):
                    titulo_safe = noticia.get('titulo') or ""
                    print(f"      📝 Usando resumen editado manualmente: {titulo_safe[:50]}...")
                    resumen = noticia['resumen']
                    # Intentamos recuperar entidades si vienen en el JSON
                    entidades_clave = noticia.get('entidades_clave', [])
                
                # CASO 2: GENERAR RESUMEN CON IA (Automático)
                else:
                    print(f"  Resumiendo y generando audio para noticia nueva: {noticia['sitio'][:50]}...")
                    
                    # === FASE 1: Entidades (solo si no es manual) ===
                    print("      -> Fase 1/3: Extrayendo entidades clave con IA...")
                    prompt_entidades = mcmcn_prompts.PromptsAnalisis.extraer_entidades_clave(texto_crudo)
                    respuesta_entidades_json = generar_texto_con_gemini(prompt_entidades)
                    
                    if respuesta_entidades_json:
                        try:
                            json_limpio = respuesta_entidades_json
                            if "```" in json_limpio:
                                start_idx = json_limpio.find('[')
                                end_idx = json_limpio.rfind(']')
                                if start_idx != -1 and end_idx != -1:
                                    json_limpio = json_limpio[start_idx:end_idx+1]
                            entidades_clave = json.loads(json_limpio)
                            print(f"      ✅ Entidades extraídas: {', '.join(entidades_clave)}")
                        except:
                            entidades_clave = []

                    # === FASE 2: Resumen ===
                    if es_noticia_breve:
                        print("      -> Fase 2/3: Usando el prompt de resumen MUY BREVE.")
                        prompt_para_ia = mcmcn_prompts.PromptsAnalisis.resumen_muy_breve(texto=texto_crudo, fuente_original=fuente_original)
                    else:
                        print("      -> Fase 2/3: Generando resumen enriquecido con IA. (Incluye verificación de fechas)")
                        prompt_para_ia = mcmcn_prompts.PromptsAnalisis.resumen_noticia_enriquecido(
                            texto=texto_crudo,
                            fuente_original=fuente_original,
                            entidades_clave=entidades_clave,
                            idioma_destino=idioma_destino,
                            contexto_calendario=obtener_festividades_contexto()
                        )
                    
                    resumen = generar_texto_con_gemini(prompt_para_ia)

                # ----------------------------------------------------------------
                # PROCESAMIENTO COMÚN (Limpieza, Sentimiento, Audio)
                # ----------------------------------------------------------------
                if resumen:
                    sitio_safe = noticia.get('sitio', '')
                    
                    if fuente_original and fuente_original != "PROPIA":
                        if sitio_safe:
                             fuente_final = f"{sitio_safe} (repost de {fuente_original})"
                        else:
                             fuente_final = fuente_original
                    else:
                        fuente_final = sitio_safe
                    audio_file_path = os.path.join(AUDIO_CACHE_DIR, f"{noticia_hash}.mp3")
                    
                    texto_limpio = limpiar_artefactos_ia(resumen)
                    texto_limpio = reemplazar_urls_por_mencion(texto_limpio)

                    # Si estamos en PREVIEW, guardamos el objeto parcial y CONTINUAMOS (Saltar TTS)
                    if solo_preview:
                         nueva_noticia_procesada = {
                            'fuente': fuente_final,
                            'resumen': texto_limpio, # Guardamos el limpio ya
                            'titulo': noticia.get('titulo', ''), # Importante para editar
                            'sitio': noticia.get('sitio', ''),
                            'fecha': noticia['fecha'],
                            'id': noticia_hash,
                            'es_breve': es_noticia_breve,
                            'entidades_clave': entidades_clave
                        }
                         resumenes_finales.append(nueva_noticia_procesada)
                         continue # <--- SALTAR RESTO DEL BUCLE (TTS)

                    # Filtrar noticias cortas (SOLO si no es manual, si es manual el usuario manda)
                    # Si viene 'entidades_clave' asumimos que puede ser manual, pero mejor flag explícito.
                    # Asumimos: si 'resumen' estaba en input, es manual -> NO FILTRAR.
                    es_manual = 'resumen' in noticia and noticia.get('resumen')
                    
                    if not es_manual and len(texto_limpio.split()) < MIN_WORDS_FOR_AUDIO:
                        print(f"      🗑️  Ignorando noticia por tener menos de {MIN_WORDS_FOR_AUDIO} palabras.")
                        continue

                    # === FASE 3: Sentimiento ===
                    print(f"      -> Fase 3/3: Analizando sentimiento...")
                    prompt_sentimiento = mcmcn_prompts.PromptsAnalisis.analizar_sentimiento_texto(texto=texto_limpio)
                    sentimiento_noticia = generar_texto_con_gemini(prompt_sentimiento).lower().strip()
                    if sentimiento_noticia not in ['positivo', 'negativo', 'neutro']: sentimiento_noticia = 'neutro'
                    
                    # Extraer localidad
                    localidad_extraida = extraer_localidad_con_ia(texto_crudo)

                    # === GENERACIÓN DE AUDIO (TTS) ===
                    sitio_print = noticia.get('sitio', '')
                    print(f"      🎙️  Generando audio para: {sitio_print[:30]}...")
                    audio_segment = sintetizar_ssml_a_audio(f"<speak>{html.escape(texto_limpio)}</speak>")

                    if audio_segment:
                        audio_segment.export(audio_file_path, format="mp3")
                        nueva_noticia_procesada = {
                            'fuente': fuente_final,
                            'resumen': resumen, # Original o editado
                            'fecha': noticia['fecha'].strftime("%Y-%m-%d"),
                            'id': noticia_hash,
                            'audio_path': audio_file_path,
                            'es_breve': es_noticia_breve,
                            'localidad': localidad_extraida,
                            'sentimiento': sentimiento_noticia,
                            'entidades_clave': entidades_clave
                        }
                        resumenes_finales.append(nueva_noticia_procesada)
                        nuevas_noticias_para_cache[noticia_hash] = nueva_noticia_procesada

        if not resumenes_finales:
            print("No se pudieron generar resúmenes válidos. Abortando.")
            sys.exit(0)

        # --- MODO PREVIEW (Post-Resumen): GUARDAR Y SALIR ---
        if solo_preview:
            print("👀 MODO PREVIEW ACTIVADO: Guardando noticias resumidas y saliendo...")
            archivo_preview = "prevision_noticias_resumidas.json"
            
            # Serializar fechas para JSON
            export_data = []
            for n in resumenes_finales:
                n_copy = n.copy()
                # Asegurar que no hay objetos datetime
                if 'fecha' in n_copy and isinstance(n_copy['fecha'], datetime):
                     n_copy['fecha'] = n_copy['fecha'].strftime("%Y-%m-%d")
                export_data.append(n_copy)
                
            with open(archivo_preview, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
                
            print(f"✅ Preview resumida guardada en: {archivo_preview}")
            try:
                os.rmdir(output_dir)
            except:
                pass 
            sys.exit(0)


             
        # Guardamos el caché actualizado (incluyendo las nuevas entidades)
        cache_noticias.update(nuevas_noticias_para_cache)
        
        # --- LIMPIEZA AUTOMÁTICA ---
        limpiar_cache_antiguo(cache_noticias, horas_retencion=72)
        # ---------------------------
        
        guardar_cache_noticias(cache_noticias)

        debug_noticias_antes_agrupacion(resumenes_finales)
        noticias_agrupadas = agrupar_noticias_por_temas_mejorado(resumenes_finales)
        
        # --- NUEVO PASO: Fusión de bloques temáticos similares ---
        bloques_originales = noticias_agrupadas.get('bloques_tematicos', [])
        if bloques_originales:
            noticias_agrupadas['bloques_tematicos'] = fusionar_bloques_similares(bloques_originales)
        # --- FIN DEL NUEVO PASO ---

        # INICIO DE LOS CAMBIOS DE NORMALIZACIÓN
        print("\n--- FASE 2: Generando audio con la nueva introducción estructurada ---")

        dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        dia_semana_str = dias_semana[datetime.now().weekday()]

        print(f"\n--- Obteniendo textos de CTA para el {dia_semana_str} ---")
        
        cta_texts_dir = CTA_TEXTS_DIR
        cta_inicio_text = _get_cta_text("inicio", dia_semana_str, cta_texts_dir)
        cta_intermedio_text = _get_cta_text("intermedio", dia_semana_str, cta_texts_dir)
        cta_cierre_text = _get_cta_text("cierre", dia_semana_str, cta_texts_dir)
        
        segmentos_audio = []
        transcript_data = [] # <-- Inicializar lista para transcripción
        audio_assets_dir = AUDIO_ASSETS_DIR

        # --- Cargar la cortinilla para los CTAs ---
        cortinilla_cta_audio = None
        ruta_cortinilla_cta = os.path.join(audio_assets_dir, "cortinilla_cta.mp3")
        if os.path.exists(ruta_cortinilla_cta):
            try:
                cortinilla_cta_audio = AudioSegment.from_file(ruta_cortinilla_cta)
                print("✅ Cortinilla CTA cargada correctamente.")
            except Exception as e:
                print(f"⚠️ Advertencia: No se pudo cargar 'cortinilla_cta.mp3'. Error: {e}")
        # ------------------------------------------

        # --- NUEVO: Cargar la sintonía específica para los bloques temáticos ---
        sinto_bloque_audio = None
        ruta_sinto_bloque = os.path.join(audio_assets_dir, "sinto_bloque.mp3")
        if os.path.exists(ruta_sinto_bloque):
            try:
                sinto_bloque_audio = AudioSegment.from_file(ruta_sinto_bloque)
                print("✅ Sintonía de bloque ('sinto_bloque.mp3') cargada correctamente.")
            except Exception as e:
                print(f"⚠️ Advertencia: No se pudo cargar 'sinto_bloque.mp3'. Error: {e}")
        # --------------------------------------------------------------------
# --- LÓGICA DE CARGA DE TRANSICIONES MODIFICADA (clickrozalen) ---
        print("\n🎵 Cargando músicas de transición universales (clickrozalen)...")
        transiciones = {
            'positivo': {},
            'negativo': {},
            'neutro': {}
        }
        # Mantenemos las constantes de duración, la función agregar_transicion las usará
        SEGMENT_DURATION_MS, FADE_DURATION_MS = 10000, 2000 

        # Pool universal para todos los archivos 'clickrozalen'
        pool_universal = {}
        
        # 1. Definir el patrón de búsqueda específico para tus archivos
        patron_busqueda = "clickrozalen*.mp3"
        ruta_busqueda = os.path.join(audio_assets_dir, patron_busqueda)
        print(f"    -> Buscando archivos que coincidan con '{patron_busqueda}' en '{audio_assets_dir}'...")
        
        files = glob.glob(ruta_busqueda)

        if not files:
            print(f"    ⚠️ ADVERTENCIA: No se encontró ningún archivo de transición con el patrón '{patron_busqueda}'.")
            print(f"    -> Asegúrate de que los archivos están en '{audio_assets_dir}' y se llaman 'clickrozalen...mp3'.")
        
        # 2. Cargar los archivos encontrados
        for f in files:
            try:
                audio = AudioSegment.from_file(f)
            except Exception as e:
                print(f"    ⚠️ Error cargando transición '{f}': {e}")
                continue
            
            # Comprobar si el audio es válido (no está vacío)
            if len(audio) > 0:
                pool_universal[f] = audio
            else:
                print(f"    -> Aviso: Archivo '{f}' está vacío o corrupto. Omitiendo.")

        print(f"    -> {len(pool_universal)} transiciones 'clickrozalen' cargadas en el pool universal.")

        # 3. Asignar el pool universal a todos los sentimientos
        if pool_universal:
            transiciones['positivo'] = pool_universal
            transiciones['negativo'] = pool_universal
            transiciones['neutro'] = pool_universal
            print("    ✅ Pool universal 'clickrozalen' asignado a todos los sentimientos.")
        else:
            print("    -> No se cargaron transiciones. La función 'agregar_transicion' usará silencios.")
        # --- FIN DE LA MODIFICACIÓN ---
        # --------------------------------------------------------------------
        def agregar_transicion(sentimiento: str = 'neutro') -> AudioSegment:
            pool_sentimiento = transiciones.get(sentimiento)
            # Fallback a neutro si no hay transiciones para el sentimiento específico
            if not pool_sentimiento:
                pool_sentimiento = transiciones['neutro']
            
            if not pool_sentimiento: return AudioSegment.silent(duration=1000)
            
            path = random.choice(list(pool_sentimiento.keys()))
            audio = pool_sentimiento[path]
            
            if len(audio) < SEGMENT_DURATION_MS: 
                return audio.fade_in(FADE_DURATION_MS).fade_out(FADE_DURATION_MS)
                
            max_start = len(audio) - SEGMENT_DURATION_MS
            
            # Intentar encontrar un segmento con volumen decente (evitar silencios)
            best_segment = None
            best_dbfs = -float('inf')
            
            for _ in range(10): # 10 intentos
                start = random.randint(0, max_start)
                segmento = audio[start:start+SEGMENT_DURATION_MS]
                
                # Si encontramos un segmento con buen volumen, lo usamos
                if segmento.dBFS > -30: 
                    return segmento.fade_in(FADE_DURATION_MS).fade_out(FADE_DURATION_MS)
                
                # Si no, guardamos el "menos malo" por si acaso
                if segmento.dBFS > best_dbfs:
                    best_dbfs = segmento.dBFS
                    best_segment = segmento
                    
            # Si fallan todos los intentos, devolvemos el mejor encontrado
            return best_segment.fade_in(FADE_DURATION_MS).fade_out(FADE_DURATION_MS)

        print("\n🎤 Ensamblando introducción profesional por segmentos...")
        todos_los_resumenes = [n['resumen'] for n in resumenes_finales]
        contenido_completo_texto = "\n\n- ".join(todos_los_resumenes)

        # Obtener el mensaje de la audiencia antes de generar la introducción,
        # para que la IA pueda tenerlo en cuenta si es necesario para el tono.
        mensaje_del_dia = leer_pregunta_del_dia()

        # NUEVO: Analizar sentimiento general de las noticias
        sentimiento_general = analizar_sentimiento_general_noticias(resumenes_finales)
        print(f"  ✨ Sentimiento general de las noticias del día: {sentimiento_general.upper()}")

        # --- INICIO DE LA NUEVA LÓGICA DE INTRODUCCIÓN UNIFICADA ---
        print("  -> Generando monólogo de inicio unificado con IA...")
        
        # NUEVO: Extraer dato curioso para "El Chisme Culto" (DESACTIVADO POR PETICIÓN DE USUARIO)
        # print("  🕵️‍♀️ Buscando dato curioso para 'El Chisme Culto'...")
        # dato_curioso_json = generar_texto_con_gemini(
        #     mcmcn_prompts.PromptsAnalisis.extraer_dato_curioso(contenido_completo_texto)
        # )
        dato_curioso_gancho = ""
        dato_curioso_resolucion = ""
        
        # try:
        #     if dato_curioso_json:
        #         # Limpiar json por si acaso
        #         dato_curioso_json = dato_curioso_json.replace("```json", "").replace("```", "").strip()
        #         dato_obj = json.loads(dato_curioso_json)
        #         dato_curioso_gancho = dato_obj.get("gancho", "")
        #         dato_curioso_resolucion = dato_obj.get("resolucion", "")
        #         print(f"    ✅ Dato curioso encontrado: {dato_curioso_gancho[:50]}...")
        # except Exception as e:
        #     print(f"    ⚠️ No se pudo extraer dato curioso: {e}")

        # 1. Obtener plantilla base del día para REINTERPRETACIÓN
        print("      🗣️ Obteniendo plantilla base para reinterpretación...")
        dia_semana = datetime.now().weekday()
        saludo_base_raw = mcmcn_prompts.obtener_plantilla_por_dia(dia_semana, mcmcn_prompts.PlantillasSSML.FRASES_SALUDO_POR_DIA)
        
        # --- FIX: Limpiar SSML del saludo base antes de enviarlo al prompt ---
        # Si le pasamos SSML a la IA, tiende a repetirlo en la salida.
        # Al limpiarlo, le damos solo el texto semántico para que lo reinterprete.
        saludo_base = convertir_ssml_a_texto_plano(saludo_base_raw)
        
        # También aseguramos que el CTA esté limpio de etiquetas complejas si las tuviera
        cta_inicio_limpio = convertir_ssml_a_texto_plano(cta_inicio_text)

        # 2. Generar MONÓLOGO UNIFICADO (Saludo reinterpretado + Sumario)
        print("      🧠 Generando monólogo de inicio unificado (reinterpretado)...")
        
        # NUEVO: Obtener efemérides de hoy para enriquecer el saludo
        efemerides_hoy = obtener_efemerides_hoy()
        if efemerides_hoy:
             print(f"      🗓️ Efeméride detectada: {efemerides_hoy[:50]}...")
             
        # NUEVO: Obtener meteo para enriquecer (Retranca)
        datos_meteo_hoy = obtener_pronostico_meteo()
        if datos_meteo_hoy:
             print(f"      ☁️ Meteo obtenida: {datos_meteo_hoy[:40]}...")

        # NUEVO: Obtener deportes (Solo Lunes o si hay noticias relevantes)
        # 0 = Lunes.
        datos_deportes_hoy = ""
        if dia_semana == 0: # Solo comprobar los lunes
             print("      ⚽ Es lunes: Buscando resultados deportivos...")
             datos_deportes_hoy = obtener_resultados_futbol()
             if datos_deportes_hoy:
                 print(f"      🥅 Deportes: {datos_deportes_hoy[:40]}...")
        
        prompt_inicio_unificado = mcmcn_prompts.PromptsCreativos.generar_monologo_inicio_unificado(
            contenido_noticias=contenido_completo_texto,
            texto_cta=cta_inicio_limpio,
            texto_base_saludo=saludo_base,
            dato_efemeride=efemerides_hoy,
            dato_meteo=datos_meteo_hoy,
            dato_deportes=datos_deportes_hoy,
            sentimiento_general=sentimiento_general
        )
        
        texto_monologo_inicio = generar_texto_con_gemini(prompt_inicio_unificado)
        
        # 3. Añadir la sintonía de inicio ANTES del monólogo.
        ruta_sintonia_inicio = os.path.join(AUDIO_ASSETS_DIR, "inicio.mp3")
        if os.path.exists(ruta_sintonia_inicio):
            segmentos_audio.append(AudioSegment.from_file(ruta_sintonia_inicio))
        
        # 4. Limpiar, sintetizar y añadir el monólogo de inicio.
        if texto_monologo_inicio:
            texto_limpio = limpiar_artefactos_ia(texto_monologo_inicio)
            print(f"      ✅ Monólogo de inicio generado: '{texto_limpio[:100]}...'")
            transcript_data.append({'type': 'intro', 'content': texto_limpio})
            
            # Lógica para insertar cortinilla si existe el marcador
            if "[CORTINILLA]" in texto_limpio:
                print("      ✂️ Marcador [CORTINILLA] detectado. Dividiendo audio...")
                partes = texto_limpio.split("[CORTINILLA]")
                
                # Parte 1: Saludo + Resumen
                if partes[0].strip():
                    audio_p1 = sintetizar_ssml_a_audio(f"<speak>{html.escape(partes[0].strip())}</speak>")
                    if audio_p1:
                        segmentos_audio.append(audio_p1)
                
                # Insertar Cortinilla (Clickrozalen)
                print("      🎵 Insertando cortinilla 'clickrozalen'...")
                segmentos_audio.append(agregar_transicion())
                
                # Parte 2: CTA + Adivinanza + Cierre
                if len(partes) > 1 and partes[1].strip():
                    audio_p2 = sintetizar_ssml_a_audio(f"<speak>{html.escape(partes[1].strip())}</speak>")
                    if audio_p2:
                        segmentos_audio.append(audio_p2)
            else:
                # Comportamiento normal si no hay marcador
                monologo_inicio_audio = sintetizar_ssml_a_audio(f"<speak>{html.escape(texto_limpio)}</speak>")
                if monologo_inicio_audio:
                    segmentos_audio.append(monologo_inicio_audio)
        else:
            # Fallback por si la IA falla.
            print("      ⚠️ Fallo en la generación del monólogo. Usando saludo estático.")
            if saludo_base:
                saludo_audio_fallback = sintetizar_ssml_a_audio(saludo_base)
                if saludo_audio_fallback:
                    segmentos_audio.append(saludo_audio_fallback)
        
        # 5. Añadir la primera transición para dar paso a las noticias.
        segmentos_audio.append(agregar_transicion())

        print("\n🎯 Procesando bloques temáticos y noticias para narración...")
        bloques_tematicos = noticias_agrupadas.get('bloques_tematicos', [])
        noticias_individuales = noticias_agrupadas.get('noticias_individuales', [])

        # --- INICIO DE LA NUEVA LÓGICA DE PROCESAMIENTO DE AUDIO ---
        # Se crea una lista plana de tareas para tener control total sobre las transiciones.
        tareas_audio = []
        for bloque in bloques_tematicos:
            # 1. Añadir la introducción del bloque como una tarea.
            if bloque.get('transicion_elegante'):
                tareas_audio.append({'tipo': 'intro_bloque', 'data': bloque})
            # 2. Añadir cada noticia del bloque como una tarea individual.
            for noticia in bloque.get('noticias', []):
                tareas_audio.append({'tipo': 'noticia', 'data': noticia})
        
        # 3. Añadir las noticias individuales.
        for noticia in noticias_individuales:
            tareas_audio.append({'tipo': 'noticia', 'data': noticia})

        # Contar solo las noticias para la inserción del CTA intermedio.
        num_noticias = sum(1 for t in tareas_audio if t['tipo'] == 'noticia')
        punto_insercion_cta = num_noticias // 2 if num_noticias > 0 else -1
        noticias_procesadas = 0

        fecha_actual_str = datetime.now().strftime("%A, %d de %B de %Y")

        # --- INICIO DE LA NUEVA LÓGICA DE PROCESAMIENTO DE AUDIO (MODIFICADA: UNIFICACIÓN TOTAL) ---
        # 1. Procesar TODOS los bloques temáticos como crónicas unificadas
        for bloque in bloques_tematicos:
            print(f"  🎪 Generando crónica unificada para el bloque: '{bloque.get('descripcion_tema')}'")
            
            # Guardamos el número de noticias procesadas ANTES de empezar el bloque
            noticias_antes_del_bloque = noticias_procesadas
            
            # Generar narración unificada
            cronica_unificada_texto = generar_narracion_fluida_bloque(bloque, fecha_actual_str)
            
            if cronica_unificada_texto:
                transcript_data.append({
                    'type': 'block',
                    'title': bloque.get('descripcion_tema', 'Bloque Temático'),
                    'content': cronica_unificada_texto
                }) # <-- Capturar bloque
                
                # --- MODIFICACIÓN: Insertar cortinillas entre noticias del bloque ---
                audio_cronica = AudioSegment.empty()
                # Separamos por párrafos (que la IA ha generado con doble salto de línea)
                parrafos = [p.strip() for p in cronica_unificada_texto.split('\n') if p.strip()]
                
                if len(parrafos) > 1:
                    print(f"      🎵 Insertando cortinillas (clickrozalen) entre {len(parrafos)} noticias del bloque...")
                    for i, parrafo in enumerate(parrafos):
                        # Generamos audio para este párrafo/noticia
                        audio_parrafo = sintetizar_ssml_a_audio(f"<speak>{html.escape(parrafo)}</speak>")
                        if audio_parrafo:
                            audio_cronica += audio_parrafo
                            # Si NO es el último párrafo, añadimos la cortinilla
                            # MODIFICADO: No añadir cortinilla después del primer párrafo (intro)
                            if i < len(parrafos) - 1:
                                if i == 0:
                                    # Después del intro, solo pequeña pausa para respirar
                                    print("      🤫 Silencio breve tras intro de bloque (sin cortinilla)...")
                                    audio_cronica += AudioSegment.silent(duration=800) 
                                else:
                                    # Entre noticias normales, sí ponemos cortinilla
                                    audio_cronica += agregar_transicion()
                                    audio_cronica += AudioSegment.silent(duration=600)
                else:
                    # Fallback: Si solo hay 1 párrafo, lo hacemos todo junto
                    audio_cronica = sintetizar_ssml_a_audio(f"<speak>{html.escape(cronica_unificada_texto)}</speak>")
                # ------------------------------------------------------------------
                sentimiento_bloque = analizar_sentimiento_general_noticias(bloque.get('noticias', []))
                
                if audio_cronica:
                    segmentos_audio.append(audio_cronica)
                    segmentos_audio.append(agregar_transicion(sentimiento_bloque))
                    
                    # Sumamos todas las noticias del bloque al contador
                    noticias_en_bloque = len(bloque.get('noticias', []))
                    noticias_procesadas += noticias_en_bloque

                    # Comprobamos si debemos insertar el CTA intermedio
                    # Lo insertamos DESPUÉS del bloque si cruzamos el umbral
                    if noticias_antes_del_bloque < punto_insercion_cta <= noticias_procesadas and cta_intermedio_text:
                        print("\n🎯 Insertando CTA intermedio (tras bloque temático)...")
                        
                        # FIX: Limpiar SSML del CTA intermedio
                        cta_intermedio_limpio = convertir_ssml_a_texto_plano(cta_intermedio_text)
                        
                        prompt_cta_intermedio = mcmcn_prompts.PromptsCreativos.reescritura_cta_creativa(
                            cta_intermedio_limpio,
                            tono_actual="informativo y sugerente"
                        )
                        texto_cta_reescrito = generar_texto_con_gemini(prompt_cta_intermedio)
                        if texto_cta_reescrito:
                            cta_intermedio_audio = sintetizar_ssml_a_audio(f"<speak>{html.escape(texto_cta_reescrito)}</speak>")
                            if cta_intermedio_audio:
                                # Insertamos: [Cortinilla] -> [CTA] -> [Transición existente]
                                # 1. Insertamos el CTA antes de la última transición (index -1)
                                segmentos_audio.insert(-1, cta_intermedio_audio)
                                
                                # 2. Insertamos la cortinilla ANTES del CTA (index -2 ahora)
                                if cortinilla_cta_audio:
                                    segmentos_audio.insert(-2, cortinilla_cta_audio)
                                else:
                                    # Si no hay cortinilla específica, usamos una transición del pool
                                    segmentos_audio.insert(-2, agregar_transicion())
                                    
                        print("    ✅ CTA intermedio procesado e insertado (con cortinilla previa).")
            else:
                print("      ⚠️ Fallo al generar crónica unificada. Saltando bloque.")

        # 2. Procesar noticias individuales restantes
        for noticia in noticias_individuales:
            audio_noticia, texto_noticia = _generar_y_cachear_audio_noticia(noticia, fecha_actual_str) # <-- Unpack tuple
            if audio_noticia:
                transcript_data.append({
                    'type': 'news',
                    'title': noticia.get('fuente', 'Noticia'),
                    'content': texto_noticia
                }) # <-- Capturar noticia
                sentimiento_noticia = noticia.get('sentimiento', 'neutro')
                segmentos_audio.append(audio_noticia)
                segmentos_audio.append(agregar_transicion(sentimiento_noticia))

        # --- FASE 2.5: Procesando sección de la audiencia ---
        print("\n--- FASE 2.5: Procesando sección de la audiencia ---")
        # mensaje_del_dia ya se obtuvo al inicio de la FASE 2

        if mensaje_del_dia:
            autor = mensaje_del_dia.get('autor', 'un oyente')
            texto_mensaje = mensaje_del_dia.get('texto', '')
            
            print(f"  -> Generando segmento integrado para el mensaje de: {autor}")

            # 1. Llamamos al NUEVO prompt unificado que genera TODO el segmento, pasando el sentimiento general
            prompt_segmento = mcmcn_prompts.PromptsCreativos.generar_segmento_audiencia_integrado(
                autor, texto_mensaje,
                sentimiento_general=sentimiento_general # <-- PASAMOS SENTIMIENTO
            )
            texto_segmento_completo = generar_texto_con_gemini(prompt_segmento)
            
            if texto_segmento_completo:
                # 2. Limpiamos y sintetizamos el segmento completo en un único paso
                segmento_limpio = limpiar_artefactos_ia(texto_segmento_completo)
                print(f"      ✅ Segmento de audiencia generado: '{segmento_limpio[:90]}...'")
                transcript_data.append({'type': 'audience', 'content': segmento_limpio}) # <-- Capturar audiencia
                
                segmento_ssml = f"<speak>{html.escape(segmento_limpio)}</speak>"
                segmento_audio = sintetizar_ssml_a_audio(segmento_ssml)
                
                if segmento_audio:
                    # 3. Añadimos el audio del segmento y una transición DESPUÉS
                    segmentos_audio.append(segmento_audio)
                    segmentos_audio.append(agregar_transicion())
            else:
                print("      ⚠️ No se pudo generar el segmento de la audiencia.")
        else:
            print("  -> No hay mensaje de la audiencia programado para hoy.")


        # --- FASE 2.6: Audio Programado (Mirra/Colaboradores) ---
        print("\n--- FASE 2.6: Buscando audios programados por fecha ---")
        fecha_prefijo = datetime.now().strftime("%Y%m%d") + "_"
        dir_programados = os.path.join(AUDIO_ASSETS_DIR, "programados")
        
        # Buscar archivo que empiece por el prefijo
        archivo_programado = None
        if os.path.exists(dir_programados):
            for f in os.listdir(dir_programados):
                # Soporte para MP3, WAV y OGG
                if f.startswith(fecha_prefijo) and f.lower().endswith((".mp3", ".wav", ".ogg")):
                    archivo_programado = os.path.join(dir_programados, f)
                    print(f"  🎙️  Audio programado encontrado: {f}")
                    break
        else:
             # Crear directorio si no existe para facilitar uso futuro
             os.makedirs(dir_programados, exist_ok=True)

        if archivo_programado:
             try:
                 with open(archivo_programado, "rb") as f_audio:
                     audio_bytes = f_audio.read()
                 
                 # Determinar mimetype según extensión
                 ext = os.path.splitext(archivo_programado)[1].lower()
                 mime_type = "audio/mp3" # default
                 if ext == ".wav": mime_type = "audio/wav"
                 elif ext == ".ogg": mime_type = "audio/ogg"
                 
                 print(f"  -> Generando intro y respuesta para el audio programado ({mime_type}) con Gemini...")
                 prompt_audio_prog = """
                 Escucha este audio que se va a emitir en el podcast. 
                 Genera dos textos breves para la presentadora, Dorotea. 
                 
                 1) INTRO: Una frase para dar paso al audio sin revelar todo el contenido, solo creando expectación (max 20 palabras).
                 2) OUTRO: Una respuesta ingeniosa, empática o comentario sobre lo escuchado (max 30 palabras).
                 
                 Responde EXCLUSIVAMENTE en formato JSON: 
                 { "intro": "...", "outro": "..." }
                 """
                 
                 resp_audio_prog = generar_texto_multimodal_audio_con_gemini(prompt_audio_prog, audio_bytes, mime_type=mime_type)
                 
                 intro_txt = ""
                 outro_txt = ""
                 
                 if resp_audio_prog:
                     # Limpiar JSON
                     json_limpio = resp_audio_prog
                     if "```" in json_limpio:
                          start = json_limpio.find('{')
                          end = json_limpio.rfind('}')
                          if start != -1 and end != -1:
                               json_limpio = json_limpio[start:end+1]
                     
                     try:
                         data_prog = json.loads(json_limpio)
                         intro_txt = data_prog.get("intro", "")
                         outro_txt = data_prog.get("outro", "")
                     except:
                         print("      ⚠️ Error parseando JSON de audio programado.")
                 
                 # Si falla la IA, usamos genéricos
                 if not intro_txt: intro_txt = "Y ahora, escuchemos este audio que nos han enviado."
                 if not outro_txt: outro_txt = "Interesante aporte. ¡Gracias por compartirlo!"

                 # Generar Audios
                 print(f"      ✅ Intro generada: {intro_txt}")
                 print(f"      ✅ Consigna generada: {outro_txt}")
                 
                 transcript_data.append({'type': 'scheduled_audio_intro', 'content': intro_txt})
                 
                 audio_intro_prog = sintetizar_ssml_a_audio(f"<speak>{html.escape(intro_txt)}</speak>")
                 audio_file_prog = AudioSegment.from_file(archivo_programado)
                 audio_outro_prog = sintetizar_ssml_a_audio(f"<speak>{html.escape(outro_txt)}</speak>")
                 
                 if audio_intro_prog and audio_file_prog and audio_outro_prog:
                      # Insertar: Transición -> Intro -> Audio -> Outro -> Transición
                      segmentos_audio.append(agregar_transicion())
                      segmentos_audio.append(audio_intro_prog)
                      segmentos_audio.append(audio_file_prog)
                      
                      transcript_data.append({'type': 'scheduled_audio_content', 'content': '[Audio Programado Reproducido]'})
                      
                      segmentos_audio.append(audio_outro_prog)
                      transcript_data.append({'type': 'scheduled_audio_outro', 'content': outro_txt})
                      
                      segmentos_audio.append(agregar_transicion())
                      print("      ✅ Bloque de audio programado insertado correctamente.")

             except Exception as e:
                 print(f"      ❌ Error procesando audio programado: {e}")

        else:
             print("  -> No se encontraron audios programados para hoy.")


        print("\n--- FASE 3: Generando cierre del podcast ---")

        # --- INICIO DE LA NUEVA LÓGICA DE CIERRE UNIFICADO ---
        print("  -> Generando monólogo de cierre unificado (resumen + despedida)...")
        
        # 1. Preparar el contexto con los temas tratados para la IA.
        contexto_cierre = []
        for bloque in noticias_agrupadas.get('bloques_tematicos', []):
            contexto_cierre.append(bloque.get('descripcion_tema', 'varios temas'))
        for noticia in noticias_agrupadas.get('noticias_individuales', []):
            contexto_cierre.append(noticia.get('resumen')[:80] + "...")
        
        # 2. Obtener plantilla base de despedida y firma para REINTERPRETACIÓN
        print("      🗣️ Obteniendo plantilla base de despedida y firma...")
        dia_semana = datetime.now().weekday()
        despedida_base_raw = mcmcn_prompts.obtener_plantilla_por_dia(dia_semana, mcmcn_prompts.PlantillasSSML.FRASES_CIERRE_POR_DIA)
        firma_base_raw = mcmcn_prompts.obtener_plantilla_por_dia(dia_semana, mcmcn_prompts.PlantillasSSML.FRASES_FIRMA_FINAL_POR_DIA)
        
        # --- FIX: Limpiar SSML de despedida y firma ---
        despedida_base = convertir_ssml_a_texto_plano(despedida_base_raw)
        firma_base = convertir_ssml_a_texto_plano(firma_base_raw)
        
        # Limpiar CTA cierre
        cta_cierre_limpio = convertir_ssml_a_texto_plano(cta_cierre_text)

        # 3. Llamar al nuevo prompt unificado que genera todo el monólogo de cierre.
        # SELECCIONAMOS 3 temas/noticias ALEATORIOS para dar variedad y brevedad.
        if len(contexto_cierre) > 3:
            contexto_seleccionado = random.sample(contexto_cierre, 3)
        else:
            contexto_seleccionado = contexto_cierre
            
        contexto_cierre_str = "\n".join(contexto_seleccionado) 
        
        prompt_cierre_unificado = mcmcn_prompts.PromptsCreativos.generar_monologo_cierre_unificado(
            contexto=contexto_cierre_str,
            texto_cta=cta_cierre_limpio,
            texto_base_despedida=despedida_base,
            texto_firma=firma_base,
            # dato_curioso_resolucion=dato_curioso_resolucion, # DESACTIVADO
            sentimiento_general=sentimiento_general
        )
        
        texto_monologo_cierre = generar_texto_con_gemini(prompt_cierre_unificado)
        
        # 4. Limpiar, sintetizar y añadir el monólogo de cierre.
        if texto_monologo_cierre:
            texto_limpio = limpiar_artefactos_ia(texto_monologo_cierre)
            print(f"      ✅ Monólogo final generado: '{texto_limpio[:100]}...'")
            transcript_data.append({'type': 'outro', 'content': texto_limpio}) # <-- Capturar cierre
            monologo_cierre_audio = sintetizar_ssml_a_audio(f"<speak>{html.escape(texto_limpio)}</speak>")
            if monologo_cierre_audio:
                segmentos_audio.append(monologo_cierre_audio)
        else:
            # Fallback por si la IA falla.
            print("      ⚠️ Fallo en la generación del monólogo. Usando despedida estática.")
            if despedida_base:
                despedida_audio_fallback = sintetizar_ssml_a_audio(despedida_base)
                if despedida_audio_fallback:
                    segmentos_audio.append(despedida_audio_fallback)

        # 4. Añadir la sintonía de cierre DESPUÉS del monólogo.
        ruta_sintonia_cierre = os.path.join(AUDIO_ASSETS_DIR, "cierre.mp3")
        if os.path.exists(ruta_sintonia_cierre):
            segmentos_audio.append(AudioSegment.from_file(ruta_sintonia_cierre))
            
        # 5. BONUS: Comentario Post-Créditos (Engage)
        print("      🎬 Generando comentario post-créditos (engage)...")
        try:
             # Usamos el contexto de cierre para que comente sobre algo real
             prompt_comentario = mcmcn_prompts.PromptsCreativos.generar_comentario_post_creditos(contexto_cierre_str)
             texto_comentario = generar_texto_con_gemini(prompt_comentario)
             
             if texto_comentario:
                 texto_comentario = limpiar_artefactos_ia(texto_comentario)
                 print(f"      😉 Comentario post-créditos: '{texto_comentario}'")
                 
                 # 2 segundos de silencio antes
                 silencio_extra = AudioSegment.silent(duration=2000)
                 segmentos_audio.append(silencio_extra)
                 
                 # Audio del comentario (volumen suave)
                 audio_comentario = sintetizar_ssml_a_audio(f"<speak><prosody volume='soft'>{html.escape(texto_comentario)}</prosody></speak>")
                 if audio_comentario:
                      segmentos_audio.append(audio_comentario)
        except Exception as e:
             print(f"      ⚠️ No se pudo generar comentario post-créditos: {e}")

        # FASE 4: ENSAMBLAJE INTELIGENTE (BASADO EN TAMAÑO)
        # ============================================================
        print("\n--- FASE 4: Ensamblando y masterizando el podcast final ---")

        # Calcular duración total para decidir método
        duracion_total_seg = sum(len(s) for s in segmentos_audio if s) / 1000
        print(f"  📊 Duración total estimada: {duracion_total_seg / 60:.1f} minutos")

        # Silencio inicial
        podcast_final = AudioSegment.silent(duration=500)

        # Método adaptativo según duración
        if duracion_total_seg < 1200:  # Menos de 20 minutos
            print("  ⚡ Usando ensamblaje directo (podcast corto)")
            for segmento in segmentos_audio:
                if segmento:
                    podcast_final += segmento
        else:
            print("  🔧 Usando ensamblaje por lotes (podcast largo)")
            BATCH_SIZE = 8
            
            for i in range(0, len(segmentos_audio), BATCH_SIZE):
                batch = segmentos_audio[i:i + BATCH_SIZE]
                for segmento in batch:
                    if segmento:
                        podcast_final += segmento
                
                # Liberar memoria cada 3 lotes
                if (i // BATCH_SIZE) % 3 == 0:
                    gc.collect()
                
                print(f"     Progreso: {min(i + BATCH_SIZE, len(segmentos_audio))}/{len(segmentos_audio)} segmentos")

        print(f"  ✅ Ensamblaje completado")

        # Masterizar
        podcast_masterizado = masterizar_a_lufs(podcast_final, TARGET_LUFS)

        # Exportar
        nombre_podcast_final = os.path.join(output_dir, f"podcast_completo_{timestamp}.mp3")
        podcast_masterizado.export(nombre_podcast_final, format="mp3", bitrate=BITRATE)
        
        # Generar transcripción HTML
        generar_html_transcripcion(transcript_data, output_dir, timestamp) # <-- Generar HTML

        print(f"\n🎉 ¡Podcast generado con éxito! Archivo: {nombre_podcast_final}")


    except FileNotFoundError as e:
        print(f"Error: Archivo no encontrado - {e}.")
        sys.exit(1)
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Script de generación de podcast Micomicona")
    parser.add_argument("--preview", action="store_true", help="Solo generar archivo de previsión de noticias, sin audios.")
    parser.add_argument("--only-special", action="store_true", help="Solo procesar episodios especiales (EE_*) sin generar el podcast diario.")
    parser.add_argument("--skip-special", action="store_true", help="Saltar la verificación y generación de episodios especiales automáticos.")
    parser.add_argument("--file-list", nargs='+', help="Lista específica de archivos EE_*.txt a procesar (ignora búsqueda automática).")
    parser.add_argument("--from-json", help="Ruta al archivo JSON con noticias seleccionadas manualmente.")
    args = parser.parse_args()

    # Cargar configuración para obtener el archivo de feeds
    config_app = CONFIG
    archivo_feeds = config_app.get('generation_config', {}).get('feeds_file', 'feeds.txt')
    
    if args.only_special:
        print("🚀 Modo: Solo Episodios Especiales. Saltando generación del noticiero diario.")
    elif args.from_json:
        print(f"🔄 Modo: Generando podcast desde selección manual ({args.from_json})")
        procesar_feeds_google(archivo_feeds, min_items=20, archivo_entrada_json=args.from_json)
    elif args.preview:
        print(f"🔮 Modo: Preview de noticias (sin audio)")
        procesar_feeds_google(archivo_feeds, min_items=20, solo_preview=True)
    else:
        print(f"🚀 Modo: Generación automática estándar usando {archivo_feeds}")
        procesar_feeds_google(archivo_feeds, min_items=20)

    # ---------------------------------------------------------
    # AUTOMATIZACIÓN DE EPISODIOS ESPECIALES (EE_*.txt)
    # ---------------------------------------------------------
    # Busca archivos que empiecen por EE_ y genera episodios independientes.
    if not args.preview and not args.skip_special: # Solo generar si no estamos en preview ni se ha pedido saltar
        print("\n🔎 Buscando guiones de Episodios Especiales automáticos (EE_*.txt)...")
        
        if args.file_list:
             ee_files = args.file_list
             print(f"  -> Usando lista manual de archivos: {ee_files}")
        else:
             ee_files = glob.glob("EE_*.txt")
        
        if ee_files:
            print(f"  -> Se han encontrado {len(ee_files)} guiones especiales.")
            for script_file in ee_files:
                print(f"  🎙️  Procesando: {script_file}")
                
                try:
                    with open(script_file, 'r', encoding='utf-8') as f:
                        guion_content = f.read()
                    
                    if guion_content.strip():
                        # Generar carpeta de salida compatible con el historial (podcast_apg_...)
                        timestamp_folder = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_dir = f"podcast_apg_ESPECIAL_{timestamp_folder}"
                        os.makedirs(output_dir, exist_ok=True)
                        print(f"     📁 Carpeta destino: {output_dir}")

                        # Generar nombre de salida:
                        base_name = os.path.splitext(script_file)[0]
                        output_ee = os.path.join(output_dir, f"{base_name}.mp3")
                        
                        # Usar ruta absoluta
                        output_path_ee_abs = os.path.abspath(output_ee)
                        
                        result_path = generar_episodio_especial(guion_content, output_path_ee_abs)
                        
                        if os.path.exists(result_path):
                            print(f"     ✅ Episodio especial generado: {output_ee}")
                            # Mover también el guion original procesado a la carpeta
                            processed_name = os.path.join(output_dir, f"{script_file}.processed")
                            os.rename(script_file, processed_name)
                            print(f"     -> Archivo procesado movido a: {processed_name}")
                        else:
                            print(f"     ❌ Error: No se generó el archivo de audio para {script_file}")
                    else:
                        print(f"     ⚠️ El archivo {script_file} está vacío.")
                        
                except Exception as e:
                    print(f"     ❌ Error procesando {script_file}: {e}")
        else:
            print("  -> No se encontraron guiones especiales (EE_*.txt).")