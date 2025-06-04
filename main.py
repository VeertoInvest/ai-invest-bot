import logging
import os
import pytz
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import Updater

from news_handler import handle_news
from undervalued_stocks import find_undervalued_stocks

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Чтение токена из переменных окружения
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")

# Проверка наличия ключа
if not TELEGRAM_API_KEY:
    raise ValueError("TELEGRAM_API_KEY not found in environment variables")

# Запуск Telegram-бота
updater = Updater(token=TELEGRAM_API_KEY, use_context=True)
dispatcher = updater.dispatcher

# Планировщик задач
def scheduled_job():
    logging.info("🕒 Запуск плановой задачи: анализ новостей и акций")
    handle_news()
    find_undervalued_stocks()

scheduler = BackgroundScheduler(timezone=pytz.utc)
scheduler.add_job(scheduled_job, 'interval', hours=4)
scheduler.start()

# Flask-приложение для Render ping
app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Бот работает!"

# Запуск бота
if __name__ == '__main__':
    updater.start_polling()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
