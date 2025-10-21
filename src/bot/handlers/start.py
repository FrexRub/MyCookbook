import logging
import re
import asyncio

from aiogram import F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.bot.parser import process_recipe
from src.core.config import URL_PATTERN, configure_logging
from src.core.database import MongoManager

router = Router()

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Вы запустили бот для Кулинарной книги",
    )


@router.message(F.new_chat_members)
async def welcome_new_members(message: Message, mongo: MongoManager):
    group_collection = mongo.get_collection("groups")

    for user in message.new_chat_members:
        # Приветственное сообщение
        welcome_text = f"""
        Добро пожаловать, {user.full_name}! 🎉

        Правила группы:
        1. Будьте вежливы
        2. Соблюдайте тематику
        3. Не спамьте

        Приятного общения! 😊
        """
        await message.answer(welcome_text)

        # Подготовка данных пользователя
        user_data = {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
        }

        # Добавление пользователя в чат-группу (создание/обновление)
        await group_collection.update_one(
            {"chat_id": message.chat.id},
            {"$addToSet": {"chat_users": user.id}},  # Добавляем ID в список
            upsert=True,
        )

        # Отдельное сохранение данных о пользователе (опционально)
        users_collection = mongo.get_collection("users")
        await users_collection.update_one(
            {"user_id": user.id},
            {"$set": user_data},
            upsert=True,
        )

        logger.info(
            f"Пользователь {user.full_name} добавлен в группу {message.chat.title}"
        )


@router.message(F.left_chat_member)
async def goodbye_member(message: Message):
    try:
        await message.answer(f"{message.left_chat_member.full_name} покинул нас 😢")
    except TelegramForbiddenError:
        logger.warning("Бот был исключен из чата, невозможно выполнить действия")


@router.message(F.chat.type.in_(["group", "supergroup"]), F.text.contains("http"))
async def handle_http_url(message: Message, mongo: MongoManager):
    chat_title = message.chat.title
    user_name = message.from_user.first_name
    text = message.text

    url_text = re.findall(URL_PATTERN, text)
    if not url_text:
        await message.reply("Не удалось найти ссылку в сообщении.")
        return

    url = url_text[0]
    logger.info(
        f"Добавление в группу '{chat_title}' пользователем {user_name} новой ссылки: {url}"
    )

    recipe_collection = mongo.get_collection("recipes")
    user_id = message.from_user.id
    chat_id = message.chat.id

    existing_recipes = await recipe_collection.find({"url": url}).to_list(length=None)

    # если url уже кем нибудь добавлялось, то добавляем данные user_id пользователя (и его группы) без парсинга
    if existing_recipes:
        await message.answer("Рецепт уже занесён в книгу рецептов.")
        result = await recipe_collection.update_many(
            {"url": url}, {"$addToSet": {"user_id": user_id, "chat_id": chat_id}}
        )

        if result.modified_count > 0:
            logger.info(f"Данные добавлены в {result.modified_count} рецепт(ов).")
        else:
            logger.info("Рецепт уже содержит данные этого пользователя и чата.")

    else:

        def on_process_done(task: asyncio.Task, msg: Message):
            async def send_message():
                if task.exception():
                    error = task.exception()
                    await msg.answer(f"Произошла ошибка при обработке: {error}")
                    logger.error(f"Произошла ошибка при обработке: {error}")
                else:
                    await msg.answer(
                        "Рецепт успешно обработан и добавлен в книгу рецептов."
                    )
                    logger.info("Рецепт успешно обработан и добавлен в БД.")

            asyncio.create_task(send_message())

        # Создание задачи
        task = asyncio.create_task(
            process_recipe(
                bot=message.bot,
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                url=url,
                mongo=mongo,
            )
        )

        task.add_done_callback(lambda t: on_process_done(t, message))


# Обработчик текстовых сообщений в группах
@router.message(F.chat.type.in_(["group", "supergroup"]), F.text)
async def handle_group_message(message: Message):
    user_name = message.from_user.first_name
    text = message.text

    # Пример: отвечать на определенные фразы
    if "привет бот" in text.lower():
        await message.reply(f"Привет, {user_name}! Я здесь! 👋")
