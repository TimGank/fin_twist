from telegram import Update
from telegram.ext import ContextTypes
from src.db.database import SessionLocal
from src.db.models import User
from src.db.crud import get_stats

async def budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Устанавливает или показывает месячный бюджет.
    Использование: /budget <сумма>
    """
    user_tg = update.effective_user
    args = context.args

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_tg.id).first()
        if not user:
            user = User(telegram_id=user_tg.id, username=user_tg.username)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Если аргументов нет, показываем текущий статус бюджета
        if not args:
            if user.monthly_budget == 0:
                await update.message.reply_text(
                    "У тебя пока не установлен бюджет на месяц. \n"
                    "Чтобы установить его, напиши: `/budget 50000`",
                    parse_mode='Markdown'
                )
            else:
                total_month, _ = get_stats(db, user.id, "month")
                remains = user.monthly_budget - total_month
                percent = (total_month / user.monthly_budget) * 100 if user.monthly_budget > 0 else 0
                
                status_emoji = "✅" if remains > 0 else "⚠️"
                
                await update.message.reply_text(
                    f"📅 *Твой бюджет на месяц: {user.monthly_budget:.2f} RUB*\n\n"
                    f"Потрачено: {total_month:.2f} RUB ({percent:.1f}%)\n"
                    f"Осталось: {remains:.2f} RUB {status_emoji}",
                    parse_mode='Markdown'
                )
            return

        # Если есть аргументы, пытаемся установить новый бюджет
        try:
            new_budget = float(args[0])
            if new_budget < 0:
                raise ValueError
            
            user.monthly_budget = new_budget
            db.commit()
            
            await update.message.reply_text(
                f"✅ Твой месячный бюджет теперь: *{new_budget:.2f} RUB*",
                parse_mode='Markdown'
            )
        except (ValueError, IndexError):
            await update.message.reply_text("Пожалуйста, укажи корректную сумму. Например: `/budget 50000`", parse_mode='Markdown')
