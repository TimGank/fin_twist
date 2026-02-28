from openai import AsyncOpenAI
from config.settings import OPENROUTER_API_KEY, OPENROUTER_MODEL

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

    async def get_response(self, prompt: str, system_prompt: str = "Ты — полезный финансовый ассистент."):
        try:
            response = await self.client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                extra_headers={
                    "HTTP-Referer": "https://github.com/alexnastin/FinTwist",
                    "X-Title": "FinTwist Assistant",
                }
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error LLM: {str(e)}"

llm_service = LLMService()
