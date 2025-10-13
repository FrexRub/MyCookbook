from enum import Enum
from typing import Any

from langgraph.graph import StateGraph, END, START
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph

from src.llm.llm_states import ParsingState

from src.core.config import setting


class MealType(Enum):
    SNACKS = "закуски"
    FIRST = "первые блюда"
    SECOND = "вторые блюда"
    GARNISH = "гарниры"
    SALADS = "cалаты"
    DESSERTS = "десерты"
    DRINKS = "напитки"
    SAUCES = "соусы и приправы"


class ParsingnAgent:
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
        system_prompt = SystemMessage(
            content="Ты кулинарный блогер, прекрасно разбирающийся в кулинарии всех стран"
        )
        prompt = PromptTemplate(
            input_variables=["url_site"],
            template="""
            Изучи содержание интернет страницы 
            {url_site} 
            и верни название блюда, которое описано на данной странице, перечисли ингредиенты с необходимым количеством 
            и этапы приготовления блюда

            Описание: {description}

            Ответь только одним из двух вариантов:
            - "проектная работа" - если это временная задача, проект, фриланс, разовая работа
            - "постоянная работа" - если это постоянная должность, штатная позиция, долгосрочное трудоустройство

            Тип работы:
            """,
        )

        message = HumanMessage(content=prompt.format(description=state["url"]))
        response = await self.llm.ainvoke([message])
        print("job_type:", response.content.strip())
        job_type = response.content.strip().lower()

        return {"job_type": job_type}

    async def classify(self, url_pars: str):
        """Основной метод для классификации вакансии/услуги"""
        initial_state = {
            "url": url_pars,
            "title": "",
            "description": "",
            "category": "",
            "ingredients": list(),
            "processed": False,
        }

        # Запускаем рабочий процесс
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
