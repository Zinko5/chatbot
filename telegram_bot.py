import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from config import TELEGRAM_BOT_TOKEN
from chatbot import bot

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start"""
    await update.message.reply_text(
        "👋 ¡Hola! Soy el Bot de Noticias de Bolivia.\n\n"
        "Estoy leyendo las últimas noticias de El Deber para ti.\n"
        "Pregúntame lo que quieras saber sobre la actualidad.\n\n"
        "Ejemplos:\n"
        "• ¿Qué pasó con el censo?\n"
        "• Noticias de economía\n"
        "• ¿Ganó Oriente Petrolero?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los mensajes de texto"""
    user_text = update.message.text
    
    # Verificar si el bot está listo
    if not bot.initialized:
        if bot.initializing:
            await update.message.reply_text("⏳ Me estoy inicializando y leyendo las noticias... Dame unos segundos.")
        else:
            # Si no está inicializado ni inicializando, forzamos inicialización
            bot.initialize_async()
            await update.message.reply_text("⏳ Iniciando sistema... Por favor espera un momento.")
        return

    # Indicador de "escribiendo..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    # Obtener respuesta del chatbot (esto es síncrono en chatbot.py, así que lo ejecutamos direct)
    # Idealmente chatbot.py debería ser async, pero para este MVP lo llamamos así.
    # Si tarda mucho, podría bloquear el event loop de telegram, pero por ahora está bien.
    response = bot.answer(user_text)
    
    # Telegram tiene límite de 4096 caracteres. Si es muy largo, cortar o dividir.
    # Por simplicidad, enviamos todo (bot.answer suele ser breve)
    if len(response) > 4000:
        response = response[:4000] + "..."
        
    await update.message.reply_text(response, parse_mode='Markdown')

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: No se ha configurado el TELEGRAM_BOT_TOKEN en .env")
        exit(1)
        
    print("🚀 Iniciando Bot de Telegram...")
    
    # Inicializar el cerebro del bot
    bot.initialize_async()
    
    # Crear la aplicación
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Handlers
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(message_handler)
    
    print("✅ Bot de Telegram escuchando...")
    application.run_polling()
