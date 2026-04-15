from typing import List, Dict, Any, Tuple
import os
import json
import sys
from datetime import datetime, timedelta
import feedparser

from src.agents.base import BaseAgent
from src.config.settings import CONFIG, MIN_WORDS_FOR_AUDIO
from src.utils.caching import calculate_hash
from src.core.text_processing import (
    reparar_codificacion, preprocesar_texto_para_fechas,
    limpiar_html, limpiar_artefactos_ia, reemplazar_urls_por_mencion,
    stable_text_hash
)
from src.core.geography import obtener_provincia, obtener_info_gal
from src.web_scraper import extract_first_external_link, fetch_article_text
from src.llm_utils import generar_texto_con_gemini
from src.calendar_utils import obtener_festividades_contexto
from src.monitoring import logger
from mcmcn_prompts import PromptsAnalisis

# Se asume que las funciones de utilidad importadas a continuación
# son llamadas desde dorototal.py en su forma original:
from dorototal import parsear_fecha_segura, extraer_nombre_de_url, detectar_duplicados_y_similares, identificar_fuente_original, extraer_localidad_con_ia, es_noticia_valida

class ResearcherAgent(BaseAgent):
    """
    Agente encargado de la Fase 1:
    Recopilar feeds RSS, parsear, filtrar por ventana de tiempo,
    extraer enlaces externos, y resumir noticias con IA.
    """

    def __init__(self, name: str = "ResearcherAgent"):
        super().__init__(name=name)

    def execute(self, feeds_file: str, idioma_destino: str = 'es',
                window_hours_override: int = None, max_items_override: int = None,
                archivo_entrada_json: str = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:

        noticias_candidatas_totales = []
        noticias_descartadas = []

        # --- MODO 1: CARGAR DESDE JSON ---
        if archivo_entrada_json:
            print(f"📂 Cargando noticias seleccionadas desde: {archivo_entrada_json}")
            try:
                with open(archivo_entrada_json, 'r', encoding='utf-8') as f:
                    noticias_candidatas_totales = json.load(f)
                    for n in noticias_candidatas_totales:
                        if isinstance(n['fecha'], str):
                            try:
                                n['fecha'] = datetime.fromisoformat(n['fecha'])
                            except ValueError:
                                n['fecha'] = datetime.now()
            except Exception as e:
                print(f"❌ Error leyendo JSON de entrada: {e}")
                sys.exit(1)
        else:
            # --- MODO 2: RSS ---
            logger.step("Lectura de Feeds RSS", "RUNNING")
            with open(feeds_file, 'r', encoding='utf-8') as f:
                feeds_urls = [url.strip() for url in f.read().replace(',', '\n').splitlines() if url.strip()]

            if not feeds_urls:
                print(f"Advertencia: El archivo de feeds '{feeds_file}' está vacío.")
                sys.exit(1)

            gen_config = CONFIG.get('generation_config', {})
            window_hours = window_hours_override if window_hours_override is not None else int(gen_config.get('news_window_hours', 24))
            max_noticias = max_items_override if max_items_override is not None else int(gen_config.get('max_news_items', 50))

            print(f"      ⚙️  Ventana temporal: {window_hours}h | Máx. noticias: {max_noticias}")
            limite_temporal = datetime.now() - timedelta(hours=window_hours)

            for url in feeds_urls:
                try:
                    logger.info(f"Leyendo feed: {url}")
                    feed = feedparser.parse(url)

                    sitio = feed.feed.get('title', '').replace(" on Facebook", "").strip()
                    if not sitio:
                        link_feed = feed.feed.get('link', '') or url
                        sitio = extraer_nombre_de_url(link_feed)
                    for entry in feed.entries:
                        fecha_pub = parsear_fecha_segura(entry)
                        if fecha_pub < limite_temporal:
                            continue
                        contenido = entry.get('summary', entry.get('description', ''))
                        if not contenido:
                            noticias_descartadas.append({
                                "titulo": entry.get('title', 'Sin título'),
                                "sitio": sitio,
                                "motivo": "Contenido/summary vacío"
                            })
                            continue

                        contenido = reparar_codificacion(contenido)
                        titulo_reparado = reparar_codificacion(entry.get('title', ''))
                        if not titulo_reparado or titulo_reparado == "None" or len(titulo_reparado) < 3:
                             words = contenido.split()[:8]
                             titulo_reparado = " ".join(words) + "..." if words else "Noticia sin título"

                        noticia_hash = stable_text_hash(contenido)
                        noticias_candidatas_totales.append({
                            'sitio': sitio,
                            'contenido_rss': contenido,
                            'fecha': fecha_pub,
                            'hash': noticia_hash,
                            'titulo': titulo_reparado,
                            'link': entry.get('link', '')
                        })
                except Exception as e:
                    print(f"Advertencia: No se pudo procesar el feed '{url}'. Error: {e}")

        if not noticias_candidatas_totales:
             return [], [], noticias_descartadas

        noticias_candidatas_totales.sort(key=lambda x: x['fecha'], reverse=True)

        if not archivo_entrada_json:
            if len(noticias_candidatas_totales) > max_noticias:
                excedentes = noticias_candidatas_totales[max_noticias:]
                for ne in excedentes:
                    noticias_descartadas.append({
                        "titulo": ne.get('titulo', 'Sin título'),
                        "sitio": ne.get('sitio', 'Desconocido'),
                        "motivo": f"Fuera del límite máximo ({max_noticias} noticias)"
                    })
                noticias_candidatas_totales = noticias_candidatas_totales[:max_noticias]

        if archivo_entrada_json:
            noticias_seleccionadas = noticias_candidatas_totales
        else:
            noticias_seleccionadas = detectar_duplicados_y_similares(noticias_candidatas_totales, noticias_descartadas)

        resumenes_noticiero = []
        resumenes_agenda = []

        for noticia in noticias_seleccionadas:
            noticia_hash = noticia.get('hash') or noticia.get('id')
            if not noticia_hash:
                noticia_hash = stable_text_hash(noticia.get('contenido_rss', '') or noticia.get('texto', ''))

            es_noticia_breve = False
            if 'texto' not in noticia and 'contenido_rss' in noticia:
                contenido_base = noticia['contenido_rss']
                texto_externo = ""
                enlace_externo = extract_first_external_link(contenido_base)
                if enlace_externo:
                    scraped_text = fetch_article_text(enlace_externo)
                    if scraped_text:
                        texto_externo = f"\n\n[FUENTE ENLAZADA ({enlace_externo})]:\n{scraped_text[:2000]}"
                noticia['texto'] = limpiar_html(contenido_base) + texto_externo

            texto_origen = noticia.get('texto', '')
            texto_crudo = preprocesar_texto_para_fechas(texto_origen) if texto_origen else ""
            fuente_original = identificar_fuente_original(texto_crudo) if texto_crudo else ""
            if fuente_original == "PROPIA":
                fuente_original = noticia.get('sitio', '') or "la organización"

            resumen = None
            entidades_clave = []
            sentimiento_noticia = 'neutro'
            es_agenda = False
            fecha_evento = ""

            if 'resumen' in noticia and noticia.get('resumen'):
                resumen = noticia['resumen']
                entidades_clave = noticia.get('entidades_clave', [])
                es_agenda = noticia.get('es_agenda', False)
                fecha_evento = noticia.get('fecha_evento', '')
            else:
                prompt_ia = PromptsAnalisis.procesamiento_noticia_completo(
                    texto_crudo, fuente_original, idioma_destino, obtener_festividades_contexto()
                )
                respuesta_json = generar_texto_con_gemini(prompt_ia)
                try:
                    start_j = respuesta_json.find('{')
                    end_j = respuesta_json.rfind('}')
                    if start_j != -1 and end_j != -1:
                        data = json.loads(respuesta_json[start_j:end_j+1])
                        resumen = data.get('resumen', '')
                        entidades_clave = data.get('entidades_clave', [])
                        sentimiento_noticia = data.get('sentimiento', 'neutro')
                        es_agenda = data.get('es_agenda', False)
                        fecha_evento = data.get('fecha_evento', '')
                    else:
                        raise ValueError("No se detectó un JSON válido")
                except Exception as e:
                    noticias_descartadas.append({
                        "titulo": noticia.get('titulo', 'Sin Título'),
                        "sitio": noticia.get('sitio', 'Desconocido'),
                        "motivo": f"Fallo LLM Estructurado: {e}"
                    })
                    continue

            if not resumen:
                continue

            texto_limpio_resumen = limpiar_artefactos_ia(resumen)
            texto_limpio_resumen = reemplazar_urls_por_mencion(texto_limpio_resumen)

            es_manual = 'resumen' in noticia and noticia.get('resumen')
            if not es_manual and len(texto_limpio_resumen.split()) < MIN_WORDS_FOR_AUDIO:
                continue

            sitio_safe = noticia.get('sitio', '')
            fuente_final = f"{sitio_safe} (repost de {fuente_original})" if (fuente_original and fuente_original != "PROPIA" and sitio_safe) else (fuente_original or sitio_safe)
            localidad_extraida = extraer_localidad_con_ia(texto_crudo)

            nueva_noticia_procesada = {
                'fuente': fuente_final,
                'resumen': texto_limpio_resumen,
                'titulo': noticia.get('titulo', ''),
                'sitio': noticia.get('sitio', ''),
                'fecha': noticia['fecha'].strftime("%Y-%m-%d"),
                'id': noticia_hash,
                'es_breve': es_noticia_breve,
                'entidades_clave': entidades_clave,
                'sentimiento': sentimiento_noticia,
                'localidad': localidad_extraida,
                'es_agenda': es_agenda,
                'fecha_evento': fecha_evento
            }

            if es_agenda:
                resumenes_agenda.append(nueva_noticia_procesada)
            else:
                resumenes_noticiero.append(nueva_noticia_procesada)

        return resumenes_noticiero, resumenes_agenda, noticias_descartadas
