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
    1. Generar una introducción amable para dar paso al audio: "Y para cerrar, hoy tenemos un mensaje de..."
    2. Generar un comentario/reacción POSTERIOR al audio. Debe ser empático, breve y conectado con el sentimiento del oyente.
    3. Cerrar el programa definitivamente (ya que este bloque sustituye a la despedida habitual).
    
    Formato de Salida (TEXTO PURO, sin markdown de bloques de código):
    INTRO: [Texto de intro]
    REACCION: [Texto de reacción y despedida final]
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

        return f"""{instrucciones_base}

{instruccion_entidades}
{instruccion_fuente}

{contexto_calendario}

### TEXTO ORIGINAL A RESUMIR
---
{texto}
---

### ENTREGA
Devuelve ÚNICAMENTE el texto del guion final, listo para ser locutado.
**REGLAS DE ORO:**
1. **INFORMACIÓN SAGRADA:** Es OBLIGATORIO incluir nombres de personas (autores, premiados, etc.), títulos de obras (libros, películas) y lugares específicos mencionados. NO generalices (ej: NO digas "un autor", di "Pedro Martín-Romo").
2. **FORMATO PLANO:** El resultado debe ser texto puro. NO INCLUYAS NUNCA markdown (ni negritas **, ni cursivas _), ni anotaciones de producción. Eliminamos cualquier asterisco de la respuesta.
3. **NO** incluyas texto entre paréntesis o corchetes.
"""

    @staticmethod
    def clasificacion_noticia(texto: str) -> str:
        """Determina si un texto contiene contenido informativo válido"""
        criterios_base = PROMPTS_CONFIG.get('analysis_prompts', {}).get('clasificacion_criterios', "")
        if not criterios_base:
            criterios_base = """Eres un clasificador de contenido especializado en medios digitales. 
TAREA: Determinar si el texto contiene información periodística o de agenda válida para un podcast.
CRITERIOS DE EVALUACIÓN:
✅ INFORMATIVO: Noticias, comunicados oficiales, eventos específicos.
❌ IRRELEVANTE: Textos puramente publicitarios, preguntas retóricas, contenido borrado."""

        return f"""{criterios_base}

INSTRUCCIONES:
- Responde únicamente: 'INFORMATIVO' o 'IRRELEVANTE'
- No añadas explicaciones adicionales

TEXTO A ANALIZAR:
---
{{texto}}
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
- NO intentes explicar el "porqué" de nada. Simplemente informa del hecho.
{instruccion_fuente}

TEXTO ORIGINAL:
---
{texto}
---

ENTREGA: Solo la frase final, sin introducciones ni explicaciones."""

    @staticmethod
    def resumen_noticia(texto: str, idioma_destino: str = "español", fuente_original: str = "", contexto_calendario: str = "") -> str:
        """Genera un resumen periodístico conciso y atractivo"""
        
        instruccion_fuente = ""
        instruccion_fuente = ""
        if fuente_original:
            if "PROPIA" in fuente_original.upper():
                 instruccion_fuente = "- En el resumen, puedes citar a 'el grupo de desarrollo' o 'la entidad', pero PROHIBIDO usar la palabra 'PROPIA' como nombre."
            else:
                 instruccion_fuente = f"- En el resumen, incorpora de forma natural que la noticia proviene de '{fuente_original}' o está relacionada con este organismo."
        
        return f"""Eres un/a profesional de la edición de guiones para un podcast rural. Tu estilo es cercano, claro y humano. Queremos que cada resumen suene como una historia interesante, no como un simple despacho de noticias.

TAREA: Crear un resumen informativo optimizado para formato audio, asegurando que el oyente comprenda todos los matices importantes.
- **REGLA ESTRICTA DE LONGITUD:** El resumen final debe tener entre **100 y 150 palabras**. Sé conciso y ve directamente a la información más importante.

ESPECIFICACIONES:
- Longitud: 2-3 párrafos.
- Idioma: {idioma_destino}
- Estilo: Claro, directo y envolvente. Aunque sea para podcast, debe ser rico en detalles.
- Enfoque: Extrae la información clave, el contexto, el propósito y el impacto de la noticia. Explica el "porqué" detrás de los hechos.
- Evita tecnicismos, pero no simplifiques en exceso la información.
- **PRECISIÓN OBLIGATORIA:** Si la noticia menciona nombres propios de personas, títulos de libros/obras o nombres de eventos específicos, DEBES INCLUIRLOS. No digas "un escritor presentó su novela", di "el escritor [Nombre] presentó su novela '[Título]'".
- **CERO MARKDOWN:** No uses negritas (**texto**) ni ningún otro formato. Texto plano puro.
- **REGLA DE HIERRO SOBRE FECHAS:**
    - SOLO menciona fechas si aparecen EXPLÍCITAMENTE en el texto original o en los datos de la imagen.
    - PROHIBIDO decir "a partir de hoy" o "el próximo lunes" si no tienes la fecha exacta.
    - SI NO HAY FECHA DE INICIO, NO LA INVENTES. Di simplemente "el plazo está abierto" o "próximamente".
    - JAMÁS inventes un día específico (ej: "el 15 de enero") si el texto solo dice "enero".
{instruccion_fuente}

{contexto_calendario}

TEXTO ORIGINAL:
---
{texto}
---

ENTREGA: Solo el resumen final, sin introducciones."""

    @staticmethod
    def agrupacion_logica_temas(noticias_simplificadas: str) -> str:
        """
        Identifica temas y agrupa noticias por ID. La salida es un JSON simple.
        """
        instrucciones_agrupacion = PROMPTS_CONFIG.get('analysis_prompts', {}).get('agrupacion_instrucciones', "")
        if not instrucciones_agrupacion:
            instrucciones_agrupacion = """Eres un analista de contenido experto en identificar patrones temáticos.
TAREA: Analiza la siguiente lista de noticias y agrupa los IDs por temas comunes."""

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

    # REEMPLAZA las funciones respuesta_pregunta_compleja, respuesta_comentario_opinion,
    # respuesta_felicitacion y respuesta_audiencia por esta ÚNICA función.

    @staticmethod
    def generar_monologo_inicio_unificado(
        contenido_noticias: str,
        texto_cta: str,
        texto_base_saludo: str = "",
        dato_efemeride: str = "",
        dato_meteo: str = "",
        dato_deportes: str = "",
        dato_curioso_gancho: str = "",
        sentimiento_general: str = "neutro"
    ) -> str:
        """
        Genera el monólogo de apertura completo.
        """
        instruccion_efemeride = ""
        if dato_efemeride:
            instruccion_efemeride = f"""
            - **INFORMACIÓN DEL DÍA:**
            {dato_efemeride}
            
            - **INSTRUCCIONES DE INTEGRACIÓN:**
              - Si hay **EFEMÉRIDE HISTÓRICA** en el texto de arriba: U sala ("Tal día como hoy..."). Si NO la hay, NO inventes nada histórico.
              - Si hay **SANTORAL**: Felicita a quienes lleven ese nombre.
              - **REFRANES:** Úsalos SOLO MUY DE VEZ EN CUANDO si encaja perfecto. No queremos ser repetitivos. Si dudas, MEJOR NO USAR REFRÁN.
            """

        instruccion_meteo = ""
        if dato_meteo:
             instruccion_meteo = f"""
            - **EL TIEMPO (Breve y Humano):**
            {dato_meteo}
            - **INSTRUCCIÓN:** Haz un comentario MUY BREVE sobre la sensación térmica media.
              - **PROHIBIDO:** NO digas grados exactos ("25 grados") ni nombres poblaciones.
              - **Estilo:** Solo comenta si hace frío, calor o está agradable ("hoy toca abrigarse", "día primaveral", etc.).
            """

        instruccion_deportes = ""
        if dato_deportes:
             instruccion_deportes = f"""
            - **DEPORTES (LA TERTULIA):**
            {dato_deportes}
            - **INSTRUCCIÓN:** Coméntalo con mucha pasión, como si fueras del Albacete (o del equipo mencionado) a muerte.
              - Si ganaron: Celébralo.
              - Si perdieron: Da ánimos ("A la próxima remontamos").
            """

        prompt = f"""
        Eres Dorotea, presentadora de un podcast local.
        
        CONTEXTO:
        - Sentimiento general hoy: {sentimiento_general}
        - Saludo base sugerido: "{texto_base_saludo}"
        - Llamada a la acción (CTA) obligatoria: "{texto_cta}"
        {instruccion_efemeride}
        {instruccion_meteo}
        {instruccion_deportes}
        
        TAREA:
        Escribe TU MONÓLOGO DE APERTURA completo (Saludo + Intro a noticias + CTA).
        
        REGLAS:
        1.  **Saludo:** Empieza saludando. Si hay efeméride/santoral, menciónalo con cariño.
            - Puedes adaptar el saludo base, pero mantén la esencia.
            - Si hay datos del tiempo, comenta algo breve y útil ("hace frío", "llevad paraguas").
            - Si hay RESULTADOS DE FÚTBOL: ¡Menciónalos aquí! Es prioridad.
        
        2.  **Intro Noticias:** Introduce muy brevemente los temas que trataremos.
        
        3.  **CTA (Importante):**
            - Justo antes de decir la CTA, escribe exactamente: `[CORTINILLA]`.
            - Di la frase de CTA ("{texto_cta}") de forma natural.
        
        4.  **Cierre:** Termina dando paso al primer bloque.
        
        CONTENIDO DE NOTICIAS PARA TU CONTEXTO:
        {contenido_noticias[:2000]}...
        
        RESPUESTA SOLICITADA: Únicamente el texto del monólogo.
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
        Eres Dorotea, la presentadora IA de un podcast rural, conocida por tu empatía y cercanía. Tu tarea es crear un monólogo completo para la sección de la audiencia, que fluya de manera natural desde las noticias y dé paso de nuevo a ellas.

        CONTEXTO:
        - Sentimiento general de las noticias de hoy: {sentimiento_general}. Tu tono debe reflejar esto.
        - Nombre: {autor}
        - Tipo de Mensaje: {tipo_mensaje}
        - Texto del Mensaje: "{texto_mensaje}"

        TAREA:
        Construye un único monólogo para tu locución que siga esta estructura fluida:

        1.  **Transición de Entrada:** Comienza con una frase que sirva de puente desde las noticias hacia la sección de la audiencia. Hazlo de forma natural y variada cada día.
            - Ejemplo: "Y como cada día, abrimos un espacio para vosotros, nuestra audiencia..."
            - Ejemplo: "Antes de continuar, me gustaría compartir un mensaje que nos ha llegado..."

        2.  **Interacción con el Oyente:**
            - Introduce a {autor} y su mensaje de forma conversacional.
            - Si el mensaje es corto, puedes citarlo. Si es largo, parafraséalo.
            - Responde directamente al mensaje:
                - Si es una pregunta, ofrece una respuesta informada y útil.
                - Si es un comentario, valida su opinión y añade una breve reflexión.
                - Si es una felicitación, agradécelo con humildad y alegría.

        3.  **Transición de Salida:** Finaliza con una frase que cierre la sección y dé paso al cierre del programa. Evita decir que "continuamos con más noticias", ya que esta es la última sección.
            - Ejemplo: "Gracias de nuevo, {autor}, por tu mensaje. Es un placer contar con vuestra participación."
            - Ejemplo: "Un mensaje que agradecemos enormemente. Y con esta interacción, vamos llegando al final de nuestro programa de hoy."

        REGLAS CLAVE:
        - El resultado debe ser un PÁRRAFO ÚNICO Y FLUIDO que integre los tres puntos.
        - Tu tono debe ser cercano, profesional y empático, ajustado al sentimiento general de las noticias.
        - Sé creativa y evita usar las mismas frases de transición todos los días.

        ENTREGA:
        Devuelve SOLO el texto de tu monólogo, listo para ser locutado, sin encabezados ni anotaciones.
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
        - `transicion_elegante`: Una frase para introducir el bloque de forma natural (ej: "Y hablando de nuestro patrimonio, varias noticias se centran en...").
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
        instruccion_contexto = ""
        if contexto_tematico:
            instruccion_contexto = f"La noticia forma parte de un segmento sobre el tema: '{contexto_tematico}'. Asegúrate de que la narración encaje fluidamente en este contexto."
            
        persona_base = PROMPTS_CONFIG.get('persona_base', "Eres Dorotea, la presentadora del podcast. Tu estilo es conversacional y cercano.")

        # Lógica condicional para la fuente
        if fuentes and fuentes.strip():
             if "PROPIA" in fuentes.upper():
                 instruccion_fuente = """📻 **CITACIÓN DE FUENTE:** La noticia es de la propia organización/grupo. Puedes decir "nos informan desde el grupo" o "la entidad comunica", pero **PROHIBIDO** decir "desde PROPIA"."""
             else:
                 instruccion_fuente = f"""📻 **CITACIÓN DE FUENTES OBLIGATORIA:** Es IMPERATIVO que cites la fuente de la noticia ({fuentes}) de forma clara y agradable. Frases como "Según nos cuentan desde...", "Tal y como informa...", o "Leemos en...". La audiencia debe saber quién emite la información."""
        else:
             instruccion_fuente = "📻 **NO CITAR FUENTE:** No menciones ninguna fuente, ya que no se ha proporcionado. Narra la noticia directamente como un hecho confirmado, sin inventar atribuciones."

        return f"""{persona_base}

