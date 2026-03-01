import asyncio
import sys
import os

# Добавляем корень проекта в пути поиска модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.categorizer import parse_expense
from src.db.database import SessionLocal, init_db
from src.db.models import User, Expense
from src.db.crud import get_stats, get_detailed_stats, delete_last_expense
from src.llm.llm_service import llm_service

async def main():
    print("\n--- ТЕСТОВЫЙ ИНТЕРФЕЙС ФИНТВИСТ (КОНСОЛЬ) ---")
    print("Инициализация базы...")
    init_db()
    
    # Создаем или находим тестового пользователя (ID 12345)
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == 12345).first()
        if not user:
            user = User(telegram_id=12345, username="terminal_user")
            db.add(user)
            db.commit()
            db.refresh(user)
        user_id = user.id

    print("Команды: /stats, /budget <сумма>, /advice, /undo, exit")
    print("Или просто вводи траты (например: 'кофе 200').")
    
    while True:
        text = input("\nВы: ").strip()
        if not text: continue
        if text.lower() in ['exit', 'quit', 'выход']:
            break
            
        # Обработка команды /undo
        if text.startswith("/undo"):
            with SessionLocal() as db:
                deleted = delete_last_expense(db, user_id)
                if deleted:
                    print(f"Бот: ↩️ Удалена последняя трата: {deleted.item} ({deleted.amount} RUB)")
                else:
                    print("Бот: Нечего удалять.")
            continue

        # Обработка команды /advice
        if text.startswith("/advice"):
            print("ФинТвист думает над советами... 🧐")
            with SessionLocal() as db:
                expenses = get_detailed_stats(db, user_id)
                if not expenses:
                    print("Бот: Пока нет трат для анализа.")
                    continue
                
                history_text = "\n".join([f"- {e.item}: {e.amount} RUB ({e.category})" for e in expenses])
                prompt = f"Проанализируй траты и дай 3 совета по экономии:\n{history_text}"
                
                try:
                    advice = await llm_service.get_response(prompt, json_format=False)
                    print(f"\n--- ФИНАНСОВЫЙ СОВЕТ ---\n{advice}")
                except Exception as e:
                    print(f"Ошибка LLM: {e}")
            continue

        # Обработка команды /stats
        if text.startswith("/stats"):
            parts = text.split()
            period = parts[1] if len(parts) > 1 else "month"
            if period not in ["day", "week", "month"]:
                print("Бот: Укажите период: day, week или month (по умолчанию month).")
                continue
            
            with SessionLocal() as db:
                total, by_category = get_stats(db, user_id, period)
                print(f"--- Статистика за {period} ---")
                if total == 0:
                    print("Трат пока нет.")
                else:
                    print(f"Всего потрачено: {total:.2f} RUB")
                    for amount, cat in by_category:
                        print(f" - {cat}: {amount:.2f} RUB ({(amount/total*100):.1f}%)")
            continue

        # Обработка команды /budget
        if text.startswith("/budget"):
            parts = text.split()
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if len(parts) == 1:
                    # Показать текущий бюджет
                    if user.monthly_budget == 0:
                        print("Бюджет не установлен. Напишите '/budget 50000'")
                    else:
                        total_month, _ = get_stats(db, user_id, "month")
                        remains = user.monthly_budget - total_month
                        print(f"Бюджет: {user.monthly_budget:.2f} RUB")
                        print(f"Потрачено за месяц: {total_month:.2f} RUB")
                        print(f"Осталось: {remains:.2f} RUB")
                else:
                    try:
                        new_budget = float(parts[1])
                        user.monthly_budget = new_budget
                        db.commit()
                        print(f"✅ Установлен бюджет: {new_budget:.2f} RUB")
                    except ValueError:
                        print("Ошибка: укажите число для бюджета.")
            continue

        # Обычная обработка трат
        print("ФинТвист думает... 🧐")
        expenses_list = await parse_expense(text)
        
        if not expenses_list:
            print("Бот: Не совсем понял. Попробуй формат 'название сумма'.")
            continue

        with SessionLocal() as db:
            saved = []
            for data in expenses_list:
                new_expense = Expense(
                    user_id=user_id,
                    item=data.get("item", "Неизвестно"),
                    amount=data.get("amount", 0),
                    category=data.get("category", "разное")
                )
                db.add(new_expense)
                saved.append(f"{new_expense.item}: {new_expense.amount} RUB ({new_expense.category})")
            db.commit()
            
            # Проверка лимитов после сохранения
            user = db.query(User).filter(User.id == user_id).first()
            budget_msg = ""
            if user.monthly_budget > 0:
                total_month, _ = get_stats(db, user_id, "month")
                if total_month > user.monthly_budget:
                    budget_msg = f"\n⚠️ ВНИМАНИЕ! Превышен лимит бюджета! ({total_month:.2f} / {user.monthly_budget:.2f})"
                elif total_month > user.monthly_budget * 0.8:
                    budget_msg = f"\n🔔 Почти предел: израсходовано >80% ({total_month:.2f} / {user.monthly_budget:.2f})"

        print(f"Бот: Записал траты:\n  " + "\n  ".join(saved) + budget_msg)

if __name__ == '__main__':
    asyncio.run(main())

if __name__ == '__main__':
    asyncio.run(main())
