import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers import start, admin, user

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN topilmadi. .env faylini tekshiring.")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # MUHIM: admin router user routerdan OLDIN turadi
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    print("Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot polling boshlandi.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())