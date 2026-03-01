from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.db.database import SessionLocal
from src.db.models import User
from src.db.crud import get_stats

# Этапы для ConversationHandler
SELECTING_STATS_PERIOD = 0

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает у пользователя период для статистики."""
    keyboard = [
        [
            InlineKeyboardButton("За сегодня", callback_data="day"),
            InlineKeyboardButton("За неделю", callback_data="week"),
            InlineKeyboardButton("За месяц", callback_data="month"),
        ],
        [InlineKeyboardButton("Отмена", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("За какой период показать статистику?", reply_markup=reply_markup)
    return SELECTING_STATS_PERIOD

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает статистику за выбранный период."""
    query = update.callback_query
    await query.answer()
    period = query.data

    if period == "cancel":
        await query.edit_message_text(text="Действие отменено.")
        return ConversationHandler.END

    user_tg_id = query.from_user.id
    
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_tg_id).first()
        if not user:
            await query.edit_message_text("Сначала напишите /start")
            return ConversationHandler.END

        total, by_category = get_stats(db, user.id, period)

    period_text = {
        "day": "сегодня",
        "week": "эту неделю",
        "month": "этот месяц"
    }.get(period)

    if total == 0:
        reply = f"За {period_text} у тебя не было трат. Время потратить деньги! 💸"
    else:
        reply = (
            f"За {period_text} ты потратил(а) **{total:.2f} RUB**.\n\n"
            "Вот разбивка по категориям:\n"
        )
        for amount, category in by_category:
            percentage = (amount / total) * 100
            reply += f" - **{category.capitalize()}**: {amount:.2f} RUB ({percentage:.1f}%)\n"

    await query.edit_message_text(text=reply, parse_mode='Markdown')
    return ConversationHandler.END

async def cancel_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет операцию выбора статистики."""
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END
