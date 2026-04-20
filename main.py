from core.db import init_db
from bots.telegram_bot import run_telegram_bot


def main():
    # 1. Убеждаемся, что база на месте
    init_db()

    # 2. Запускаем Телеграм-бота
    run_telegram_bot()


if __name__ == "__main__":
    main()