from pathlib import Path
import logging

from openai import OpenAI
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from pydantic import SecretStr, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s",
    )


class LlmSettings(BaseSettings):
    openrouter_api_key: SecretStr
    base_url_llm: str
    model_llm: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # игнорирование наличия других полей в .env - файле
        case_sensitive=False,  # регистронезависимость
    )


class BotSettings(BaseSettings):
    bot_token: SecretStr
    admin_id: int

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # игнорирование наличия других полей в .env - файле
        case_sensitive=False,  # регистронезависимость
    )


class RedisSettings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf8", extra="ignore"
    )

    @property
    def url(self):
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class MongoSettings(BaseSettings):
    mongo_initdb_root_username: str
    mongo_initdb_root_password: str
    mongo_initdb_database: str
    mongo_initdb_host: str = "localhost"
    mongo_initdb_port: int = 27017

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf8", extra="ignore"
    )

    @property
    def url(self):
        # return f"mongodb://{self.mongo_initdb_root_username}:{self.mongo_initdb_root_password}@{self.mongo_initdb_host}:{self.mongo_initdb_port}/{self.mongo_initdb_database}?authSource={self.mongo_initdb_root_username}"
        # DATABASE_URL=mongodb://admin:password123@localhost:6000/fastapi?authSource=admin
        res: str = (
            f"mongodb://{self.mongo_initdb_root_username}:{self.mongo_initdb_root_password}"
            f"@{self.mongo_initdb_host}:{self.mongo_initdb_port}"
            f"/{self.mongo_initdb_database}?authSource={self.mongo_initdb_root_username}"
        )
        return res


class Setting(BaseModel):
    llm: LlmSettings = LlmSettings()
    bot: BotSettings = BotSettings()
    redis: RedisSettings = RedisSettings()
    mongo: MongoSettings = MongoSettings()


setting = Setting()

llm_client = OpenAI(
    api_key=setting.llm.openrouter_api_key.get_secret_value(),
    base_url=setting.llm.base_url_llm,
)

bot = Bot(
    token=setting.bot.bot_token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

storage = RedisStorage.from_url(url=setting.redis.url)

dp = Dispatcher(storage=storage)
