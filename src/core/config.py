from pathlib import Path
import logging

from openai import OpenAI
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


class Setting(BaseModel):
    llm: LlmSettings = LlmSettings()


setting = Setting()

llm_client = OpenAI(
    api_key=setting.llm.openrouter_api_key.get_secret_value(),
    base_url=setting.llm.base_url_llm,
)
