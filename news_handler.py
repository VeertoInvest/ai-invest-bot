import requests
import os

def handle_news():
    api_key = os.getenv("NEWS_API_KEY")  # Обязательно должен быть в окружении
    if not api_key:
        print("❌ NEWS_API_KEY не установлен в переменных окружения.")
        return ["Ошибка: отсутствует ключ API для новостей."]

    url = (
        f"https://newsapi.org/v2/top-headlines?"
        f"category=business&language=ru&pageSize=5&apiKey={api_key}"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if response.status_code != 200 or data.get("status") != "ok":
            print(f"❌ Ошибка API новостей: {data}")
            return ["Ошибка при получении новостей."]

        articles = data.get("articles", [])
        cleaned = []

        for article in articles:
            title = article.get("title", "").strip()
            url = article.get("url", "").strip()

            if title and url:
                cleaned.append(f"📰 {title}\n🔗 {url}")
            else:
                print("⚠️ Пропущена статья без заголовка или ссылки.")

        if not cleaned:
            return ["Новости не найдены."]

        return cleaned

    except Exception as e:
        print(f"❌ Исключение при получении новостей: {e}")
        return ["Произошла ошибка при обработке новостей."]
