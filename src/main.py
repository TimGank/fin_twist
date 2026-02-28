import logging
import os
import asyncio

# --- Управление режимом ---
IS_TERMINAL = os.getenv("TERMINAL_MODE", "False").lower() == "true"

# --- Патч для APScheduler (только для режима Telegram) ---
if not IS_TERMINAL:
    try:
        import apscheduler.util
        def patched_astimezone(obj):
            import pytz
            return pytz.UTC if obj is None else obj
        apscheduler.util.astimezone = patched_astimezone
    except ImportError:
        pass # apscheduler может быть не установлен

from src.db.database import init_db
from src.bot.handlers import (
    start, handle_message, stats_command, stats_callback, cancel_stats,
    SELECTING_STATS_PERIOD, THINKING_PHRASES
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Логика для режима терминала ---
async def terminal_mode():
    # ... (код для terminal_mode останется здесь)
    pass

# --- Основной запуск ---
def main():
    if IS_TERMINAL:
        # asyncio.run(terminal_mode())
        print("Терминальный режим временно отключен для интеграции новых команд.")
        print("Пожалуйста, установите TERMINAL_MODE=False в .env и тестируйте через Telegram.")
    else:
        from telegram.ext import (
            Application, CommandHandler, MessageHandler, filters,
            ConversationHandler, CallbackQueryHandler
        )
        init_db()
        
        application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

        stats_conversation_handler = ConversationHandler(
            entry_points=[CommandHandler("stats", stats_command)],
            states={
                SELECTING_STATS_PERIOD: [
                    CallbackQueryHandler(stats_callback, pattern="^(day|week|month|cancel)$")
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_stats)],
        )

        application.add_handler(stats_conversation_handler)
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("Бот запущен в Telegram...")
        application.run_polling()

if __name__ == '__main__':
    main()
