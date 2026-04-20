import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from core.ai_brain import extract_expenses_from_text
from core.db import add_expense
from core.scanner import scan_receipt

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ЭТУ СТРОКУ ТЫ ДОЛЖЕН УВИДЕТЬ В КОНСОЛИ
print("\n" + "=" * 40)
print("🚀 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
print("=" * 40 + "\n", flush=True)


@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Привет! Пришли фото чека или текст.")


@dp.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    status_msg = await message.answer("📸 Читаю фото...")

    file_path = f"temp_{user_id}.jpg"
    try:
        # 1. Качаем фото
        file = await message.bot.get_file(message.photo[-1].file_id)
        await message.bot.download_file(file.file_path, file_path)

        # 2. OCR
        raw_text = scan_receipt(file_path)
        clean_text = raw_text.strip() if raw_text else ""

        # ЛОГИРУЕМ В КОНСОЛЬ
        print(f"🔍 [SCANNER] Распознано: '{clean_text}'", flush=True)

        if not clean_text:
            await status_msg.edit_text("🤷‍♂️ Пусто. Не смог ничего прочитать.")
            return

        # 3. ПОКАЗЫВАЕМ В ТЕЛЕГРАМЕ
        await status_msg.edit_text(f"📝 **Текст с фото:**\n\n`{clean_text}`\n\n⌛ Анализирую...")

        # 4. ИИ
        expenses = extract_expenses_from_text(clean_text)

        if not expenses:
            await message.answer("❌ ИИ не нашел трат в этом тексте.")
            return

        # 5. Итог
        res = ["✅ **Записано:**"]
        for exp in expenses:
            add_expense(user_id, exp["amount"], exp["category"], exp["description"])
            res.append(f"— {exp['category']}: {exp['amount']} руб.")

        await message.answer("\n".join(res), parse_mode="Markdown")

    except Exception as e:
        print(f"❌ ОШИБКА: {e}", flush=True)
        await message.answer("❌ Что-то пошло не так.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@dp.message()
async def handle_text(message: Message):
    if not message.text: return
    expenses = extract_expenses_from_text(message.text)
    if expenses:
        for exp in expenses:
            add_expense(message.from_user.id, exp["amount"], exp["category"], exp["description"])
        await message.answer("✅ Сохранил текст!")


async def main_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def run_telegram_bot():
    asyncio.run(main_bot())