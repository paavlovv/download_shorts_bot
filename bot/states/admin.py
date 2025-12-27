from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    waiting_for_type = State()  # Ожидаем выбор типа рассылки
    waiting_for_text = State()  # Ожидаем текст рассылки
    waiting_for_photo = State()  # Ожидаем фото для рассылки
    waiting_for_caption = State()  # Ожидаем текст к фото
    waiting_for_confirm = State()  # Ожидаем подтверждение
