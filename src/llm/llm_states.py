from typing import TypedDict


class ParsingState(TypedDict):
    url: str
    title: str
    description: list[str]
    category: str
    ingredients: dict[str, str]
    status: str
