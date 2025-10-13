import asyncio
from enum import Enum
from typing import Any

from langgraph.graph import StateGraph, END, START
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph.state import CompiledStateGraph

from src.llm.llm_states import ParsingState
from src.core.config import setting
from src.utils.parsing import get_content


class MealType(Enum):
    SNACKS = "закуски"
    FIRST = "первые блюда"
    SECOND = "вторые блюда"
    GARNISH = "гарниры"
    SALADS = "cалаты"
    DESSERTS = "десерты"
    DRINKS = "напитки"
    SAUCES = "соусы и приправы"


class ParsingAgent:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        """Инициализация агента"""
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=setting.llm.openrouter_api_key.get_secret_value(),
            base_url="https://api.aitunnel.ru/v1/",
            temperature=temperature,
        )
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> CompiledStateGraph:
        workflow = StateGraph(ParsingState)

        workflow.add_node("parsing_site", self._parsing_site)

        workflow.add_edge(START, "parsing_site")
        workflow.add_edge("parsing_site", END)

        return workflow.compile()

    async def _parsing_site(self, state: ParsingState) -> dict[str, Any]:
        message = [
            SystemMessage(
                content="Ты кулинарный блогер, прекрасно разбирающийся в кулинарии и читать сайты с кулинарными рецептами"
            )
        ]
        prompt = PromptTemplate(
            input_variables=["content"],
            template="""
            Изучи содержание контента полученного с сайта с помощью парсинга 
            {content} 

            и верни название блюда, перечисли используемые ингредиенты с указанным количеством 
            и этапы приготовления блюда

            """,
        )

        message.append(HumanMessage(content=prompt.format(content=state["content"])))
        response = await self.llm.ainvoke(message)
        print("content:", response.content)

        return {"content": response.content}

    async def classify(self, content: str):
        """Основной метод для классификации вакансии/услуги"""
        initial_state = {
            "content": content,
            "title": "",
            "description": "",
            "category": "",
            "ingredients": list(),
            "processed": False,
        }

        result = await self.workflow.ainvoke(initial_state)

        # Формируем итоговый ответ в формате JSON
        # classification_result = {
        #     "job_type": result["job_type"],
        #     "category": result["category"],
        #     "search_type": result["search_type"],
        #     "confidence_scores": result["confidence_scores"],
        #     "success": result["processed"],
        # }

        return "classification_result"


async def main():
    content = get_content(
        "https://1000.menu/cooking/90658-pasta-orzo-s-gribami-i-slivkami"
    )
    app = ParsingAgent()
    res = await app.classify(content)
    print(res)


asyncio.run(main())
