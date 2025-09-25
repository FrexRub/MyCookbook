from datetime import date

from langgraph.graph import StateGraph, START, END

from src.graph.state import UserState
from src.graph.utils import (
    calculate_age,
    generate_success_message,
    generate_failure_message,
    check_drive,
)

graph = StateGraph(UserState)

graph.add_node("calculate_age", calculate_age)
graph.add_node("generate_success_message", generate_success_message)
graph.add_node("generate_failure_message", generate_failure_message)

graph.add_edge(START, "calculate_age")
graph.add_conditional_edges(
    "calculate_age",
    check_drive,
    {"можно": "generate_success_message", "нельзя": "generate_failure_message"},
)
graph.add_edge("generate_success_message", END)
graph.add_edge("generate_failure_message", END)

app = graph.compile()

result = app.invoke(
    {
        "name": "Алексей",
        "surname": "Яковенко",
        "birth_date": date.fromisoformat("2009-02-19"),
    }
)
print(result)
