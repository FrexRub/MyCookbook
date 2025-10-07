import logging
from aiogram import Router, Bot
from aiogram.types import ChatMemberUpdated
from aiogram.exceptions import TelegramForbiddenError

from src.core.config import configure_logging

router = Router()

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def handle_bot_added_as_member(chat_member: ChatMemberUpdated, bot: Bot):
    """Обработка добавления бота как участника"""
    chat_id = chat_member.chat.id

    try:
        admins = await bot.get_chat_administrators(chat_id)

        creator = next((admin for admin in admins if admin.status == "creator"), None)
        if creator:
            user = creator.user
            logger.info(
                f"Создатель чата: {user.first_name} , {user.last_name or ''} (ID: {user.id}) @{user.username or 'нет'}"
            )

        # Сохраняем информацию о чате в БД
        # await save_chat_to_db(chat_id, chat_member.chat.title)

    except TelegramForbiddenError:
        logger.warning(f"Нет доступа к информации о чате {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке добавления бота: {e}")


async def handle_bot_removed(chat_id: int, chat_title: str):
    """Обработка удаления бота из чата"""
    logger.info(f"Выполняем cleanup для чата {chat_title} (ID: {chat_id})")
    # Удаляем чат из БД, чистим кэш и т.д.


async def cleanup_chat_data(chat_id: int):
    """Очистка данных чата"""
    # Удаление из базы данных
    # Очистка кэша
    # Обновление статистики
    pass


@router.my_chat_member()
async def handle_bot_status_change(chat_member: ChatMemberUpdated, bot: Bot):
    old_status = chat_member.old_chat_member.status
    new_status = chat_member.new_chat_member.status
    chat_id = chat_member.chat.id
    chat_title = chat_member.chat.title

    logger.info(
        f"Статус бота изменился: {chat_title} (ID: {chat_id}) - {old_status} -> {new_status}"
    )

    # Бота удалили из группы - основная обработка
    if new_status in ["kicked", "left"]:
        logger.info("❌ Бота удалили из группы")

        try:
            # Попытка выполнить какие-то финальные действия
            # Например, отправить сообщение владельцу бота
            await handle_bot_removed(chat_id, chat_title)

        except TelegramForbiddenError:
            logger.info(
                f"Бот был исключен из чата {chat_id}, невозможно выполнить действия"
            )

        finally:
            # Обязательные действия (очистка БД и т.д.)
            await cleanup_chat_data(chat_id)
        return

    # Бота добавили в группу
    if new_status == "member":
        await handle_bot_added_as_member(chat_member, bot)

    # Бота сделали администратором
    elif new_status == "administrator":
        # await handle_bot_promoted(chat_member, bot)
        logger.info(f"Бот назначен администратором в чатеа {chat_id}")
