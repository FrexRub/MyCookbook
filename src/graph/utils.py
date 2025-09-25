from datetime import date

from src.graph.state import UserState


def calculate_age(state: UserState) -> dict:
    today = date.today()
    age = today.year - state["birth_date"].year
    if (today.month, today.day) < (state["birth_date"].month, state["birth_date"].day):
        age -= 1
    return {"age": age}
