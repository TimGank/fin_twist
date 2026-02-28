import logging
import os
import asyncio
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackQueryHandler
)
from src.db.database import init_db
from src.bot.handlers import (
    start, handle_message
)

def start_bot():
    IS_TERMINAL = os.getenv("TERMINAL_MODE", "False").lower() == "true"
    if IS_TERMINAL:
        print("Terminal mode is not supported in this version.")
        return

    init_db()
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Бот запущен в Telegram...")
    application.run_polling()

if __name__ == '__main__':
    start_bot()
