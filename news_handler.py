import os
import requests
import openai
from datetime import datetime, timedelta

# API-ключи
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or os.getenv("NEWSAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Логирование ключей
if OPENAI_API_KEY:
    print(f"🔑 OpenAI ключ загружен: {OPENAI_API_KEY[:10]}...")
else:
    print("❌ OpenAI ключ не найден!")

if NEWS_API_KEY:
    print(f"🗞️ NewsAPI ключ загружен: {NEWS_API_KEY[:10]}...")
else:
    print("❌ NEWS_API_KEY не найден!")

# Получение новостей
def fetch_news_for_ticker(ticker, max_articles=3):
    if not NEWS_API_KEY:
        print("❌ NEWS_API_KEY не задан.")
        return []

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": ticker,
        "language": "en",
        "pageSize": max_articles,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
        "from": (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d'),
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            print(f"❌ Ошибка от NewsAPI: {data}")
            return []

        print(f"✅ Найдено {len(data.get('articles', []))} новостей по {ticker}")
        return data.get("articles", [])

    except Exception as e:
        print(f"❌ Ошибка при получении новостей: {e}")
        return []

# Анализ новости
def ai_analyze_news(article):
    try:
        content = article.get("title", "") + "\n\n" + article.get("description", "")
        if not content.strip():
            return "⚠️ Недостаточно данных для анализа."

        prompt = (
            f"Прочти следующую новость и сделай краткий анализ:\n"
            f"1. Основной смысл.\n"
            f"2. Тональность (позитивная, негативная, нейтральная).\n"
            f"3. Тип новости (финансовая, продуктовая, судебная, рынок и т.д.).\n"
            f"4. Насколько сильно она повлияет на цену акций?\n"
            f"5. Краткая рекомендация (покупать / держать / продавать).\n\n"
            f"Текст:\n\"{content}\"\n\nОтветь кратко и на русском языке:"
        )

        print(f"📨 Отправляем запрос в OpenAI...")
        print(f"[PROMPT] {prompt[:200]}...")

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )

        return response["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"❌ Ошибка AI-анализа: {e}")
        return "❌ Не удалось получить анализ новости."
