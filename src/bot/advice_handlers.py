from telegram import Update
from telegram.ext import ContextTypes
from src.db.database import SessionLocal
from src.db.models import User
from src.db.crud import get_detailed_stats
from src.llm.llm_service import llm_service
import random

ADVICE_THINKING_PHRASES = [
    "Так-так, смотрю, на что уходят твои богатства... 🧐",
    "Сейчас нейросеть выпишет тебе рецепт экономии... 💊",
    "Анализирую историю трат за месяц... 📂",
    "Ищу, где зарыты твои лишние расходы... 💰",
    "Секунду, готовлю финансовую стратегию... 🚀"
]

async def advice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Анализирует траты за месяц и дает советы через LLM.
    """
    user_tg = update.effective_user
    
    status_message = await update.message.reply_text(random.choice(ADVICE_THINKING_PHRASES))
    await update.message.reply_chat_action("typing")

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            await status_message.edit_text("Сначала напиши что-нибудь боту, чтобы я тебя запомнил.")
            return

        expenses = get_detailed_stats(db, user.id)
        
        if not expenses:
            await status_message.edit_text("За этот месяц трат еще не было. Пока нечего анализировать! 😉")
            return

        # Формируем список трат для LLM
        history_text = "\n".join([f"- {e.item}: {e.amount} RUB ({e.category})" for e in expenses])
        
        prompt = f"""
Проанализируй следующие расходы пользователя за этот месяц и дай 3 коротких и конкретных совета по экономии:
{history_text}

Ответь в дружелюбном стиле на русском языке. Сначала похвали за что-то (если есть за что), а потом дай советы.
"""
        
        system_prompt = "Ты — опытный финансовый консультант. Твоя задача — помогать людям разумно тратить деньги."
        
        try:
            # Вызываем LLM
            response = await llm_service.get_response(prompt, system_prompt, json_format=False)
            await status_message.edit_text(response, parse_mode='Markdown')
        except Exception as e:
            await status_message.edit_text(f"Ой, что-то пошло не так при общении с нейросетью: {str(e)}")
