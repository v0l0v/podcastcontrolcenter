import os
import sys
import json
import argparse
from datetime import datetime
from src.utils import cargar_configuracion, guardar_configuracion
from src.news_engine import procesar_feeds
from src.content_generator import agrupar_noticias_logica, enriquecer_tema, generar_cronica_bloque, generar_monologo_inicio_unificado, generar_monologo_cierre_unificado
from src.audio_engine import generar_tts, mezclar_con_fondo, masterizar_audio
from pydub import AudioSegment

# --- CONFIGURACIÓN ---
CONFIG = cargar_configuracion()
FEEDS_FILE = 'feeds.txt'
OUTPUT_DIR_BASE = 'podcast_apg'

def main():
    parser = argparse.ArgumentParser(description="Micomicona Podcast Generator v2")
    parser.add_argument("--manual", action="store_true", help="Modo manual: solo procesa noticias, no genera audio final")
    args = parser.parse_args()
    
    print("🚀 Iniciando MicomiconaPG v2...")
    
    # 1. Procesar Feeds
    noticias = procesar_feeds(FEEDS_FILE)
    if not noticias:
        print("❌ No hay noticias para procesar.")
        return

    if args.manual:
        print("✅ Noticias procesadas. Modo manual activado. Saliendo.")
        return

    # 2. Agrupación (Simplificada para v2)
    print("🤖 Agrupando noticias...")
    noticias_simplificadas = json.dumps([{"id": n['id'], "resumen": n['resumen']} for n in noticias], ensure_ascii=False)
    grupos = agrupar_noticias_logica(noticias_simplificadas)
    
    bloques_finales = []
    ids_usados = set()
    
    for tema, ids in grupos.items():
        noticias_bloque = [n for n in noticias if n['id'] in ids and n['id'] not in ids_usados]
        if len(noticias_bloque) >= 2:
            print(f"  -> Tema detectado: {tema}")
            resumenes_json = json.dumps([n['resumen'] for n in noticias_bloque], ensure_ascii=False)
            info_tema = enriquecer_tema(tema, resumenes_json)
            
            cronica = generar_cronica_bloque(
                info_tema.get('descripcion', tema),
                info_tema.get('transicion', f"Hablamos de {tema}"),
                noticias_bloque
            )
            
            bloques_finales.append({
                'tema': tema,
                'cronica': cronica,
                'noticias': noticias_bloque
            })
            ids_usados.update([n['id'] for n in noticias_bloque])
            
    # Noticias sueltas
    sueltas = [n for n in noticias if n['id'] not in ids_usados]
    
    # 3. Generación de Guiones (Inicio/Cierre)
    print("✍️  Generando guiones de presentadora...")
    resumen_noticias = "; ".join([b['tema'] for b in bloques_finales])
    cta_inicio = "Suscríbete a nuestro newsletter." # Placeholder, cargar de archivo real si existe
    
    guion_inicio = generar_monologo_inicio_unificado(resumen_noticias, cta_inicio)
    guion_cierre = generar_monologo_cierre_unificado(resumen_noticias, "Gracias por escuchar.")
    
    # 4. Generación de Audio
    print("🎤 Generando audios...")
    audio_final = AudioSegment.silent(duration=1000)
    
    # Intro
    audio_inicio = generar_tts(guion_inicio)
    if audio_inicio:
        audio_final += audio_inicio
        
    # Bloques
    for bloque in bloques_finales:
        print(f"  -> Audio bloque: {bloque['tema']}")
        audio_bloque = generar_tts(bloque['cronica'])
        if audio_bloque:
            audio_final += AudioSegment.silent(duration=500) # Pausa
            audio_final += audio_bloque
            
    # Sueltas (Rápido)
    if sueltas:
        print("  -> Audio noticias breves...")
        texto_sueltas = "Y en otras noticias breves: " + ". ".join([n['resumen'] for n in sueltas[:3]])
        audio_sueltas = generar_tts(texto_sueltas)
        if audio_sueltas:
            audio_final += AudioSegment.silent(duration=500)
            audio_final += audio_sueltas
            
    # Cierre
    audio_cierre = generar_tts(guion_cierre)
    if audio_cierre:
        audio_final += AudioSegment.silent(duration=500)
        audio_final += audio_cierre
        
    # 5. Masterización y Guardado
    print("🎛️  Masterizando...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{OUTPUT_DIR_BASE}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    audio_master = masterizar_audio(audio_final)
    output_file = os.path.join(output_dir, "podcast_final.mp3")
    audio_master.export(output_file, format="mp3")
    
    print(f"✅ Podcast generado en: {output_file}")

if __name__ == "__main__":
    main()
