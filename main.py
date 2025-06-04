import os
import sys
import logging
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
import threading

import pytz
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_job, 'interval', hours=4, timezone=pytz.utc)
scheduler.start()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подгружаем ключи из переменных окружения
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Проверка обязательных переменных
missing_keys = []
if not TELEGRAM_API_KEY: missing_keys.append("TELEGRAM_API_KEY")
if not OPENAI_API_KEY: missing_keys.append("OPENAI_API_KEY")
if not NEWS_API_KEY: missing_keys.append("NEWS_API_KEY")

if missing_keys:
    logger.error(f"❌ Missing environment variables: {', '.join(missing_keys)}")
    sys.exit(1)

bot = Bot(token=TELEGRAM_API_KEY)

def scheduled_job():
    logger.info("📬 Выполняется задача: анализ и отправка данных.")
    # Тут вставь логику отправки новостей

# Планировщик задач
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_job, 'interval', hours=4)
scheduler.start()

# Flask keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

logger.info("✅ Bot started and keep_alive active.")
