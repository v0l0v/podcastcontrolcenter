# src/prompts.py
from typing import Dict, Any, List
from enum import Enum
from src.utils import cargar_configuracion

# Cargar configuración global
CONFIG = cargar_configuracion()
PODCAST_INFO = CONFIG.get('podcast_info', {})
PROMPTS_CONFIG = CONFIG.get('prompts', {})

class TipoDia(Enum):
    LUNES = 0
    MARTES_JUEVES = "default"
    VIERNES = 4
    FIN_DE_SEMANA = "finde"

class ConfiguracionPodcast:
    PRESENTADORA = PODCAST_INFO.get('presentadora', "Dorotea")
    EMAIL_CONTACTO = PODCAST_INFO.get('email_contacto', "contacto@micomicona.com")
    EMAIL_ALIAS_SSML = PODCAST_INFO.get('email_alias_ssml', "contacto arroba micomicona punto com")
    REGION = PODCAST_INFO.get('region', "Castilla la Mancha")
    PAUSA_ESTANDAR = PODCAST_INFO.get('pausa_estandar', "600ms")

class PlantillasSSML:
    @staticmethod
    def _fmt(template_key, sub_key):
        template = PROMPTS_CONFIG.get(template_key, {}).get(sub_key, "")
        return template.format(
            presentadora=ConfiguracionPodcast.PRESENTADORA,
            region=ConfiguracionPodcast.REGION,
            pausa=ConfiguracionPodcast.PAUSA_ESTANDAR,
            email=ConfiguracionPodcast.EMAIL_CONTACTO,
            email_alias=ConfiguracionPodcast.EMAIL_ALIAS_SSML
        )

    FRASES_SALUDO_POR_DIA: Dict[Any, str] = {
        TipoDia.LUNES.value: _fmt.__func__("saludos", "lunes"),
        TipoDia.MARTES_JUEVES.value: _fmt.__func__("saludos", "martes_jueves"),
        TipoDia.VIERNES.value: _fmt.__func__("saludos", "viernes"),
        TipoDia.FIN_DE_SEMANA.value: _fmt.__func__("saludos", "finde")
    }

    FRASES_CIERRE_POR_DIA: Dict[Any, str] = {
        TipoDia.LUNES.value: _fmt.__func__("despedidas", "lunes"),
        TipoDia.MARTES_JUEVES.value: _fmt.__func__("despedidas", "martes_jueves"),
        TipoDia.VIERNES.value: _fmt.__func__("despedidas", "viernes"),
        TipoDia.FIN_DE_SEMANA.value: _fmt.__func__("despedidas", "finde")
    }

    FRASES_FIRMA_FINAL_POR_DIA: Dict[Any, str] = {
        TipoDia.LUNES.value: _fmt.__func__("firmas", "lunes"),
        TipoDia.MARTES_JUEVES.value: _fmt.__func__("firmas", "martes_jueves"),
        TipoDia.VIERNES.value: _fmt.__func__("firmas", "viernes"),
        TipoDia.FIN_DE_SEMANA.value: _fmt.__func__("firmas", "finde")
    }

class PromptsAnalisis:
    @staticmethod
    def resumen_noticia_enriquecido(texto: str, fuente_original: str, entidades_clave: List[str], idioma_destino: str = "español") -> str:
        instruccion_fuente = f"- Integra de forma natural que la noticia proviene de '{fuente_original}'." if fuente_original else ""
        instruccion_entidades = ""
        if entidades_clave:
            lista_entidades_str = ", ".join(f"'{entidad}'" for entidad in entidades_clave)
            instruccion_entidades = f"- CONTENIDO OBLIGATORIO: El resumen DEBE incluir y dar protagonismo a las siguientes entidades clave: {lista_entidades_str}."

        instrucciones_base = PROMPTS_CONFIG.get('analysis_prompts', {}).get('resumen_instrucciones', """Eres un guionista y editor de radio experto en crear resúmenes de noticias concisos y potentes para un podcast.""")

        return f"""{instrucciones_base}
{instruccion_entidades}
{instruccion_fuente}
### TEXTO ORIGINAL A RESUMIR
---
{texto}
---
### ENTREGA
Devuelve ÚNICAMENTE el texto del guion final, listo para ser locutado.
**REGLA FINAL INQUEBRANTABLE:** El resultado debe ser texto puro. NO INCLUYAS NUNCA, bajo ninguna circunstancia, anotaciones de producción como '(Música...)' o '[SFX]', o cualquier texto entre paréntesis o corchetes.
"""

    @staticmethod
    def clasificacion_noticia(texto: str) -> str:
        criterios_base = PROMPTS_CONFIG.get('analysis_prompts', {}).get('clasificacion_criterios', """Eres un clasificador de contenido especializado en medios digitales.""")
        return f"""{criterios_base}
INSTRUCCIONES:
- Responde únicamente: 'INFORMATIVO' o 'IRRELEVANTE'
TEXTO A ANALIZAR:
---
{texto}
---"""

    @staticmethod
    def resumen_muy_breve(texto: str, fuente_original: str = "") -> str:
        instruccion_fuente = f"- Menciona de forma natural que la información proviene de '{fuente_original}'." if fuente_original else ""
        return f"""Eres un/a profesional de la comunicación radiofónica que debe dar un aviso muy corto.
TAREA: Convierte el siguiente texto en una frase informativa para el podcast.
REGLAS ESTRICTAS:
- **Longitud MÍNIMA: 25 palabras.**
- Longitud MÁXIMA: 50 palabras.
- Sé directo y puramente informativo.
{instruccion_fuente}
TEXTO ORIGINAL:
---
{texto}
---
ENTREGA: Solo la frase final, sin introducciones ni explicaciones."""

    @staticmethod
    def agrupacion_logica_temas(noticias_simplificadas: str) -> str:
        instrucciones_agrupacion = PROMPTS_CONFIG.get('analysis_prompts', {}).get('agrupacion_instrucciones', """Eres un analista de contenido experto en identificar patrones temáticos.""")
        return f"""
        {instrucciones_agrupacion}
        LISTA DE NOTICIAS (JSON):
        ---
        {noticias_simplificadas}
        ---
        FORMATO DE RESPUESTA ESPERADO (SOLO JSON):
        {{
          "astronomia_verano": ["id_noticia_15", "id_noticia_20"],
          "iniciativas_agua_tierra": ["id_noticia_4", "id_noticia_11", "id_noticia_19"]
        }}
        """

    @staticmethod
    def extraer_entidades_clave(texto_noticia: str) -> str:
        return f"""
        Eres un sistema de extracción de información (Information Extraction).
        TAREA: Analiza el siguiente texto de una noticia y extrae las 5-7 entidades, conceptos o palabras clave más importantes.
        TEXTO A ANALIZAR:
        ---
        {texto_noticia}
        ---
        FORMATO DE RESPUESTA ESPERADO (SOLO JSON):
        ["Palabra Clave 1", "Concepto Clave 2", "Nombre de Proyecto", "Lugar Relevante"]
        """

    @staticmethod
    def analizar_sentimiento_texto(texto: str) -> str:
        return f"""Eres un/a profesional experto/a en análisis de sentimientos.
        TAREA: Analiza el siguiente texto y clasifica su sentimiento general.
        REGLAS:
        - Responde únicamente con una de estas palabras: 'positivo', 'negativo', 'neutro'.
        TEXTO A ANALIZAR:
        ---
        {texto}
        ---"""

