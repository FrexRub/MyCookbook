from aiogram import Router
from aiogram.types import ChatMemberUpdated


router = Router()


@router.my_chat_member()
async def handle_bot_status_change(chat_member: ChatMemberUpdated):
    old_status = chat_member.old_chat_member.status
    new_status = chat_member.new_chat_member.status
    chat_id = chat_member.chat.id
    chat_title = chat_member.chat.title

    print(f"Статус бота изменился в чате: {chat_title} (ID: {chat_id})")
    print(f"Было: {old_status} -> Стало: {new_status}")

    # Бота добавили в группу
    if new_status == "member":
        print("✅ Бот добавлен в группу как участник")
        # Здесь можно: сохранить ID группы в БД, отправить приветствие и т.д.

    # Бота сделали администратором
    elif new_status == "administrator":
        print("👑 Бота назначили администратором")

    # Бота удалили из группы
    elif new_status in ["kicked", "left"]:
        print("❌ Бота удалили из группы")
        # Здесь можно: удалить группу из БД, уведомить владельца и т.д.
