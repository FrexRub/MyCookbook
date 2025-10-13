import requests
from bs4 import BeautifulSoup
import json


def fetch_webpage(url):
    """Загрузка веб-страницы"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Ошибка при загрузке страницы: {e}")
        return None


def extract_text_content(html):
    """Извлечение текстового содержимого со страницы"""
    soup = BeautifulSoup(html, "html.parser")

    # Удаляем ненужные элементы
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    # Получаем основной текст
    text = soup.get_text(separator="\n", strip=True)

    # Очищаем текст от лишних пробелов
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines[:2000])  # Ограничиваем длину для экономии токенов


# "https://1000.menu/cooking/90658-pasta-orzo-s-gribami-i-slivkami"
def get_content(url: str):
    html_text = fetch_webpage(url)
    content = extract_text_content(html_text)

    return content
