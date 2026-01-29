
import sys
import os
from datetime import datetime

# Adjust path to find modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import mcmcn_prompts

def verify_date_injection():
    # Mock data
    news_content = "Noticia de prueba."
    cta = "Suscríbete."
    
    # Current date for verification
    today_str = datetime.now().strftime("%A, %d de %B de %Y")
    
    # Generate prompt
    prompt = mcmcn_prompts.PromptsCreativos.generar_monologo_inicio_unificado(
        contenido_noticias=news_content,
        texto_cta=cta,
        fecha_actual_str=today_str
    )
    
    print(f"[-] Fecha enviada: {today_str}")
    
    if today_str in prompt:
        print("[SUCCESS] La fecha actual está presente en el prompt generado.")
        return True
    else:
        print("[FAIL] La fecha actual NO se encontró en el prompt.")
        return False

if __name__ == "__main__":
    verify_date_injection()
