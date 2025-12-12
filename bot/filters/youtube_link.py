import re

from aiogram.filters import Filter


class IsYouTubeShorts(Filter):
    async def __call__(self, message) -> bool:
        if not message.text:
            return False

        pattern = r"(https?://)?(www\.)?(youtube\.com/shorts/|youtu\.be/shorts/)[^\s]+"
        return bool(re.search(pattern, message.text))
