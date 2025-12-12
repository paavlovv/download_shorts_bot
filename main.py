import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import BOT_TOKEN
from bot.database.models import init_db
from bot.handlers import admin, download, start
from bot.middlewares.user_tracking import UserTrackingMiddleware

logging.basicConfig(level=logging.INFO)


async def main():
    """Точка входа в приложение"""

    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(UserTrackingMiddleware())

    dp.include_router(admin.router)  # Админ-команды (первые, т.к. с фильтром)
    dp.include_router(start.router)  # /start
    dp.include_router(download.router)  # Скачивание

    print("🚀 Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
