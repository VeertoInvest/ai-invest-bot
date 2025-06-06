import os
import logging
import requests
import openai
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# Загрузка переменных окружения
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
PORT = int(os.getenv("PORT", 10000))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

# Инициализация Telegram бота
bot = Bot(token=TELEGRAM_API_KEY)
dispatcher = Dispatcher(bot, update_queue=None, workers=0, use_context=True)

# Хранилище любимых тикеров пользователей
user_favorites = {}

# Команда /start
def start(update: Update, context):
    update.message.reply_text("Добро пожаловать! Используйте /news чтобы получить новости по акциям.")

# Команда /news
def news_command(update: Update, context):
    update.message.reply_text("Пожалуйста, введите тикер акции, по которой вы хотите получить новости.")

# Обработка текстовых сообщений (ввод тикера)
def handle_ticker_input(update: Update, context):
    ticker = update.message.text.upper()
    chat_id = update.effective_chat.id

    # Сохраняем тикер в любимые
    if chat_id in user_favorites:
        user_favorites[chat_id].add(ticker)
    else:
        user_favorites[chat_id] = {ticker}

    # Получаем новости
    articles = fetch_news_for_ticker(ticker)
    if not articles:
        update.message.reply_text(f"Новости по тикеру {ticker} не найдены.")
        return

    for article in articles[:5]:
        summary = summarize_article(article)
        message = f"*{article['title']}*\n{summary}\n[Читать полностью]({article['url']})"
        update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)

# Команда /favorites
def favorites_command(update: Update, context):
    chat_id = update.effective_chat.id
    favorites = user_favorites.get(chat_id, set())
    if not favorites:
        update.message.reply_text("У вас нет сохраненных любимых тикеров.")
    else:
        favorites_list = ', '.join(favorites)
        update.message.reply_text(f"Ваши любимые тикеры: {favorites_list}")

# Получение новостей через NewsAPI
def fetch_news_for_ticker(ticker):
    url = f"https://newsapi.org/v2/everything?q={ticker}&language=en&sortBy=publishedAt"
    headers = {"X-Api-Key": os.getenv("NEWS_API_KEY")}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    data = response.json()
    return data.get("articles", [])

# Краткий AI-анализ новости с помощью OpenAI
def summarize_article(article):
    prompt = f"Сделай краткий анализ следующей новости:\n\n{article['title']}\n{article['description']}"
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        return response.choices[0].message['content'].strip()
    except Exception:
        return "Не удалось получить анализ новости."

# Настройка webhook маршрута
@app.route(f"/{TELEGRAM_API_KEY}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Главная страница
@app.route("/")
def index():
    return "Бот работает!"

# Регистрация обработчиков команд и сообщений
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("news", news_command))
dispatcher.add_handler(CommandHandler("favorites", favorites_command))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_ticker_input))

# Установка webhook при запуске
if __name__ == "__main__":
    webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/{TELEGRAM_API_KEY}"
    bot.set_webhook(url=webhook_url)
    logging.info(f"\u2705 Webhook установлен: {webhook_url}")
    app.run(host="0.0.0.0", port=PORT)
