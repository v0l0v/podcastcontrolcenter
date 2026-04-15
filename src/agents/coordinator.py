from typing import Dict, Any, List
import os
from datetime import datetime

from src.agents.base import BaseAgent
from src.agents.researcher import ResearcherAgent
from src.agents.writer import WriterAgent
from src.agents.audio import AudioAgent
from src.agents.publisher import PublisherAgent
from src.monitoring import logger

class CoordinatorAgent(BaseAgent):
    """
    Agente Orquestador. Encargado de coordinar el flujo de trabajo
    entre Researcher, Writer, Audio, y Publisher agents.
    """
    def __init__(self, name: str = "CoordinatorAgent"):
        super().__init__(name=name)
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.audio = AudioAgent()
        self.publisher = PublisherAgent()

    def execute(self, feeds_file: str, output_dir: str, timestamp: str, solo_preview: bool = False,
                idioma_destino: str = 'es', window_hours_override: int = None,
                max_items_override: int = None, archivo_entrada_json: str = None) -> None:

        logger.step("Inicio del Proceso", "START")
        logger.info(f"Directorio de salida: {output_dir}")

        # Fase 1: Research
        resumenes_noticiero, resumenes_agenda, noticias_descartadas = self.researcher.execute(
            feeds_file=feeds_file,
            idioma_destino=idioma_destino,
            window_hours_override=window_hours_override,
            max_items_override=max_items_override,
            archivo_entrada_json=archivo_entrada_json
        )

        if not (resumenes_noticiero or resumenes_agenda):
            logger.error("No hay noticias válidas tras el filtrado.")
            return

        # Fase 2: Writer
        script_data = self.writer.execute(
            resumenes_noticiero=resumenes_noticiero,
            resumenes_agenda=resumenes_agenda,
            solo_preview=solo_preview
        )

        if solo_preview:
            # En modo preview, se delega a Writer hacer el guardado en json
            # Pero podemos hacerlo aquí en el coordinador para mejor estructura
            import json
            archivo_preview = "prevision_noticias_resumidas.json"
            def format_fechas_noticias(lista):
                for n_c in lista:
                    if 'fecha' in n_c and isinstance(n_c['fecha'], datetime):
                         n_c['fecha'] = n_c['fecha'].strftime("%Y-%m-%d")

            noticias_agrupadas = script_data
            for bloque in noticias_agrupadas.get('bloques_tematicos', []):
                format_fechas_noticias(bloque.get('noticias', []))
            format_fechas_noticias(noticias_agrupadas.get('noticias_individuales', []))

            with open(archivo_preview, 'w', encoding='utf-8') as f:
                json.dump(noticias_agrupadas, f, indent=4, ensure_ascii=False)

            print(f"✅ Preview ESTRUCTURADA guardada en: {archivo_preview}")
            try: os.rmdir(output_dir)
            except: pass
            return

        # Fase 3 & 4: Audio Synth and Assembly
        output_audio_filename = os.path.join(output_dir, f"podcast_completo_{timestamp}.mp3")
        final_audio_path, transcript_data = self.audio.execute(
            script_data=script_data,
            output_path=output_audio_filename,
            timestamp=timestamp
        )

        # Fase 5: Publishing
        self.publisher.execute(
            transcript_data=transcript_data,
            output_dir=output_dir,
            timestamp=timestamp,
            audio_path=final_audio_path
        )

        print(f"\n🎉 ¡Podcast generado con éxito! Archivo: {final_audio_path}")
