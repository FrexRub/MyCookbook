import aiohttp
import asyncio
import logging
import json


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
    ExceptClientResponseError,
)
from src.llm.llm_states import ParsingState
from src.core.config import setting
from src.core.config import configure_logging


configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


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

        workflow.add_node("parsing_site", self._parsing_site_ai_node)

        workflow.add_edge(START, "parsing_site")
        workflow.add_edge("parsing_site", END)

        return workflow.compile()

    async def _fetch_webpage(self, state: ParsingState, timeout=30, retries=2) -> str:
        """Асинхронная загрузка веб-страницы"""

        url: str = state["url"]
        logger.info(f"Start fetch webpage {url}")
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        for attempt in range(retries + 1):
            try:
                async with aiohttp.ClientSession(
                    timeout=timeout_obj, headers=default_headers
                ) as session:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        return await response.text()

            except aiohttp.ClientResponseError as e:
                logger.warning(
                    f"Ошибка ClientResponseError при загрузке страницы {url}"
                )
                raise ExceptClientResponseError(e)

            except aiohttp.ClientError as e:
                logger.warning(f"Ошибка ClientError при загрузке страницы {url}")
                raise ExceptClientError(e)

            except asyncio.TimeoutError:
                logger.warning(
                    f"Таймаут при загрузке страницы {url}, попытка {attempt + 1}/{retries + 1}"
                )
                if attempt < retries:
                    await asyncio.sleep(2**attempt)
                else:
                    raise ExceptTimeoutError(f"Таймаут при загрузке страницы {url}")

    async def _extract_text_content(self, html_content: str):
        """Извлечение текстового контента со скаченной страницы Интернет"""

        def sync_parse():
            soup = BeautifulSoup(html_content, "html.parser")
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            text = soup.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return "\n".join(lines[:2000])

        logger.info("Start extract text content from")
        return await asyncio.to_thread(sync_parse)

    async def _parsing_site_ai_node(self, state: ParsingState) -> dict[str, Any]:
        try:
            html_content = await self._fetch_webpage(state=state)
        except ExceptClientResponseError as e:
            if e.status == 404:
                return {"status": "Страница не найдена"}
            elif (e.status == 401) or (e.status == 403):
                return {"status": "Отсутствует право доступа"}
            else:
                return {"status": f"Ошибка сервера с кодом {e.status}"}
        except ExceptClientError:
            return {"status": "Ошибка сервиса"}
        except ExceptTimeoutError:
            return {"status": "Таймаут при загрузке страницы"}

        content = await self._extract_text_content(html_content=html_content)
        message = [
            SystemMessage(
                content=(
                    "Ты кулинарный блогер, прекрасно разбирающийся в кулинарии. "
                    "Верни ответ ТОЛЬКО в формате JSON без каких-либо дополнительных текстов, объяснений или комментариев. "
                    "Формат JSON должен быть точно таким: "
                    '{"title": "название", "ingredients": {"ингредиент": "количество"}, "description": ["шаг 1", "шаг 2"], "category": "категория"}'
                )
            )
        ]
        prompt = PromptTemplate(
            input_variables=["content"],
            template="""
            Проанализируй этот кулинарный рецепт и верни информацию в JSON формате:
            {content} 

           Требуемый JSON формат:
            - title: название блюда
            - ingredients: список ингредиентов с указанием количества в формате словаря
            - description: пошаговые этапы приготовления блюда в формате списка ["шаг 1", "шаг 2", ...]
            - category: к какому виду блюд относится (например, суп, десерт, основное блюдо, закуска и т.д.)
            """,
        )

        message.append(HumanMessage(content=prompt.format(content=content)))

        # Получение результата работы модели
        response = await self.llm.ainvoke(message)

        try:
            # Сериализуем результат из json в словарь
            res_json = json.loads(response.content)
        except Exception as e:
            print(f"Error {e}")
            return {"status": f"{e}"}

        state_result = {
            "title": res_json["title"],
            "description": res_json["description"],
            "category": res_json["category"],
            "ingredients": res_json["ingredients"],
        }
        return state_result

    async def classify(self, url: str):
        """Основной метод для классификации вакансии/услуги"""
        initial_state = {
            "url": url,
            "title": "",
            "description": "",
            "category": "",
            "ingredients": dict(),
            "status": "Ok",
        }

        result = await self.workflow.ainvoke(initial_state)

        state_result = {
            "title": result["title"],
            "description": result["description"],
            "category": result["category"],
            "ingredients": result["ingredients"],
            "status": result["status"],
        }

        return state_result


async def main():
    app = ParsingAgent()
    res = await app.classify(
        "https://1000.menu/cooking/90658-pasta-orzo-s-gribami-i-slivkami"
        # "https://share.google/iPyxfhgn5gFRPTRNW"
    )

    if res["status"] == "Ok":
        print(f"Result:\n {res}")
    else:
        print(res["status"])


asyncio.run(main())
