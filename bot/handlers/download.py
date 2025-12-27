from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message, URLInputFile

from bot.filters.youtube_link import IsYouTubeShorts
from bot.keyboards.inline import get_resolution_keyboard
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
    await process_video_info(message, url)


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
    await process_video_info(message, url)


async def process_video_info(message: Message, url: str):
    """Получить информацию о видео и показать превью с выбором разрешения"""
    user_id = message.from_user.id

    loading_msg = await message.answer("⏳ Loading...")

    try:
        result = await youtube_service.get_video_info(url, user_id)

        if result.success and result.video_info:
            video_info = result.video_info

            # Формируем текст с информацией о видео
            duration_minutes = video_info.duration // 60
            duration_seconds = video_info.duration % 60

            caption = (
                f"🎬 <b>{video_info.title}</b>\n\n"
                f"⏱ Длительность: {duration_minutes}:{duration_seconds:02d}\n\n"
                f"📊 Выберите качество видео:"
            )

            # Отправляем превью с кнопками выбора разрешения
            if video_info.thumbnail:
                try:
                    await message.answer_photo(
                        photo=URLInputFile(video_info.thumbnail),
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=get_resolution_keyboard(
                            video_info.available_resolutions
                        ),
                    )
                except Exception as e:
                    # Если не удалось загрузить превью, отправляем только текст
                    await message.answer(
                        caption,
                        parse_mode="HTML",
                        reply_markup=get_resolution_keyboard(
                            video_info.available_resolutions
                        ),
                    )
            else:
                await message.answer(
                    caption,
                    parse_mode="HTML",
                    reply_markup=get_resolution_keyboard(
                        video_info.available_resolutions
                    ),
                )
        else:
            await message.answer(f"❌ {result.error}")

    finally:
        await loading_msg.delete()


@router.callback_query(F.data.startswith("resolution:"))
async def resolution_callback_handler(callback: CallbackQuery):
    """Обработчик выбора разрешения"""
    resolution = callback.data.split(":")[1]
    user_id = callback.from_user.id

    print(f"👤 Пользователь {user_id} выбрал разрешение: {resolution}p")

    # Обновляем сообщение
    await callback.message.edit_caption(
        caption=f"⏳ Скачиваю видео в разрешении {resolution}p...", reply_markup=None
    )

    try:
        result = await youtube_service.download_video_by_resolution(user_id, resolution)

        if result.success:
            video_file = FSInputFile(result.video_path)

            # Получаем размер файла
            import os

            file_size = os.path.getsize(result.video_path) / (1024 * 1024)  # В МБ

            print(f"📤 Отправляем видео: {file_size:.2f} MB")

            # Отправляем видео БЕЗ сжатия
            # supports_streaming=False отключает потоковую передачу и сжатие
            await callback.message.answer_video(
                video=video_file,
                caption=f"✅ Готово! Качество: {resolution}p\n📦 Размер: {file_size:.1f} MB",
                supports_streaming=False,  # Отключаем сжатие!
                width=None,  # Не указываем размеры
                height=None,
            )

            youtube_service.cleanup(result.video_path)
            youtube_service.clear_cache(user_id)

            # Удаляем сообщение с превью
            await callback.message.delete()
        else:
            await callback.message.edit_caption(
                caption=f"❌ {result.error}", reply_markup=None
            )

    except Exception as e:
        print(f"❌ Ошибка при отправке: {e}")
        await callback.message.edit_caption(
            caption=f"❌ Ошибка: {str(e)}", reply_markup=None
        )

    await callback.answer()
