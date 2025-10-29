import time
import logging

from langchain_huggingface import HuggingFaceEmbeddings
import torch
from langchain_chroma import Chroma

from consumer.core.config import configure_logging, COLLECTION_NAME, CHROMA_PATH

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)

SHOP_DATA = [
    {
        "text": 'Ноутбук Lenovo IdeaPad 5: 16 ГБ RAM, SSD 512 ГБ, экран 15.6", цена 55000 руб.',
        "metadata": {
            "id": "1",
            "type": "product",
            "category": "laptops",
            "price": 55000,
            "stock": 3,
        },
    },
    {
        "text": "Смартфон Xiaomi Redmi Note 12: 128 ГБ, камера 108 МП, цена 18000 руб.",
        "metadata": {
            "id": "2",
            "type": "product",
            "category": "phones",
            "price": 18000,
            "stock": 10,
        },
    },
]


def generate_chroma_db():
    try:
        start_time = time.time()

        logger.info("Загрузка модели эмбеддингов...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info(f"Модель загружена за {time.time() - start_time:.2f} сек")

        logger.info("Создание Chroma DB...")
        chroma_db = Chroma.from_texts(
            texts=[item["text"] for item in SHOP_DATA],
            embedding=embeddings,
            ids=[str(item["metadata"]["id"]) for item in SHOP_DATA],
            metadatas=[item["metadata"] for item in SHOP_DATA],
            persist_directory=CHROMA_PATH,
            collection_name=COLLECTION_NAME,
        )
        logger.info(f"Chroma DB создана за {time.time() - start_time:.2f} сек")

        return chroma_db
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise


if __name__ == "__main__":
    generate_chroma_db()
