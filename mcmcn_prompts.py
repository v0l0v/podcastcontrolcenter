# mcmcn_prompts.py
# v6.2 - Versión Corregida y Estructurada
# Cambios: Corregida la indentación de los métodos de respuesta a la audiencia.
# Eliminada la función `leer_preguntas_audiencia` que no pertenece a este módulo.

from datetime import datetime
from typing import Dict, Any, List
from enum import Enum

# =================================================================================
# CONFIGURACIÓN Y CONSTANTES
# =================================================================================

class TipoDia(Enum):
    """Enum para mejorar la legibilidad del código"""
    LUNES = 0
    MARTES_JUEVES = "default"
    VIERNES = 4
    FIN_DE_SEMANA = "finde"

import json
import os

def cargar_configuracion():
    config_path = os.path.join(os.path.dirname(__file__), 'podcast_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

CONFIG = cargar_configuracion()
PODCAST_INFO = CONFIG.get('podcast_info', {})

class ConfiguracionPodcast:
    """Centraliza configuraciones globales del podcast"""
    PRESENTADORA = PODCAST_INFO.get('presentadora', "Dorotea")
    EMAIL_CONTACTO = PODCAST_INFO.get('email_contacto', "contacto@micomicona.com")
    EMAIL_ALIAS_SSML = PODCAST_INFO.get('email_alias_ssml', "contacto arroba micomicona punto com")
    REGION = PODCAST_INFO.get('region', "Castilla la Mancha")
    PAUSA_ESTANDAR = PODCAST_INFO.get('pausa_estandar', "600ms")

    PROMPT_ANALISIS_AUDIO_OYENTE = """
    Analiza este audio de un oyente para un podcast.
    Extrae la siguiente información en formato JSON:
    {
        "nombre_oyente": "Nombre si se menciona, o 'Anónimo'",
        "tema_principal": "Resumen breve del tema en 3-5 palabras",
        "sentimiento": "Alegría, Queja, Duda, Saludo, etc.",
        "transcripcion_resumida": "Breve resumen de lo que dice"
    }
    """

    PROMPT_RESPUESTA_OYENTE = """
    Actúa como Dorotea, la presentadora del podcast "Noticias de Castilla-La Mancha".
    Acabas de escuchar un audio de un oyente ({nombre_oyente}) sobre "{tema_principal}".
    
    Tu tarea:
    1. Generar una introducción amable para dar paso al audio: "Escuchamos ahora un mensaje de..."
    2. Generar un comentario/reacción POSTERIOR al audio. Debe ser empático, breve y conectado con el sentimiento del oyente.
    3. NO te despidas del programa bajo ningún concepto. No digas "adiós", "hasta mañana" ni "nos escuchamos pronto". La despedida real vendrá después. Limítate a reaccionar y cerrar la intervención.
    
    Formato de Salida (TEXTO PURO, sin markdown de bloques de código):
    INTRO: [Texto de intro]
    REACCION: [Texto de reacción]
    """

# =================================================================================
# SECCIÓN 1: PLANTILLAS DE GUION (SSML TEMPLATES)
# Contiene todas las frases SSML predefinidas que forman el esqueleto del podcast.
# =================================================================================

PROMPTS_CONFIG = CONFIG.get('prompts', {})

class PlantillasSSML:
    """Encapsula todas las plantillas SSML estáticas"""
    
    # Helper para formatear
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

    # --- Plantillas de Saludo Dinámicas ---
    FRASES_SALUDO_POR_DIA: Dict[Any, str] = {
        TipoDia.LUNES.value: _fmt.__func__("saludos", "lunes"),
        TipoDia.MARTES_JUEVES.value: _fmt.__func__("saludos", "martes_jueves"),
        TipoDia.VIERNES.value: _fmt.__func__("saludos", "viernes"),
        TipoDia.FIN_DE_SEMANA.value: _fmt.__func__("saludos", "finde")
    }

    # --- Plantillas de Despedida ---
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

    # Fallback templates
    SSML_SALUDO_FALLBACK = f"""
<speak>
  ¡Hola y bienvenidos a una nueva entrega del podcast de Micomicona punto com. 
  Soy {ConfiguracionPodcast.PRESENTADORA} <emphasis level="moderate"> tu presentadora virtual generada por inteligencia artificial.
  Cada día, te resumo las últimas noticias de los grupos de acción local de {ConfiguracionPodcast.REGION}.</emphasis>.
  <break time="{ConfiguracionPodcast.PAUSA_ESTANDAR}"/>
  Recuerda, si tienes cualquier idea, propuesta o sugerencia, puedes escribirme a 
  <sub alias="{ConfiguracionPodcast.EMAIL_ALIAS_SSML}">{ConfiguracionPodcast.EMAIL_CONTACTO}</sub>.
  Gracias por tu confianza. 
</speak>
"""

# =================================================================================
# SECCIÓN 2: PROMPTS DE PROCESAMIENTO Y ANÁLISIS DE CONTENIDO
# Instrucciones para la IA enfocadas en tareas técnicas: clasificar, resumir, etc.
# =================================================================================

class PromptsAnalisis:
    """Prompts especializados en análisis y procesamiento de contenido"""

    @staticmethod
    def resumen_noticia_enriquecido(
        texto: str,
        fuente_original: str,
        entidades_clave: List[str],
        idioma_destino: str = "español",
        contexto_calendario: str = ""
    ) -> str:
        """
        Genera un guion de resumen periodístico con control estricto de duración y contenido.
        """
        instruccion_fuente = ""
        instruccion_fuente = ""
        if fuente_original:
            if "PROPIA" in fuente_original.upper():
                instruccion_fuente = "- OBLIGATORIO: Narra la noticia directamente o atribúyela a 'la organización', 'el grupo' o 'esta entidad'. PROHIBIDO decir 'desde PROPIA' o usar la palabra 'PROPIA' como nombre propio."
            else:
                instruccion_fuente = f"- OBLIGATORIO: Menciona explícitamente en el guion que la noticia proviene de '{fuente_original}'. Usa fórmulas variadas como 'nos informan desde...', 'según...', 'en... han comunicado'."

        instruccion_entidades = ""
        if entidades_clave:
            lista_entidades_str = ", ".join(f"'{entidad}'" for entidad in entidades_clave)
            instruccion_entidades = f"- CONTENIDO OBLIGATORIO: El resumen DEBE incluir y dar protagonismo a las siguientes entidades clave: {lista_entidades_str}."

        instrucciones_base = PROMPTS_CONFIG.get('analysis_prompts', {}).get('resumen_instrucciones', "")
        if not instrucciones_base:
            # Fallback si no hay config
            instrucciones_base = """Eres un guionista y editor de radio experto en crear resúmenes de noticias concisos y potentes para un podcast.
### TAREA
Crear un guion de resumen optimizado para formato audio, respetando reglas estrictas de duración y contenido."""

        persona_base = PROMPTS_CONFIG.get('persona_base', "Eres Dorotea.")

        return f"""{persona_base}

{instrucciones_base}

{instruccion_entidades}
{instruccion_fuente}

{contexto_calendario}

### REGLA DE ORO: FUSIÓN DE EVENTOS (CRÍTICO)
- Si este texto contiene información sobre el MISMO EVENTO reportado por diferentes fuentes, FUSIÓNALOS en un solo relato coherente.
- CITA explícitamente a todas las fuentes (ej: 'según informa el Ayuntamiento y recoge el diario Lanza').

### TEXTO ORIGINAL A RESUMIR
---
{texto}
---

### ENTREGA
Devuelve ÚNICAMENTE el texto del guion final.
**REGLAS DE ORO:**
1. **INFORMACIÓN SAGRADA:** Incluye nombres propios, títulos y lugares.
2. **FORMATO PLANO:** Sin markdown ni asteriscos.
3. **CERO ENLACES:** Sin URLs ni hashtags.
"""

    @staticmethod
    def clasificacion_noticia(texto: str) -> str:
        """Determina si un texto contiene contenido informativo válido y localiza eventos"""
        criterios_base = PROMPTS_CONFIG.get('analysis_prompts', {}).get('clasificacion_criterios', "")
        if not criterios_base:
            criterios_base = "Clasifica si el texto es INFORMATIVO o IRRELEVANTE."

        return f"""{criterios_base}

INSTRUCCIONES CLAVES PARA CLASIFICAR:
Debes responder ÚNICAMENTE con UNA de estas tres palabras:
1. 'AGENDA': Si el texto anuncia un evento futuro, acto, plazo de apertura o algo que el oyente puede hacer/ver próximamente.
2. 'NOTICIERO': Si el texto anuncia un hecho ya consumado, una medida aprobada, subvención o resumen de situación actual o pasada.
3. 'IRRELEVANTE': Si es mera publicidad genérica sin fecha ni hechos concretos, saludos o contenido vacío.

No añadas explicaciones ni símbolos adicionales.

TEXTO A ANALIZAR:
---
{texto}
---"""
    @staticmethod
    def resumen_muy_breve(texto: str, fuente_original: str = "") -> str:
        """Genera una mención muy breve, ideal para anuncios o datos simples."""
        
        instruccion_fuente = ""
        instruccion_fuente = ""
        if fuente_original:
            if "PROPIA" in fuente_original.upper():
                instruccion_fuente = "- Puedes atribuir la información a 'la organización' o 'el grupo', pero NUNCA digas 'PROPIA'."
            else:
                instruccion_fuente = f"- Menciona de forma natural que la información proviene de '{fuente_original}'."

        return f"""Eres un/a profesional de la comunicación radiofónica que debe dar un aviso muy corto.

TAREA: Convierte el siguiente texto en una frase informativa para el podcast.

REGLAS ESTRICTAS:
- **Longitud MÍNIMA: 25 palabras.**
- Longitud MÁXIMA: 50 palabras.
- Sé directo y puramente informativo.
- NO añadas contexto, opiniones, ni información que no esté en el texto original.
- **LIMPIEZA TOTAL:** Queda terminantemente prohibido incluir URLs, enlaces, hashtags (#) o arrobas (@).
- NO intentes explicar el "porqué" de nada. Simplemente informa del hecho.
{instruccion_fuente}

TEXTO ORIGINAL:
---
{texto}
---

ENTREGA: Solo la frase final, sin introducciones ni explicaciones."""

    @staticmethod
    def seleccionar_puntos_clave_dia(contexto_completo: str) -> str:
        """
        Actúa como un EDITOR DE MESA. Filtra el ruido y elige los 3 puntos más interesantes.
        Diseñado para Gemini Flash.
        """
        return f"""
        Actúa como el Editor Jefe de una radio local. Tienes una montaña de datos sobre el día de hoy. 
        Tu misión es filtrar el ruido y seleccionar los 3 puntos más "jugosos" para que la presentadora (Dorotea) abra el programa.

        DATOS DISPONIBLES:
        ---
        {contexto_completo}
        ---

        TAREA:
        Selecciona los 3 elementos con más "gancho" emocional o informativo. Prioriza:
        1. Un dato meteorológico si es extremo o muy relevante para el campo.
        2. Un resultado deportivo o efeméride muy local.
        3. El titular más curioso de las noticias del día.

        FORMATO DE SALIDA (JSON):
        {{
            "punto_1": "Breve descripción informativa del punto 1",
            "punto_2": "Breve descripción informativa del punto 2",
            "punto_3": "Breve descripción informativa del punto 3",
            "sentimiento_dominante": "positivo/negativo/neutro"
        }}

        REGLA: Devuelve SOLO el JSON, sin texto adicional.
        """

    @staticmethod
    def procesamiento_noticia_completo(texto: str, fuente_original: str = "", idioma_destino: str = "español", contexto_calendario: str = "") -> str:
        """
        Produce simultáneamente el resumen periodístico, la extracción de entidades y
        el análisis de sentimiento, usando una única llamada estructurada a la API.
        """
        instrucciones_base = PROMPTS_CONFIG.get('analysis_prompts', {}).get('resumen_instrucciones', "")
        if not instrucciones_base:
            instrucciones_base = "Resume esta noticia de forma periodística y concisa para radio."

        instruccion_fuente = ""
        if fuente_original:
            if "PROPIA" in fuente_original.upper():
                instruccion_fuente = "OBLIGATORIO: Atribuye explícitamente la noticia a 'la organización' o 'el grupo'. NUNCA digas 'PROPIA'."
            else:
                instruccion_fuente = f"OBLIGATORIO: Menciona explícitamente que la noticia proviene de '{fuente_original}' de forma natural dentro del locutado."

        persona_base = PROMPTS_CONFIG.get('persona_base', "Eres Dorotea.")

        return f"""Eres un sistema de periodismo y análisis experto en producción de guiones para podcast.

{persona_base}

{instrucciones_base}

{contexto_calendario}
{instruccion_fuente}

### TEXTO ORIGINAL A PROCESAR:
---
{texto}
---

### REGLA DE FORMATO DE SALIDA DE OBLIGADO CUMPLIMIENTO:
Devuelve ÚNICAMENTE un objeto JSON válido. NO envuelvas la respuesta en bloques markdown (ni ```json).
Debe comenzar directamente con {{ y terminar con }}.

Estructura obligatoria del JSON:
{{
  "entidades_clave": ["Entidad 1", "Concepto 2", "Persona 3"], // Array de 3 a 5 palabras clave breves.
  "resumen": "Tu guion de radio adaptado (respetando los límites de palabras, citando fuentes, con fechas absolutas, etc. NUNCA incluyas URLs, hashtags ni arrobas).",
  "sentimiento": "positivo", // Exclusivamente: 'positivo', 'negativo' o 'neutro'.
  "es_agenda": true, // Booleano: true (evento futuro), false (hecho actual/pasado).
  "fecha_evento": "25 de noviembre" // String breve indicando la fecha si es_agenda=true. Vacío en caso contrario.
}}
"""
    @staticmethod
    def resumen_noticia(texto: str, idioma_destino: str = "español", fuente_original: str = "", contexto_calendario: str = "") -> str:
        """Genera un resumen periodístico conciso y atractivo (Deprecated)"""
        
        # Obtenemos las instrucciones base desde la configuración (JSON)
        # Aquí ya están incluidas todas las reglas de estilo, fuentes y fechas.
        instrucciones_base = PROMPTS_CONFIG.get('analysis_prompts', {}).get('resumen_instrucciones', "")
        
        if not instrucciones_base:
            # Fallback mínimo por seguridad
            instrucciones_base = "Resume esta noticia de forma periodística y concisa para radio."

        persona_base = PROMPTS_CONFIG.get('persona_base', "Eres Dorotea.")

        return f"""{persona_base}

{instrucciones_base}

CONTEXTO ADICIONAL:
- Fuente Original: {fuente_original}
{contexto_calendario}

TEXTO ORIGINAL A RESUMIR:
---
{texto}
---

ENTREGA: Solo el resumen final, sin introducciones."""

    @staticmethod
    def agrupacion_logica_temas(noticias_simplificadas: str, es_agenda: bool = False) -> str:
        """
        Identifica temas y agrupa noticias por ID. Soporta lógica distintiva si es agenda.
        """
        instrucciones_agrupacion = PROMPTS_CONFIG.get('analysis_prompts', {}).get('agrupacion_instrucciones', "")
        if not instrucciones_agrupacion:
            instrucciones_agrupacion = """Eres un editor de mesa 'agresivamente inclusivo'. Tu misión NO es crear subsecciones pequeñas, sino MACROGRUPOS (ej: 'Cultura, Ocio y Fiestas', 'Sucesos y Emergencias Regionales', 'Política y Ayudas', 'Desarrollo Rural'). Intenta englobar la mayor cantidad de noticias dentro de grandes paraguas temáticos para que casi ninguna quede fuera suelta."""

        instruccion_extra_evento = "Es muy común que varios grupos publiquen noticias distintas que, en realidad, hablan del MISMO EVENTO EXACTO (ej: la misma feria, la misma visita de un político). DEBES AGRUPARLAS obligatoriamente bajo el mismo ID de tema. No crees un tema separado por fuente para el mismo evento."

        if es_agenda:
            contexto_tipo = "Estas noticias son de AGENDA (eventos futuros). Agrupa los eventos que sean el mismo acto (por ej: ferias iguales), o en su defecto crea bloques por tipo de plan ('Eventos Culturales', 'Cursos y Formación', 'Ferias')."
        else:
            contexto_tipo = "Estas noticias conforman el NOTICIERO (hechos pasados y actuales). " + instruccion_extra_evento

        return f"""
        {instrucciones_agrupacion}
        
        INSTRUCCIONES CLAVE DE NEGOCIO:
        {contexto_tipo}
        
        - REGLA CRÍTICA: Si varias noticias hablan del MISMO EVENTO, júntalas en el mismo grupo. Es vital para que luego Dorotea pueda fusionarlas en un solo texto.

        TAREA: Analiza la siguiente lista de noticias y agrupa los IDs por temas comunes.
        Devuelve ÚNICAMENTE un JSON válido: {{"Tema": ["id1", "id2"]}}

        LISTA DE NOTICIAS (JSON):
        ---
        {noticias_simplificadas}
        ---
        """

    @staticmethod
    def extraer_dato_curioso(noticias_texto: str) -> str:
        return f"""
        Analiza las siguientes noticias y encuentra el dato más CURIOSO, SORPRENDENTE o "RANDOM" (pero verídico).
        
        Tu objetivo es generar un JSON con dos campos para una sección llamada "El Chisme Culto":
        1. "gancho": Una pregunta o frase incompleta que despierte mucha curiosidad (sin revelar la respuesta).
        2. "resolucion": La respuesta breve y explicativa.

        Ejemplo:
        {{
            "gancho": "¿Sabíais que hay un pueblo en nuestra región que ha multiplicado su población por diez en un solo fin de semana?",
            "resolucion": "Pues se trata de Villarrubia, que acogió el festival X recibiendo a más de 5000 visitantes."
        }}

        NOTICIAS:
        {noticias_texto}

        Responde SOLO con el JSON.
        """

    @staticmethod
    def extraer_agenda_futura(noticias_texto: str, fecha_actual: str) -> str:
        return f"""
        Analiza las noticias y extrae ÚNICAMENTE eventos futuros con fecha y lugar confirmados.
        Fecha actual: {fecha_actual}

        Reglas:
        1. Ignora eventos pasados o sin fecha concreta.
        2. Ignora convocatorias de subvenciones o plazos administrativos aburridos.
        3. Busca: conciertos, mercadillos, fiestas, talleres, inauguraciones, marchas...
        4. Formato de salida: JSON con una lista de objetos {{"fecha": "...", "evento": "..."}}.
        5. Si no hay eventos interesantes, devuelve una lista vacía [].

        NOTICIAS:
        {noticias_texto}

        Responde SOLO con el JSON.
        """
    @staticmethod
    def extraer_entidades_clave(texto_noticia: str) -> str:
        """
        Extrae las entidades y conceptos clave de un texto para ayudar en la agrupación.
        """
        return f"""
        Eres un sistema de extracción de información (Information Extraction).

        TAREA: Analiza el siguiente texto de una noticia y extrae las 5-7 entidades, conceptos o palabras clave más importantes.

        REGLAS:
        - Incluye nombres de personas, lugares, organizaciones, proyectos, eventos o temas centrales.
        - Devuelve ÚNICAMENTE un array JSON de strings. No incluyas explicaciones.
        - Las palabras clave deben ser concisas (2-3 palabras máximo).

        TEXTO A ANALIZAR:
        ---
        {texto_noticia}
        ---

        FORMATO DE RESPUESTA ESPERADO (SOLO JSON):
        ["Palabra Clave 1", "Concepto Clave 2", "Nombre de Proyecto", "Lugar Relevante"]
        """
    
    @staticmethod
    def analizar_sentimiento_texto(texto: str) -> str:
        """
        Analiza el sentimiento de un texto y devuelve 'positivo', 'negativo' o 'neutro'.
        """
        return f"""Eres un/a profesional experto/a en análisis de sentimientos.

        TAREA: Analiza el siguiente texto y clasifica su sentimiento general.

        REGLAS:
        - Responde únicamente con una de estas palabras: 'positivo', 'negativo', 'neutro'.
        - No añadas explicaciones adicionales.

        TEXTO A ANALIZAR:
        ---
        {texto}
        ---"""

    @staticmethod
    def analizar_imagen(texto_noticia_asociado: str) -> str:
        """
        Prompt para extraer información de carteles o imágenes adjuntas.
        """
        return f"""
        Actúa como un asistente visual que extrae información de imágenes, carteles o flyers de eventos.
        
        CONTEXTO: Esta imagen acompaña a una noticia con el siguiente texto:
        "{texto_noticia_asociado[:500]}..."

        TAREA:
        Analiza la IMAGEN y extrae cualquier dato relevante que COMPLEMENTE al texto, especialmente:
        1. FECHAS concretas (Día, Mes, Año).
        2. HORAS (Inicio, Fin).
        3. LUGAR exacto (Calle, Edificio, Municipio).
        4. PRECIOS o ENTRADAS.
        5. ORGANIZADORES.
        
        Tu respuesta se añadirá al resumen de la noticia. No describas la imagen ("veo un cartel azul"), simplemente lista los DATOS FACTUALES encontrados.
        Si la imagen no tiene texto legible o relevante, responde: "IMAGEN_SIN_DATOS".
        """

# =================================================================================
# SECCIÓN 3: PROMPTS DE GENERACIÓN CREATIVA Y GUIONIZACIÓN
# Instrucciones para la IA donde actúa como guionista, locutora o creativa.
# =================================================================================

class PromptsCreativos:
    """Prompts especializados en generación de contenido creativo para el podcast"""

    # --- INICIO DE LA CORRECCIÓN DE INDENTACIÓN ---
    # Las siguientes 3 funciones ahora están correctamente indentadas como métodos estáticos
    # dentro de la clase `PromptsCreativos`.

    # REEMPLAZA    @staticmethod
    def generar_monologo_inicio_unificado(
        puntos_clave: Dict[str, str],
        pueblo_saludo: str = "",
        texto_cta: str = ""
    ) -> str:
        """
        Genera el monologo de apertura usando los puntos clave seleccionados por el editor.
        Usa PLACEHOLDERS deterministas para evitar alucinaciones.
        """
        p1 = puntos_clave.get("punto_1", "")
        p2 = puntos_clave.get("punto_2", "")
        p3 = puntos_clave.get("punto_3", "")
        
        instruccion_cta = f'\n📢 CTA (OBLIGATORIA):\n"{texto_cta}"\n(Antes de la CTA, escribe `[CORTINILLA]`)' if texto_cta else ""
        persona_base = PROMPTS_CONFIG.get('persona_base', "Eres Dorotea.")

        return f"""
        {persona_base}
        
        ## TU MISIÓN
        Eres la locutora estrella. Vas a abrir el podcast con energía. 
        El "Editor de Mesa" te ha pasado estos 3 puntos clave para hoy:
        1. {p1}
        2. {p2}
        3. {p3}

        ## INSTRUCCIONES DE PLACEHOLDERS (CRÍTICO)
        Para que no te equivoques con los datos, USA ESTOS MARCADORES EXACTOS donde corresponda:
        - `[FECHA_HOY]`: Para la fecha de hoy.
        - `[DATO_1]`: Para comentar el punto 1.
        - `[DATO_2]`: Para comentar el punto 2.
        - `[DATO_3]`: Para comentar el punto 3.
        - `[PUEBLO_SALUDO]`: Para el saludo especial a {pueblo_saludo}.

        Ejemplo de estilo: "¡Buenos días! En este [FECHA_HOY], mandamos un abrazo a la gente de [PUEBLO_SALUDO]... y ojo con [DATO_1] que viene fuerte..."

        {instruccion_cta}

        ## REGLAS DE ESTILO:
        1. **Lenguaje Oral**: Escribe para ser leído. Usa frases cortas, cercanía manchega y mucha empatía.
        2. **Brevedad**: No te enrolles. Tienes 45-60 segundos de gloria.
        3. **No inventes**: Si no hay datos, no los rellenes. Ciñete a los marcadores.

        Devuelve SOLO el texto de la locución.
        """
        return prompt

    @staticmethod
    def generar_segmento_audiencia_integrado(autor: str, texto_mensaje: str, sentimiento_general: str = "neutro") -> str:
        """
        Genera un segmento de audio completo y fluido para la interacción con la audiencia.
        """
        # Clasificación interna para adaptar el tono de la respuesta
        tipo_mensaje = "una pregunta"
        texto_lower = texto_mensaje.lower()
        if '?' not in texto_mensaje:
            palabras_felicitacion = ['felicidades', 'enhorabuena', 'gracias', 'me encanta', 'gran trabajo']
            if any(palabra in texto_lower for palabra in palabras_felicitacion):
                tipo_mensaje = "una felicitación"
            else:
                tipo_mensaje = "un comentario"

        return f"""
        Eres Dorotea, la carismática presentadora IA de un podcast rural. Tienes una personalidad cercana, curtida, amable y empática de Castilla-La Mancha. Tu tarea es responder al mensaje de un oyente de forma muy directa y sin dar rodeos, pero manteniendo tu inconfundible esencia "Dorotea".

        CONTEXTO:
        - Nombre del oyente: {autor}
        - Tipo de Mensaje: {tipo_mensaje}
        - Texto del Mensaje: "{texto_mensaje}"

        TAREA:
        Construye una locución muy concisa siguiendo estos pasos simples:
        1. Menciona rápidamente que tienes un mensaje de {autor} y responde DIRECTAMENTE aportando la información o comentario que corresponda. NO le des las gracias a esta persona en concreto.
        2. Si el mensaje original es largo, no lo recites al pie de la letra, hazle un guiño breve y natural.
        3. Concluye tu respuesta con un agradecimiento general a la audiencia por los mensajes y una muy breve llamada a la acción (CTA). En ese CTA debes mencionar el grupo de Telegram llamado "Micomicona" y decirles que busquen el enlace en la web de "micomicona.com".
        4. ¡TERMINA EN SECO! Justo después de esa brevísima invitación, pon punto final. NO cierres la sección y NO digas que continuamos con el programa. Tu frase se acaba para dar paso limpio a la cortinilla del siguiente bloque.

        REGLAS CLAVE:
        - **LIMITACIÓN DE TIEMPO ESTRICTA:** Tu locución NO DEBE superar los 30 a 45 segundos de audio (aproximadamente unas 50 a 65 palabras totales), a menos que sea EXPRESAMENTE necesario responder algo complejo.
        - ¡No te enrolles! Sé muy "Dorotea" pero totalmente expeditiva y al grano. Apunta directo a la respuesta y a la rápida CTA final a micomicona.com.
        - El resultado debe ser texto plano (PÁRRAFO ÚNICO) listo para ser locutado.
        - **PROHIBICIÓN ESTRICTA DE TRANSICIONES:** NADA de hacer puentes al siguiente bloque. Tienes terminantemente prohibido decir: "bueno", "adiós", "seguimos", "continuamos con más noticias", o "vamos al siguiente tema". La intervención se corta sola en cuanto terminas tu pequeña CTA.

        ENTREGA:
        Devuelve SOLO el texto de tu monólogo, listo para ser locutado.
        """

    @staticmethod
    def generar_social_pack(resumen_noticias: str) -> str:
        """
        Genera contenido para redes sociales (Facebook e Instagram) basado en el resumen de noticias.
        Devuelve un JSON con los textos.
        """
        return f"""
        Eres un Social Media Manager experto en comunicar noticias locales con un tono cercano y atractivo.
        
        TAREA:
        Basándote en el siguiente resumen de las noticias del podcast de hoy, genera un pack de contenidos para redes sociales.
        
        RESUMEN DEL PODCAST:
        ---
        {resumen_noticias}
        ---

        OBJETIVOS:
        1. **Facebook:** Un post informativo pero coloquial, que invite a escuchar el episodio completo. Usa emojis moderados. Divide en párrafos claros.
        2. **Instagram (Feed/Caption):** Un texto visual, con hashtags relevantes, frases cortas y mucho "gancho".
        
        FORMATO DE SALIDA (JSON ÚNICAMENTE):
        {{
            "facebook_post": "Texto del post para Facebook...",
            "instagram_caption": "Texto para el caption de Instagram..."
        }}
        
        REGLAS:
        - No inventes noticias que no estén en el resumen.
        - Tono: Profesional pero cercano (estilo 'Dorotea').
        - Incluye llamadas a la acción (CTA) para escuchar el podcast.
        """

    @staticmethod
    def generar_analisis_fuentes(datos_analisis: str) -> str:
        """
        Genera un guion de episodio especial agradeciendo y analizando la actividad de las fuentes.
        """
        persona_base = PROMPTS_CONFIG.get('persona_base', "Eres Dorotea, la presentadora del podcast.")

        return f"""
        {persona_base}
        
        OBJETIVO:
        Redactar el "Informe Semanal de Actividad de los GAL". Debes seguir ESTRICTAMENTE la estructura solicitada, basándote en los datos de la tabla.
        
        INPUT - DATOS DE ACTIVIDAD Y TITULARES:
        ---
        {datos_analisis}
        ---

        REGLA DE ORO DE CANTIDADES: NUNCA digas el número exacto de noticias (ej: "ha publicado 5"). Usa siempre cuantificadores relativos ("bastante activo", "liderando", "un aluvión de novedades", "constante").
        
        ESTRUCTURA DEL GUION (Respetar orden y contenido):

        1. **Inicio:**
           - ETIQUETA OBLIGATORIA: `[SINTONIA_INICIO]`
           - Saludo cordial y presentación del análisis semanal.

        2. **BLOQUE 1: El Podio Semanal (Top 3 '7d'):**
           - **Quiénes:** Menciona ÚNICAMENTE a los 3 grupos con mayor número en la columna '7d'.
           - **Contenido:** Para estos 3 ganadores, tienes una lista de "TITULARES DESTACADOS" en el input. NO LOS LEAS LITERALMENTE. Úsalos para comentar brevemente sobre qué han estado trabajando (ej: "hemos visto que han lanzado un taller de...", "muy centrados en sus ayudas a...").
           - **Estilo:** Reconocimiento y entusiasmo.
           - ETIQUETA OBLIGATORIA: `[CORTINILLA]`

        3. **BLOQUE 2: La Constancia Mensual (Top '30d'):**
           - **Fuente de Datos:** IGNORA la tabla general de 7 días. Usa EXCLUSIVAMENTE la lista "RANKING MENSUAL" (30 días) del final del input.
           - **Quiénes:** Selecciona **7 u 8 grupos** de esa lista, tomándolos estrictamente en ORDEN DESCENDENTE.
           - **Contenido:** Cita sus nombres.
           - **Detalle:** Nombra **algunos** de los proyectos de **alguno** de ellos (no hace falta de todos, solo los más interesantes según los titulares facilitados).
           - **Conexión:** Si alguno ya salió en el Bloque 1, haz mención especial.
           - **Estilo:** Descendente y fluido.
           - ETIQUETA OBLIGATORIA: `[CORTINILLA]`

        4. **BLOQUE 3: Los que suman en silencio (Sin Actividad):**
           - **Cálculo:** Cuenta cuántos grupos tienen '0' en la columna '7d' o '30d' (según veas en la tabla).
           - **Contenido:** NO DES NOMBRES. Solo di la cifra total (ej: "Y hay unos 15 grupos que esta semana no han publicado...").
           - **Mensaje:** Explica brevemente la importancia de veces no publicar noticias porque se está trabajando en gestión interna, reuniones o proyectos de largo recorrido. Valida su esfuerzo invisible "detrás de las cámaras".

        5. **Cierre:**
           - Reflexión final sobre el esfuerzo colectivo de todos para mantener vivo el medio rural.
           - Despedida hasta la próxima semana.
           - ETIQUETA OBLIGATORIA: `[SINTONIA_CIERRE]` (¡Siempre al final!)
        
        ENTREGA: ÚNICAMENTE EL GUION (TEXTO PLANO).
        """

    @staticmethod
    def enriquecimiento_creativo_tema(tema: str, resumenes_json: str) -> str:
        """
        Genera el contenido creativo para un bloque temático ya definido.
        Recibe los resúmenes como una cadena de texto JSON.
        """
        return f"""
        Eres un/a guionista de podcast experto/a en crear transiciones fluidas y atractivas para un programa local de {ConfiguracionPodcast.REGION}.
        
        TAREA: Para un bloque de noticias sobre el tema "{tema}", genera una descripción y una transición.
        
        A continuación te proporciono un array JSON con los resúmenes de las noticias del bloque:
        ---
        {resumenes_json}
        ---
    
        INSTRUCCIONES:
        - `descripcion_tema`: Un texto breve que describa el tema del bloque (ej: "Iniciativas para fomentar el turismo rural.").
        - `transicion_elegante`: Una frase para introducir el bloque de forma natural.
        
        REGLAS DE ORO PARA LA TRANSICIÓN:
        - **PROHIBIDO INVENTAR CONTEXTO PASADO:** NUNCA digas "Tras repasar X...", "Después de hablar de Y...", "Dejamos atrás la política...". NO SABES de qué se ha hablado antes.
        - **MIRA SOLO HACIA DELANTE:** Tu transición debe servir SOLAMENTE para abrir la puerta al NUEVO tema.
        - **EVITA FÓRMULAS CLICHÉ Y MULETILLAS:** Tienes ESTRICTAMENTE PROHIBIDO usar las siguientes frases o variaciones de las mismas: "En torno a...", "Cambiando de tercio...", "En otro orden de cosas...", "El foco se pone en...", "Y un tema que cobra importancia hoy es...", "Pasamos ahora a abordar noticias sobre...".
        - **SÉ NATURAL Y DIRECTA:** Usa formas frescas de introducir un tema. Ejemplos permitidos:
          - "Atención a lo que llega desde..."
          - "Nos detenemos ahora en..."
          - "Si hay algo de lo que se habla hoy es de..."
          - O simplemente entra directo al tema: "La vivienda vacía puede ser la clave..."
        - **CONTEXTO GEOGRÁFICO:** El podcast se emite desde {ConfiguracionPodcast.REGION}. Puedes mencionar otras comunidades (como Andalucía o Extremadura) **SOLO SI** la noticia trata explícitamente sobre ellas o sobre un proyecto compartido. NUNCA uses frases como "nos vamos al campo andaluz" o "actualidad extremeña" para presentar el bloque general, salvo que TODAS las noticias sean de esa región. Si son noticias locales, asume que son de {ConfiguracionPodcast.REGION}.
        - Devuelve ÚNICAMENTE un objeto JSON válido con las claves "descripcion" y "transicion".

        FORMATO DE RESPUESTA (SOLO JSON):
        {{
          "descripcion": "...",
          "transicion": "..."
        }}
        """
# (Método narracion_fluida_bloque_priorizada eliminado por falta de uso)

    @staticmethod
    def narracion_profesional(
        fuentes: str, 
        resumen: str, 
        fecha_noticia_str: str,
        fecha_actual_str: str,
        contexto_tematico: str = ""
    ) -> str:
        """Convierte un resumen en una narración de podcast profesional"""
        
        # Obtenemos las instrucciones centralizadas desde el JSON
        instrucciones_narracion = PROMPTS_CONFIG.get('analysis_prompts', {}).get('narracion_instrucciones', "")
        
        if not instrucciones_narracion:
            # Fallback seguro
            instrucciones_narracion = "Narra esta noticia para un podcast de forma natural."

        instruccion_contexto = ""
        if contexto_tematico:
            instruccion_contexto = f"La noticia forma parte de un segmento sobre el tema: '{contexto_tematico}'. Asegúrate de que la narración encaje fluidamente en este contexto."
            
        persona_base = PROMPTS_CONFIG.get('persona_base', "Eres Dorotea, la presentadora del podcast.")

        return f"""{persona_base}

{instrucciones_narracion}

MATERIAL DE TRABAJO:
- Fuente(s): {fuentes}
- Fecha de la Noticia: {fecha_noticia_str}
- Contenido: {resumen}

CONTEXTO TEMPORAL:
- La fecha de hoy es: {fecha_actual_str} ([SOLO PARA REFERENCIA, NO USAR RELATIVOS])

{instruccion_contexto}

REGLAS ADICIONALES Y TONO (¡MUY IMPORTANTE!):
- NO INVENTES CONTEXTO INSTITUCIONAL: Cíñete a los hechos descritos en la noticia. Está terminantemente prohibido añadir conclusiones inventadas, propaganda u opiniones políticas o institucionales que no estén textualmente en las fuentes originales.
- ENLACES A REDES Y WEBS: Si en el texto original aparece un enlace a YouTube, Facebook, Instagram o cualquier página web, DEBES conservarlo. En lugar de leer la URL entera, añade una frase natural al final como: "Recuerda visitar su web [o perfil], te dejamos el enlace en las notas del podcast: [AQUÍ ESCRIBES LA URL LITERAL]".
- PROHIBIDO USAR MULETILLAS ROBÓTICAS: NO EMPIECES NUNCA con "Y otra noticia interesante nos llega desde...". Varía tus aperturas y sé creativa. Ejemplos permitidos: "Nos vamos hasta...", "Desde X nos cuentan que...", "Ojo a lo que pasa en...".
- HUYE DEL TONO BUROCRÁTICO: No parezcas un tablón de anuncios de un ayuntamiento. NO USES frases formales como "Los interesados deberán cumplir con los requisitos", "Se ruega a la ciudadanía", "Este proyecto busca empoderar". Traduce ese lenguaje administrativo a lenguaje de radio cercano. Ejemplo: en vez de "Los interesados pueden postularse en...", di "Si te cuadra, échale un ojo en su web...".
- SÉ CERCANA O DIRECTA: Eres Dorotea, una locutora. Tienes que sonar natural.

ENTREGA: Párrafo de locución listo para ser leído al aire, TEXTO PLANO PURO.
"""

    @staticmethod
    def resumen_final(contexto: str, sentimiento_general: str = "neutro") -> str:
        """Genera un resumen final conciso de los temas cubiertos en el podcast."""
        return f"""Eres un/a profesional de la comunicación y guionista de podcast.

TAREA:
Basado en los temas tratados hoy, crea un párrafo de resumen muy breve (1-2 frases) en un tono de cierre. No menciones la palabra 'resumen' o 'podcast'. El objetivo es cerrar el programa, recordando los temas principales de forma elegante.
TEMAS TRATADOS HOY:
---
{contexto}
---

INSTRUCCIONES:
- Conecta los temas de forma natural en una o dos frases, como una reflexión final.
- Utiliza un tono profesional y optimista, adaptado al sentimiento general de las noticias: {sentimiento_general}.
- Utiliza un tono profesional, optimista y que invite a la reflexión.

EJEMPLO DE RESPUESTA:
"Hemos repasado los eventos culturales del verano, la última etapa de la vuelta ciclista y las iniciativas que impulsan el desarrollo rural. Un día más, el territorio de Castilla-La Mancha demuestra su energía y vitalidad."

ENTREGA: Solo el texto del resumen, sin encabezados ni explicaciones ni ningún tipo de formato de marcado.
"""

    @staticmethod
    def reescritura_cta_creativa(texto_original: str, tono_actual: str = "formal") -> str:
        """Reescribe CTAs para evitar repetición y mantener frescura."""
        return f"""Eres un/a profesional de la comunicación, especialista en adaptar mensajes institucionales para un podcast. Tu fortaleza es hacer que la información importante suene cercana, clara y directa, sin perder la formalidad.

TEXTO BASE A REINTERPRETAR:
---
{texto_original}
---

TAREA:
Reinterpreta el texto base para que suene fresco y original, manteniendo siempre el mensaje clave.

ESTILO Y TONO:
- **Lenguaje claro y directo:** Usa un vocabulario accesible y construye frases sencillas. Evita un lenguaje demasiado publicitario o enrevesado.
- **Cercano pero formal:** El tono debe ser profesional y riguroso, pero con una calidez que conecte con la audiencia.
- **Fresco y original:** Aunque el mensaje se repita, la forma de contarlo debe ser nueva cada vez.
- **Tono específico del día:** Adapta la reescritura al tono general sugerido: {tono_actual}.
- **REGLA INQUEBRANTABLE:** No empieces NUNCA con un saludo (ej: "Hola", "Buenos días"). El texto debe ser una continuación directa del contenido anterior.

ENTREGA: Solo el texto reescrito, listo para locución, sin ningún tipo de formato de marcado.
"""

    @staticmethod
    def generar_guion_micropodcast_resumen(contenido_noticias: str) -> str:
        """
        Genera un guion de 59 segundos (~140-150 palabras) resumiendo las noticias del día.
        """
        persona_base = PROMPTS_CONFIG.get('persona_base', "Eres Dorotea, la presentadora del podcast rural.")
        
        return f"""
        {persona_base}
        
        TU MISIÓN:
        Vas a generar un "micropodcast" de impacto de aproximadamente 59 segundos (unas 140-150 palabras).
        El objetivo es captar al oyente desde el primer segundo con lo más curioso o importante del día en Castilla-La Mancha.
        
        TEMAS DEL DÍA:
        ---
        {contenido_noticias}
        ---
        
        REGLAS DE ORO:
        1. **Gancho inicial**: Empieza con algo que llame la atención. "¿Habéis visto lo que pasa hoy en...?" o "Atención, porque hoy la noticia más sonada es...".
        2. **Selección**: No intentes contar todo. Elige 2 o 3 noticias que sean muy curiosas, positivas o de gran impacto y cuéntalas de forma vibrante.
        3. **Estilo Dorotea**: Tu cercanía, tus refranes, tu alma rural. Que se note que eres tú.
        4. **Cierre**: Una invitación calurosa a escuchar el podcast completo en micomicona.com.
        5. **Duración (CRÍTICO)**: NO superes las 140-145 palabras. Si te pasas, el audio durará más de un minuto. Sé concisa.
        6. **Formato**: Texto plano puro, sin markdown ni asteriscos.
        
        ENTREGA: Solo el texto del guion listo para locutar.
        """

    @staticmethod
    def generar_sumario_intro(
        contenido_noticias: str,
        dato_curioso_gancho: str = "",
        sentimiento_general: str = "neutro"
    ) -> str:
        """
        Genera SOLO el sumario de noticias y el gancho, sin saludos ni despedidas.
        """
        instruccion_gancho = ""
        if dato_curioso_gancho:
            instruccion_gancho = f"""
        3.  **SECCIÓN "LA ADIVINANZA DEL DÍA" (GANCHO):**
            - Justo antes de dar paso a las noticias, haz una pausa clara y di EXACTAMENTE: "En la sección 'La adivinanza del día' estad atentos pues..."
            - A continuación, lanza esta pregunta/gancho al aire para dejar a la audiencia intrigada.
            - Gancho: "{dato_curioso_gancho}"
            - **IMPORTANTE:** Usa puntos suspensivos (...) antes de la frase introductoria para marcar la pausa.
        """

        return f"""
        Eres Dorotea, la presentadora IA del podcast de Micomicona.
        
        TAREA:
        Genera el bloque de introducción de contenidos que va JUSTO DESPUÉS del saludo inicial.
        NO saludes. NO te presentes. NO digas la fecha. Eso ya se ha dicho.

        ESTRUCTURA:
        1.  **Transición de entrada:** Una frase muy breve para conectar con el saludo anterior (ej: "Hoy traemos una agenda cargada...", "Vamos con los temas de hoy...").
        2.  **Sumario de titulares:** Selecciona 3 de los temas más interesantes de hoy:
            - Resúmelos en una frase impactante cada uno.
            - Crea "hype" o curiosidad.
            - Contenido: "{contenido_noticias}"
        {instruccion_gancho}
        4.  **Transición a noticias:** Finaliza con una frase que dé paso al primer bloque (ej: "¡Empezamos!", "Vamos con los detalles.").

        REGLAS CLAVE:
        - Tono: {sentimiento_general}.
        - Párrafo único y fluido.
        - NADA de saludos ni despedidas.

        ENTREGA:
        Texto listo para locutar.
        """


    @staticmethod
    def generar_monologo_cierre_unificado(
        contexto: str,
        texto_cta: str,
        texto_base_despedida: str = "",
        texto_firma: str = "",
        dato_curioso_resolucion: str = "",
        sentimiento_general: str = "neutro"
    ) -> str:
        """
        NUEVO PROMPT UNIFICADO: Genera todo el monólogo de cierre en una sola llamada.
        """
        instruccion_cta = ""
        if texto_cta:
            instruccion_cta = f"""
        2.  **Integración del Mensaje Clave (CTA):** Antes de la despedida final, integra de forma natural el siguiente mensaje. Adáptalo a tu estilo, no lo leas literalmente.
            - Mensaje a integrar: "{texto_cta}"
        """

        instruccion_resolucion = ""
        if dato_curioso_resolucion:
            instruccion_resolucion = f"""
        3.  **RESOLUCIÓN "EL CHISME CULTO":**
            - Antes de irte del todo, resuelve el misterio que planteaste al principio.
            - Respuesta: "{dato_curioso_resolucion}"
            - Hazlo con gracia, como "Ah, por cierto, lo que os preguntaba antes..."
        """

        instruccion_despedida = ""
        if texto_base_despedida:
            instruccion_despedida = f"""
        4.  **Despedida Final (REINTERPRETACIÓN):**
            - Tienes un guion base para la despedida de hoy:
            ---
            "{texto_base_despedida}"
            ---
            - **TU TAREA:** No leas este texto literalmente. Úsalo como guía semántica.
            - Reinterprétalo con tu propio estilo (cercano, reflexivo).
            - **OBLIGATORIO:** Debes incluir la esencia del mensaje: agradecimiento por escuchar, disculpa humilde por posibles errores ("sigo aprendiendo") y buenos deseos para el resto del día/semana.
            """
        else:
            instruccion_despedida = f"""
        4.  **Despedida Final:** Cierra con una despedida personal. Agradece la compañía, pide disculpas si has cometido algún error porque sigues aprendiendo, y desea a la audiencia un buen resto de día/semana.
            """

        instruccion_firma = ""
        if texto_firma:
            instruccion_firma = f"""
        5.  **Firma Final (REINTERPRETACIÓN OBLIGATORIA):**
            - Tienes una frase base para cerrar el programa: "{texto_firma}"
            - **TU TAREA:** No la leas literalmente. Úsalo como guía semántica.
            - Reinterprétala con tu propio estilo para que suene natural como última frase, pero manteniendo el significado original.
            """

        instrucciones_despedida = PROMPTS_CONFIG.get('analysis_prompts', {}).get('despedida_instrucciones', "Cierra el programa.")
        persona_base = PROMPTS_CONFIG.get('persona_base', "Eres Dorotea.")

        return f"""
        {persona_base}

        ESTÁS EN EL DOMINIO FINAL DEL PODCAST. NO ESTÁS EMPEZANDO. ESTÁS TERMINANDO.
        
        {instrucciones_despedida}

        CONTEXTO:
        - Sentimiento general hoy (determinará la música final): {sentimiento_general}
        
        ESTRUCTURA VARIABLE (Usa si aplica):
        1.  **Reflexión Final (Resumen):** "{contexto}" (Úsalo solo para dar una pincelada de cierre, NO para volver a contar las noticias).
        {instruccion_cta}
        {instruccion_resolucion}
        {instruccion_despedida}
        {instruccion_firma}

        REGLAS DE ORO (COMPORTAMIENTO OBLIGATORIO):
        - **LONGITUD MÁXIMA:** Todo el monólogo no debe durar más de 30 segundos locutados (aproximadamente 60-80 palabras como máximo). Sé directa, breve y muy concisa. ¡NO TE ENROLLES!
        - **PROHIBIDO SALUDAR:** No digas "Hola", "Buenos días", "Buenas tardes", "Bienvenidos".
        - **PROHIBIDO PRESENTARSE:** No digas "Soy Dorotea y esto es...". Ya se ha dicho al principio.
        - **EMPIEZA DIRECTO:** Tu primera frase debe ser una conclusión o una reflexión sobre lo escuchado.
        - **TONO DE CIERRE:** Tu voz se está apagando, estás despidiendo a los amigos hasta mañana.

        ENTREGA:
        Devuelve SOLO el texto de tu monólogo, listo para ser locutado.
        """

    @staticmethod
    def generar_comentario_post_creditos(contexto_noticias: str) -> str:
        """
        Genera una frase de 'post-créditos' cómplice y espontánea, basada en lo leído.
        """
        instrucciones_post = PROMPTS_CONFIG.get('analysis_prompts', {}).get('post_creditos_instrucciones', "Di algo espontáneo.")
        persona_base = PROMPTS_CONFIG.get('persona_base', "Eres Dorotea.")

        return f"""
        {persona_base}
        
        {instrucciones_post}
        
        CONTEXTO DE LO QUE HAS LEÍDO HOY:
        {contexto_noticias}
        
        REGLA DE ORO:
        - El comentario debe ser MUY BREVE, como máximo de 30 segundos al ser locutado (unas 50-60 palabras máximo). ¡NO TE ENROLLES!
        
        ENTREGA: Solo el texto.
        """

# (Método resumen_y_cierre_unificado eliminado por falta de uso)


# (Método introduccion_dinamica eliminado por falta de uso)

    # Este método ya estaba dentro de la clase, solo se actualiza su contenido
# (Método generar_saludo_dinamico eliminado por falta de uso)

# Las siguientes funciones estaban duplicadas al final del archivo y se eliminan.
# @staticmethod
# def introduccion_dinamica(contenido_noticias: str, sentimiento_general: str = "neutro") -> str: ...
# @staticmethod
# def generar_saludo_dinamico(dia_semana: int, sentimiento_general: str = "neutro") -> str: ...

# =================================================================================
# FUNCIONES DE UTILIDAD Y HELPERS
# =================================================================================

def obtener_plantilla_por_dia(dia_semana: int, plantillas_dict: Dict[Any, str]) -> str:
    """
    Función helper para obtener la plantilla correcta según el día de la semana.
    
    Args:
        dia_semana: 0=Lunes, 1-3=Martes-Jueves, 4=Viernes, 5-6=Fin de semana
        plantillas_dict: Diccionario con las plantillas por día
    
    Returns:
        str: Plantilla SSML correspondiente
    """
    if dia_semana == 0:
        return plantillas_dict[TipoDia.LUNES.value]
    elif dia_semana in [1, 2, 3]:
        return plantillas_dict[TipoDia.MARTES_JUEVES.value]
    elif dia_semana == 4:
        return plantillas_dict[TipoDia.VIERNES.value]
    else:  # 5, 6 (sábado, domingo)
        return plantillas_dict[TipoDia.FIN_DE_SEMANA.value]

def obtener_tono_actual(texto: str) -> str:
    """Clasifica el tono de un texto para adaptar los prompts siguientes."""
    # Podríamos usar un prompt de IA para esto o una lógica basada en palabras clave
    # Por simplicidad, aquí lo haremos de forma determinista
    
    texto_lower = texto.lower()
    if any(palabra in texto_lower for palabra in ['fiesta', 'festival', 'concierto', 'alegría']):
        return "festivo y alegre"
    elif any(palabra in texto_lower for palabra in ['aviso', 'importante', 'riesgo', 'peligro']):
        return "formal y cauteloso"
    elif any(palabra in texto_lower for palabra in ['juventud', 'raíz', 'emprender']):
        return "inspirador y cercano"
    else:
        return "formal"


# =================================================================================
# VALIDACIÓN Y TESTING
# =================================================================================

def validar_configuracion() -> bool:
    """Valida que todas las configuraciones estén correctamente definidas."""
    try:
        # Verificar que todas las plantillas tengan contenido
        assert all(PlantillasSSML.FRASES_SALUDO_POR_DIA.values()), "Plantillas de saludo vacías"
        assert all(PlantillasSSML.FRASES_CIERRE_POR_DIA.values()), "Plantillas de cierre vacías"
        assert all(PlantillasSSML.FRASES_FIRMA_FINAL_POR_DIA.values()), "Plantillas de firma vacías"
        
        # Verificar configuración básica
        assert ConfiguracionPodcast.PRESENTADORA, "Nombre de presentadora no definido"
        assert ConfiguracionPodcast.EMAIL_CONTACTO, "Email de contacto no definido"
        
        return True
    except AssertionError as e:
        print(f"Error de validación: {e}")
        return False

if __name__ == "__main__":
    # Test básico de validación
    if validar_configuracion():
        print("✅ Configuración validada correctamente")
        
        # Test de obtención de plantillas
        for dia in range(7):
            plantilla = obtener_plantilla_por_dia(dia, PlantillasSSML.FRASES_SALUDO_POR_DIA)
            print(f"Día {dia}: {'✅' if plantilla else '❌'}")
    else:
        print("❌ Error en la configuración")
