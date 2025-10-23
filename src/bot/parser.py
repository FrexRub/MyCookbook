import logging

from aiogram import Bot
from pymongo.errors import (
    DuplicateKeyError,
    OperationFailure,
    PyMongoError,
    ServerSelectionTimeoutError,
    WriteConcernError,
    WriteError,
)

from src.core.config import configure_logging
from src.core.database import MongoManager
from src.llm.agents import ParsingAgent

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


# noqa: C901
async def process_recipe(
    bot: Bot,
    chat_id: int,
    user_id: int,
    url: str,
    mongo: MongoManager,
) -> None:
    """Фоновая обработка URL рецепта"""
    try:
        agent = ParsingAgent()
        res = await agent.classify(url)

        status = res.get("status", "error").lower()
        if status != "ok":
            await bot.send_message(
                user_id,
                f"Ошибка обработки рецепта: {res.get('status', 'Неизвестная ошибка')}",
            )
            return

        recipes = res.get("recipes", [])
        if not recipes:
            await bot.send_message(chat_id, "Не найдено рецептов по ссылке.")
            return

        multiple = len(recipes) > 1

        recipe_collection = mongo.get_collection("recipes")
        if multiple:
            msg_parts = ["В вашу кулинарную книгу добавлены новые рецепты: \n"]
        else:
            msg_parts = ["В вашу кулинарную книгу добавлен новый рецепт: \n"]

        for index, recipe in enumerate(recipes, start=1):
            title = recipe.get("title", "Без названия")
            category = recipe.get("category", "Не указано")
            ingredients = recipe.get("ingredients", {})
            steps = recipe.get("description", [])

            if multiple:
                msg_parts.append(f"Рецепт №{index}\n{'―' * 30}")

            msg_parts.append(f"🍽 *{title}*\n📂 Категория: {category}\n")

            recipe_data = {
                "title": title,
                "description": steps,
                "category": category,
                "ingredients": ingredients,
                "url": url,
                "user_id": [user_id],
                "chat_id": [chat_id],
            }

            try:
                result = await recipe_collection.insert_one(recipe_data)
                logger.info(f"Рецепт добавлен: {result.inserted_id}")
            except DuplicateKeyError:
                logger.warning("Такой рецепт уже существует в базе данных.")
                await bot.send_message(user_id, "Такой рецепт уже есть в базе.")
            except (WriteError, WriteConcernError, OperationFailure) as e:
                logger.error(f"Ошибка записи в MongoDB: {e}")
                await bot.send_message(user_id, "Ошибка записи в базу данных.")
            except ServerSelectionTimeoutError:
                logger.error("Не удалось подключиться к MongoDB (таймаут соединения).")
                await bot.send_message(user_id, "Сервер базы данных недоступен.")
            except PyMongoError as e:
                logger.exception(f"Неизвестная ошибка MongoDB: {e}")
                await bot.send_message(user_id, "Произошла внутренняя ошибка при работе с базой данных.")

        msg = "\n".join(msg_parts)
        await bot.send_message(user_id, msg, parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"Ошибка при обработке рецепта: {e}")
        await bot.send_message(user_id, f"Ошибка при обработке ссылки: {e}")
