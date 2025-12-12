from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📥 Download")]],
        resize_keyboard=True,
        input_field_placeholder="Отправьте ссылку на YouTube Shorts",
    )
    return keyboard
