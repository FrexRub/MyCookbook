import logging
import asyncio
import re
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.exceptions import TelegramForbiddenError
from aiogram.utils.chat_action import ChatActionSender

from src.core.database import MongoManager
from src.core.config import configure_logging, URL_PATTERN

router = Router()

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Вы запустили бот для Кулинарной книги",
    )


# Получение ID группы
@router.message(Command("group_id"))
async def group_info(message: Message, bot: Bot, mongo: MongoManager):
    chat_info = (
        f"📊 <b>Информация о чате:</b>\n"
        f"🆔 <b>ID чата:</b> <code>{message.chat.id}</code>\n"
        f"📝 <b>Тип чата:</b> {message.chat.type}\n"
        f"👥 <b>Название:</b> {message.chat.title if message.chat.title else 'Личный чат'}\n"
        f"👤 <b>Ваш ID:</b> <code>{message.from_user.id}</code>\n"
    )

    # Дополнительная информация для групп
    if message.chat.type in ["group", "supergroup"]:
        members_count = await bot.get_chat_members_count(message.chat.id)
        chat_info += f"👥 <b>Участников:</b> {members_count}\n"
        chat_info += f"👥 <b>ID группы:</b> {message.chat.id}"

    await message.answer(chat_info, parse_mode="HTML")


# Приветствие новых участников
@router.message(F.new_chat_members)
async def welcome_new_members(message: Message):
    for user in message.new_chat_members:
        welcome_text = f"""
            Добро пожаловать, {user.full_name}! 🎉
            
            Правила группы:
            1. Будьте вежливы
            2. Соблюдайте тематику
            3. Не спамьте
            
            Приятного общения! 😊
        """
        await message.answer(welcome_text)


@router.message(F.left_chat_member)
async def goodbye_member(message: Message):
    try:
        await message.answer(f"{message.left_chat_member.full_name} покинул нас 😢")
    except TelegramForbiddenError:
        logger.warning("Бот был исключен из чата, невозможно выполнить действия")


@router.message(F.chat.type.in_(["group", "supergroup"]), F.text.contains("http"))
async def handle_http_url(message: Message, bot: Bot):
    chat_id = message.chat.id
    chat_title = message.chat.title
    user_name = message.from_user.first_name
    text = message.text

    url_text = re.findall(URL_PATTERN, text)

    # эммитация печати текста ботом
    async with ChatActionSender(bot=bot, chat_id=chat_id, action="typing"):
        await asyncio.sleep(2)
        await message.answer(
            f"{user_name}, добавьте хештег для удобства поиска",
            disable_notification=True,
        )

    logger.info(
        f"Добавление в группу: '{chat_title}' пользователем: {user_name} новой ссылки c рецептами: {url_text}"
    )


# Обработчик текстовых сообщений в группах
@router.message(F.chat.type.in_(["group", "supergroup"]), F.text)
async def handle_group_message(message: Message, bot: Bot):
    chat_id = message.chat.id
    chat_title = message.chat.title
    user_name = message.from_user.first_name
    text = message.text

    logger.info(f"Сообщение в группе '{chat_title}': {user_name}: {text}")

    # Пример: отвечать на определенные фразы
    if "привет бот" in text.lower():
        await message.reply(f"Привет, {user_name}! Я здесь! 👋")

    # if "http" in text.lower():
    #     # эммитация печати текста ботом
    #     async with ChatActionSender(bot=bot, chat_id=chat_id, action="typing"):
    #         await asyncio.sleep(2)
    #         await message.answer(f"{user_name}, добавьте хештег для удобства поиска")
