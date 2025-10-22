import logging
import asyncio
from bson import ObjectId
from bson.errors import InvalidId

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from src.core.config import configure_logging, setting
from src.core.database import MongoManager

router = Router()

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


def create_recipe_inline_kb(recipes: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for recipe in recipes:
        title = recipe.get("title", "Без названия")
        id = recipe.get("_id")
        builder.row(InlineKeyboardButton(text=title, callback_data=f"id_{id}"))
    # Добавляем кнопку "На главную"
    builder.row(InlineKeyboardButton(text="На главную", callback_data="back_home"))
    # Настраиваем размер клавиатуры
    builder.adjust(1)
    return builder.as_markup()


def create_categories_inline_kb(categories: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(
            InlineKeyboardButton(text=category, callback_data=f"ctg_{category}")
        )

    builder.adjust(1)
    return builder.as_markup()


@router.message(Command("my_recipes"))
async def my_recipes_info(message: Message, bot: Bot, mongo: MongoManager):
    recipe_collection = mongo.get_collection("recipes")
    user_id = message.from_user.id

    try:
        # Находим все рецепты, где user_id содержится в списке user_id документа
        cursor = recipe_collection.find(
            {"user_id": user_id},  # фильтр
            {"title": 1, "category": 1},  # проекция: только title и category
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
        categories: list[str] = list()
        for category, titles in dict_recipes.items():
            msg_lines.append(f"\n📂 *{category}*:")
            categories.append(category)
            for title in titles:
                msg_lines.append(f" 🍽 {title}")

        await bot.send_message(
            message.chat.id,
            "\n".join(msg_lines),
            parse_mode="Markdown",
            reply_markup=create_categories_inline_kb(categories),
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
            {"chat_id": chat_id}, {"title": 1, "category": 1}
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
        await bot.send_message(
            message.chat.id,
            "Рецепты:",
            parse_mode="Markdown",
            reply_markup=create_recipe_inline_kb(recipes),
        )

    except Exception as e:
        await bot.send_message(message.chat.id, f"Ошибка при получении рецептов: {e}")


@router.callback_query(F.data.startswith("id_"))
async def find_recipe_by_id(call: CallbackQuery, mongo: MongoManager):
    await call.answer()
    try:
        id_rec = call.data.replace("id_", "")

        if not ObjectId.is_valid(id_rec):
            await call.message.answer("Неверный формат ID рецепта")
            return

        recipe_collection = mongo.get_collection("recipes")
        recipe = await recipe_collection.find_one({"_id": ObjectId(id_rec)})

        ingredients = recipe.get("ingredients", {})
        steps = recipe.get("description", [])

        msg_parts: list[str] = [
            f"🍽 *{recipe['title']}*\n\n📂 Категория: {recipe['category']}\n"
        ]

        msg_parts.append("🧂 *Ингредиенты:*")

        if ingredients:
            msg_parts.extend([f"  • {k}: {v}" for k, v in ingredients.items()])
        else:
            msg_parts.append("  (ингредиенты не указаны)")

        msg_parts.append("\n👨‍🍳 *Этапы приготовления:*")

        if steps:
            msg_parts.extend([f"  {i+1}. {step}" for i, step in enumerate(steps)])
        else:
            msg_parts.append("  (шаги не указаны)")

        msg_parts.append(f"\n🌐 *[cтраница рецепта]({recipe['url']})*")
        msg = "\n".join(msg_parts)

        async with ChatActionSender(
            bot=setting.bot, chat_id=call.from_user.id, action="typing"
        ):
            await asyncio.sleep(2)
            await call.message.answer(msg, parse_mode="Markdown", reply_markup=None)
    except InvalidId:
        await call.message.answer("Неверный формат ID рецепта")
    except Exception as e:
        await call.message.answer("Ошибка при загрузке рецепта")
        print(f"Error: {e}")


@router.callback_query(F.data.startswith("ctg_"))
async def cmd_category(call: CallbackQuery, mongo: MongoManager):
    await call.answer()
    category = call.data.replace("ctg_", "")
    recipe_collection = mongo.get_collection("recipes")
    cursor = recipe_collection.find({"category": category}, {"title": 1})
    recipes = await cursor.to_list(length=100)

    msg_text = f"Рецепты категории {category}:\n\n"
    async with ChatActionSender(
        bot=setting.bot, chat_id=call.from_user.id, action="typing"
    ):
        await asyncio.sleep(2)
        await call.message.answer(
            msg_text, reply_markup=create_recipe_inline_kb(recipes)
        )
