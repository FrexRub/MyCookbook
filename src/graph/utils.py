from datetime import date

from src.graph.state import UserState


def calculate_age(state: UserState) -> dict:
    today = date.today()
    age = today.year - state["birth_date"].year
    if (today.month, today.day) < (state["birth_date"].month, state["birth_date"].day):
        age -= 1
    return {"age": age}


def check_drive(state: UserState) -> str:
    if state["age"] >= 18:
        return "можно"
    else:
        return "нельзя"


def generate_success_message(state: UserState) -> dict:
    return {
        "message": f"Поздравляем, {state['name']} {state['surname']}! "
        f"Вам уже {state['age']} лет и вы можете водить!"
    }


def generate_failure_message(state: UserState) -> dict:
    return {
        "message": f"К сожалению, {state['name']} {state['surname']}, "
        f"вам ещё только {state['age']} лет и вы не можете водить."
    }
