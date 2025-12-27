import asyncio
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yt_dlp

from bot.database.repository import add_download_stat


@dataclass
class VideoInfo:
    """Информация о видео"""

    url: str
    title: str
    thumbnail: str
    duration: int
    available_resolutions: List[str]


class DownloadResult:
    def __init__(
        self,
        success: bool,
        video_path: Optional[str] = None,
        error: Optional[str] = None,
        video_info: Optional[VideoInfo] = None,
    ):
        self.success = success
        self.video_path = video_path
        self.error = error
        self.video_info = video_info


class YouTubeDownloader:
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.active_downloads: Dict[int, bool] = {}
        self.video_cache: Dict[int, VideoInfo] = {}
        self.cookies_path = Path(__file__).parent.parent.parent / "cookies.txt"

    def is_user_downloading(self, user_id: int) -> bool:
        return self.active_downloads.get(user_id, False)

    def _get_ydl_opts(self, output_path: str = None, format_string: str = "best"):
        """Получить базовые настройки yt-dlp с максимальной совместимостью"""
        opts = {
            "quiet": False,
            "no_warnings": False,
            "format": format_string,
            "geo_bypass": True,
            "nocheckcertificate": True,
        }

        if output_path:
            opts["outtmpl"] = output_path
            opts["merge_output_format"] = "mp4"

        # Добавляем cookies если есть
        if self.cookies_path.exists():
            opts["cookiefile"] = str(self.cookies_path.absolute())
            print(f"✅ Используем cookies из: {self.cookies_path}")

        return opts

    async def get_video_info(self, url: str, user_id: int) -> DownloadResult:
        """Получить информацию о видео и доступные разрешения"""
        if self.is_user_downloading(user_id):
            return DownloadResult(
                success=False, error="Вы уже обрабатываете видео. Дождитесь завершения."
            )

        self.active_downloads[user_id] = True

        try:
            ydl_opts = self._get_ydl_opts()
            ydl_opts["quiet"] = True

            print(f"🔍 Получаем информацию о видео: {url}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)

            # Получаем доступные разрешения
            formats = info.get("formats", [])
            resolutions = set()

            for fmt in formats:
                height = fmt.get("height")
                if height:
                    resolutions.add(height)

            available_resolutions = sorted(list(resolutions))
            print(f"✅ Доступные разрешения: {available_resolutions}")

            # Фильтруем стандартные разрешения
            standard_resolutions = ["480", "720"]
            display_resolutions = [
                res
                for res in standard_resolutions
                if any(int(res) <= ar for ar in available_resolutions)
            ]

            if not display_resolutions:
                display_resolutions = ["360", "480", "720"]

            video_info = VideoInfo(
                url=url,
                title=info.get("title", "Без названия"),
                thumbnail=info.get("thumbnail", ""),
                duration=info.get("duration", 0),
                available_resolutions=display_resolutions,
            )

            self.video_cache[user_id] = video_info
            return DownloadResult(success=True, video_info=video_info)

        except Exception as e:
            error_text = str(e)
            print(f"❌ Ошибка получения информации: {error_text}")

            # Упрощенное сообщение об ошибке
            if "403" in error_text or "Forbidden" in error_text:
                return DownloadResult(
                    success=False,
                    error="⚠️ Не удалось получить доступ к видео.\n\n"
                    "Попробуйте:\n"
                    "1. Другую ссылку\n"
                    "2. Обновить бота (pip install --upgrade yt-dlp)",
                )

            return DownloadResult(success=False, error=f"Ошибка: {error_text[:100]}")

        finally:
            self.active_downloads[user_id] = False

    async def download_video_by_resolution(
        self, user_id: int, resolution: str
    ) -> DownloadResult:
        """Скачать видео в определенном разрешении"""
        if self.is_user_downloading(user_id):
            return DownloadResult(
                success=False, error="Вы уже загружаете видео. Дождитесь завершения."
            )

        video_info = self.video_cache.get(user_id)
        if not video_info:
            return DownloadResult(
                success=False,
                error="Информация о видео не найдена. Отправьте ссылку заново.",
            )

        self.active_downloads[user_id] = True

        try:
            video_path = await self._download_video(video_info.url, user_id, resolution)
            add_download_stat(user_id, video_info.url)
            return DownloadResult(success=True, video_path=video_path)

        except Exception as e:
            error_text = str(e)
            print(f"❌ Ошибка скачивания: {error_text}")
            return DownloadResult(
                success=False, error=f"Не удалось скачать: {error_text[:100]}"
            )

        finally:
            self.active_downloads[user_id] = False

    async def download_and_process(self, url: str, user_id: int) -> DownloadResult:
        """Старый метод для обратной совместимости"""
        if self.is_user_downloading(user_id):
            return DownloadResult(
                success=False, error="Вы уже загружаете видео. Дождитесь завершения."
            )

        self.active_downloads[user_id] = True

        try:
            video_path = await self._download_video(url, user_id)
            add_download_stat(user_id, url)
            return DownloadResult(success=True, video_path=video_path)

        except Exception as e:
            return DownloadResult(success=False, error=str(e))

        finally:
            self.active_downloads[user_id] = False

    async def _download_video(
        self, url: str, user_id: int, resolution: Optional[str] = None
    ) -> str:
        """Скачать видео - версия с выбором format_id"""
        output_path = self.download_dir / f"{user_id}_{uuid.uuid4().hex[:8]}.mp4"

        print(f"\n{'=' * 60}")
        print(f"🎬 НАЧИНАЕМ СКАЧИВАНИЕ")
        print(f"{'=' * 60}")
        print(f"📹 URL: {url}")
        print(
            f"🎯 Запрошенное разрешение: {resolution}p"
            if resolution
            else "🎯 Лучшее качество"
        )

        try:
            # Получаем информацию о видео
            info_opts = self._get_ydl_opts()
            info_opts["quiet"] = True

            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)

            # Анализируем форматы и выбираем подходящий
            formats = info.get("formats", [])

            selected_format_id = None
            selected_height = None

            if resolution and formats:
                target_height = int(resolution)

                # Ищем форматы с видео и аудио
                suitable_formats = []
                for fmt in formats:
                    height = fmt.get("height")
                    vcodec = fmt.get("vcodec", "none")
                    acodec = fmt.get("acodec", "none")
                    format_id = fmt.get("format_id")

                    # Ищем форматы с видео
                    if height and vcodec != "none":
                        # Если есть аудио - отлично, если нет - тоже подойдет
                        diff = abs(height - target_height)
                        suitable_formats.append(
                            {
                                "id": format_id,
                                "height": height,
                                "has_audio": acodec != "none",
                                "diff": diff,
                            }
                        )

                # Сортируем: сначала по близости к целевому разрешению, потом по наличию аудио
                suitable_formats.sort(key=lambda x: (x["diff"], not x["has_audio"]))

                if suitable_formats:
                    best = suitable_formats[0]
                    selected_format_id = best["id"]
                    selected_height = best["height"]

                    print(
                        f"✅ Выбран формат: {selected_format_id} ({selected_height}p)"
                    )
                    print(
                        f"   Имеет аудио: {'Да' if best['has_audio'] else 'Нет (будет добавлен)'}"
                    )

            # Формируем строку формата
            if selected_format_id:
                if resolution:
                    # Выбираем конкретный format_id + лучший аудио если нужно
                    format_string = (
                        f"{selected_format_id}+bestaudio/{selected_format_id}/best"
                    )
                else:
                    format_string = "bestvideo+bestaudio/best"
            else:
                format_string = "best"

            print(f"📥 Итоговый формат: {format_string}")
            print(f"💾 Выходной файл: {output_path}")
            print(f"{'=' * 60}\n")

            # Скачиваем с выбранным форматом
            download_opts = self._get_ydl_opts(str(output_path), format_string)

            with yt_dlp.YoutubeDL(download_opts) as ydl:
                print(f"⬇️ Скачиваем...")
                await asyncio.to_thread(ydl.download, [url])

            if not os.path.exists(output_path):
                raise Exception("Файл не был создан после скачивания")

            file_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"\n✅ УСПЕШНО СКАЧАНО!")
            print(f"📦 Размер: {file_size:.2f} MB")

            if selected_height:
                print(
                    f"🎯 Фактическое разрешение: {selected_height}p (запрошено: {resolution}p)"
                )

            print(f"📁 Файл: {output_path}\n")

        except Exception as e:
            error_text = str(e)
            print(f"\n❌ ОШИБКА ПРИ СКАЧИВАНИИ:")
            print(f"{error_text}\n")

            if os.path.exists(output_path):
                os.remove(output_path)

            raise Exception(f"Не удалось скачать видео: {error_text[:150]}")

        return str(output_path)

    def cleanup(self, video_path: str):
        """Удалить временный файл"""
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
                print(f"🗑️ Удален временный файл: {video_path}")
            except Exception as e:
                print(f"⚠️ Не удалось удалить файл: {e}")

    def clear_cache(self, user_id: int):
        """Очистить кэш пользователя"""
        if user_id in self.video_cache:
            del self.video_cache[user_id]
            print(f"🧹 Очищен кэш для пользователя {user_id}")
