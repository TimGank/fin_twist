import os
import json
import httpx  # Используем для гибкой настройки таймаутов
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GLM_API_KEY")

# СЕНЬОРСКИЙ ФИКС: Создаем кастомный клиент для работы с сетью
# Ставим таймаут побольше (20 секунд), чтобы медленный интернет не рвал связь
http_client = httpx.Client(
    timeout=20.0,
    verify=True  # Можно поставить False, если есть проблемы с сертификатами SSL
)

client = OpenAI(
    api_key=API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    http_client=http_client
)


def extract_expenses_from_text(user_text: str) -> list:
    if not user_text or not user_text.strip():
        return []

    system_prompt = (
        "Ты — финансовый помощник. Извлеки траты из текста и верни СТРОГО JSON: "
        '{"expenses": [{"amount": 100, "category": "Еда", "description": "Кофе"}]}. '
        "Ответ должен содержать ТОЛЬКО JSON."
    )

    try:
        response = client.chat.completions.create(
            model="glm-4.7-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.1,
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        data = json.loads(content)
        return data.get("expenses", [])

    except Exception as e:
        # Здесь мы теперь увидим реальную причину ошибки в терминале
        print(f"❌ [AI_BRAIN CONNECTION ERROR]: {e}", flush=True)
        return []