import random
import asyncio
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from src.core.categorizer import parse_expense
from src.db.database import SessionLocal
from src.db.models import User, Expense, ErrorLog
from src.db.crud import get_stats, delete_last_expense

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
        "Я помогу тебе следить за тратами. Просто напиши, что купил. \n\n"
        "Основные команды:\n"
        "📊 /stats — статистика трат\n"
        "💰 /budget — управление бюджетом\n"
        "💡 /advice — советы по экономии\n"
        "❓ /help — все команды"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Команды бота ФинТвист:*\n\n"
        "📝 *Учет трат:* Просто пиши текст, например: 'кофе 200' или 'такси 300 и обед 500'.\n\n"
        "📊 /stats — Посмотреть расходы за день, неделю или месяц.\n"
        "💰 /budget <сумма> — Установить месячный лимит (например, `/budget 50000`).\n"
        "💰 /budget — Посмотреть остаток лимита на этот месяц.\n"
        "💡 /advice — Получить советы по экономии от нейросети.\n"
        "↩️ /undo — Удалить последнюю записанную трату.\n"
        "❓ /help — Показать это сообщение."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def undo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            await update.message.reply_text("Я тебя еще не знаю. Начни с /start")
            return
        
        deleted = delete_last_expense(db, user.id)
        if deleted:
            await update.message.reply_text(
                f"↩️ Удалена последняя трата: *{deleted.item}* на сумму *{deleted.amount:.2f} RUB*.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("У тебя пока нет записанных трат, которые можно удалить.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_tg = update.effective_user
    if not text: return
    user_id_in_db = None

    # Если это похоже на вопрос о командах или просто общение
    if any(word in text.lower() for word in ["команд", "что ты умеешь", "помоги", "help"]):
        await help_command(update, context)
        return

    status_message = await update.message.reply_text(random.choice(THINKING_PHRASES))
    await update.message.reply_chat_action("typing")
    
    try:
        # Устанавливаем таймаут на обработку LLM
        expenses_list = await asyncio.wait_for(parse_expense(text), timeout=120)
        
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_tg.id).first()
            if not user:
                user = User(telegram_id=user_tg.id, username=user_tg.username)
                db.add(user)
                db.commit()
                db.refresh(user)
            user_id_in_db = user.id

            if not expenses_list:
                # Если траты не найдены, попробуем ответить через LLM как просто ассистент
                from src.llm.llm_service import llm_service
                answer = await asyncio.wait_for(llm_service.get_response(
                    f"Пользователь спрашивает: '{text}'. Если это вопрос о твоих функциях, расскажи о них (учет трат, бюджет /budget, статистика /stats, советы /advice). Если это просто фраза, вежливо ответь, что ты — финансовый ассистент и помогаешь записывать расходы.",
                    json_format=False
                ), timeout=30)
                await status_message.edit_text(answer)
                return

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
                    f"✅ {new_expense.item}: {new_expense.amount:.2f} {new_expense.currency} ({new_expense.category})"
                )
            
            db.commit()

        if saved_messages:
            reply = "Готово! Записал твои траты:\n" + "\n".join(saved_messages)
            
            # Проверка бюджета
            with SessionLocal() as db:
                user = db.query(User).filter(User.telegram_id == user_tg.id).first()
                if user and user.monthly_budget > 0:
                    total_month, _ = get_stats(db, user.id, "month")
                    if total_month > user.monthly_budget:
                        reply += f"\n\n⚠️ *Внимание! Превышен лимит бюджета!* \nПотрачено {total_month:.2f} из {user.monthly_budget:.2f} RUB."
                    elif total_month > user.monthly_budget * 0.8:
                        reply += f"\n\n🔔 *Почти предел:* ты израсходовал(а) более 80% бюджета ({total_month:.2f} / {user.monthly_budget:.2f} RUB)."
            
            await status_message.edit_text(reply, parse_mode='Markdown')
        else:
            await status_message.edit_text("Не удалось распознать сумму. Напиши, например: 'кофе 200'")

    except (asyncio.TimeoutError, Exception) as e:
        error_info = traceback.format_exc()
        with SessionLocal() as db:
            # Пытаемся сохранить ошибку в БД
            log = ErrorLog(
                user_id=user_id_in_db,
                request_text=text,
                output_text="Извините, сейчас не могу функционировать...",
                error_trace=error_info
            )
            db.add(log)
            db.commit()

        await status_message.edit_text(
            "извините, сейчас не могу функционировать, час пик, работы много, вас много, а я один, попробуйте чуть позже, когда подразгребусь с задачами)"
        )
