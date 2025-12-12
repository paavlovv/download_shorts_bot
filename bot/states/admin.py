from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    waiting_for_text = State()  # Ожидаем текст рассылки
    waiting_for_confirm = State()  # Ожидаем подтверждение
