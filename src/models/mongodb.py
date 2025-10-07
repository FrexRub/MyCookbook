from enum import Enum
from typing import Optional
from typing_extensions import Annotated
from bson import ObjectId

from pydantic import ConfigDict, BaseModel, Field
from pydantic.functional_validators import BeforeValidator


PyObjectId = Annotated[str, BeforeValidator(str)]


class StatusBot(Enum):
    member = "member"
    administrator = "administrator"
    kicked = "kicked"
    left = "left"


class TelegramGroupModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: Optional[str]
    chat_id: int = Field(...)
    status: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "title": "Test group",
                "chat_id": -186816318,
                "status": "member",
                "gpa": 3.0,
            }
        },
    )
