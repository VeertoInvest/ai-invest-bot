
import requests
from bs4 import BeautifulSoup

def get_latest_news(query, api_key):
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={api_key}&language=ru"
    response = requests.get(url)
    data = response.json()
    if "articles" not in data:
        return []

    articles = data["articles"]
    return [article["title"] for article in articles[:5]]
