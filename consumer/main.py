import asyncio
import logging
from faststream import FastStream

from consumer.core.config import bot, broker
from consumer.parser import process_recipe
from consumer.core.database import MongoManager

logger = logging.getLogger(__name__)
mongo_manager = MongoManager()
app = FastStream(broker)


@app.on_startup
async def connect_to_mongo():
    """Подключение к MongoDB при старте FastStream."""
    await mongo_manager.connect()
    logger.info("Подключение к MongoDB установлено.")


@app.on_shutdown
async def close_mongo():
    """Закрытие соединения с MongoDB при завершении работы."""
    await mongo_manager.close()
    logger.info("Соединение с MongoDB закрыто.")


@broker.subscriber("recipe_processing_queue")
async def handle_recipe_message(data: dict):
    """Обработчик сообщений из очереди RabbitMQ."""
    url = data["url"]
    user_id = data["user_id"]
    chat_id = data["chat_id"]

    await process_recipe(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        url=url,
        mongo=mongo_manager,
    )


if __name__ == "__main__":
    print("🚀 Запуск FastStream потребителя...")
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("Работа потребителя завершена.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        print("До свидания")
