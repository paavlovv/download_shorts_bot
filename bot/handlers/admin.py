import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.repository import get_all_users, get_download_count, get_user_count
from bot.filters.admin import IsAdmin
from bot.keyboards.inline import (
    get_admin_keyboard,
    get_back_to_admin_keyboard,
    get_broadcast_confirm_keyboard,
    get_broadcast_type_keyboard,
    get_cancel_keyboard,
)
from bot.services.broadcast import BroadcastService
from bot.states.admin import BroadcastStates

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("admin"), IsAdmin())
async def admin_panel_handler(message: Message):
    """Открыть админ-панель"""
    users_count = get_user_count()
    downloads_count = get_download_count()

    text = (
        "🔧 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"📥 Загрузок: <b>{downloads_count}</b>\n\n"
        "Выберите действие:"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_keyboard())


@router.callback_query(F.data == "admin:back", IsAdmin())
async def admin_back_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню админки"""
    await state.clear()

    users_count = get_user_count()
    downloads_count = get_download_count()

    text = (
        "🔧 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"📥 Загрузок: <b>{downloads_count}</b>\n\n"
        "Выберите действие:"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin:stats", IsAdmin())
async def admin_stats_handler(callback: CallbackQuery):
    """Подробная статистика"""
    users_count = get_user_count()
    downloads_count = get_download_count()

    avg_per_user = downloads_count / users_count if users_count > 0 else 0

    text = (
        "📊 <b>СТАТИСТИКА</b>\n\n"
        f"👥 Всего пользователей: <b>{users_count}</b>\n"
        f"📥 Всего загрузок: <b>{downloads_count}</b>\n"
        f"📈 Среднее на пользователя: <b>{avg_per_user:.2f}</b>\n"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=get_back_to_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin:users", IsAdmin())
async def admin_users_handler(callback: CallbackQuery):
    """Список последних пользователей"""
    users = get_all_users()

    if not users:
        text = "👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\nПользователей пока нет."
    else:
        # Показываем последних 10
        text = "👥 <b>ПОСЛЕДНИЕ ПОЛЬЗОВАТЕЛИ</b>\n\n"
        for user in users[-10:]:
            username = f"@{user['username']}" if user["username"] else "без username"
            name = user["first_name"] or "Без имени"
            text += f"• {name} ({username})\n"

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=get_back_to_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast", IsAdmin())
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Начать процесс рассылки - выбор типа"""
    users_count = get_user_count()

    text = (
        "📢 <b>РАССЫЛКА</b>\n\n"
        f"Рассылка будет отправлена <b>{users_count}</b> пользователям.\n\n"
        "Выберите тип рассылки:"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=get_broadcast_type_keyboard()
    )
    await state.set_state(BroadcastStates.waiting_for_type)
    await callback.answer()


@router.callback_query(F.data == "broadcast:type:text", IsAdmin())
async def broadcast_type_text_handler(callback: CallbackQuery, state: FSMContext):
    """Выбран тип рассылки: только текст"""
    await state.update_data(broadcast_type="text")

    text = "📝 <b>ТЕКСТОВАЯ РАССЫЛКА</b>\n\nОтправьте текст сообщения для рассылки:"

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=get_cancel_keyboard()
    )
    await state.set_state(BroadcastStates.waiting_for_text)
    await callback.answer()


@router.callback_query(F.data == "broadcast:type:photo", IsAdmin())
async def broadcast_type_photo_handler(callback: CallbackQuery, state: FSMContext):
    """Выбран тип рассылки: текст + фото"""
    await state.update_data(broadcast_type="photo")

    text = "🖼 <b>РАССЫЛКА С ФОТО</b>\n\nОтправьте фото для рассылки:"

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=get_cancel_keyboard()
    )
    await state.set_state(BroadcastStates.waiting_for_photo)
    await callback.answer()


@router.callback_query(F.data == "broadcast:cancel", IsAdmin())
async def broadcast_cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Отменить рассылку"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Рассылка отменена.", reply_markup=get_back_to_admin_keyboard()
    )
    await callback.answer("Отменено")


@router.message(BroadcastStates.waiting_for_photo, F.photo, IsAdmin())
async def broadcast_photo_received(message: Message, state: FSMContext):
    """Получено фото для рассылки"""
    photo_id = message.photo[-1].file_id  # Берем самое большое фото
    await state.update_data(photo_id=photo_id)

    text = "✅ Фото получено!\n\nТеперь отправьте текст (подпись) к фото:"

    await message.answer(text, reply_markup=get_cancel_keyboard())
    await state.set_state(BroadcastStates.waiting_for_caption)


