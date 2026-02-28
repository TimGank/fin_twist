import json
from src.llm.llm_service import llm_service

SYSTEM_PROMPT = """
Ты — эксперт по учету личных финансов. Твоя задача — извлечь из сообщения пользователя данные о трате.
Верни ТОЛЬКО JSON в формате:
{
  "item": "название товара или услуги",
  "amount": число (сумма),
  "category": "категория (еда, транспорт, развлечения, жилье, разное)",
  "currency": "RUB"
}
Если данных недостаточно, верни JSON с пустыми полями.
"""

async def parse_expense(text: str):
    response = await llm_service.get_response(text, system_prompt=SYSTEM_PROMPT)
    try:
        clean_response = response.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_response)
    except Exception:
        return None
