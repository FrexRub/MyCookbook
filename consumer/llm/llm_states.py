from typing import TypedDict

from pydantic import BaseModel, Field


class SearchRecipe(BaseModel):
    id: str = Field(description="id рецепта")
    category: str = Field(
        description="к какому виду блюд относится (например, суп, десерт, основное блюдо, закуска и т.д.)"
    )


class SearchRecipesList(BaseModel):
    recipes: list[SearchRecipe] = Field(
        description="список найденных рецептов"
    )


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


class RecipesList(BaseModel):
    recipes: list[ParsingRecipe] = Field(
        description="список рецептов, найденных на странице"
    )


class ParsingState(TypedDict):
    url: str
    status: str
    recipes: list[ParsingRecipe]
