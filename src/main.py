import logging
import asyncio
import os
import sys

# ПАТЧ: apscheduler не дружит с Python 3.14 таймзонами. 
# Мы принудительно устанавливаем переменную окружения TZ, 
# либо патчим функцию astimezone до импорта телеграма.
import apscheduler.util
def patched_astimezone(obj):
    import pytz
    if obj is None:
        return pytz.UTC
    if isinstance(obj, str):
        return pytz.timezone(obj)
    return obj

apscheduler.util.astimezone = patched_astimezone

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config.settings import TELEGRAM_BOT_TOKEN
from src.bot.handlers import start, handle_message
from src.db.database import init_db

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # Инициализация базы данных
    init_db()
    
    # Для Python 3.12+ и 3.14 необходимо явно создать цикл событий
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Теперь строим приложение
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
