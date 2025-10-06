from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from src.core.database import MongoManager

router = Router()


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

    # users_collection = mongo.get_collection("users")

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


# Прощание с вышедшими участниками
@router.message(F.left_chat_member)
async def goodbye_member(message: Message):
    await message.answer(f"{message.left_chat_member.full_name} покинул нас 😢")


# Обработчик события, когда бота добавляют в группу
@router.message(lambda message: message.chat.type in ["group", "supergroup"])
async def handle_group_message(message: Message):
    chat_id = message.chat.id
    chat_title = message.chat.title

    print(f"ID группы: {chat_id}")
    print(f"Название группы: {chat_title}")

    # Можно отправить сообщение с ID группы
    await message.answer(f"ID этой группы: {chat_id}")
