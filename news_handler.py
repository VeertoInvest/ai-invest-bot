import os
import requests
from openai import OpenAI

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def fetch_news_for_ticker(ticker, limit=3):
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={ticker}&sortBy=publishedAt&language=en&pageSize={limit}&apiKey={NEWS_API_KEY}"
    )
    response = requests.get(url)
    data = response.json()

    articles = []
    for article in data.get("articles", []):
        articles.append({
            "title": article["title"],
            "description": article["description"] or "",
            "url": article["url"]
        })

    return articles

def ai_analyze_news(article):
    try:
        prompt = f"Проанализируй новость и выдай краткий вывод: {article['title']}\n{article['description']}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ Ошибка анализа новости: {e}")
        return "Не удалось получить анализ новости."

