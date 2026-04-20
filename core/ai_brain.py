import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Подтягиваем переменные окружения
load_dotenv()

API_KEY = os.getenv("GLM_API_KEY")
if not API_KEY:
    raise ValueError("❌ Не найден GLM_API_KEY в файле .env!")

# СЕНЬОРСКИЙ ПОДХОД: Используем стандартный клиент OpenAI,
# но перенаправляем его на сервера GLM
client = OpenAI(
    api_key=API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)


def extract_expenses_from_text(user_text: str) -> list:
    """
    Принимает текст пользователя и возвращает список словарей с тратами.
    """
    # Жесткий системный промпт — залог того, что ИИ не будет болтать лишнего
    system_prompt = """
    Ты финансовый анализатор. Твоя задача — извлечь все траты из текста пользователя.
    Верни СТРОГО валидный JSON в следующем формате:
    {"expenses": [{"amount": 100, "category": "Еда", "description": "Кофе"}]}

    Категории могут быть: Еда, Транспорт, Подписки, Развлечения, Здоровье, Быт, Другое.
    Если в тексте нет трат, верни {"expenses": []}.
    Твой ответ должен содержать ТОЛЬКО JSON, без Markdown-разметки (без ```json) и без приветствий.
    """

    try:
        response = client.chat.completions.create(
            model="glm-4.7-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.1,  # Минимум креативности, максимум точности
        )

        # Получаем сырой ответ
        raw_content = response.choices[0].message.content.strip()

        # Защита от "дурака" (иногда ИИ всё же оборачивает ответ в маркдаун)
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:-3].strip()
        elif raw_content.startswith("```"):
            raw_content = raw_content[3:-3].strip()

        # Превращаем строку в Python-словарь
        data = json.loads(raw_content)

        # Возвращаем только сам список трат
        return data.get("expenses", [])

    except json.JSONDecodeError:
        print("❌ Ошибка: ИИ вернул невалидный JSON!")
        print(f"Сырой ответ ИИ: {raw_content}")
        return []
    except Exception as e:
        print(f"❌ Ошибка при обращении к API GLM: {e}")
        return []


# Тестовый блок
if __name__ == "__main__":
    test_message = "Взял кофе в спешелти за 350р, а потом еще оплатил Яндекс Плюс 299 рублей."
    print(f"Обрабатываем текст: '{test_message}'\n")

    result = extract_expenses_from_text(test_message)

    print("🧠 Ответ от ИИ:")
    print(json.dumps(result, indent=2, ensure_ascii=False))