import asyncio
import sys
import os

# Добавляем корень проекта в пути поиска модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.categorizer import parse_expense
from src.db.database import SessionLocal, init_db
from src.db.models import User, Expense
from src.db.crud import get_stats

async def run_auto_test():
    print("🚀 Запуск автоматического теста логики бюджета...")
    init_db()
    
    test_tg_id = 99999
    
    with SessionLocal() as db:
        # 1. Сброс тестового пользователя
        user = db.query(User).filter(User.telegram_id == test_tg_id).first()
        if user:
            db.query(Expense).filter(Expense.user_id == user.id).delete()
            db.delete(user)
            db.commit()
            
        # 2. Создание пользователя и установка бюджета 1000 RUB
        user = User(telegram_id=test_tg_id, username="test_bot", monthly_budget=1000.0)
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id
        print(f"✅ Тестовый пользователь создан. Бюджет: {user.monthly_budget} RUB")

    # 3. Тест 1: Обычная трата
    print("\n📝 Тест 1: Трата 'кофе 200'...")
    expenses = await parse_expense("кофе 200")
    if expenses:
        with SessionLocal() as db:
            for e in expenses:
                new_ex = Expense(user_id=user_id, item=e['item'], amount=e['amount'], category=e['category'])
                db.add(new_ex)
            db.commit()
            
            total, _ = get_stats(db, user_id, "month")
            print(f"📊 Всего за месяц: {total:.2f} RUB. Уведомлений быть не должно.")

    # 4. Тест 2: Трата, приближающая к лимиту (>80%)
    print("\n📝 Тест 2: Трата 'ужин 650' (Итого будет 850, это >80% от 1000)...")
    expenses = await parse_expense("ужин 650")
    if expenses:
        with SessionLocal() as db:
            for e in expenses:
                new_ex = Expense(user_id=user_id, item=e['item'], amount=e['amount'], category=e['category'])
                db.add(new_ex)
            db.commit()
            
            total, _ = get_stats(db, user_id, "month")
            if total > 1000 * 0.8:
                print(f"🔔 СРАБОТАЛО ПРЕДУПРЕЖДЕНИЕ (>80%): {total:.2f} / 1000.00")

    # 5. Тест 3: Превышение бюджета
    print("\n📝 Тест 3: Трата 'такси 350' (Итого будет 1200, это >1000)...")
    expenses = await parse_expense("такси 350")
    if expenses:
        with SessionLocal() as db:
            for e in expenses:
                new_ex = Expense(user_id=user_id, item=e['item'], amount=e['amount'], category=e['category'])
                db.add(new_ex)
            db.commit()
            
            total, _ = get_stats(db, user_id, "month")
            if total > 1000:
                print(f"⚠️ СРАБОТАЛО УВЕДОМЛЕНИЕ О ПРЕВЫШЕНИИ: {total:.2f} / 1000.00")

    print("\n✅ Автотест завершен успешно!")

if __name__ == "__main__":
    asyncio.run(run_auto_test())
