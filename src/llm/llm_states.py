from typing import TypedDict


class ParsingState(TypedDict):
    url: str
    title: str
    description: str
    category: str
    ingredients: list[dict[str, float]]
    processed: bool
