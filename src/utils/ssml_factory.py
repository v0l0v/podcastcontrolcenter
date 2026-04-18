
import html

class SSMLFactory:
    """
    Fábrica centralizada para generar etiquetas SSML (Speech Synthesis Markup Language).
    Asegura que el texto esté correctamente escapado y formateado para la síntesis de voz.
    """

    @staticmethod
    def wrap_speak(content: str) -> str:
        """Envuelve el contenido en etiquetas <speak>."""
        if content.startswith("<speak>"):
            return content
        return f"<speak>{content}</speak>"

    @staticmethod
    def prosody(text: str, rate: str = "medium", volume: str = "medium", pitch: str = "medium") -> str:
        """Aplica etiquetas de prosodia (ritmo, volumen, tono)."""
        escaped_text = html.escape(text)
        return f'<prosody rate="{rate}" volume="{volume}" pitch="{pitch}">{escaped_text}</prosody>'

    @staticmethod
    def pause(ms: int = 500) -> str:
        """Inserta una pausa de X milisegundos."""
        return f'<break time="{ms}ms"/>'

    @staticmethod
    def emphasis(text: str, level: str = "moderate") -> str:
        """Aplica énfasis a un fragmento de texto."""
        escaped_text = html.escape(text)
        return f'<emphasis level="{level}">{escaped_text}</emphasis>'

    @staticmethod
    def whisper(text: str) -> str:
        """Genera un efecto de susurro (prosody volume='soft')."""
        return SSMLFactory.prosody(text, volume="soft", rate="slow")

    @staticmethod
    def sentence_bundle(sentences: list, rate: str = "medium", break_ms: int = 450) -> str:
        """Agrupa varias frases con una prosodia y pausa común entre ellas."""
        bundle = ""
        for sentence in sentences:
            if sentence.strip():
                bundle += f'{SSMLFactory.prosody(sentence.strip(), rate=rate)}{SSMLFactory.pause(break_ms)}'
        return bundle
