import os
import sys
import json
import time

# Añadir el path al proyecto para importar configuraciones si las necesitas (como las keys de Gemini)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ Error: Necesitas instalar la librería google-genai.")
    print("Prueba a ejecutar: pip install google-genai")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv no encontrado, asumiendo variables de entorno ya cargadas.")

# Asegurarte de que la API key está presente (la puedes coger del entorno o de tu .env)
# Asume que se ha cargado en el entorno antes de ejecutar, o lo configuras aquí
if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
    
if "GEMINI_API_KEY" not in os.environ:
    print("⚠️ Recuerda cargar GOOGLE_API_KEY o GEMINI_API_KEY en tu entorno antes de ejecutar.")

client = genai.Client()

# Prompt especializado para extracción de datos culturales
PROMPT_EXTRACCION = """
Eres un erudito experto en historia, folclore y tradiciones de Castilla-La Mancha.
Acabo de pasarte un documento con información sobre costumbres locales, historia o folclore.

Tu objetivo es leer este documento y extraer elementos muy valiosos y concretos que podamos usar en una IA locutora de radio para dar "toque humano" a sus guiones.

Necesito que devuelvas ÚNICAMENTE un JSON estructurado con las siguientes claves y listas:

{
  "oficios_tradicionales": [
    "lista de oficios mencionados (ej: alfareros, esparteros), pero dales acción. Ej: 'los esparteros tejiendo la pleita'"
  ],
  "comidas_tipicas": {
    "Nombre de la provincia o comarca si se menciona": [
       "plato 1 que se mencione",
       "plato 2"
    ],
    "Castilla-La Mancha General": [
       "plato 3",
       "..."
    ]
  },
  "refranes_o_dichos": [
    "lista de sabiduria popular tal cual aparece en el texto"
  ]
}

Reglas:
1. Extrae SOLO información que aparezca explícitamente en el PDF. No inventes.
2. Si un apartado (ej. refranes) no aparece en el texto, déjalo vacío [].
3. La salida debe ser JSON puro, sin marcadores markdown de código (```json).
"""

def analizar_pdf(ruta_pdf: str) -> dict:
    if not os.path.exists(ruta_pdf):
        print(f"❌ El archivo {ruta_pdf} no existe.")
        return {}

    print(f"📄 Subiendo {ruta_pdf} a Gemini (File API)...")
    
    try:
        # Subir el archivo
        # En la API v2 de genai, subir archivos requiere permisos. 
        # Si prefieres evitar la API de File (por si da problemas con tu project ID),
        # también se puede instalar PyPDF2 y mandarlo como texto, pero la File API de genai es genial para PDFs puros.
        archivo_gemini = client.files.upload(file=ruta_pdf)
        print(f"✅ Archivo subido exitosamente. URI: {archivo_gemini.uri}")
        
        # Generar contenido
        print("🤖 Analizando y extrayendo costumbrismo... (esto puede tardar unos segundos)")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[archivo_gemini, PROMPT_EXTRACCION],
            config=types.GenerateContentConfig(
                temperature=0.2, # Baja temperatura porque queremos extracción factual, no inventada.
                response_mime_type="application/json"
            )
        )
        
        # Eliminar el archivo para no acumular basura en tu proyecto GCP
        client.files.delete(name=archivo_gemini.name)
        
        texto_limpio = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(texto_limpio)
        return data
        
    except Exception as e:
        print(f"❌ Error procesando {ruta_pdf}: {e}")
        return {}

def main():
    directorio_datos = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    print("==================================================")
    print("🌾 EXTRACTOR DE COSTUMBRISMO MANCHEGO 🌾")
    print("==================================================")
    
    # Busca PDFs en la carpeta data y subcarpetas
    archivos_pdf = []
    for root, _, files in os.walk(directorio_datos):
        for f in files:
            if f.lower().endswith('.pdf'):
                ruta_completa = os.path.join(root, f)
                ruta_relativa = os.path.relpath(ruta_completa, directorio_datos)
                archivos_pdf.append((ruta_completa, ruta_relativa))
    
    if not archivos_pdf:
        print(f"ℹ️ No se encontraron archivos PDF en '{directorio_datos}' o sus subcarpetas.")
        print("Sube ahí tus PDFs divididos (ej. oficios.pdf, refranes.pdf) y vuelve a ejecutar.")
        return

    print("Se encontraron los siguientes PDFs:")
    for idx, (_, ruta_relativa)  in enumerate(archivos_pdf):
        print(f"  [{idx+1}] {ruta_relativa}")
    
    print("\nProcesando todos uno por uno...")
    
    todos_los_datos = []
    
    for ruta_completa, ruta_relativa in archivos_pdf:
        datos = analizar_pdf(ruta_completa)
        if datos:
            todos_los_datos.append({
                "origen": ruta_relativa,
                "extraccion": datos
            })
            
    # Guardar resultados
    if todos_los_datos:
        ruta_salida = os.path.join(directorio_datos, 'costumbrismo_extraido.json')
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            json.dump(todos_los_datos, f, ensure_ascii=False, indent=4)
        print(f"\n✅ ¡Trabajo completado! Resultados guardados en: {ruta_salida}")
        print("Ahora puedes copiar esos datos en tu archivo 'costumbrismo.py'")

if __name__ == "__main__":
    main()
