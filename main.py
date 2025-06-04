import os
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from news_handler import handle_news
from undervalued_stocks import analyze_undervalued_stocks
import pytz

TOKEN = os.getenv("TELEGRAM_API_KEY")
PORT = int(os.environ.get("PORT", 8443))

bot = Bot(token=TOKEN)
app = Flask(__name__)
scheduler = BackgroundScheduler(timezone=pytz.utc)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я бот для анализа новостей и поиска недооцененных акций.")

def send_news(context: CallbackContext):
    news = handle_news()
    context.bot.send_message(chat_id=context.job.context, text=news)

def send_stocks(context: CallbackContext):
    report = analyze_undervalued_stocks()
    context.bot.send_message(chat_id=context.job.context, text=report)

def scheduled_job():
    # Здесь можно добавить логику для автоматической отправки
    pass

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("news", lambda u, c: u.message.reply_text(handle_news())))
    dispatcher.add_handler(CommandHandler("stocks", lambda u, c: u.message.reply_text(analyze_undervalued_stocks())))

    scheduler.add_job(scheduled_job, 'interval', hours=4)
    scheduler.start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()