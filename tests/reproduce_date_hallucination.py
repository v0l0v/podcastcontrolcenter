
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm_utils import generar_texto_con_gemini
import mcmcn_prompts

def test_date_hallucination():
    print("Testing date hallucination fix...")
    
    # Text provided by the user (simulated input)
    texto_noticia = """
    Ayuntamiento de Ciruelos
    COMIDA A DOMICILIO DE PERSONAS MAYORES
    El Ayuntamiento de Ciruelos junto con la Diputación de Toledo gestionará el servicio de comidas a domicilio con la empresa Gesgourmet.
    Periodo de valided: hasta el 31 de diciembre de 2026
    La Diputación Provincial de Toledo establece una subvención de 5 € por menú diario.
    Fecha límite para el envío: 9 de febrero de 2026 a las 14:00.
    """
    
    # We want to check both the summary and the professional narration if possible, 
    # but the user reported the issue in the generated output which seems to come from 'resumen_noticia' 
    # (as it appeared in the 'resumen de dorotea' section).
    
    # Let's test `mcmcn_prompts.PromptsAnalisis.resumen_noticia`
    prompt = mcmcn_prompts.PromptsAnalisis.resumen_noticia(
        texto=texto_noticia,
        idioma_destino="español",
        fuente_original="Ayuntamiento de Ciruelos",
        contexto_calendario="Fecha actual: 26 de enero de 2026"
    )
    
    print("\n--- Generating Summary ---")
    resumen = generar_texto_con_gemini(prompt)
    print(f"Generated Summary:\n{resumen}\n")
    
    if "15 de enero" in resumen:
        print("❌ FAILURE: Date hallucination detected ('15 de enero' found).")
        sys.exit(1)
    else:
        print("✅ SUCCESS: No '15 de enero' hallucination found in summary.")

    # Let's also test `mcmcn_prompts.PromptsCreativos.narracion_profesional` just in case
    prompt_narration = mcmcn_prompts.PromptsCreativos.narracion_profesional(
        fuentes="Ayuntamiento de Ciruelos",
        resumen=resumen, # Feed the generated summary
        fecha_noticia_str="26/01/2026",
        fecha_actual_str="26 de enero de 2026"
    )

    print("\n--- Generating Narration ---")
    narracion = generar_texto_con_gemini(prompt_narration)
    print(f"Generated Narration:\n{narracion}\n")

    if "15 de enero" in narracion:
        print("❌ FAILURE: Date hallucination detected in narration ('15 de enero' found).")
        sys.exit(1)
    else:
        print("✅ SUCCESS: No '15 de enero' hallucination found in narration.")

if __name__ == "__main__":
    test_date_hallucination()
