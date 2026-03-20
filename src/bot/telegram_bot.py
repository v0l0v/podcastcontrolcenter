import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Cargar variables de entorno (donde debe estar TELEGRAM_BOT_TOKEN)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# Configuración básica de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Archivo donde Dorotea lee las preguntas
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
BUZON_FILE = os.path.join(PROJECT_ROOT, 'preguntas_audiencia.txt')
BUZON_DIR = os.path.join(PROJECT_ROOT, 'buzon_del_oyente')

# Asegurar directorios
os.makedirs(BUZON_DIR, exist_ok=True)

def registrar_mensaje(fecha: str, autor: str, texto: str, chat_id: int, plataforma: str, tipo: str, audio: str = None):
    """Guarda un mensaje en el buzón, reemplazando el anterior del mismo usuario para hoy."""
    nuevo_bloque = (
        f"---\n"
        f"fecha: {fecha}\n"
        f"autor: {autor}\n"
        f"texto: {texto}\n"
        f"plataforma: {plataforma}\n"
        f"tipo: {tipo}\n"
    )
    if audio:
        nuevo_bloque += f"audio: {audio}\n"
    nuevo_bloque += f"_telegram_chat_id: {chat_id}\n"

    bloques_finales = []
    if os.path.exists(BUZON_FILE):
        with open(BUZON_FILE, 'r', encoding='utf-8') as f:
            contenido = f.read()
            bloques = contenido.split('---')
            
            for b in bloques:
                b = b.strip()
                if not b: continue
                
                # Parsear campos básicos del bloque existente
                lineas = b.split('\n')
                b_fecha = ""
                b_chat_id = ""
                b_audio = ""
                for l in lineas:
                    if l.startswith("fecha:"): b_fecha = l.split(":", 1)[1].strip()
                    if l.startswith("_telegram_chat_id:"): b_chat_id = l.split(":", 1)[1].strip()
                    if l.startswith("audio:"): b_audio = l.split(":", 1)[1].strip()
                
                # ¿Es el mismo usuario en la misma fecha?
                if b_fecha == fecha and str(b_chat_id) == str(chat_id):
                    # Reemplazamos: eliminar audio previo si existía
                    if b_audio and os.path.exists(b_audio):
                        try:
                            os.remove(b_audio)
                            logger.info(f"Audio anterior eliminado: {b_audio}")
                        except Exception as e:
                            logger.error(f"Error eliminando audio viejo: {e}")
                    continue # No añadir este bloque a bloques_finales (se reemplaza)
                
                bloques_finales.append("---\n" + b + "\n")

    # Añadir el nuevo bloque al final
    bloques_finales.append(nuevo_bloque)
    
    with open(BUZON_FILE, 'w', encoding='utf-8') as f:
        f.writelines(bloques_finales)
    
    logger.info(f"Mensaje de {autor} registrado (reemplazando anterior si existía).")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje cuando se emita el comando /start."""
    user = update.effective_user
    await update.message.reply_text(
        f"¡Hola {user.first_name}! 👋\n\n"
        "Soy el buzón directo de Dorotea. Escríbeme cualquier cosa o mándame una nota de voz "
        "y se la haré llegar para que te responda en el próximo podcast de Micomicona.com."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Procesa los mensajes de texto entrantes."""
    if not update.message or not update.message.text:
        return
        
    user = update.effective_user
    mensaje = update.message.text
    chat_type = update.message.chat.type

    # Lógica de filtrado (antes se pedía #dorotea en grupos, ahora se procesa todo como antes)
    es_privado = chat_type == 'private'
    # tiene_hashtag = "#dorotea" in mensaje.lower() # Eliminado por petición de restaurar comportamiento anterior
    
    # Limpiar el hashtag del mensaje si lo tuviera (por si acaso lo siguen usando)
    import re
    mensaje_limpio = re.sub(r'(?i)#dorotea', '', mensaje).strip()
    
    if not mensaje_limpio:
        return # Evitar guardar mensajes vacíos
    
    # Escribir en el archivo de la audiencia con el formato correcto
    from datetime import datetime
    fecha_actual = datetime.now().strftime("%d-%m-%Y")
    origen = "Grupo" if not es_privado else "Privado"
    
    # Registrar el mensaje con la nueva lógica de reemplazo
    registrar_mensaje(
        fecha=fecha_actual,
        autor=user.first_name,
        texto=mensaje_limpio,
        chat_id=chat_id_interno,
        plataforma="Telegram",
        tipo=origen
    )
    
    if es_privado:
        await update.message.reply_text("¡Recibido! 📝 Ya está en el buzón con la fecha de hoy.")
    else:
        # Respuesta corta para no saturar grupos
        await update.message.reply_text(f"¡Anotado para hoy, {user.first_name}! 📝")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Procesa las notas de voz."""
    user = update.effective_user
    voice = update.message.voice
    
    if not voice:
        return

    # 1. Preparar metadatos
    from datetime import datetime
    ahora = datetime.now()
    fecha_str = ahora.strftime("%d-%m-%Y")
    timestamp_file = ahora.strftime("%Y%m%d_%H%M%S")
    
    # 2. Descargar el archivo
    file_id = voice.file_id
    new_file = await context.bot.get_file(file_id)
    
    file_extension = "ogg" # Telegram voice es .ogg (Opus)
    filename = f"{timestamp_file}_{user.first_name}.{file_extension}"
    dest_path = os.path.join(BUZON_DIR, filename)
    
    await new_file.download_to_drive(dest_path)
    logger.info(f"Nota de voz de {user.first_name} descargada en {dest_path}")

    # Registrar en preguntas_audiencia.txt (con lógica de reemplazo)
    registrar_mensaje(
        fecha=fecha_str,
        autor=user.first_name,
        texto="[NOTA DE VOZ]",
        chat_id=chat_id_interno,
        plataforma="Telegram",
        tipo=origen,
        audio=dest_path
    )
    
    # 4. Responder al usuario
    if es_privado:
        await update.message.reply_text("¡He recibido tu nota de voz! 🎙️ (He reemplazado tu mensaje anterior de hoy si lo había).")
    else:
        await update.message.reply_text(f"¡Anotado para hoy, {user.first_name}! 🎙️ (Mensaje actualizado)")

def main() -> None:
    """Inicia el bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ ERROR: No se ha encontrado TELEGRAM_BOT_TOKEN en el archivo .env")
        logger.error("Abre BotFather en Telegram, crea un bot, y pon el token en tu .env")
        return

    # Crear la aplicación
    application = Application.builder().token(token).build()

    # Manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Iniciar el bot en modo polling
    logger.info("🤖 Bot de Dorotea arrancando y escuchando mensajes... Presiona Ctrl+C para detener.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
