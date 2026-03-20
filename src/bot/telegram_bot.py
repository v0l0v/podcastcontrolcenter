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

    # Lógica de filtrado
    es_privado = chat_type == 'private'
    tiene_hashtag = "#dorotea" in mensaje.lower()

    if not es_privado and not tiene_hashtag:
        # En grupos, ignorar si no tiene el hashtag
        return

    # Limpiar el hashtag del mensaje
    import re
    mensaje_limpio = re.sub(r'(?i)#dorotea', '', mensaje).strip()
    
    if not mensaje_limpio:
        return # Evitar guardar mensajes vacíos si solo ponen el hashtag
    
    # Escribir en el archivo de la audiencia con el formato correcto
    from datetime import datetime
    fecha_actual = datetime.now().strftime("%d-%m-%Y")
    origen = "Grupo" if not es_privado else "Privado"
    
    chat_id_interno = update.message.chat_id
    bloque_formateado = f"\n---\nfecha: {fecha_actual}\nautor: {user.first_name} (Telegram {origen})\ntexto: {mensaje_limpio}\n_telegram_chat_id: {chat_id_interno}\n"
    
    with open(BUZON_FILE, 'a', encoding='utf-8') as f:
        f.write(bloque_formateado)
    
    logger.info(f"Mensaje de {user.first_name} guardado con formato de bloque.")
    
    if es_privado:
        await update.message.reply_text("¡Recibido! 📝 Ya está en el buzón con la fecha de hoy.")
    else:
        # Respuesta corta para no saturar grupos
        await update.message.reply_text(f"¡Anotado para hoy, {user.first_name}! 📝")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Procesa las notas de voz."""
    user = update.effective_user
    
    # TODO: Integrar la descarga y transcripción del audio.
    await update.message.reply_text("¡Nota de voz recibida! 🎙️ (El transcriptor de Dorotea está en la fase 2 de desarrollo...)")

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
