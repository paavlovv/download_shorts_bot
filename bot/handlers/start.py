from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.reply import get_main_keyboard

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    """Обработчик команды /start"""

    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот для скачивания YouTube Shorts.\n\n"
        "📎 Отправь мне ссылку на видео или нажми кнопку 📥 Download",
        reply_markup=get_main_keyboard(),
    )