@router.message(BroadcastStates.waiting_for_caption, IsAdmin())
async def broadcast_caption_received(message: Message, state: FSMContext):
    """Получен текст к фото"""
    caption = message.text
    data = await state.get_data()
    photo_id = data.get("photo_id")
    users_count = get_user_count()

    await state.update_data(broadcast_text=caption)

    text = (
        "📢 <b>ПОДТВЕРЖДЕНИЕ РАССЫЛКИ</b>\n\n"
        f"Получателей: <b>{users_count}</b>\n\n"
        "Текст сообщения:\n"
        "━━━━━━━━━━━━━━━━\n"
        f"{caption}\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Отправить?"
    )

    # Отправляем превью с фото
    await message.answer_photo(
        photo=photo_id,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_broadcast_confirm_keyboard(),
    )
    await state.set_state(BroadcastStates.waiting_for_confirm)


@router.message(BroadcastStates.waiting_for_text, IsAdmin())
async def broadcast_text_received(message: Message, state: FSMContext):
    """Получен текст для рассылки"""
    broadcast_text = message.text
    users_count = get_user_count()

    await state.update_data(broadcast_text=broadcast_text)

    text = (
        "📢 <b>ПОДТВЕРЖДЕНИЕ РАССЫЛКИ</b>\n\n"
        f"Получателей: <b>{users_count}</b>\n\n"
        "Текст сообщения:\n"
        "━━━━━━━━━━━━━━━━\n"
        f"{broadcast_text}\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Отправить?"
    )

    await message.answer(
        text, parse_mode="HTML", reply_markup=get_broadcast_confirm_keyboard()
    )
    await state.set_state(BroadcastStates.waiting_for_confirm)


@router.callback_query(F.data == "broadcast:confirm", IsAdmin())
async def broadcast_confirm_handler(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и отправка рассылки"""
    data = await state.get_data()
    broadcast_text = data.get("broadcast_text")
    broadcast_type = data.get("broadcast_type", "text")
    photo_id = data.get("photo_id")

    if not broadcast_text:
        await callback.answer("❌ Ошибка: текст не найден", show_alert=True)
        await state.clear()
        return

    # Удаляем сообщение с подтверждением
    try:
        await callback.message.delete()
    except:
        pass

    status_msg = await callback.message.answer("📢 Начинаю рассылку...")

    users = get_all_users()
    total = len(users)
    success = 0
    failed = 0

    for i, user in enumerate(users, 1):
        try:
            if broadcast_type == "photo" and photo_id:
                await callback.bot.send_photo(
                    user["user_id"], photo=photo_id, caption=broadcast_text
                )
            else:
                await callback.bot.send_message(user["user_id"], broadcast_text)
            success += 1
        except Exception as e:
            logger.error(f"Failed to send to {user['user_id']}: {e}")
            failed += 1

        # Обновляем прогресс каждые 10 сообщений
        if i % 10 == 0 or i == total:
            try:
                progress = (i / total) * 100
                await status_msg.edit_text(
                    f"📢 Рассылка в процессе...\n\n"
                    f"Прогресс: {i}/{total} ({progress:.1f}%)\n"
                    f"✅ Успешно: {success}\n"
                    f"❌ Ошибок: {failed}"
                )
            except:
                pass

        await asyncio.sleep(0.05)

    # Финальный отчет
    await status_msg.edit_text(
        f"✅ <b>РАССЫЛКА ЗАВЕРШЕНА!</b>\n\n"
        f"📊 Всего: {total}\n"
        f"✅ Отправлено: {success}\n"
        f"❌ Ошибок: {failed}",
        parse_mode="HTML",
        reply_markup=get_back_to_admin_keyboard(),
    )

    await state.clear()
    await callback.answer("✅ Рассылка завершена!")


@router.callback_query(F.data == "admin:refresh", IsAdmin())
async def admin_refresh_handler(callback: CallbackQuery):
    """Обновить данные в админке"""
    users_count = get_user_count()
    downloads_count = get_download_count()

    text = (
        "🔧 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"📥 Загрузок: <b>{downloads_count}</b>\n\n"
        "Выберите действие:"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=get_admin_keyboard()
    )
    await callback.answer("🔄 Данные обновлены")
