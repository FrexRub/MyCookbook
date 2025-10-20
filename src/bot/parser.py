import logging
from aiogram import Bot

from src.core.config import configure_logging
from src.llm.agents import ParsingAgent
from src.core.database import MongoManager

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def process_recipe(
    bot: Bot, chat_id: int, user_id: int, url: str, mongo: MongoManager
):
    """Фоновая обработка URL рецепта"""
    """Фоновая обработка URL рецепта с поддержкой нового формата ответа"""
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
            msg_parts = [f"В вашу кулинарную книгу добавлены новые рецепты: \n\n"]
        else:
            msg_parts = [f"В вашу кулинарную книгу добавлен новый рецепт: \n\n"]

        for index, recipe in enumerate(recipes, start=1):
            title = recipe.get("title", "Без названия")
            category = recipe.get("category", "Не указано")
            ingredients = recipe.get("ingredients", {})
            steps = recipe.get("description", [])

            if multiple:
                msg_parts.append(f"Рецепт №{index}\n{'―'*30}")

            msg_parts.append(f"🍽 *{title}*\n📂 Категория: {category}\n")

            # msg_parts.append("🧂 *Ингредиенты:*")

            # if ingredients:
            #     msg_parts.extend([f"  • {k}: {v}" for k, v in ingredients.items()])
            # else:
            #     msg_parts.append("  (ингредиенты не указаны)")
            #
            # msg_parts.append("\n👨‍🍳 *Этапы приготовления:*")
            #
            # if steps:
            #     msg_parts.extend([f"  {i+1}. {step}" for i, step in enumerate(steps)])
            # else:
            #     msg_parts.append("  (шаги не указаны)")

            # msg = "\n".join(msg_parts)

            recipe_data = {
                "title": title,
                "description": steps,
                "category": category,
                "ingredients": ingredients,
                "url": url,
                "user_id": [user_id],
                "chat_id": [chat_id],
            }

            result = await recipe_collection.insert_one(recipe_data)

            if result.inserted_id:
                logger.info("Рецепт успешно добавлен в базу данных!")
            else:
                logger.error("Произошла ошибка при добавлении рецепта.")

        msg = "\n".join(msg_parts)
        await bot.send_message(user_id, msg, parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"Ошибка при обработке рецепта: {e}")
        await bot.send_message(user_id, f"Ошибка при обработке ссылки: {e}")
