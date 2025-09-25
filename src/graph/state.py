from typing import TypedDict
from datetime import date


class UserState(TypedDict):
    name: str
    surname: str
    age: int
    birth_date: date
    message: str  # Новое поле для хранения сообщения пользователю
