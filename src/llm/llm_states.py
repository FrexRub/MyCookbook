from typing import TypedDict


class ParsingState(TypedDict):
    content: str
    title: str
    description: str
    category: str
    ingredients: list[dict[str, float]]
    processed: bool
