import asyncio
import logging

from src.core.config import configure_logging, bot, dp
from src.bot.handlers.start import router as start_router


configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

dp.include_router(start_router)


async def main():
    logger.info("Start Bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
