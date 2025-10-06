import logging
from aiogram import Router
from aiogram.types import ChatMemberUpdated

from src.core.config import configure_logging

router = Router()

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.my_chat_member()
async def handle_bot_status_change(chat_member: ChatMemberUpdated):
    old_status = chat_member.old_chat_member.status
    new_status = chat_member.new_chat_member.status
    chat_id = chat_member.chat.id
    chat_title = chat_member.chat.title

    logger.info(f"Статус бота изменился в чате: {chat_title} (ID: {chat_id})")
    logger.info(f"Было: {old_status} -> Стало: {new_status}")

    # Бота добавили в группу
    if new_status == "member":
        logger.info("✅ Бот добавлен в группу как участник")
        # Здесь можно: сохранить ID группы в БД, отправить приветствие и т.д.

    # Бота сделали администратором
    elif new_status == "administrator":
        logger.info("👑 Бота назначили администратором")

    # Бота удалили из группы
    elif new_status in ["kicked", "left"]:
        logger.info("❌ Бота удалили из группы")
        # Здесь можно: удалить группу из БД, уведомить владельца и т.д.
