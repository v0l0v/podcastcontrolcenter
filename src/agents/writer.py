import json
import os
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime
from pydub import AudioSegment

from src.agents.base import BaseAgent
from src.config.settings import AUDIO_ASSETS_DIR
from src.utils.caching import calculate_hash, get_cached_content, cache_content
from src.core.text_processing import (
    convertir_ssml_a_texto_plano, limpiar_artefactos_ia, normalize_text_for_similarity, composite_similarity
)
from src.llm_utils import generar_texto_con_gemini
from src.monitoring import logger
import mcmcn_prompts

# Funciones extraídas de dorototal que usamos aquí
from dorototal import (
    analizar_sentimiento_general_noticias,
    obtener_pueblo_aleatorio,
    debe_interpretar_cta,
    _get_cta_text,
    detectar_duplicados_y_similares,
    cluster_by_dynamic_keyphrases,
    agrupacion_simple_por_palabras_clave,
    _enforce_unique_assignment,
    leer_pregunta_del_dia
)
from src.calendar_utils import obtener_efemerides_hoy, obtener_fecha_humanizada_es, obtener_oficio_del_dia
from src.weather_utils import obtener_pronostico_meteo
from src.sports_utils import obtener_resultados_futbol
from src.humanization import obtener_toque_humano
from costumbrismo import obtener_saludo_aleatorio

MIN_NEWS_PER_BLOCK = 2

