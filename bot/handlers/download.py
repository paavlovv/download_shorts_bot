from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message

from bot.filters.youtube_link import IsYouTubeShorts
from bot.services.youtube import YouTubeDownloader

router = Router()
youtube_service = YouTubeDownloader()


@router.message(Command("download"))
async def download_command_handler(message: Message):
    """Обработчик команды /download <url>"""

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        await message.answer(
            "❌ Использование: /download <ссылка>\n\n"
            "Пример: /download https://youtube.com/shorts/ABC123"
        )
        return

    url = parts[1]
    await process_download(message, url)


@router.message(F.text == "📥 Download")
async def download_button_handler(message: Message):
    """Обработчик кнопки Download"""
    await message.answer(
        "📎 Отправьте ссылку на YouTube Shorts:\n\n"
        "Например: https://youtube.com/shorts/ABC123"
    )


@router.message(IsYouTubeShorts())
async def download_link_handler(message: Message):
    """Обработчик просто отправленной ссылки"""
    url = message.text
    await process_download(message, url)


async def process_download(message: Message, url: str):
    user_id = message.from_user.id

    loading_msg = await message.answer("⏳ Loading...")

    try:
        result = await youtube_service.download_and_process(url, user_id)

        if result.success:
            video_file = FSInputFile(result.video_path)
            await message.answer_video(video_file, caption="✅ Готово!")

            youtube_service.cleanup(result.video_path)
        else:
            await message.answer(f"❌ {result.error}")

    finally:
        await loading_msg.delete()
