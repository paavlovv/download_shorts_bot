import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
DATABASE_PATH = "bot_database.db"
DOWNLOAD_DIR = "downloads"

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in .env file!")
