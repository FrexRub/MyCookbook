from aiogram.types import BotCommand, BotCommandScopeDefault

from src.core.config import bot


async def set_commands():
    commands = [
        BotCommand(command="start", description="Старт"),
        BotCommand(command="group_id", description="Информация о группе"),
        BotCommand(command="help", description="Опрос"),
        BotCommand(command="my_recipes", description="Мои рецепты"),
        BotCommand(command="group_recipes", description="Рецепты группы"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())
