from bot.database.repository import get_all_users


class BroadcastService:
    def __init__(self, bot):
        self.bot = bot

    async def send_to_all(self, text: str):
        users = get_all_users()
        success = 0
        failed = 0

        for user in users:
            try:
                await self.bot.send_message(user["user_id"], text)
                success += 1
            except Exception:
                failed += 1

        return success, failed
