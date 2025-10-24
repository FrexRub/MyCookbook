import asyncio
import logging

from src.bot.commands import set_commands
from src.bot.handlers.chat_member import router as chat_member_router
from src.bot.handlers.chat_recipe import router as chat_recipe
from src.bot.handlers.start import router as start_router
from src.core.config import bot, configure_logging, dp, broker
from src.core.database import mongo_manager, mongo_middleware

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

dp.include_router(start_router)
dp.include_router(chat_member_router)
dp.include_router(chat_recipe)


async def main():
    logger.info("Start Bot")
    await mongo_manager.connect()
    dp.startup.register(set_commands)
    dp.update.middleware(mongo_middleware)

    await broker.connect()
    logger.info("Подключение к RabbitMQ установлено")

    try:
        await dp.start_polling(bot)
    finally:
        # Полное завершение всех задач
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        await broker.close()
        await mongo_manager.close()
        if bot.session:
            await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Чат прерван пользователем")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        print("До свидания")