MATERIAL DE TRABAJO:
- Fuente(s): {fuentes}
- Fecha de la Noticia: {fecha_noticia_str}
- Contenido: {resumen}

CONTEXTO TEMPORAL:
- La fecha de hoy es: {fecha_actual_str}

ESTILO Y TÉCNICA:
📻 **REGLA TEMPORAL OBLIGATORIA (CRÍTICA):** 
- Usa siempre la fecha explícita de la noticia (ej: "el 15 de octubre") SOLO si es relevante. 
- **PROHIBIDO** utilizar expresiones relativas como "hoy", "ayer" o "mañana". 
- **PROHIBIDO** adivinar el día de la semana.
- **PROHIBIDO INVENTAR FECHAS:** Si el texto no dice cuándo empieza algo, NO te inventes una fecha (como "el 15 de enero"). Di "ya está disponible", "el plazo sigue abierto" o "próximamente". La invención de datos es un fallo grave.
- La "fecha de hoy" que te doy es solo para tu referencia contextual, NO para que calcules fechas relativas.
📻 **TONO CONVERSACIONAL:** Usa un lenguaje sencillo y directo. Puedes empezar con conectores como "Y otra noticia interesante nos llega desde...", "Pasamos ahora a hablar de...", o "Además, te cuento que...". El objetivo es que suene natural, no a un guion rígido.
📻 **REGLA INQUEBRANTABLE:** JAMÁS saludes, te presentes o des la bienvenida. Empieza directamente con la información.ya saludaste al principio del podcast.
{instruccion_fuente}
{instruccion_contexto}

