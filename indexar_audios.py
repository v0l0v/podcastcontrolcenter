
import os
import glob
import json
from pydub import AudioSegment
import random

def indexar_transiciones(audio_assets_dir):
    print(f"🔍 Indexando transiciones en: {audio_assets_dir}")
    meta = {}
    patron = "clickrozalen*.mp3"
    files = glob.glob(os.path.join(audio_assets_dir, patron))
    
    SEGMENT_DURATION_MS = 10000
    
    for f in files:
        filename = os.path.basename(f)
        try:
            audio = AudioSegment.from_file(f)
            duration = len(audio)
            
            if duration < SEGMENT_DURATION_MS:
                meta[filename] = [{"start": 0, "end": duration}]
                continue
            
            # Buscamos hasta 5 segmentos buenos por cada archivo para tener variedad
            segmentos_buenos = []
            max_start = duration - SEGMENT_DURATION_MS
            
            # Escaneamos el archivo en saltos de 5 segundos para encontrar zonas con volumen
            for start in range(0, max_start, 5000):
                segmento = audio[start:start+SEGMENT_DURATION_MS]
                if segmento.dBFS > -30:
                    segmentos_buenos.append({"start": start, "end": start + SEGMENT_DURATION_MS})
            
            if not segmentos_buenos:
                # Si no hay ninguno "bueno", pillamos el de mayor volumen
                print(f"  ⚠️ {filename} no tiene segmentos claros. Buscando el menos malo...")
                # (Simplemente guardamos uno aleatorio por ahora como fallback)
                segmentos_buenos.append({"start": 0, "end": SEGMENT_DURATION_MS})
                
            meta[filename] = segmentos_buenos
            print(f"  ✅ {filename}: {len(segmentos_buenos)} segmentos encontrados.")
            
        except Exception as e:
            print(f"  ❌ Error procesando {filename}: {e}")
            
    meta_path = os.path.join(audio_assets_dir, "audio_meta.json")
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=4)
    print(f"\n✨ Indexación completada. Archivo guardado en: {meta_path}")

if __name__ == "__main__":
    assets_path = "/home/victor/proyectos/podcastcontrolcenter/audio_assets"
    indexar_transiciones(assets_path)
