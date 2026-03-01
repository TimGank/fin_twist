import json
import logging
from src.llm.llm_service import llm_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Ты — эксперт по учету личных финансов. Твоя задача — извлечь из сообщения пользователя данные о тратах.
Пользователь может написать об одной или нескольких покупках.

ПРАВИЛА:
1. Распознавай сумму, даже если написано 'р', 'руб', 'рублей'.
2. Если указано количество (например, '2 губки 50р'), сумма — это итоговая стоимость за все количество (если не указано 'каждая').
3. Если написано 'Принкл 200р', item — 'Принкл', amount — 200.

Верни ТОЛЬКО JSON-массив объектов. Каждый объект должен иметь формат:
{
  "item": "название товара или услуги",
  "amount": число (итоговая сумма за эту позицию),
  "category": "категория (еда, транспорт, развлечения, жилье, хозтовары, разное)",
  "currency": "RUB"
}

ПРИМЕРЫ:
- 'кофе 200' -> [{"item": "кофе", "amount": 200, "category": "еда", "currency": "RUB"}]
- '2 губки 50р' -> [{"item": "2 губки", "amount": 50, "category": "хозтовары", "currency": "RUB"}]
- 'Принкл 200р' -> [{"item": "Принкл", "amount": 200, "category": "еда", "currency": "RUB"}]
- 'такси 300 и обед 500' -> [{"item": "такси", "amount": 300, "category": "транспорт", "currency": "RUB"}, {"item": "обед", "amount": 500, "category": "еда", "currency": "RUB"}]

Если в тексте нет трат, верни пустой массив [].
"""

async def parse_expense(text: str):
    if not llm_service:
        logger.error("LLM-сервис не инициализирован. Проверь, запущен ли Ollama.")
        return []

    response = await llm_service.get_response(text, system_prompt=SYSTEM_PROMPT, json_format=True)
    
    if response.startswith("Error LLM:"):
        logger.error(f"LLM вернула ошибку: {response}")
        return []

    try:
        # Ollama в режиме format='json' возвращает строку с валидным JSON
        data = json.loads(response)
        
        # Обработка случая, когда LLM возвращает {"items": [...]}
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
            
        return data if isinstance(data, list) else [data]
    except Exception as e:
        logger.error(f"Ошибка парсинга JSON от Ollama: {e}, Response: {response}")
        return []
