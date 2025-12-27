from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
                InlineKeyboardButton(
                    text="📢 Рассылка", callback_data="admin:broadcast"
                ),
            ],
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin:users")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin:refresh")],
        ]
    )
    return keyboard


def get_broadcast_confirm_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Отправить", callback_data="broadcast:confirm"
                ),
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data="broadcast:cancel"
                ),
            ]
        ]
    )
    return keyboard


def get_broadcast_type_keyboard():
    """Клавиатура выбора типа рассылки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Только текст", callback_data="broadcast:type:text"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🖼 Текст + Фото", callback_data="broadcast:type:photo"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data="broadcast:cancel"
                )
            ],
        ]
    )
    return keyboard


def get_cancel_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast:cancel")]
        ]
    )
    return keyboard


def get_back_to_admin_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад в админку", callback_data="admin:back")]
        ]
    )
    return keyboard


def get_resolution_keyboard(available_resolutions: List[str]):
    """Клавиатура выбора разрешения видео"""
    resolution_names = {
        "480": "480p 📺",
        "720": "720p HD 🎬",
    }

    buttons = []
    row = []

    for resolution in available_resolutions:
        name = resolution_names.get(resolution, f"{resolution}p")
        button = InlineKeyboardButton(
            text=name, callback_data=f"resolution:{resolution}"
        )
        row.append(button)

        # По 2 кнопки в ряд
        if len(row) == 2:
            buttons.append(row)
            row = []

    # Добавляем оставшиеся кнопки
    if row:
        buttons.append(row)

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
