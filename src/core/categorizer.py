import json
import logging
from src.llm.llm_service import llm_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Ты — эксперт по учету личных финансов. Твоя задача — извлечь из сообщения пользователя данные о тратах.
Пользователь может написать об одной или нескольких покупках.
Верни ТОЛЬКО JSON-массив объектов. Каждый объект должен иметь формат:
{
  "item": "название товара или услуги",
  "amount": число (итоговая сумма за эту позицию),
  "category": "категория (еда, транспорт, развлечения, жилье, разное)",
  "currency": "RUB"
}
Пример ответа:
[{"item": "кофе", "amount": 200, "category": "еда", "currency": "RUB"}, {"item": "булки", "amount": 100, "category": "еда", "currency": "RUB"}]

Если в тексте нет трат, верни пустой массив [].
"""

async def parse_expense(text: str):
    if not llm_service:
        logger.error("LLM-сервис не инициализирован. Проверь, запущен ли Ollama.")
        return []

    response = await llm_service.get_response(text, system_prompt=SYSTEM_PROMPT)
    
    if response.startswith("Error LLM:"):
        logger.error(f"LLM вернула ошибку: {response}")
        return []

    try:
        # Ollama в режиме format='json' возвращает строку с валидным JSON
        data = json.loads(response)
        return data if isinstance(data, list) else [data]
    except Exception as e:
        logger.error(f"Ошибка парсинга JSON от Ollama: {e}, Response: {response}")
        return []
