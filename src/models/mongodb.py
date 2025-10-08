from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]


class StatusBot(str, Enum):
    MEMBER = "member"
    ADMINISTRATOR = "administrator"
    KICKED = "kicked"
    LEFT = "left"


class TelegramGroupModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: Optional[str] = Field(..., description="Название группы/чата")
    chat_id: int = Field(..., description="ID группы/чата")
    status: str = Field(..., description="статус бота в группе/чате")
    username_tg: Optional[str] = Field(
        description="короткое имя пользователя в формате telegram"
    )
    first_name: Optional[str] = Field(description="имя пользователя")
    last_name: Optional[str] = Field(description="фамилия пользователя")
    user_id: Optional[int] = Field(description="ID администратора")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="время создания"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="время обновления"
    )
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "title": "Test group",
                "chat_id": -186816318,
                "status": "member",
                "username_tg": "@superuser",
                "first_name": "Иван",
                "last_name": "Петров",
                "user_id": 176732681,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
            }
        },
    )
