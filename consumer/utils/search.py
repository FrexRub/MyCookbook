import logging
from typing import Any

from consumer.vectoring.models.chroma import chrome
from consumer.core.config import configure_logging
from consumer.vectoring.models.chroma import RecipeVector
from consumer.llm.agents import SearchAgent


configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

search_agent = SearchAgent()


async def format_context(context: list[dict[str, Any]]) -> str:
    """Форматирование контекста для промпта."""
    formatted_context = []
    for item in context:
        metadata_str = "\n".join(f"{k}: {v}" for k, v in item["metadata"].items())
        formatted_context.append(f"Текст: {item['text']}\nМетаданные:\n{metadata_str}\nОценка: {item['score']}")
    return "\n---\n".join(formatted_context)


async def search_recipe(query: str) -> list[RecipeVector]:
    """Поиск рецепта в ChromaDB."""
    try:
        results = await chrome.asimilarity_search(query=query, k=3)
    except Exception as e:
        logger.exception(f"Ошибка при поиске рецепта: {e}")
        raise

    formatted_context = await format_context(results)
    logger.info(f"Форматированный контекст: {formatted_context}")

    response = await search_agent.search_recepts(query=query, content=formatted_context)
    logger.info(f"Ответ от агента: {response}")
    return results
