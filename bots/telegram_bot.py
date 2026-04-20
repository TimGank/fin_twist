import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BufferedInputFile
from dotenv import load_dotenv # <--- Добавь этот импорт

# Код для работы с ядром
from core.ai_brain import extract_expenses_from_text
from core.db import add_expense
from core.scanner import scan_receipt
from core.analytics import generate_stats_chart, generate_excel_export

# ВАЖНО: Загружаем переменные из .env ПЕРЕД созданием бота
load_dotenv()

# Теперь os.getenv точно найдет строку, а не None
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Привет! Я ФинТвист. Пришли текст (например, 'кофе 200') или фото чека.")


@dp.message(Command("last"))
async def last_expense_cmd(message: Message):
    from core.db import get_last_expense

    last = get_last_expense(message.from_user.id)

    if not last:
        await message.answer("🤷‍♂️ У тебя еще нет записей о тратах.")
        return

    amount, category, desc, date = last

    # Сеньорский штрих: форматируем вывод
    text = (
        f"🔍 **Твоя последняя запись:**\n\n"
        f"💰 Сумма: `{amount} руб.`\n"
        f"🗂 Категория: `{category}`\n"
        f"📝 Описание: `{desc}`\n"
        f"📅 Дата: `{date}`\n\n"
        f"Если это ошибка, используй /undo"
    )

    await message.answer(text, parse_mode="Markdown")



@dp.message(Command("stats"))
async def stats_cmd(message: Message):
    # Генерация графиков через Matplotlib [cite: 83, 142]
    chart = generate_stats_chart(message.from_user.id)
    if not chart: return await message.answer("Трат пока нет.")
    await message.answer_photo(BufferedInputFile(chart.read(), filename="stats.png"))


@dp.message(Command("export"))
async def export_cmd(message: Message):
    # Экспорт в Excel через Pandas [cite: 83, 143]
    excel = generate_excel_export(message.from_user.id)
    if not excel: return await message.answer("Данных нет.")
    await message.answer_document(BufferedInputFile(excel.read(), filename="report.xlsx"))


@dp.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    status = await message.answer("📸 Сканирую чек...")
    path = f"temp_{user_id}.jpg"

    try:
        await message.bot.download(message.photo[-1], destination=path)
        # Гибридная система: QR или EasyOCR [cite: 82, 137, 138]
        text = scan_receipt(path)
        if not text: return await status.edit_text("Не удалось прочитать.")

        await status.edit_text(f"📝 Текст: `{text[:100]}...` \n⌛ Анализирую...")
        expenses = extract_expenses_from_text(text)

        for exp in expenses:
            add_expense(user_id, exp["amount"], exp["category"], exp["description"])
        await message.answer("✅ Чек успешно записан!")
    finally:
        if os.path.exists(path): os.remove(path)


@dp.message()
async def handle_text(message: Message):
    """Четкая запись трат."""
    user_id = message.from_user.id
    expenses = extract_expenses_from_text(message.text)

    if expenses:
        response_lines = ["✅ Записал:"]

        for exp in expenses:
            # Сохраняем в базу
            add_expense(
                user_id=user_id,
                amount=exp["amount"],
                category=exp["category"],
                description=exp["description"]
            )
            # Формируем строку по твоему формату: Категория, сумма
            response_lines.append(f"— {exp['category']}, {exp['amount']} руб.")

        await message.answer("\n".join(response_lines))
    else:
        await message.answer("🤷‍♂️ Не удалось распознать трату. Напиши проще, например: 'такси 300'")

async def main_bot():
    """Главная функция запуска бота."""
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

def run_telegram_bot():
    """Точка входа для запуска из main.py."""
    import asyncio
    asyncio.run(main_bot())