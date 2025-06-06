import os
import requests
import openai
from datetime import datetime, timedelta

# API-ключи
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or os.getenv("NEWSAPI_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Отладочные логи
if openai.api_key:
    print(f"🔑 OpenAI ключ загружен: {openai.api_key[:8]}...")
else:
    print("❌ OpenAI ключ не найден!")

if NEWS_API_KEY:
    print(f"🗞️ NewsAPI ключ загружен: {NEWS_API_KEY[:8]}...")
else:
    print("❌ NEWS_API_KEY не найден!")

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

def ai_analyze_news(article):
    try:
        title = article.get("title") or ""
        description = article.get("description") or ""
        content = f"{title}\n\n{description}"

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

        print(f"[AI prompt] {prompt[:200]}...")  # Показываем начало запроса

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Используй gpt-4 если у тебя есть доступ
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )

        result = response['choices'][0]['message']['content'].strip()
        print(f"[AI result] {result[:200]}")  # Показываем начало результата
        return result

    except Exception as e:
        print(f"❌ Ошибка AI-анализа: {e}")
        return "❌ Не удалось получить анализ новости."
