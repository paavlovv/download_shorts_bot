import asyncio
import os
import uuid
from pathlib import Path
from typing import Dict, Optional

import yt_dlp

from bot.database.repository import add_download_stat


class DownloadResult:
    def __init__(
        self,
        success: bool,
        video_path: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.video_path = video_path
        self.error = error


class YouTubeDownloader:
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.active_downloads: Dict[int, bool] = {}

        self.cookies_path = Path(__file__).parent.parent.parent / "cookies.txt"

    def is_user_downloading(self, user_id: int) -> bool:
        return self.active_downloads.get(user_id, False)

    async def download_and_process(self, url: str, user_id: int) -> DownloadResult:
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

    async def _download_video(self, url: str, user_id: int) -> str:
        output_path = self.download_dir / f"{user_id}_{uuid.uuid4().hex[:8]}.mp4"

        print(f"\n{'=' * 60}")
        print(f"🔍 ДИАГНОСТИКА COOKIES:")
        print(f"{'=' * 60}")
        print(f"Путь к cookies: {self.cookies_path}")
        print(f"Абсолютный путь: {self.cookies_path.absolute()}")
        print(f"Файл существует: {self.cookies_path.exists()}")

        if self.cookies_path.exists():
            file_size = self.cookies_path.stat().st_size
            print(f"Размер файла: {file_size} байт")

            with open(self.cookies_path, "r") as f:
                lines = f.readlines()[:5]
                print(f"Первые строки cookies.txt:")
                for i, line in enumerate(lines, 1):
                    print(f"  {i}: {line.strip()}")
        else:
            print(f"❌ ФАЙЛ НЕ НАЙДЕН!")
        print(f"{'=' * 60}\n")

        ydl_opts = {
            "format": "best[height<=1080]/best",
            "outtmpl": str(output_path),
            "quiet": False,
        }

        if self.cookies_path.exists():
            ydl_opts["cookiefile"] = str(self.cookies_path)
            print(f"✅ Параметр 'cookiefile' установлен: {self.cookies_path}")
        else:
            print(f"⚠️  Файл cookies.txt не найден, пробуем без cookies")

        print(f"🚀 Начинаем скачивание: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])

        return str(output_path)

    def cleanup(self, video_path: str):
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
