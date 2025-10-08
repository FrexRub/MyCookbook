import logging
from typing import Optional

from async_pymongo import AsyncClient

from src.core.config import configure_logging, setting

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


class MongoManager:
    def __init__(self):
        self.client: Optional[AsyncClient] = None
        self.db = None
        self._is_connected: bool = False

    async def connect(self):
        if self._is_connected:
            return

        self.client = AsyncClient(setting.mongo.url)
        self.db = self.client[setting.mongo.mongo_initdb_database]
        try:
            await self.client.admin.command("ping")
            self._is_connected = True
            logger.info("✅ MongoDB подключена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к MongoDB: {e}")
            raise

    async def close(self):
        if self.client:
            await self.client.close()
            self._is_connected = False
            logger.info("🔌 MongoDB отключена")

    def get_collection(self, name: str):
        if not self._is_connected or self.db is None:
            raise RuntimeError(
                "MongoDB не подключена. Вызовите connect() перед использованием."
            )
        return self.db[name]


mongo_manager = MongoManager()


async def mongo_middleware(handler, event, data):
    data["mongo"] = mongo_manager
    return await handler(event, data)
