import asyncio
import sys
import os

# Добавляем корень проекта в пути поиска модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.categorizer import parse_expense

async def test_alex_cases():
    print("🚀 Тестирование запросов Лёхи...")
    
    cases = [
        "Принкл 200р",
        "2 губки 50р",
        "Перчатка 100р"
    ]
    
    for text in cases:
        print(f"\nЗапрос: '{text}'")
        result = await parse_expense(text)
        print(f"Результат: {result}")
        if result and len(result) > 0:
            print(f"✅ УСПЕХ: {result[0].get('item')} - {result[0].get('amount')} RUB")
        else:
            print("❌ ОШИБКА: не распознано")

if __name__ == "__main__":
    asyncio.run(test_alex_cases())
