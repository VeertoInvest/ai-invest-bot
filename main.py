import os
import logging
import threading
import time
import schedule
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from news_handler import handle_news
from undervalued_stocks import analyze_undervalued_stocks
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

def tickers_command(update, context):
    keyboard = [
        [InlineKeyboardButton("AAPL", callback_data="news_AAPL"),
         InlineKeyboardButton("MSFT", callback_data="news_MSFT")],
        [InlineKeyboardButton("GOOGL", callback_data="news_GOOGL"),
         InlineKeyboardButton("AMZN", callback_data="news_AMZN")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите тикер:", reply_markup=reply_markup)

def button_callback(update, context):
    query = update.callback_query
    query.answer()

    if query.data.startswith("news_"):
        ticker = query.data.split("_")[1]
        query.edit_message_text(f"🔍 Новости по {ticker}...")
        articles = fetch_news_for_ticker(ticker)
        if articles:
            for article in articles:
                context.bot.send_message(chat_id=query.message.chat.id, text=article)
        else:
            context.bot.send_message(chat_id=query.message.chat.id, text="❌ Новости не найдены.")

dispatcher.add_handler(CommandHandler("tickers", tickers_command))
dispatcher.add_handler(CallbackQueryHandler(button_callback))


# 🔧 Логирование
logging.basicConfig(level=logging.INFO)

# 📌 Переменные окружения
TOKEN = os.getenv("TELEGRAM_API_KEY")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_API_KEY is not set")

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=1, use_context=True)

# 📌 Переменная для хранения chat_id
last_chat_id = None

from news_handler import fetch_news_for_ticker  # добавим эту функцию

def news_command(update, context):
    user_input = context.args
    if not user_input:
        update.message.reply_text("Введите тикер, например: /news AAPL")
        return

    ticker = user_input[0].upper()
    update.message.reply_text(f"🔍 Ищу новости по {ticker}...")

    articles = fetch_news_for_ticker(ticker)
    if not articles:
        update.message.reply_text("❌ Новости не найдены.")
        return

    for article in articles:
        update.message.reply_text(article)

# 📍 Команда /start
def start(update, context):
    global last_chat_id
    last_chat_id = update.effective_chat.id
    logging.info(f"User {update.effective_user.id} sent /start")
    context.bot.send_message(chat_id=last_chat_id,
                             text="Привет! Я бот для анализа новостей и недооценённых акций.")

# 📍 Команда /news
def news(update, context):
    logging.info(f"User {update.effective_user.id} sent /news")
    articles = handle_news()
    if articles:
        for article in articles:
            if article.strip():
                context.bot.send_message(chat_id=update.effective_chat.id, text=article)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Нет свежих новостей.")

# 📍 Команда /undervalued
def undervalued(update, context):
    logging.info(f"User {update.effective_user.id} sent /undervalued")
    tickers = ["AAPL", "MSFT", "GOOG"]
    results = analyze_undervalued_stocks(tickers)
    if results:
        for stock, pe in results:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"{stock} с P/E {pe}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Нет недооценённых акций.")

# 🕒 Рассылка новостей каждые 4 часа
def send_news_job():
    if last_chat_id:
        logging.info("📨 Авторассылка новостей")
        articles = handle_news()
        for article in articles:
            if article.strip():
                bot.send_message(chat_id=last_chat_id, text=article)
    else:
        logging.warning("⚠️ Нет chat_id для авторассылки")

# 🕓 Планировщик
schedule.every(4).hours.do(send_news_job)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

# 📍 Роут Webhook'а
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# 📍 Роут для Render'а
@app.route("/", methods=["GET"])
def root():
    return "Бот работает!", 200

# 🎯 Регистрация команд
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("news", news))
dispatcher.add_handler(CommandHandler("undervalued", undervalued))

# 📡 Установка Webhook при запуске
if __name__ == "__main__":
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    bot.delete_webhook()
    bot.set_webhook(url=webhook_url)
    logging.info(f"✅ Webhook установлен: {webhook_url}")
    app.run(host="0.0.0.0", port=10000)
