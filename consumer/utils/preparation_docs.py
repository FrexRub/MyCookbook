import asyncio
from typing import Any
import logging

from consumer.core.config import PUNCTUATION_PATTERN, WHITESPACE_PATTERN
from consumer.core.exceptions import ExceptNormalizeTextError
from consumer.vectoring.models.chroma import RecipeMetadate, PyObjectId, RecipeVector
from consumer.core.config import configure_logging


configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def normalize_text(text: str) -> str:
    """Нормализация текста: удаление знаков препинания и специальных символов."""
    if not isinstance(text, str):
        raise ValueError("Входной текст должен быть строкой")

    await asyncio.sleep(0.001)
    # Удаление знаков препинания
    text = PUNCTUATION_PATTERN.sub(" ", text)
    # Удаление переносов строк и лишних пробелов
    text = WHITESPACE_PATTERN.sub(" ", text)
    # Приведение к нижнему регистру
    return text.lower().strip()


async def recipe_to_metadata(recipe: dict[str, Any], id_recipe: PyObjectId) -> RecipeVector:
    text: str = (
        f"Заголовок {recipe['title']} Категория {recipe['category']} Ингредиенты "
        + ", ".join(f"{k} {v}" for k, v in recipe["ingredients"].items())
        + "Этапы "
        + " ".join(recipe["description"])
    )

    metadat: RecipeMetadate = RecipeMetadate(
        id=id_recipe, category=recipe["category"], ingredients=recipe["ingredients"]
    )
    try:
        text_for_vector: str = await normalize_text(text)
    except ValueError as e:
        logger.error(f"Ошибка при нормализации текста: {text}")
        raise ExceptNormalizeTextError(f"{e}")

    return RecipeVector(text=text_for_vector, metadata=metadat)
