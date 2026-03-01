import logging
import os
import asyncio
import pytz # Явно импортируем pytz

# --- Патч для APScheduler (должен быть до импорта telegram.ext) ---
try:
    import apscheduler.util
    def patched_astimezone(obj):
        import pytz
        return pytz.UTC if obj is None else pytz.timezone(str(obj))
    apscheduler.util.astimezone = patched_astimezone
except ImportError:
    pass

from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackQueryHandler
)
from src.db.database import init_db
from src.bot.handlers import (
    start, handle_message, help_command, undo_command
)
from src.bot.budget_handlers import budget_command
from src.bot.advice_handlers import advice_command
from src.bot.stats_handlers import (
    stats_command, stats_callback, cancel_stats,
    SELECTING_STATS_PERIOD
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def start_bot():
    # Инициализация базы данных
    init_db()
    
    # Для Python 3.12+ и 3.14 необходимо явно создать цикл событий
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    stats_handler = ConversationHandler(
        entry_points=[CommandHandler("stats", stats_command)],
        states={
            SELECTING_STATS_PERIOD: [
                CallbackQueryHandler(stats_callback, pattern="^(day|week|month|cancel)$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_stats)],
    )

    application.add_handler(stats_handler)
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('undo', undo_command))
    application.add_handler(CommandHandler('budget', budget_command))
    application.add_handler(CommandHandler('advice', advice_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Бот запущен в Telegram...")
    application.run_polling()

if __name__ == '__main__':
    start_bot()
