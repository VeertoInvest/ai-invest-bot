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
    prompt = (
        f"Проанализируй новость об акции компании:\n\n"
        f"Заголовок: {article['title']}\n"
        f"Описание: {article['description']}\n\n"
        f"1. Определи тональность (позитив / нейтрально / негативно).\n"
        f"2. Определи тип новости (финансовая, продуктовая, корпоративная и т.д.).\n"
        f"3. Оцени силу воздействия (сильное / среднее / слабое).\n"
        f"4. Сделай краткую инвестиционную рекомендацию (купить / держать / продать)."
    )

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка анализа AI: {e}"
