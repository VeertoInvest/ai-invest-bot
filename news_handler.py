import requests
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

def handle_news():
    url = f"https://newsapi.org/v2/top-headlines?country=us&category=business&pageSize=5&apiKey={NEWSAPI_KEY}"
    response = requests.get(url)
    data = response.json()

    headlines = [article["title"] for article in data.get("articles", [])]

    if not headlines:
        return "Нет свежих новостей."

    news_text = "\n".join(f"- {title}" for title in headlines)
    return f"📰 Последние бизнес-новости:\n{news_text}"