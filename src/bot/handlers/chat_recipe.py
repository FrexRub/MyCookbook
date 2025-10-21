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
                message.chat.id, "🍳 У вас пока нет сохранённых рецептов."
            )
            return

        # Группируем рецепты по категориям
        dict_recipes: dict[str, list[str]] = {}
        for recipe in recipes:
            title = recipe.get("title", "Без названия")
            category = recipe.get("category", "Без категории")
            dict_recipes.setdefault(category, []).append(title)

        # Формируем читаемое сообщение
        msg_lines = ["📚 *Ваши сохранённые рецепты:*"]
        for category, titles in dict_recipes.items():
            msg_lines.append(f"\n📂 *{category}*:")
            for title in titles:
                msg_lines.append(f" 🍽 {title}")

        await bot.send_message(
            message.chat.id, "\n".join(msg_lines), parse_mode="Markdown"
        )

    except Exception as e:
        await bot.send_message(message.chat.id, f"Ошибка получения данных из базы: {e}")


@router.message(Command("group_recipes"))
async def group_recipes_info(message: Message, bot: Bot, mongo: MongoManager):
    user_id = message.from_user.id
    groups_collection = mongo.get_collection("groups")
    recipe_collection = mongo.get_collection("recipes")

    try:
        # Находим группу, где пользователь является участником
        group = await groups_collection.find_one({"chat_users": user_id})
        if not group:
            await bot.send_message(
                message.chat.id,
                "❗ Вы не входите ни в одну группу, зарегистрированную в базе данных.",
            )
            return

        chat_id = group["chat_id"]

        # Получаем все рецепты для найденной группы
        cursor = recipe_collection.find(
            {"chat_id": chat_id}, {"_id": 0, "title": 1, "category": 1}
        )
        recipes = await cursor.to_list(length=100)

        if not recipes:
            await bot.send_message(
                message.chat.id, "🍳 В этой группе пока нет сохранённых рецептов."
            )
            return

        # Группируем рецепты по категориям
        dict_recipes: dict[str, list[str]] = {}
        for recipe in recipes:
            title = recipe.get("title", "Без названия")
            category = recipe.get("category", "Без категории")
            dict_recipes.setdefault(category, []).append(title)

        # Формируем сообщение для пользователя
        msg_lines = [f"📚 *Рецепты группы {group['title']}:*"]
        for category, titles in dict_recipes.items():
            msg_lines.append(f"\n📂 *{category}*:")
            msg_lines.extend([f" 🍽 {t}" for t in titles])

        await bot.send_message(
            message.chat.id, "\n".join(msg_lines), parse_mode="Markdown"
        )

    except Exception as e:
        await bot.send_message(message.chat.id, f"Ошибка при получении рецептов: {e}")
