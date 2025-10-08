import logging
from datetime import datetime

from aiogram import Bot, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import ChatMemberUpdated

from src.core.config import configure_logging
from src.core.database import MongoManager
from src.models.mongodb import TelegramGroupModel

router = Router()

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def handle_bot_added_as_member(
    chat_member: ChatMemberUpdated, bot: Bot, mongo: MongoManager
):
    """Обработка добавления бота как участника"""
    chat_id = chat_member.chat.id
    new_status = chat_member.new_chat_member.status
    chat_title = chat_member.chat.title

    try:
        admins = await bot.get_chat_administrators(chat_id)
        creator = next((admin for admin in admins if admin.status == "creator"), None)
        if creator:
            user = creator.user

            new_group: TelegramGroupModel = TelegramGroupModel(
                title=chat_title,
                chat_id=chat_id,
                status=new_status,
                username_tg=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                user_id=user.id,
            )

        else:
            new_group: TelegramGroupModel = TelegramGroupModel(
                title=chat_title,
                chat_id=chat_id,
                status=new_status,
            )
        group_collection = mongo.get_collection("groups")

        # Обновляем существующую запись или создаем новую
        result = await group_collection.update_one(
            {"chat_id": chat_id},
            {"$set": new_group.model_dump(by_alias=True, exclude_none=True)},
            upsert=True,
        )

        if result.upserted_id:
            logger.info(f"Данные чата с ID: {chat_id} добавлены в базу данных")
        else:
            logger.info(f"Данные чата с ID: {chat_id} обновлены в базе данных")

    except TelegramForbiddenError:
        logger.warning(f"Нет доступа к информации о чате {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке добавления бота: {e}")


async def handle_bot_removed(
    chat_member: ChatMemberUpdated, bot: Bot, mongo: MongoManager
):
    """Обработка удаления бота из чата"""
    chat_id = chat_member.chat.id
    chat_title = chat_member.chat.title

    try:
        group_collection = mongo.get_collection("groups")

        # Ищем информацию о группе в базе
        group_data = await group_collection.find_one({"chat_id": chat_id})

        if group_data and group_data.get("user_id"):
            admin_user_id = group_data["user_id"]

            # Отправляем сообщение администратору
            try:
                message_text = (
                    f"❌ Бот был удален из группы\n"
                    f"📋 Группа: {chat_title}\n"
                    f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"Чтобы добавить бота обратно, используйте ссылку:\n"
                    f"https://t.me/your_bot_username?startgroup=true"
                )

                await bot.send_message(chat_id=admin_user_id, text=message_text)
                logger.info(f"Уведомление отправлено администратору {admin_user_id}")

            except Exception as e:
                logger.error(f"Не удалось отправить уведомление администратору: {e}")

        # Обновляем статус в базе данных
        await group_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"status": "kicked", "updated_at": datetime.utcnow()}},
        )
        logger.info(f"Статус группы {chat_id} обновлен на 'kicked'")

    except Exception as e:
        logger.error(f"Ошибка при обработке удаления бота: {e}")


@router.my_chat_member()
async def handle_bot_status_change(
    chat_member: ChatMemberUpdated, bot: Bot, mongo: MongoManager
):
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
            await handle_bot_removed(chat_member, bot, mongo)

        except TelegramForbiddenError:
            logger.info(
                f"Бот был исключен из чата {chat_id}, невозможно выполнить действия"
            )

        return

    # Бота добавили в группу
    if new_status == "member":
        await handle_bot_added_as_member(chat_member, bot, mongo)

    # Бота сделали администратором
    elif new_status == "administrator":
        logger.info(f"Бот назначен администратором в чатеа {chat_id}")
