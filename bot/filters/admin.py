from aiogram.filters import Filter
from bot.config import ADMIN_IDS


class IsAdmin(Filter):
    async def __call__(self, message) -> bool:
        return message.from_user.id in ADMIN_IDS
