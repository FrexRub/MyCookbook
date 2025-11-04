import logging

from consumer.vectoring.models.chroma import chrome
from consumer.core.config import configure_logging
from consumer.vectoring.models.chroma import RecipeVector


configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def search_recipe(query: str) -> list[RecipeVector]:
    """Поиск рецепта в ChromaDB."""
    results = await chrome.asimilarity_search(query=query, with_score=True, k=3)
    return results
