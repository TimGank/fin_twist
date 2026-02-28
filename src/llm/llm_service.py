import logging
import ollama

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, model="llama3"):
        self.model = model
        try:
            # Проверяем, доступен ли Ollama и есть ли модель
            logger.info("Проверка доступности Ollama...")
            ollama.show(self.model)
            logger.info(f"Ollama доступен. Модель '{self.model}' найдена.")
        except Exception:
            logger.error("="*50)
            logger.error(f"ОШИБКА: Модель '{self.model}' не найдена в Ollama или Ollama не запущен.")
            logger.error("Пожалуйста, установите Ollama и выполните 'ollama run llama3'")
            logger.error("="*50)
            raise

    async def get_response(self, prompt: str, system_prompt: str = "Ты — полезный финансовый ассистент."):
        logger.info(f"Отправка запроса в Ollama (модель: {self.model})...")
        try:
            # Используем async-клиент, который появится в будущих версиях,
            # а пока вызываем синхронный метод в executor'е, чтобы не блокировать asyncio.
            # Для простоты пока оставим синхронный вызов, т.к. он быстрый на локальной машине.
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                format='json' # Просим Ollama сразу вернуть валидный JSON
            )
            content = response['message']['content']
            logger.info("Ответ от Ollama получен успешно.")
            return content
        except Exception as e:
            logger.error(f"Ошибка при вызове Ollama: {str(e)}")
            return f"Error LLM: {str(e)}"

# Создаем инстанс. Если Ollama не настроен, здесь произойдет ошибка.
try:
    llm_service = LLMService()
except Exception:
    llm_service = None
