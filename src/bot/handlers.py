import random
from telegram import Update
from telegram.ext import ContextTypes
from src.core.categorizer import parse_expense
from src.db.database import SessionLocal
from src.db.models import User, Expense

THINKING_PHRASES = [
    "ФинТвист думает... 🧐",
    "Секунду, раскладываю по полочкам... 📂",
    "Так-так, сейчас всё запишем... ✍️",
    "Анализирую твои миллионы... 💰",
    "Понял, обрабатываю... 🚀"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            user = User(telegram_id=user_tg.id, username=user_tg.username)
            db.add(user)
            db.commit()

    await update.message.reply_html(
        f"Привет, {user_tg.mention_html()}! Я — ФинТвист. \n"
        "Просто напиши, что ты купил, и я всё запишу. \n"
        "Например: 'кофе 250' или 'купил такси за 400 и булку за 50'"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_tg = update.effective_user
    if not text: return

    # Отправляем сообщение-заглушку
    status_message = await update.message.reply_text(random.choice(THINKING_PHRASES))
    
    # Показываем статус печати
    await update.message.reply_chat_action("typing")
    
    # Запрашиваем нейросеть
    expenses_list = await parse_expense(text)
    
    if not expenses_list:
        await status_message.edit_text("Не совсем понял. Попробуй формат 'название сумма', например: 'пицца 800'")
        return

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            user = User(telegram_id=user_tg.id, username=user_tg.username)
            db.add(user)
            db.commit()
            db.refresh(user)

        saved_messages = []
        for data in expenses_list:
            if not data.get("amount"): continue
            
            new_expense = Expense(
                user_id=user.id,
                item=data.get("item", "Неизвестно"),
                amount=data.get("amount"),
                category=data.get("category", "разное"),
                currency=data.get("currency", "RUB")
            )
            db.add(new_expense)
            saved_messages.append(
                f"✅ {new_expense.item}: {new_expense.amount} {new_expense.currency} ({new_expense.category})"
            )
        
        db.commit()

    if saved_messages:
        reply = "Готово! Записал твои траты:\n" + "\n".join(saved_messages)
    else:
        reply = "Не удалось распознать сумму. Напиши, например: 'кофе 200'"
        
    # Редактируем сообщение на финальный результат
    await status_message.edit_text(reply)
