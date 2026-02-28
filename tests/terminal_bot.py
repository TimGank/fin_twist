import asyncio
import sys
import os

# Добавляем корень проекта в пути поиска модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.categorizer import parse_expense
from src.db.database import SessionLocal, init_db
from src.db.models import User, Expense

async def main():
    print("--- ТЕСТОВЫЙ ИНТЕРФЕЙС ФИНТВИСТ ---")
    print("Инициализация базы...")
    init_db()
    
    # Создаем тестового пользователя
    with SessionLocal() as db:
        test_user = db.query(User).filter(User.telegram_id == 12345).first()
        if not test_user:
            test_user = User(telegram_id=12345, username="test_user")
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        user_id = test_user.id

    print("Готов к работе. Введи свою трату (или 'exit' для выхода):")
    
    while True:
        text = input("
Ты: ")
        if text.lower() in ['exit', 'quit', 'выход']:
            break
            
        print("ФинТвист думает... 🧐")
        
        # Запрашиваем нейросеть напрямую через наш categorizer
        expenses_list = await parse_expense(text)
        
        if not expenses_list:
            print("Бот: Не совсем понял. Попробуй формат 'название сумма'.")
            continue

        with SessionLocal() as db:
            saved_messages = []
            for data in expenses_list:
                if not data.get("amount"): continue
                
                new_expense = Expense(
                    user_id=user_id,
                    item=data.get("item", "Неизвестно"),
                    amount=data.get("amount"),
                    category=data.get("category", "разное"),
                    currency=data.get("currency", "RUB")
                )
                db.add(new_expense)
                saved_messages.append(
                    f"✅ {new_expense.item}: {new_expense.amount} {new_expense.currency} ({new_expense.category})"
                )
            db.commit()

        if saved_messages:
            print("Бот: Записал твои траты:")
            for msg in saved_messages:
                print(f"  {msg}")
        else:
            print("Бот: Не удалось распознать сумму.")

if __name__ == '__main__':
    asyncio.run(main())
