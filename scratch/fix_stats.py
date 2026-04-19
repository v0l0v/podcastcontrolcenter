import json
from pathlib import Path

USAGE_LOG_FILE = Path("logs/usage_stats.json")

if USAGE_LOG_FILE.exists():
    with open(USAGE_LOG_FILE, 'r') as f:
        stats = json.load(f)
    
    # Datos actuales
    ti_total = stats.get("gemini_input_tokens", 0)
    to_total = stats.get("gemini_output_tokens", 0)
    calls = stats.get("api_calls", {})
    c_flash = calls.get("gemini_flash", 0)
    c_pro = calls.get("gemini_pro", 0)
    
    # Estimación de reparto histórico (asumimos que Pro gasta más por llamada)
    # Pro suele ser para resúmenes complejos (~8000 tokens)
    # Flash para filtros y extracciones (~1000 tokens)
    ti_pro = min(ti_total, c_pro * 15000) # Estimación conservadora al alza para Pro
    ti_flash = ti_total - ti_pro
    
    to_pro = min(to_total, c_pro * 500)
    to_flash = to_total - to_pro
    
    stats["tokens_input_flash"] = ti_flash
    stats["tokens_output_flash"] = to_flash
    stats["tokens_input_pro"] = ti_pro
    stats["tokens_output_pro"] = to_pro
    
    # Precios
    cost = (ti_flash * 0.075 / 1e6) + (to_flash * 0.30 / 1e6)
    cost += (ti_pro * 3.50 / 1e6) + (to_pro * 10.50 / 1e6)
    
    # TTS (Chirp 3 HD)
    cost += stats.get("tts_chars", 0) * 30.0 / 1e6
    
    stats["estimated_cost"] = round(cost, 4)
    
    with open(USAGE_LOG_FILE, 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Estadísticas actualizadas. Coste estimado histórico: ${stats['estimated_cost']}")
