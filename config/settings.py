import os
from pathlib import Path
from dotenv import load_dotenv

# Определяем путь к .env в корне проекта
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/fintwist.db")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError(f"No TELEGRAM_BOT_TOKEN provided in .env file (looked at {BASE_DIR / '.env'})")