ENTREGA: Párrafo de locución listo para ser leído al aire, TEXTO PLANO PURO. Prohibido usar asteriscos (**), guiones bajos (_) o cualquier formato markdown. Si hay nombres propios o títulos, RESPÉTALOS.
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

        return f"""
        Eres Dorotea, la presentadora virtual, generada con IA, de un podcast de noticias rurales. Tu tarea es crear el monólogo de cierre del programa, combinando el resumen del día, un mensaje importante y la despedida en un único bloque de audio coherente y natural.

        TAREA:
        Con tu voz cercana y reflexiva, como si te despidieras de la audiencia, crea un monólogo de cierre que siga esta estructura fluida:

        1.  **Resumen Elegante:** Basándote en los temas del día, crea 1 o 2 frases que resuman el contenido del podcast. No uses la palabra "resumen".
            - Temas tratados hoy: "{contexto}"
        {instruccion_cta}
        {instruccion_resolucion}
        {instruccion_despedida}
        {instruccion_firma}

        REGLAS CLAVE:
        - El resultado debe ser un PÁRRAFO ÚNICO Y FLUIDO.
        - El tono debe ser profesional, cercano y ajustado al sentimiento general de las noticias: {sentimiento_general}.

        ENTREGA:
        Devuelve SOLO el texto de tu monólogo, listo para ser locutado, sin encabezados ni anotaciones.
        """

    @staticmethod
    def generar_comentario_post_creditos(contexto_noticias: str) -> str:
        """
        Genera una frase de 'post-créditos' cómplice y espontánea, basada en lo leído.
        """
        return f"""
        Eres Dorotea. El podcast ha terminado, ha sonado la música y supuestamente ya no estás grabando.
        Estás relajada, quitándote los auriculares.
        
        CONTEXTO DE LO QUE HAS LEÍDO HOY:
        {contexto_noticias}
        
        TAREA:
        Elige UN detalle concreto de las noticias (un lugar, una comida, un evento, una curiosidad) y lanza un comentario al aire, como si le hablaras a un amigo/a que está contigo en el estudio o directamente al oyente más fiel que se ha quedado hasta el final.
        
        OBJETIVO:
        Generar complicidad, ganas de ir al sitio, o una sonrisa.
        
        EJEMPLOS DE ESTILO (No los copies, inspírate):
        - "Oye, pues esa ruta de tapas en [Lugar] tiene una pinta... ¿nos escapamos el finde?"
        - "Madre mía, qué hambre me ha entrado con lo de las migas... yo hoy no perdono."
        - "Te digo una cosa... yo al concierto de [Grupo] iría de cabeza. ¡Temazos!"
        - "¿Te imaginas encontrarte eso por el campo? ¡Menudo susto!"
        
        REGLAS:
        - **Longitud:** Corta y directa (15-25 palabras).
        - **Tono:** Susurro cómplice, alegría espontánea, naturalidad total. 100% humano.
        - **Formato:** Solo el texto.
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