class WriterAgent(BaseAgent):
    """
    Agente encargado de la Fase 2:
    Agrupar noticias por temas (con fallback dinámico),
    generar crónicas fluidas para cada bloque, y
    escribir el guion final (Intro, Bloques, Outro).
    """
    def __init__(self, name: str = "WriterAgent"):
        super().__init__(name=name)

    def execute(self, resumenes_noticiero: List[Dict[str, Any]], resumenes_agenda: List[Dict[str, Any]], solo_preview: bool = False) -> Dict[str, Any]:
        print("\n--- FASE 2: Agrupación y Guionizado ---")

        # Agrupar Noticiero
        noticias_agrupadas_noticiero = self._agrupar_noticias_por_temas_mejorado(resumenes_noticiero, es_agenda=False)
        if noticias_agrupadas_noticiero.get('bloques_tematicos'):
            noticias_agrupadas_noticiero['bloques_tematicos'] = self._fusionar_bloques_similares(noticias_agrupadas_noticiero['bloques_tematicos'])

        # Agrupar Agenda
        noticias_agrupadas_agenda = self._agrupar_noticias_por_temas_mejorado(resumenes_agenda, es_agenda=True)
        if noticias_agrupadas_agenda.get('bloques_tematicos'):
            noticias_agrupadas_agenda['bloques_tematicos'] = self._fusionar_bloques_similares(noticias_agrupadas_agenda['bloques_tematicos'])

        # Fusionar Resultados (Noticiero va antes que la Agenda)
        noticias_agrupadas = {
            'bloques_tematicos': noticias_agrupadas_noticiero.get('bloques_tematicos', []) + noticias_agrupadas_agenda.get('bloques_tematicos', []),
            'noticias_individuales': noticias_agrupadas_noticiero.get('noticias_individuales', []) + noticias_agrupadas_agenda.get('noticias_individuales', [])
        }

        if solo_preview:
             return noticias_agrupadas # Preview stops here mostly, handled by caller

        # --- GENERACIÓN DEL MONÓLOGO / GUION (Texto) ---
        print("\n🎤 Generando guion y crónicas por bloques...")
        todos_los_resumenes = [n['resumen'] for n in (resumenes_noticiero + resumenes_agenda)]
        contenido_completo_texto = "\n\n- ".join(todos_los_resumenes)

        sentimiento_general = analizar_sentimiento_general_noticias((resumenes_noticiero + resumenes_agenda))
        print(f"  ✨ Sentimiento general: {sentimiento_general.upper()}")

        texto_monologo_inicio = self._generar_intro(contenido_completo_texto, sentimiento_general, noticias_agrupadas)

        # Generar narración fluida por cada bloque (texto)
        bloques_tematicos_narrados = []
        for bloque in noticias_agrupadas.get('bloques_tematicos', []):
            texto_bloque = self._generar_narracion_fluida_bloque(bloque, es_agenda="agenda" in str(bloque.get('tema','')).lower())
            bloques_tematicos_narrados.append({
                'tema': bloque.get('tema'),
                'texto_narrado': texto_bloque,
                'noticias': bloque.get('noticias', [])
            })

        return {
            'texto_intro': texto_monologo_inicio,
            'bloques_narrados': bloques_tematicos_narrados,
            'noticias_individuales': noticias_agrupadas.get('noticias_individuales', []),
            'sentimiento_general': sentimiento_general,
            'agrupadas_raw': noticias_agrupadas
        }

    def _generar_intro(self, contenido_completo_texto: str, sentimiento_general: str, noticias_agrupadas: dict) -> str:
        dia_semana = datetime.now().weekday()
        dia_semana_str = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"][dia_semana]

        saludo_base_raw = mcmcn_prompts.obtener_plantilla_por_dia(dia_semana, mcmcn_prompts.PlantillasSSML.FRASES_SALUDO_POR_DIA)
        saludo_base = convertir_ssml_a_texto_plano(saludo_base_raw)

        cta_inicio_text, _, _ = _get_cta_text("inicio", dia_semana_str)
        cta_inicio_limpio = convertir_ssml_a_texto_plano(cta_inicio_text)

        efemerides_hoy = obtener_efemerides_hoy()
        datos_meteo_obj = obtener_pronostico_meteo()
        datos_meteo_hoy = datos_meteo_obj.get("texto", "") if isinstance(datos_meteo_obj, dict) else str(datos_meteo_obj or "")
        datos_meteo_dict = datos_meteo_obj if isinstance(datos_meteo_obj, dict) else {}
        dato_oficio_hoy = obtener_oficio_del_dia()
        datos_deportes_hoy = obtener_resultados_futbol()
        fecha_actual_str = obtener_fecha_humanizada_es()

        num_noticias_real = len(noticias_agrupadas.get('noticias_individuales', [])) + sum(len(b.get('noticias', [])) for b in noticias_agrupadas.get('bloques_tematicos', []))
        contexto_humanizacion = obtener_toque_humano(num_noticias_real, datos_meteo_dict)
        instruccion_humanizacion = contexto_humanizacion.get("humanizacion_instruccion", "")

        saludo_costumbrista = obtener_saludo_aleatorio(provincia="General_Manchega", momento_dia="manana")

        intro_inputs = {
            "contenido": contenido_completo_texto,
            "cta": cta_inicio_limpio,
            "saludo_base": saludo_base,
            "efemerides": efemerides_hoy,
            "meteo": datos_meteo_hoy,
            "deportes": datos_deportes_hoy,
            "oficio": dato_oficio_hoy,
            "semtimiento": sentimiento_general,
            "fecha": fecha_actual_str,
            "humanizacion": instruccion_humanizacion,
            "costumbrismo": saludo_costumbrista,
            "pueblo_aleatorio": "dynamic"
        }
        intro_hash = calculate_hash(intro_inputs)
        cached_intro_data = get_cached_content(f"intro_{intro_hash}")
        texto_monologo_inicio = ""

        if cached_intro_data and cached_intro_data.get('text'):
             texto_monologo_inicio = cached_intro_data.get('text')
        else:
            interpr_inicio = debe_interpretar_cta("inicio", dia_semana_str)
            prompt_inicio_unificado = mcmcn_prompts.PromptsCreativos.generar_monologo_inicio_unificado(
                contenido_noticias=contenido_completo_texto,
                texto_cta=cta_inicio_limpio if interpr_inicio else "",
                texto_base_saludo=saludo_base,
                dato_efemeride=efemerides_hoy,
                dato_meteo=datos_meteo_hoy,
                dato_deportes=datos_deportes_hoy,
                sentimiento_general=sentimiento_general,
                fecha_actual_str=fecha_actual_str,
                humanizacion_instruccion=instruccion_humanizacion,
                toque_costumbrista=saludo_costumbrista,
                dato_oficio_hoy=dato_oficio_hoy,
                pueblo_saludo=obtener_pueblo_aleatorio()
            )
            texto_monologo_inicio = generar_texto_con_gemini(prompt_inicio_unificado)

            if texto_monologo_inicio:
                if "[FECHA_HUMANIZADA]" in texto_monologo_inicio:
                    texto_monologo_inicio = texto_monologo_inicio.replace("[FECHA_HUMANIZADA]", fecha_actual_str)
                cache_content(f"intro_{intro_hash}", {"text": texto_monologo_inicio})

        return limpiar_artefactos_ia(texto_monologo_inicio)

    def _agrupar_noticias_por_temas_mejorado(self, resumenes: list, es_agenda: bool = False) -> dict:
        noticias_unicas = detectar_duplicados_y_similares(resumenes, [])
        if len(noticias_unicas) < MIN_NEWS_PER_BLOCK:
            return {"bloques_tematicos": [], "noticias_individuales": noticias_unicas}

        try:
            noticias_simplificadas = json.dumps([{"id": n.get("id"), "resumen": n.get("resumen")} for n in noticias_unicas], ensure_ascii=False, indent=2)
            prompt_agrupacion = mcmcn_prompts.PromptsAnalisis.agrupacion_logica_temas(noticias_simplificadas, es_agenda=es_agenda)
            respuesta_grupos = generar_texto_con_gemini(prompt_agrupacion)

            start_idx = respuesta_grupos.find('{')
            end_idx = respuesta_grupos.rfind('}')
            if start_idx == -1 or end_idx == -1: raise ValueError("JSON no válido")
            grupos_logicos = json.loads(respuesta_grupos[start_idx:end_idx+1])

            bloques_tematicos = []
            used_ids = set()
            noticias_por_id = {n.get("id"): n for n in noticias_unicas}
            ids_ya_en_bloques = set()

            for tema, ids_noticias in grupos_logicos.items():
                ids_noticias_unicas = [nid for nid in ids_noticias if nid not in ids_ya_en_bloques]
                if len(ids_noticias_unicas) < MIN_NEWS_PER_BLOCK: continue

                lista_resumenes = [noticias_por_id[nid]["resumen"] for nid in ids_noticias_unicas if nid in noticias_por_id]
                resumenes_json = json.dumps(lista_resumenes, indent=2, ensure_ascii=False)
                prompt_enriquecimiento = mcmcn_prompts.PromptsCreativos.enriquecimiento_creativo_tema(tema, resumenes_json)
                respuesta_creativa = generar_texto_con_gemini(prompt_enriquecimiento)

                json_limpio = respuesta_creativa
                if "```" in respuesta_creativa:
                    s = respuesta_creativa.find('{')
                    e = respuesta_creativa.rfind('}')
                    json_limpio = respuesta_creativa[s:e+1] if s != -1 and e != -1 else ""
                try:
                    info_creativa = json.loads(json_limpio)
                    bloques_tematicos.append({
                        'tema': tema,
                        'descripcion_tema': info_creativa.get("descripcion", "Noticias sobre " + tema.replace("_", " ")),
                        'transicion_elegante': info_creativa.get("transicion", "A continuación, hablamos de " + tema.replace("_", " ")),
                        'noticias': [noticias_por_id[nid] for nid in ids_noticias_unicas if nid in noticias_por_id]
                    })
                    used_ids.update(ids_noticias_unicas)
                    ids_ya_en_bloques.update(ids_noticias_unicas)
                except (json.JSONDecodeError, TypeError):
                    continue

            noticias_individuales = [n for n in noticias_unicas if n.get("id") not in used_ids]
            return {'bloques_tematicos': bloques_tematicos, 'noticias_individuales': noticias_individuales}
        except Exception:
            agrupado_dyn = cluster_by_dynamic_keyphrases(noticias_unicas)
            if agrupado_dyn['bloques_tematicos']:
                return _enforce_unique_assignment(agrupado_dyn)
            return _enforce_unique_assignment(agrupacion_simple_por_palabras_clave(noticias_unicas))

    def _fusionar_bloques_similares(self, bloques: list, umbral_similitud: float = 0.75) -> list:
        if not bloques: return []
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
                    ids_existentes = {n.get('id') for n in bloque_a['noticias']}
                    for noticia_nueva in bloque_b['noticias']:
                        if noticia_nueva.get('id') not in ids_existentes:
                            bloque_a['noticias'].append(noticia_nueva)
                    bloque_a['firma_texto'] += " " + bloque_b.get('firma_texto', '')
                    bloques_procesados.pop(j)
                else:
                    j += 1
            i += 1
        for bloque in bloques_procesados:
            if 'firma_texto' in bloque: del bloque['firma_texto']
        if len(bloques_procesados) < len(bloques):
            bloques_procesados.sort(key=lambda b: len(b.get('noticias', [])), reverse=True)
        return bloques_procesados

    def _generar_narracion_fluida_bloque(self, bloque_tematico: dict, es_agenda: bool = False) -> str:
        tema = bloque_tematico.get("descripcion_tema", "varios temas")
        transicion = bloque_tematico.get("transicion_elegante", f"Y ahora, un bloque de noticias sobre {tema}.")
        noticias = bloque_tematico.get("noticias", [])
        if not noticias: return ""
        if len(noticias) < 2: return f"{transicion}. {noticias[0].get('resumen', '')}"

        noticias_ordenadas = sorted(noticias, key=lambda x: x.get('fecha', '0000-00-00'), reverse=True)
        resumenes_para_prompt = []
        fuentes = []
        for i, n in enumerate(noticias_ordenadas):
            fuentes_de_esta_noticia = [n.get('fuente', 'desconocida')]
            for fa in n.get('fuentes_adicionales', []):
                f_add = fa.get('fuente')
                if f_add and f_add not in fuentes_de_esta_noticia: fuentes_de_esta_noticia.append(f_add)
            fuente_nombres = " y ".join(fuentes_de_esta_noticia)
            resumenes_para_prompt.append(f"Noticia {i+1} (Fuentes que reportan esto: {fuente_nombres}): \"{n.get('resumen', '')}\"")
            fuentes.extend(fuentes_de_esta_noticia)

        lista_de_noticias_str = "\n".join(resumenes_para_prompt)
        fuentes_unicas = sorted(list(set(f for f in fuentes if f)))
        num_noticias = len(noticias)
        longitud_deseada = 70 + (num_noticias * 80)
        tipo_narrativa = "ATENCIÓN: Estas noticias son una AGENDA DE EVENTOS FUTUROS (planes, ferias, cursos)." if es_agenda else "ATENCIÓN: Estas noticias son un REPORTE DE HECHOS (Noticiero)."

        prompt = f"Eres un editor y guionista de radio experto...\n{tipo_narrativa}\nTema: {tema}\nNoticias:\n{lista_de_noticias_str}\nInstrucciones:\n1. SÍNTESIS EDITORIAL.\n2. ÚNICA HISTORIA.\n3. LONGITUD: {longitud_deseada} palabras.\n4. CITACIÓN EXPLÍCITA DE FUENTES.\n5. FECHAS ABSOLUTAS.\n8. NO INVENTES.\n9. ENLACES A REDES.\nTransición:\n{transicion}"
        cronica_generada = generar_texto_con_gemini(prompt)

        if not cronica_generada:
            resumenes_fallback = ' '.join([n.get('resumen', '') for n in noticias_ordenadas])
            fuentes_fallback = ", ".join(fuentes_unicas)
            return f"{transicion}. {resumenes_fallback}. Esta información proviene de {fuentes_fallback}."
        return cronica_generada
