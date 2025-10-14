import aiohttp
import asyncio
import logging


from enum import Enum
from typing import Any

from bs4 import BeautifulSoup
from langgraph.graph import StateGraph, END, START
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph.state import CompiledStateGraph

from src.core.exceptions import (
    ExceptClientError,
    ExceptTimeoutError,
    ExceptFetchWebpage,
)
from src.llm.llm_states import ParsingState
from src.core.config import setting
from src.core.config import configure_logging


configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


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

        workflow.add_node("parsing_site", self._parsing_site_ai)

        workflow.add_edge(START, "parsing_site")
        workflow.add_edge("parsing_site", END)

        return workflow.compile()

    async def _fetch_webpage(self, state: ParsingState, timeout=30) -> str:
        """Асинхронная загрузка веб-страницы"""
        try:
            url: str = state["url"]
            logger.info(f"Start fetch webpage {url}")
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()

        except aiohttp.ClientResponseError as e:
            logger.warning(f"Ошибка при загрузке страницы {url}")
            raise ExceptClientError(f"Ошибка при загрузке страницы {url}: {e}")

        except aiohttp.ClientError as e:
            logger.warning(f"Ошибка при загрузке страницы {url}")
            raise ExceptClientError(f"Ошибка при загрузке страницы {url}: {e}")

        except asyncio.TimeoutError as e:
            logger.warning(f"Таймаут при загрузке страницы {url}")
            raise ExceptTimeoutError(f"Таймаут при загрузке страницы {url}: {e}")

        except Exception as e:
            logger.warning(f"Неожиданная ошибка при загрузке {url}: {e}")
            raise ExceptFetchWebpage(f"Неожиданная ошибка при загрузке {url}: {e}")

    async def _extract_text_content(self, html_content: str):
        """Упрощенная асинхронная версия"""

        # Создаем частичную функцию для вызова в executor
        def sync_parse():
            soup = BeautifulSoup(html_content, "html.parser")
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            text = soup.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return "\n".join(lines[:2000])

        logger.info("Start extract text content from")
        return await asyncio.to_thread(sync_parse)

    async def _parsing_site_ai(self, state: ParsingState) -> dict[str, Any]:
        try:
            html_content = await self._fetch_webpage(state=state)
        except ExceptClientError as e:
            print(f"Возникла ошибка {e}")
            return None

        content = await self._extract_text_content(html_content=html_content)
        message = [
            SystemMessage(
                content=(
                    "Ты кулинарный блогер, прекрасно разбирающийся в кулинарии, читаешь и пишешь статьи"
                    "с кулинарными рецептами"
                )
            )
        ]
        prompt = PromptTemplate(
            input_variables=["content"],
            template="""
            Подробно изучи содержание контента c рецептом
            {content} 

            и верни название блюда, перечисли используемые ингредиенты с указанным количеством 
            и этапы приготовления блюда

            """,
        )

        message.append(HumanMessage(content=prompt.format(content=content)))
        response = await self.llm.ainvoke(message)
        print("content:", response.content)

        return {"content": response.content}

    async def classify(self, url: str):
        """Основной метод для классификации вакансии/услуги"""
        initial_state = {
            "url": url,
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
    app = ParsingAgent()
    res = await app.classify(
        "https://1000.menu/cooking/90658-pasta-orzo-s-gribami-i-slivkami"
    )


asyncio.run(main())
