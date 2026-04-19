import json
import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path

# Configuración de archivos de log
LOG_DIR = Path("logs")
PROCESS_LOG_FILE = LOG_DIR / "process_log.jsonl"
USAGE_LOG_FILE = LOG_DIR / "usage_stats.json"

LOG_DIR.mkdir(exist_ok=True)

class ServiceType(Enum):
    GEMINI_FLASH = "gemini_flash"
    GEMINI_PRO = "gemini_pro"
    TTS_STANDARD = "tts_standard"
    TTS_WAVENET = "tts_wavenet"
    TTS_NEURAL2 = "tts_neural2"
    TTS_JOURNEY = "tts_journey"
    TTS_CHIRP = "tts_chirp"

class UsageTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UsageTracker, cls).__new__(cls)
            cls._instance.stats = {
                "gemini_input_tokens": 0,
                "gemini_output_tokens": 0,
                "tts_chars": 0,
                "api_calls": {s.value: 0 for s in ServiceType},
                "estimated_cost": 0.0
            }
            cls._instance.load_stats()
        return cls._instance

    def load_stats(self):
        if USAGE_LOG_FILE.exists():
            try:
                with open(USAGE_LOG_FILE, 'r') as f:
                    data = json.load(f)
                    # Resetear si es un nuevo mes o día (lógica simple por ahora: carga histórico)
                    # Podríamos implementar reset diario aquí.
                    self.stats.update(data)
            except Exception:
                pass

    def save_stats(self):
        self.calculate_cost()
        with open(USAGE_LOG_FILE, 'w') as f:
            json.dump(self.stats, f, indent=4)

    def calculate_cost(self):
        """
        Calcula el coste estimado basado en los precios actuales (Pay-as-you-go).
        Precios aproximados en USD.
        """
        # --- GEMINI (Precios por millón de tokens) ---
        FLASH_INPUT_PRICE = 0.075 / 1_000_000
        FLASH_OUTPUT_PRICE = 0.30 / 1_000_000
        PRO_INPUT_PRICE = 3.50 / 1_000_000
        PRO_OUTPUT_PRICE = 10.50 / 1_000_000

        # --- TTS (Precios por millón de caracteres) ---
        TTS_STANDARD_PRICE = 4.0 / 1_000_000
        TTS_NEURAL_PRICE = 16.0 / 1_000_000
        TTS_CHIRP_PRICE = 30.0 / 1_000_000  # Chirp 3 HD estimado

        # Estimación simplificada: asumimos que todos los tokens flash son input/output balanceado 
        # Pero como los guardamos por separado, podemos ser precisos si registramos qué modelo hizo qué.
        # Por ahora, como track_gemini no separa input/output por modelo en el histórico, 
        # usaremos una aproximación basada en el número de llamadas o guardaremos los tokens por modelo.
        
        # MEJORA: Para ser precisos, el tracker debería guardar tokens_flash y tokens_pro por separado.
        # Como no quiero romper la estructura actual del JSON drásticamente, haré una estimación
        # basada en que la mayoría de tokens ahora son Flash.
        
        cost = 0.0
        
        # Si queremos ser precisos, necesitamos cambiar cómo guardamos los tokens.
        # Vamos a añadir campos ocultos para el cálculo si no existen.
        ti_flash = self.stats.get("tokens_input_flash", 0)
        to_flash = self.stats.get("tokens_output_flash", 0)
        ti_pro = self.stats.get("tokens_input_pro", 0)
        to_pro = self.stats.get("tokens_output_pro", 0)
        
        cost += (ti_flash * FLASH_INPUT_PRICE) + (to_flash * FLASH_OUTPUT_PRICE)
        cost += (ti_pro * PRO_INPUT_PRICE) + (to_pro * PRO_OUTPUT_PRICE)
        
        # TTS
        chars = self.stats.get("tts_chars", 0)
        # Aproximación por el tipo de llamadas mayoritario
        calls = self.stats.get("api_calls", {})
        if calls.get("tts_chirp", 0) > 0 or calls.get("tts_journey", 0) > 0:
            cost += chars * TTS_CHIRP_PRICE
        elif calls.get("tts_neural2", 0) > 0:
            cost += chars * TTS_NEURAL_PRICE
        else:
            cost += chars * TTS_STANDARD_PRICE
            
        self.stats["estimated_cost"] = round(cost, 4)

    def track_gemini(self, input_tokens: int, output_tokens: int, model: str = "flash"):
        self.stats["gemini_input_tokens"] += input_tokens
        self.stats["gemini_output_tokens"] += output_tokens
        
        # Guardar tokens por modelo para cálculo exacto
        if "flash" in model.lower():
            service = ServiceType.GEMINI_FLASH
            self.stats["tokens_input_flash"] = self.stats.get("tokens_input_flash", 0) + input_tokens
            self.stats["tokens_output_flash"] = self.stats.get("tokens_output_flash", 0) + output_tokens
        else:
            service = ServiceType.GEMINI_PRO
            self.stats["tokens_input_pro"] = self.stats.get("tokens_input_pro", 0) + input_tokens
            self.stats["tokens_output_pro"] = self.stats.get("tokens_output_pro", 0) + output_tokens

        self.stats["api_calls"][service.value] += 1
        self.save_stats()

    def track_tts(self, chars: int, voice_name: str):
        self.stats["tts_chars"] += chars
        
        if "Standard" in voice_name:
            service = ServiceType.TTS_STANDARD
        elif "Wavenet" in voice_name:
            service = ServiceType.TTS_WAVENET
        elif "Neural2" in voice_name:
            service = ServiceType.TTS_NEURAL2
        elif "Journey" in voice_name:
            service = ServiceType.TTS_JOURNEY
        elif "Chirp" in voice_name:
            service = ServiceType.TTS_CHIRP
        else:
            service = ServiceType.TTS_STANDARD
            
        self.stats["api_calls"][service.value] += 1
        self.save_stats()
    
    def get_summary(self):
        return self.stats

class ProcessLogger:
    """Registra eventos del proceso en un formato fácil de leer para la UI."""
    
    def __init__(self, process_id=None):
        self.process_id = process_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        # Limpiar log anterior al iniciar un nuevo proceso principal
        if PROCESS_LOG_FILE.exists():
             # Opcional: Rotar logs. Por ahora sobreescribimos o vaciamos para la vista en tiempo real.
             # Para "Append" mode continuo, quitar esto. 
             # Pero para la UI que muestra "El proceso actual", mejor limpiar al inicio de run.
             pass

    @staticmethod
    def clear_logs():
        with open(PROCESS_LOG_FILE, 'w') as f:
            f.write("")

    def log(self, message: str, level: str = "INFO", details: dict = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details or {}
        }
        
        # Escribir a archivo JSONL (append)
        with open(PROCESS_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
        # También imprimir a stdout para que el backend lo vea si es necesario
        # (Aunque dorototal.py ya imprime, esto duplicaría si no tenemos cuidado)
        # print(f"[{level}] {message}") 

    def info(self, message, **kwargs):
        self.log(message, "INFO", kwargs)
        
    def success(self, message, **kwargs):
        self.log(message, "SUCCESS", kwargs)

    def warning(self, message, **kwargs):
        self.log(message, "WARNING", kwargs)

    def error(self, message, **kwargs):
        self.log(message, "ERROR", kwargs)

    def step(self, step_name, status="START"):
        self.log(f"Etapa: {step_name}", "STEP", {"status": status})

# Instancia global para uso sencillo
logger = ProcessLogger()
tracker = UsageTracker()
