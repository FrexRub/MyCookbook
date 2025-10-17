from typing import TypedDict
from pydantic import BaseModel, Field


class ParsingState(TypedDict):
    url: str
    title: str
    description: list[str]
    category: str
    ingredients: dict[str, str]
    status: str


class ParsingRecipe(BaseModel):
    title: str = Field(description="название")
    description: list[str] = Field(
        description="пошаговые этапы приготовления блюда в формате списка ['шаг 1', 'шаг 2', ...]"
    )
    category: str = Field(
        description="к какому виду блюд относится (например, суп, десерт, основное блюдо, закуска и т.д.)"
    )
    ingredients: dict[str, str] = Field(
        description="список ингредиентов с указанием количества в формате словаря"
    )