class PromptsCreativos:
    @staticmethod
    def generar_segmento_audiencia_integrado(autor: str, texto_mensaje: str, sentimiento_general: str = "neutro") -> str:
        return f"""
        Eres Dorotea, la presentadora IA de un podcast rural.
        CONTEXTO:
        - Sentimiento general: {sentimiento_general}.
        - Nombre: {autor}
        - Mensaje: "{texto_mensaje}"
        TAREA: Construye un monólogo fluido para la sección de audiencia.
        ENTREGA: Solo el texto del monólogo.
        """

    @staticmethod
    def enriquecimiento_creativo_tema(tema: str, resumenes_json: str) -> str:
        return f"""
        Eres un/a guionista de podcast experto/a.
        TAREA: Para un bloque sobre "{tema}", genera descripción y transición.
        NOTICIAS:
        ---
        {resumenes_json}
        ---
        FORMATO DE RESPUESTA (SOLO JSON):
        {{
          "descripcion": "...",
          "transicion": "..."
        }}
        """

    @staticmethod
    def narracion_profesional(fuentes: str, resumen: str, fecha_noticia_str: str, fecha_actual_str: str, contexto_tematico: str = "") -> str:
        instruccion_contexto = f"La noticia forma parte de un segmento sobre: '{contexto_tematico}'." if contexto_tematico else ""
        persona_base = PROMPTS_CONFIG.get('persona_base', "Eres Dorotea, la presentadora del podcast.")
        return f"""{persona_base}
MATERIAL:
- Fuente(s): {fuentes}
- Fecha Noticia: {fecha_noticia_str}
- Contenido: {resumen}
CONTEXTO TEMPORAL: Hoy es {fecha_actual_str}
ESTILO:
- Precisión temporal CRÍTICA. Usa fechas absolutas.
- Tono conversacional.
- JAMÁS saludes.
{instruccion_contexto}
ENTREGA: Párrafo de locución listo para ser leído.
"""

    @staticmethod
    def resumen_final(contexto: str, sentimiento_general: str = "neutro") -> str:
        return f"""Eres un/a profesional de la comunicación.
TAREA: Crea un párrafo de resumen muy breve (1-2 frases) de cierre.
TEMAS:
---
{contexto}
---
ENTREGA: Solo el texto del resumen.
"""

    @staticmethod
    def generar_monologo_inicio_unificado(contenido_noticias: str, texto_cta: str, dato_curioso_gancho: str = "", sentimiento_general: str = "neutro") -> str:
        # Simplificado para brevedad, la lógica completa estaba en dorototal.py
        return f"""
        Eres Dorotea. Crea el monólogo de apertura.
        Resumen noticias: {contenido_noticias}
        CTA: {texto_cta}
        Gancho: {dato_curioso_gancho}
        Sentimiento: {sentimiento_general}
        ENTREGA: Solo el texto.
        """

    @staticmethod
    def generar_monologo_cierre_unificado(contexto: str, texto_cta: str, dato_curioso_resolucion: str = "", sentimiento_general: str = "neutro") -> str:
        return f"""
        Eres Dorotea. Crea el monólogo de cierre.
        Temas: {contexto}
        CTA: {texto_cta}
        Resolución: {dato_curioso_resolucion}
        Sentimiento: {sentimiento_general}
        ENTREGA: Solo el texto.
        """

def obtener_plantilla_por_dia(dia_semana: int, plantillas_dict: Dict[Any, str]) -> str:
    if dia_semana == 0: return plantillas_dict[TipoDia.LUNES.value]
    elif dia_semana in [1, 2, 3]: return plantillas_dict[TipoDia.MARTES_JUEVES.value]
    elif dia_semana == 4: return plantillas_dict[TipoDia.VIERNES.value]
    else: return plantillas_dict[TipoDia.FIN_DE_SEMANA.value]
