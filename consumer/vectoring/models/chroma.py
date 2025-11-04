import asyncio
import logging
import json
import time
from typing import Any

import torch
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

from consumer.core.config import configure_logging, COLLECTION_NAME, CHROMA_PATH, setting
from consumer.core.exceptions import ExceptAddChromaError

PyObjectId = Annotated[str, BeforeValidator(str)]

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


class RecipeMetadate(BaseModel):
    id: PyObjectId = Field(..., description="id рецепта")
    category: str = Field(..., description="вид блюда")
    ingredients: dict[str, str] = Field(..., description="список ингредиентов")


class RecipeVector(BaseModel):
    text: str = Field(..., description="полные данные рецепта")
    metadata: RecipeMetadate = Field(..., description="метаданные рецепта")


class ChromaVectorStore:
    def __init__(self):
        """
        Инициализирует пустой экземпляр хранилища векторов.
        Соединение с базой данных будет установлено позже с помощью метода init().
        """
        self._store: Chroma | None = None

    async def init(self):
        """
        Асинхронный метод для инициализации соединения с базой данных Chroma.
        Создает embeddings на основе модели из настроек, используя CUDA если доступно.
        """
        await asyncio.sleep(0.01)
        logger.info("🧠 Инициализация ChromaVectorStore...")
        try:
            start_time = time.time()

            logger.info("Загрузка модели эмбеддингов...")

            # Определяем устройство для вычислений: GPU если доступен, иначе CPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"🚀 Используем устройство для эмбеддингов: {device}")

            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={"device": device},
                encode_kwargs={"normalize_embeddings": True},
            )
            logger.info(f"Модель загружена за {time.time() - start_time:.2f} сек")

            # Инициализируем соединение с базой данных Chroma
            self._store = Chroma(
                persist_directory=CHROMA_PATH,
                embedding_function=embeddings,
                collection_name=COLLECTION_NAME,
            )

            logger.info(f"✅ ChromaVectorStore успешно подключен к коллекции " f"'{COLLECTION_NAME}' в '{CHROMA_PATH}'")
        except Exception as e:
            logger.exception(f"❌ Ошибка при инициализации ChromaVectorStore: {e}")
            raise

    async def asimilarity_search(self, query: str, with_score: bool, k: int = 3):
        """
        Асинхронный метод для поиска похожих документов в базе данных Chroma.

        Args:
            query (str): Текстовый запрос для поиска
            with_score (bool): Включать ли оценку релевантности в результаты
            k (int): Количество возвращаемых результатов

        Returns:
            list: Список найденных документов, возможно с оценками если with_score=True

        Raises:
            RuntimeError: Если хранилище не инициализировано
        """
        logger.info(f"🔍 Поиск похожих документов по запросу: «{query}», top_k={k}")

        if not self._store:
            raise RuntimeError("ChromaVectorStore is not initialized.")

        try:
            if with_score:
                results = await self._store.asimilarity_search_with_score(query=query, k=k)
            else:
                results = await self._store.asimilarity_search(query=query, k=k)

            logger.debug(f"📄 Найдено {len(results)} результатов.")
            return results
        except Exception as e:
            logger.exception(f"❌ Ошибка при поиске: {e}")
            raise

    async def split_text_into_chunks(self, recipe: RecipeVector) -> list[Any]:
        """Разделение текста на чанки с сохранением метаданных."""
        await asyncio.sleep(0.01)

        ingredients_json: str = json.dumps(recipe.metadata.ingredients, ensure_ascii=False)
        metadata: dict[str, str] = {
            "id": str(recipe.metadata.id),
            "category": recipe.metadata.category,
            "ingredients": ingredients_json,
        }

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=setting.max_chunk_size,
            chunk_overlap=setting.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

        chunks = text_splitter.create_documents(texts=[recipe.text], metadatas=[metadata])
        return chunks

    async def add_recipe(self, recipe: RecipeVector):
        if not self._store:
            raise RuntimeError("ChromaVectorStore is not initialized.")
        try:
            logger.info(f"📝 Добавление рецепта в базу данных Chroma: {recipe.metadata.id}")

            # Получение чанков
            chunks: list[Any] = await self.split_text_into_chunks(recipe)
            logger.info(f"Документ разбит на {len(chunks)} чанков")

            # Создаем список документов для Chroma
            documents = [
                Document(
                    page_content=chunk.page_content,
                    metadata=chunk.metadata.dict() if hasattr(chunk.metadata, "dict") else chunk.metadata,
                )
                for chunk in chunks
            ]

            # Добавление документов в хранилище
            await self._store.aadd_documents(documents=documents)

            logger.info("✅ Рецепт успешно добавлен.")
        except Exception as e:
            logger.exception(f"❌ Ошибка при добавлении рецепта: {e}")
            raise ExceptAddChromaError(f"Ошибка при добавлении рецепта: {e}")


chrome = ChromaVectorStore()
