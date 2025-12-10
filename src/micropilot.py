
import os
import json
import time
import random
import sys
from datetime import datetime
from dotenv import load_dotenv

# Asegurar acceso a módulos raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import mcmcn_prompts
except ImportError:
    # Fallback si falla el import directo
    pass

import google.generativeai as genai
from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel

load_dotenv()

class MicropilotGenerator:
    def __init__(self):
        self.project_id = os.getenv('GCP_PROJECT_ID')
        self.location = os.getenv('GCP_LOCATION', 'us-central1')
        self._init_gemini()

    def _init_gemini(self):
        """Inicializa el cliente de Gemini (intentando SDK nuevo y luego Vertex)."""
        try:
            # Opción A: SDK Google Generative AI (API Key o ADC)
            api_key = os.getenv('GOOGLE_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                self.mode = "genai"
            else:
                # Opción B: Vertex AI
                vertexai.init(project=self.project_id, location=self.location)
                self.model = GenerativeModel("gemini-2.0-flash-lite-preview-02-05")
                self.mode = "vertex"
        except Exception as e:
            print(f"Error init Gemini: {e}")
            self.model = None

    def _generate_text(self, prompt):
        if not self.model:
            return "Error: Modelo no inicializado."
        
        try:
            if self.mode == "genai":
                response = self.model.generate_content(prompt)
                return response.text
            else:
                response = self.model.generate_content(prompt)
                return response.text
        except Exception as e:
            return f"Error generando texto: {e}"

    def process_raw_input(self, raw_text, group_name="Grupo Local"):
        """
        Toma texto crudo (copiado de una web o email) y extrae 3 noticias clave.
        Devuelve un objeto compatible con el JSON de dorototal.py.
        """
        
        prompt = f"""
        Eres un editor de noticias experto. Tienes el contenido en bruto de un boletín o página web de "{group_name}".
        
        TU TAREA:
        1. Analizar el texto y extraer las 3 noticias más relevantes, recientes e impactantes.
        2. Para cada noticia, generar un JSON con:
           - "titulo": Titular atractivo (max 10 palabras).
           - "resumen": Un resumen completo de 80-100 palabras para ser leído en radio. Estilo cercano y claro.
           - "sitio": "{group_name}" (o la fuente específica si se menciona).
           - "fecha": La fecha del evento/noticia (format YYYY-MM-DD o texto "Hace 2 días"). Si no hay fecha, usa la de hoy.
           - "id": un identificador único (ej. "news_01").
        
        TEXTO ORIGINAL:
        ---
        {raw_text[:15000]} 
        ---
        (El texto puede estar cortado, infiere lo necesario).

        SALIDA ESPERADA:
        ÚNICAMENTE UN JSON ARRAY VÁLIDO.
        [
            {{ "titulo": "...", "resumen": "...", "sitio": "...", "fecha": "...", "id": "..." }},
            ...
        ]
        """
        
        response = self._generate_text(prompt)
        
        # Limpieza básica de markdown
        response = response.replace("```json", "").replace("```", "").strip()
        
        try:
            news_data = json.loads(response)
            return news_data
        except json.JSONDecodeError:
            print("Error parseando JSON de Gemini. Raw:", response)
            return []

    def generate_email_draft(self, contact_name, group_name, pilot_url="[ENLACE_AQUÍ]"):
        """Genera el borrador del correo para el 'Micropiloto'."""
        return f"""
ASUNTO: He creado un episodio piloto para {group_name} (Demo Audio)

Hola {contact_name},

Espero que estés muy bien.

Soy Víctor, de Micomicona. He estado siguiendo la actividad de {group_name} y me ha parecido muy interesante vuestro trabajo reciente.

Para probar una nueva tecnología de comunicación que estamos desarrollando, me he tomado la libertad de crear un **mini-podcast generado por Inteligencia Artificial** con las noticias de vuestra última semana.

🎧 **Puedes escucharlo aquí (duración 3 min):**
{pilot_url}

Es un piloto automático que permite convertir vuestros boletines en radio profesional al instante. Me encantaría saber tu opinión sincera: ¿crees que esto sería útil para vuestros voluntarios?

Quedo a la espera de tus comentarios.

Un saludo,

Víctor
Micomicona Project
        """

def generate_pilot(text_input, group_name):
    generator = MicropilotGenerator()
    news_json = generator.process_raw_input(text_input, group_name)
    
    # Guardar para dorototal.py
    filename = "seleccion_usuario.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(news_json, f, indent=4, ensure_ascii=False)
        
    return news_json, filename

if __name__ == "__main__":
    # Test simple
    gen = MicropilotGenerator()
    print("Micropilot Generator Initialized.")
