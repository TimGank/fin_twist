import os, json
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama"
)


def extract_expenses_from_text(user_text: str) -> list:
    if not user_text or not user_text.strip(): return []

    # Сменили на более умную модель
    MODEL = "llama3.2"

    prompt = (
        "Ты — финансовый экстрактор. Выдели траты из текста и верни СТРОГО JSON. "
        "Формат: {\"expenses\": [{\"amount\": 100, \"category\": \"Еда\", \"description\": \"Кофе\"}]}. "
        "Категории: Еда, Транспорт, Жилье, Развлечения, Связь, Другое. "
        "Если в сообщении несколько трат, выдели все. Ответ должен содержать ТОЛЬКО JSON."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content.strip()

        # Чистим JSON от Markdown-мусора
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)
        return data.get("expenses", [])
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return []