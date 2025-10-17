import logging
from aiogram import Bot

from src.core.config import configure_logging
from src.llm.agents import ParsingAgent

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def process_recipe(bot: Bot, chat_id: int, url: str):
    """Фоновая обработка URL рецепта"""
    try:
        agent = ParsingAgent()
        result = await agent.classify(url)
        status = result.get("status", "ошибка")

        if status != "Ok":
            await bot.send_message(chat_id, f"Не удалось обработать ссылку: {status}")
            return

        title = result["title"]
        ingredients = "\n".join([f"{k}: {v}" for k, v in result["ingredients"].items()])
        category = result["category"]
        description = "\n".join(result["description"])

        msg = (
            f"🍽 *{title}*\n\n"
            f"Категория: {category}\n\n"
            f"Ингредиенты:\n{ingredients}\n\n"
            f"Этапы приготовления:\n{description}"
        )

        await bot.send_message(chat_id, msg, parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"Ошибка при обработке рецепта: {e}")
        await bot.send_message(chat_id, f"Ошибка при обработке ссылки: {e}")
