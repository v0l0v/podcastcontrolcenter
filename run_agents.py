import argparse
import os
import sys
import glob
from datetime import datetime

from src.config.settings import CONFIG, AUDIO_ASSETS_DIR, CTA_TEXTS_DIR
from src.monitoring import logger
from src.agents.coordinator import CoordinatorAgent
from src.audio_processor import generar_episodio_especial

def main():
    parser = argparse.ArgumentParser(description="Script de generación de podcast Micomicona (Arquitectura Agentes)")
    parser.add_argument("--preview", action="store_true", help="Solo generar archivo de previsión de noticias, sin audios.")
    parser.add_argument("--only-special", action="store_true", help="Solo procesar episodios especiales (EE_*) sin generar el podcast diario.")
    parser.add_argument("--skip-special", action="store_true", help="Saltar la verificación y generación de episodios especiales automáticos.")
    parser.add_argument("--file-list", nargs='+', help="Lista específica de archivos EE_*.txt a procesar (ignora búsqueda automática).")
    parser.add_argument("--from-json", help="Ruta al archivo JSON con noticias seleccionadas manualmente.")
    parser.add_argument("--window-hours", type=int, help="Override: Horas de ventana temporal para noticias.")
    parser.add_argument("--max-items", type=int, help="Override: Límite máximo de noticias a procesar.")
    args = parser.parse_args()

    config_app = CONFIG
    archivo_feeds = config_app.get('generation_config', {}).get('feeds_file', 'feeds_castillalamancha.txt')

    # Directorio y logs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"podcast_apg_{timestamp}"

    if not args.only_special:
        required_dirs = [AUDIO_ASSETS_DIR, CTA_TEXTS_DIR, output_dir]
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)
            if not os.path.exists(dir_path):
                print(f"❌ No se pudo crear directorio: {dir_path}")
                sys.exit(1)

        print(f"Directorio de salida creado: {output_dir}")
        logger.clear_logs()

        coordinator = CoordinatorAgent()

    if args.only_special:
        print("🚀 Modo: Solo Episodios Especiales. Saltando generación del noticiero diario.")
    elif args.from_json:
        print(f"🔄 Modo: Generando podcast desde selección manual ({args.from_json})")
        coordinator.execute(
            feeds_file=archivo_feeds,
            output_dir=output_dir,
            timestamp=timestamp,
            archivo_entrada_json=args.from_json,
            window_hours_override=args.window_hours,
            max_items_override=args.max_items
        )
    elif args.preview:
        print(f"🔮 Modo: Preview de noticias (sin audio)")
        coordinator.execute(
            feeds_file=archivo_feeds,
            output_dir=output_dir,
            timestamp=timestamp,
            solo_preview=True,
            window_hours_override=args.window_hours,
            max_items_override=args.max_items
        )
    else:
        print(f"🚀 Modo: Generación automática estándar usando {archivo_feeds}")
        coordinator.execute(
            feeds_file=archivo_feeds,
            output_dir=output_dir,
            timestamp=timestamp,
            window_hours_override=args.window_hours,
            max_items_override=args.max_items
        )

    # ---------------------------------------------------------
    # AUTOMATIZACIÓN DE EPISODIOS ESPECIALES (EE_*.txt)
    # ---------------------------------------------------------
    if not args.preview and not args.skip_special:
        print("\n🔎 Buscando guiones de Episodios Especiales automáticos (EE_*.txt)...")

        if args.file_list:
             ee_files = args.file_list
             print(f"  -> Usando lista manual de archivos: {ee_files}")
        else:
             ee_files = glob.glob("EE_*.txt")

        if ee_files:
            print(f"  -> Se han encontrado {len(ee_files)} guiones especiales.")
            for script_file in ee_files:
                print(f"  🎙️  Procesando: {script_file}")
                try:
                    with open(script_file, 'r', encoding='utf-8') as f:
                        guion_content = f.read()

                    if guion_content.strip():
                        timestamp_folder = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_dir_ee = f"podcast_apg_ESPECIAL_{timestamp_folder}"
                        os.makedirs(output_dir_ee, exist_ok=True)
                        print(f"     📁 Carpeta destino: {output_dir_ee}")

                        base_name = os.path.splitext(script_file)[0]
                        output_ee = os.path.join(output_dir_ee, f"{base_name}.mp3")
                        output_path_ee_abs = os.path.abspath(output_ee)

                        result_path = generar_episodio_especial(guion_content, output_path_ee_abs)

                        if os.path.exists(result_path):
                            print(f"     ✅ Episodio especial generado: {output_ee}")
                            processed_name = os.path.join(output_dir_ee, f"{script_file}.processed")
                            os.rename(script_file, processed_name)
                            print(f"     -> Archivo procesado movido a: {processed_name}")
                        else:
                            print(f"     ❌ Error: No se generó el archivo de audio para {script_file}")
                    else:
                        print(f"     ⚠️ El archivo {script_file} está vacío.")

                except Exception as e:
                    import traceback
                    print(f"     ❌ Error procesando {script_file}: {e}")
                    logger.error(f"Error procesando el especial {script_file}", details={"error": str(e), "traceback": traceback.format_exc()})
        else:
            print("  -> No se encontraron guiones especiales (EE_*.txt).")

if __name__ == "__main__":
    main()
