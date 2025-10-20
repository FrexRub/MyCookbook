import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from src.core.config import configure_logging
from src.core.database import MongoManager

router = Router()

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.message(Command("my_recipes"))
async def my_recipes_info(message: Message, bot: Bot, mongo: MongoManager):
    recipe_collection = mongo.get_collection("recipes")
    user_id = message.from_user.id

    try:
        # Находим все рецепты, где user_id содержится в списке user_id документа
        cursor = recipe_collection.find(
            {"user_id": user_id},  # фильтр
            {"_id": 0, "title": 1, "category": 1},  # проекция: только title и category
        )

        recipes = await cursor.to_list(length=100)  # ограничение на количество записей

        if not recipes:
            await bot.send_message(
                message.chat.id, "У вас пока нет сохранённых рецептов."
            )
            return

        # Формируем понятное сообщение с выборкой
        msg_lines = ["Ваши сохранённые рецепты:\n"]
        for recipe in recipes:
            title = recipe.get("title", "Без названия")
            category = recipe.get("category", "Без категории")
            msg_lines.append(f"🍽 {title}\n📂 {category}\n")

        await bot.send_message(message.chat.id, "\n".join(msg_lines))

    except Exception as e:
        await bot.send_message(message.chat.id, f"Ошибка получения данных из базы: {e}")
