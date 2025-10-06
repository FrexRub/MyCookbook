import asyncio
import logging

from src.bot.commands import set_commands
from src.core.database import mongo_middleware, MongoManager
from src.core.config import configure_logging, bot, dp
from src.bot.handlers.start import router as start_router
from src.bot.handlers.chat_member import router as chat_member_router


configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

dp.include_router(start_router)
dp.include_router(chat_member_router)


async def main():
    logger.info("Start Bot")
    # Инициализация MongoDB
    mongo_manager = MongoManager()
    await mongo_manager.connect()

    dp.startup.register(set_commands)
    dp.update.middleware(mongo_middleware)

    try:
        await dp.start_polling(bot)
    finally:
        await mongo_manager.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
