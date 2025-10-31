import asyncio
import logging
from faststream import FastStream

from consumer.core.config import bot, broker
from consumer.core.exceptions import ExceptProcessRecipeError
from consumer.vectoring.models.chroma import chrome
from consumer.utils.parser import process_recipe
from consumer.core.database import MongoManager


logger = logging.getLogger(__name__)
mongo_manager = MongoManager()

app = FastStream(broker)


@app.on_startup
async def connect_to_mongo():
    """Подключение к MongoDB при старте FastStream."""
    await mongo_manager.connect()
    logger.info("Подключение к MongoDB установлено.")
    """Подключение к chromeDB при старте FastStream."""
    await chrome.init()


@app.on_shutdown
async def close_mongo():
    """Закрытие соединения с MongoDB при завершении работы."""
    await mongo_manager.close()
    logger.info("Соединение с MongoDB закрыто.")


@broker.subscriber("recipe_processing_queue")
async def handle_recipe_message(data: dict[str, str | int]):
    """Обработчик сообщений из очереди RabbitMQ."""
    url: str = data["url"]
    user_id: int = data["user_id"]
    chat_id: int = data["chat_id"]

    try:
        await process_recipe(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            url=url,
            mongo=mongo_manager,
        )
    except ExceptProcessRecipeError as e:
        logger.exception(f"Ошибка при обработке рецепта: {e}")


@broker.subscriber("recipe_search_queue")
async def handle_recipe_message(data: dict[str, str | int]):
    """Обработчик сообщений из очереди RabbitMQ для поиска рецепта"""
    search_text: str = data["search_text"]
    user_id: int = data["user_id"]
    chat_id: int = data["chat_id"]
    logger.info(f"Старт поиска рецепта по запросу: {search_text}")


if __name__ == "__main__":
    logger.info("🚀 Запуск FastStream потребителя...")
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("Работа потребителя завершена.")
    except Exception as e:
        logger.exception(f"Произошла ошибка: {e}")
    finally:
        print("До свидания")
