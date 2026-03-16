import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from app.config import config
from app.handlers import start, application, admin
from app.db.session import init_models

async def main():
    if not config.bot_token:
        logging.error("BOT_TOKEN is missing in environment variables.")
        sys.exit(1)
        
    if not config.database_url:
        logging.error("DATABASE_URL is missing in environment variables.")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)
    
    await init_models()

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(application.router)
    dp.include_router(admin.router)

    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
