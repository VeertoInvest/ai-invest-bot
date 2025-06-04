import os
import logging
import pytz
import schedule
import time
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import Updater, CommandHandler
from flask import Flask
from tasks.news_handler import fetch_and_analyze_news
from tasks.undervalued_stocks import send_weekly_undervalued_stocks

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Получение API ключей из переменных окружения
TELEGRAM_API_KEY = os.environ.get("TELEGRAM_API_KEY")

# Проверка наличия ключа
if not TELEGRAM_API_KEY:
    raise ValueError("TELEGRAM_API_KEY не установлен в переменных окружения")

# Создание бота
updater = Updater(token=TELEGRAM_API_KEY, use_context=True)
dispatcher = updater.dispatcher

# Команды Telegram
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Бот запущен!")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# Планировщик для периодических задач
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_analyze_news, 'interval', hours=4, timezone=pytz.utc)
scheduler.add_job(send_weekly_undervalued_stocks, 'cron', day_of_week='sun', hour=12, timezone=pytz.utc)
scheduler.start()

# Запуск Telegram-бота
updater.start_polling()

# Flask для Render.com (health check)
app = Flask(__name__)

@app.route('/')
def index():
    return "AI-Invest-Bot is running!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
