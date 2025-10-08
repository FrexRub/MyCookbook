from datetime import date
from typing import TypedDict


class UserState(TypedDict):
    name: str
    surname: str
    age: int
    birth_date: date
    message: str  # Новое поле для хранения сообщения пользователю
