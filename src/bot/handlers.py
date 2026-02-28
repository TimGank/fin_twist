from telegram import Update
from telegram.ext import ContextTypes
from src.core.categorizer import parse_expense
from src.db.database import SessionLocal
from src.db.models import User, Expense

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
        "Например: 'кофе 250' или 'такси 400'"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_tg = update.effective_user
    if not text: return

    await update.message.reply_chat_action("typing")
    expense_data = await parse_expense(text)
    
    if expense_data and expense_data.get("amount"):
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_tg.id).first()
            if not user:
                user = User(telegram_id=user_tg.id, username=user_tg.username)
                db.add(user)
                db.commit()
                db.refresh(user)
            
            new_expense = Expense(
                user_id=user.id,
                item=expense_data.get("item"),
                amount=expense_data.get("amount"),
                category=expense_data.get("category"),
                currency=expense_data.get("currency", "RUB")
            )
            db.add(new_expense)
            db.commit()
            
            reply = (
                f"✅ Трата сохранена!\n"
                f"🔹 Товар: {new_expense.item}\n"
                f"💰 Сумма: {new_expense.amount} {new_expense.currency}\n"
                f"📂 Категория: {new_expense.category}"
            )
    else:
        reply = "Не совсем понял. Попробуй формат 'название сумма', например: 'пицца 800'"
    
    await update.message.reply_text(reply)
