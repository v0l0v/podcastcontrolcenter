import os
from typing import List, Dict, Any

from src.agents.base import BaseAgent
from dorototal import generar_html_transcripcion
from src.wp_publisher import publish_podcast_to_wp

class PublisherAgent(BaseAgent):
    """
    Agente encargado de la Fase Final:
    Generar el archivo HTML con la transcripción y enviarlo a WordPress.
    """
    def __init__(self, name: str = "PublisherAgent"):
        super().__init__(name=name)

    def execute(self, transcript_data: List[Dict[str, Any]], output_dir: str, timestamp: str, audio_path: str) -> None:
        print("\n--- FASE 5: Publicación y Distribución ---")

        # 1. Generar HTML de Transcripción
        generar_html_transcripcion(transcript_data, output_dir, timestamp)
        html_path = os.path.join(output_dir, f"podcast_summary_{timestamp}.html")

        # 2. Publicar en WordPress si el HTML y Audio existen
        if os.path.exists(audio_path) and os.path.exists(html_path):
             publish_podcast_to_wp(audio_path, html_path)
        else:
             print("⚠️ No se encontró el audio o el HTML, omitiendo publicación en WP.")
