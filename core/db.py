import sqlite3
from datetime import datetime
import os

# Путь к файлу базы данных (будет лежать в корне проекта)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fin_twist.db")


def init_db():
    """Инициализация таблиц базы данных."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 1. Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                platform TEXT,
                streak_days INTEGER DEFAULT 0,
                last_expense_date TEXT
            )
        ''')

        # 2. Таблица расходов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # 3. Таблица подписок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                service_name TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_expenses ON expenses(user_id)')
        conn.commit()


def add_xp(user_id: int, amount_xp: int):
    """Добавляет XP и проверяет уровень."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Создаем юзера, если его нет
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        # Начисляем XP
        cursor.execute('UPDATE users SET xp = xp + ? WHERE user_id = ?', (amount_xp, user_id))

        # Сеньорская математика: уровень = корень из (XP / 100)
        cursor.execute('SELECT xp FROM users WHERE user_id = ?', (user_id,))
        current_xp = cursor.fetchone()[0]
        new_level = int((current_xp / 100) ** 0.5) + 1

        cursor.execute('UPDATE users SET level = ? WHERE user_id = ?', (new_level, user_id))
        conn.commit()
        return new_level


def add_user_if_not_exists(user_id: int, platform: str = 'telegram'):
    """Проверяет, есть ли юзер в базе. Если нет — создает."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (user_id, platform) VALUES (?, ?)
            ''', (user_id, platform))
            conn.commit()


def add_expense(user_id: int, amount: float, category: str, description: str):
    """Добавляет трату в базу и обновляет дату активности юзера."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        add_user_if_not_exists(user_id)

        now = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO expenses (user_id, amount, category, description, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, category, description, now))

        cursor.execute('''
            UPDATE users SET last_expense_date = ? WHERE user_id = ?
        ''', (now, user_id))

        conn.commit()


def get_user_expenses(user_id: int):
    """Достает все траты пользователя для проверки."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT amount, category, description, created_at 
            FROM expenses WHERE user_id = ?
        ''', (user_id,))
        return cursor.fetchall()

def get_expense_stats(user_id: int):
    """Возвращает сгруппированные траты по категориям: [(Категория, Сумма), ...]"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # SQL-магия: группируем (GROUP BY) и суммируем (SUM)
        cursor.execute('''
            SELECT category, SUM(amount) 
            FROM expenses 
            WHERE user_id = ? 
            GROUP BY category
        ''', (user_id,))
        return cursor.fetchall()


if __name__ == "__main__":
    init_db()
    print("✅ База данных успешно спроектирована и создана!")