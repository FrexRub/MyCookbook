from typing import Optional
import logging

from async_pymongo import AsyncClient

from src.core.config import setting, configure_logging

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


class MongoManager:
    def __init__(self):
        self.client: Optional[AsyncClient] = None
        self.db = None

    async def connect(self):
        self.client = AsyncClient(setting.mongo.url)
        self.db = self.client[setting.mongo.mongo_initdb_database]
        try:
            await self.client.admin.command("ping")
            logger.info("✅ MongoDB подключена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к MongoDB: {e}")
            raise

    async def close(self):
        if self.client:
            await self.client.close()
            logger.info("🔌 MongoDB отключена")

    def get_collection(self, name: str):
        return self.db[name]


mongo_manager = MongoManager()


async def mongo_middleware(handler, event, data):
    data["mongo"] = mongo_manager
    return await handler(event, data)
