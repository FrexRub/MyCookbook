import asyncio
import logging

import aiohttp
from bs4 import BeautifulSoup
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from consumer.core.config import configure_logging, setting
from consumer.core.exceptions import (
    ExceptClientError,
    ExceptClientResponseError,
    ExceptTimeoutError,
)
from consumer.llm.llm_states import ParsingState, RecipesList, SearchRecipesList

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


class SearchAgent:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        """Инициализация агента"""
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=setting.llm.openrouter_api_key.get_secret_value(),
            base_url="https://api.aitunnel.ru/v1/",
            temperature=temperature,
        )

    async def search_recepts(self, query: str, content: str) -> SearchRecipesList:
        # создаём парсер для списка рецептов
        parser = JsonOutputParser(pydantic_object=SearchRecipesList)
        logger.info(f"Start search recepts with {query=}")
        prompt = PromptTemplate(
            input_variables=["query", "content"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
            template="""
                Ты кулинарный блогер, анализирующий текст рецептов.
                Найди рецепты соответствующик запросу верни их в JSON формате как список.
                Каждый рецепт должен содержать поля: id, category.
                Запрос: {query}

                {content}
            
                {format_instructions}
            
                Только JSON!
                """,
        )

        messages = [
            SystemMessage(content="Ты эксперт по кулинарии."),
            HumanMessage(content=prompt.format(content=content, query=query)),
        ]

        response = await self.llm.ainvoke(messages)

        try:
            # parser возвращает словарь, содержащий список рецептов
            res_json = parser.parse(response.content)
        except Exception as e:
            print(f"Ошибка при разборе JSON: {e}")
            return {"status": f"Ошибка парсинга: {e}"}

        return {"recipes": res_json["recipes"]}


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
        default_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        for attempt in range(retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=timeout_obj, headers=default_headers) as session:
                    async with session.get(url) as response:
                        response.raise_for_status()

                        return await response.text()

            except aiohttp.ClientResponseError as e:
                logger.warning(f"Ошибка ClientResponseError при загрузке страницы {url}")
                print(f"Ошибка ClientResponseError при загрузке страницы {url}")
                raise ExceptClientResponseError(e)

            except aiohttp.ClientError as e:
                logger.warning(f"Ошибка ClientError при загрузке страницы {url}")
                print(f"Ошибка ClientError при загрузке страницы {url}")
                raise ExceptClientError(e)

            except asyncio.TimeoutError:
                logger.warning(f"Таймаут при загрузке страницы {url}, попытка {attempt + 1}/{retries + 1}")
                print(f"Таймаут при загрузке страницы {url}, попытка {attempt + 1}/{retries + 1}")
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

        logger.info("Start extract text from content")
        return await asyncio.to_thread(sync_parse)

    async def _parsing_site_ai_node(self, state: ParsingState) -> dict[str, any]:
        try:
            html_content = await self._fetch_webpage(state=state)
        except ExceptClientResponseError as e:
            if e.status == 404:
                return {"status": "Страница не найдена"}
            elif e.status in (401, 403):
                return {"status": "Отсутствует право доступа"}
            else:
                return {"status": f"Ошибка сервера с кодом {e.status}"}
        except ExceptClientError:
            return {"status": "Ошибка сервиса"}
        except ExceptTimeoutError:
            return {"status": "Таймаут при загрузке страницы"}

        content = await self._extract_text_content(html_content=html_content)

        # создаём парсер для списка рецептов
        parser = JsonOutputParser(pydantic_object=RecipesList)

        prompt = PromptTemplate(
            input_variables=["content"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
            template="""
                Ты кулинарный блогер, анализирующий текст рецептов.
                Найди все рецепты на странице и верни их в JSON формате как список.
                Каждый рецепт должен содержать поля: title, ingredients, description, category.
            
                {content}
            
                {format_instructions}
            
                Только JSON!
                """,
        )

        messages = [
            SystemMessage(content="Ты эксперт по кулинарии."),
            HumanMessage(content=prompt.format(content=content)),
        ]

        response = await self.llm.ainvoke(messages)

        try:
            # parser возвращает словарь, содержащий список рецептов
            res_json = parser.parse(response.content)
        except Exception as e:
            print(f"Ошибка при разборе JSON: {e}")
            return {"status": f"Ошибка парсинга: {e}"}

        return {"status": "Ok", "recipes": res_json["recipes"]}

    async def classify(self, url: str):
        """Основной метод для классификации рецептов с веб-страницы"""
        initial_state = {
            "url": url,
            "status": "Ok",
            "recipes": [],  # список рецептов, заполняется в ходе работы пайплайна
        }

        result = await self.workflow.ainvoke(initial_state)

        state_result = {
            "status": result["status"],
            "url": url,
            "recipes": result.get("recipes", []),
        }

        return state_result


async def main():
    app = ParsingAgent()
    res = await app.classify(
        "https://share.google/mhpd7DAqaCSwPcnV8"
        # "https://www.kp.ru/family/eda/retsept-glintvejna"
        # "https://1000.menu/cooking/90658-pasta-orzo-s-gribami-i-slivkami"
        # "https://share.google/iPyxfhgn5gFRPTRNW"
    )

    if res["status"].lower() == "ok":
        print("\n===== РЕЗУЛЬТАТ =====\n")

        recipes = res.get("recipes", [])
        if len(recipes) > 1:
            print(f"Найдено несколько рецептов: {len(recipes)}\n")
            multiple = True
        else:
            multiple = False

        for index, recipe in enumerate(recipes, start=1):
            if multiple:
                print(f"Рецепт №{index}")
                print("―" * 40)

            print(f"🍽  Название: {recipe.get('title', 'Без названия')}")
            print(f"📂  Категория: {recipe.get('category', 'Не указано')}\n")

            print("🧂  Ингредиенты:")
            ingredients = recipe.get("ingredients", {})
            if ingredients:
                for ingredient, amount in ingredients.items():
                    print(f"   • {ingredient}: {amount}")
            else:
                print("   (ингредиенты не указаны)")

            print("\n👨‍🍳  Этапы приготовления:")
            steps = recipe.get("description", [])
            if steps:
                for step_num, step in enumerate(steps, start=1):
                    print(f"   {step_num}. {step}")
            else:
                print("   (шаги не указаны)")

            print("\n" + "=" * 50 + "\n")

    else:
        print(f"Ошибка: {res['status']}")


if __name__ == "__main__":

    asyncio.run(main())
