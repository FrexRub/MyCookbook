from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from src.core.config import bot


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Вы запустили бот для Кулинарной книги",
    )


# Получение ID группы
@router.message(Command("group_id"))
async def group_info(message: Message):
    chat_info = (
        f"📊 <b>Информация о чате:</b>\n"
        f"🆔 <b>ID чата:</b> <code>{message.chat.id}</code>\n"
        f"📝 <b>Тип чата:</b> {message.chat.type}\n"
        f"👥 <b>Название:</b> {message.chat.title if message.chat.title else 'Личный чат'}\n"
        f"👤 <b>Ваш ID:</b> <code>{message.from_user.id}</code>"
    )

    await message.answer(chat_info, parse_mode="HTML")

    # Дополнительная информация для групп
    if message.chat.type in ["group", "supergroup"]:
        members_count = await bot.get_chat_members_count(message.chat.id)
        group_info = f"👥 <b>Участников:</b> {members_count}"
        await message.answer(group_info, parse_mode="HTML")


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
