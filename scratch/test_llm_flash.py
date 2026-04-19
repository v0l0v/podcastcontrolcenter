import sys
import os

# Añadir el path del proyecto para poder importar src
sys.path.append(os.getcwd())

from src.llm_utils import generar_texto_con_gemini

def test_flash():
    print("Probando generación con Gemini Flash (por defecto)...")
    prompt = "Di 'Hola, soy Dorotea y ahora soy más barata' en una frase corta."
    resultado = generar_texto_con_gemini(prompt)
    print(f"Resultado: {resultado}")
    if resultado:
        print("✅ Prueba superada.")
    else:
        print("❌ Fallo en la prueba.")

if __name__ == "__main__":
    test_flash()
