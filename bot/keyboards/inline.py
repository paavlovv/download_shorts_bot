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
