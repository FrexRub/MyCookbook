import logging
import re
import string
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from faststream.rabbit import RabbitBroker
from openai import OpenAI
from pydantic import BaseModel, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).parent.parent

URL_PATTERN = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*\??[/\w\.-=&%]*"
HEADER_PATTERN = re.compile(r"^(#+)\s(.+)")  # для заголовков документов в Markdown
PUNCTUATION_PATTERN = re.compile(f"[{re.escape(string.punctuation)}]")  # для удаления пунктуации
WHITESPACE_PATTERN = re.compile(r"\s+")  # для удаления лишних пробелов

CHROMA_PATH = BASE_DIR / "recipe_chroma_db"
COLLECTION_NAME = "recipe_data"


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s",
    )


class LlmSettings(BaseSettings):
    openrouter_api_key: SecretStr = Field(default=SecretStr(""), description="OpenRouter API key")
    base_url_llm: str = Field(default="", description="Base URL for LLM")
    model_llm: str = Field(default="", description="LLM model name")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # игнорирование наличия других полей в .env - файле
        case_sensitive=False,  # регистронезависимость
    )


class BotSettings(BaseSettings):
    bot_token: SecretStr = Field(default=SecretStr(""), description="Token for Telegramm Bot")
    admin_id: str = Field(default="", description="id admins of grope")

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
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # игнорирование наличия других полей в .env - файле
        case_sensitive=False,  # регистронезависимость
    )

    @property
    def url(self):
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class MongoSettings(BaseSettings):
    mongo_initdb_root_username: str = ""
    mongo_initdb_root_password: str = ""
    mongo_initdb_database: str = ""
    mongo_initdb_host: str = "localhost"
    mongo_initdb_port: int = 27017

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # игнорирование наличия других полей в .env - файле
        case_sensitive=False,  # регистронезависимость
    )

    @property
    def url(self):
        # DATABASE_URL=mongodb://admin:password123@localhost:6000/fastapi?authSource=admin
        # mongodb://localhost:27017
        res: str = "mongodb://"
        if self.mongo_initdb_root_username:
            res += f"{self.mongo_initdb_root_username}:{self.mongo_initdb_root_password}@"

        res += f"{self.mongo_initdb_host}:{self.mongo_initdb_port}"
        return res


class RabitMQSettings(BaseSettings):
    rabbitmq_default_user: str = Field(default="guest", description="Admin name for RabbitMQ")
    rabbitmq_default_pass: str = Field(default="guest", description="Password user for RabbitMQ")
    rabbitmq_default_host: str = Field(default="localhost", description="Hostname")
    rabbitmq_default_port: int = Field(default=5672, description="Hostname")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # игнорирование наличия других полей в .env - файле
        case_sensitive=False,  # регистронезависимость
    )

    @property
    def url(self):
        return f"amqp://{self.rabbitmq_default_user}:{self.rabbitmq_default_pass}@{self.rabbitmq_default_host}:{self.rabbitmq_default_port}/"


class Setting(BaseModel):
    llm: LlmSettings = LlmSettings()
    bot: BotSettings = BotSettings()
    redis: RedisSettings = RedisSettings()
    mongo: MongoSettings = MongoSettings()
    rabbitmq: RabitMQSettings = RabitMQSettings()
    max_chunk_size: int = 512
    chunk_overlap: int = 50


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

broker = RabbitBroker(setting.rabbitmq.url)
