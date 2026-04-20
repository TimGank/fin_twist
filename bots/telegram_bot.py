import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BufferedInputFile
from core.analytics import generate_stats_chart, generate_excel_export

# Импортируем наше независимое "Ядро"
from core.ai_brain import extract_expenses_from_text
from core.db import add_expense

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Инициализируем бота и диспетчер (обработчик событий)
bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_cmd(message: Message):
    """Приветственное сообщение."""
    await message.answer(
        "Привет! Я твой умный финансовый трекер. 💸\n"
        "Просто пиши мне свои траты свободным текстом (например: 'Кофе 300, такси 500'), "
        "а я сам всё пойму, посчитаю и сохраню."
    )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    """Справка по командам бота."""
    help_text = (
        "🛠 **Доступные команды:**\n"
        "🔸 /start — Перезапустить бота\n"
        "🔸 /help — Показать это сообщение\n"
        "🔸 /stats — Показать статистику трат (в разработке)\n"
        "🔸 /export — Выгрузить историю в Excel (в разработке)\n\n"
        "💬 **Как записывать траты:**\n"
        "Пиши обычным текстом, например: *«Кофе 300, такси 500»* или *«Купил кроссовки за 5000»*."
    )
    await message.answer(help_text, parse_mode="Markdown")


@dp.message(Command("stats"))
async def stats_cmd(message: Message):
    """Генерация и отправка статистики."""
    status_msg = await message.answer("📊 Рисую графики...")

    # Дергаем наше Ядро
    chart_buffer = generate_stats_chart(message.from_user.id)

    if not chart_buffer:
        await status_msg.edit_text("🤷‍♂️ У тебя пока нет записанных трат. Напиши мне что-нибудь!")
        return

    # Превращаем байты из памяти в объект, который понимает Aiogram
    photo = BufferedInputFile(chart_buffer.read(), filename="stats.png")

    # Отправляем фотку
    await message.answer_photo(photo=photo, caption="Вот на что уходят деньги 💸")

    # Удаляем сообщение "Рисую графики...", оно больше не нужно
    await status_msg.delete()


@dp.message(Command("export"))
async def export_cmd(message: Message):
    """Выгрузка истории в Excel."""
    status_msg = await message.answer("⏳ Собираю данные в таблицу...")

    # Дергаем функцию генерации
    excel_buffer = generate_excel_export(message.from_user.id)

    if not excel_buffer:
        await status_msg.edit_text("🤷‍♂️ У тебя пока нет трат для выгрузки.")
        return

    # Отправляем как документ
    document = BufferedInputFile(excel_buffer.read(), filename="My_Expenses.xlsx")
    await message.answer_document(document=document, caption="📊 Твоя полная история трат!")

    await status_msg.delete()



@dp.message()
async def handle_text(message: Message):
    """Обработка текстовых сообщений."""
    user_id = message.from_user.id
    text = message.text

    # Отправляем заглушку
    status_msg = await message.answer("🧠 Думаю...")

    try:
        # 1. Скармливаем текст ИИ-мозгу
        expenses = extract_expenses_from_text(text)

        if not expenses:
            await status_msg.edit_text("🤷‍♂️ Не нашел никаких трат в твоем сообщении.")
            return

        # 2. Сохраняем в базу и готовим ответ
        reply_lines = ["✅ **Записал:**"]
        total_saved = 0

        for exp in expenses:
            add_expense(
                user_id=user_id,
                amount=exp["amount"],
                category=exp["category"],
                description=exp["description"]
            )
            reply_lines.append(f"— {exp['category']}: {exp['amount']} руб. ({exp['description']})")
            total_saved += exp["amount"]

        reply_lines.append(f"\n💰 Итого за раз: {total_saved} руб.")

        # Обновляем текст сообщения
        await status_msg.edit_text("\n".join(reply_lines), parse_mode="Markdown")

    except Exception as e:
        print(f"Ошибка в ТГ-боте: {e}")
        await status_msg.edit_text("❌ Произошла ошибка при обработке. Попробуй позже.")


async def main_bot():
    """Асинхронная точка запуска aiogram."""
    print("🚀 Telegram-бот (Aiogram) запущен! Пиши ему сообщения.")
    # Пропускаем старые апдейты, чтобы бот не отвечал на то, что ему писали, пока он был выключен
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def run_telegram_bot():
    """Синхронная обертка для вызова из main.py."""
    if not TOKEN:
        raise ValueError("❌ Не найден TELEGRAM_BOT_TOKEN в файле .env!")

    # Элегантный запуск асинхронного лупа без костылей
    asyncio.run(main_bot())