import os
import logging
import requests
import schedule
import time
import threading

from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

from news_handler import fetch_news_for_ticker, ai_analyze_news
from undervalued_stocks import weekly_undervalued_stocks_search
from memory import add_favorite, remove_favorite, get_favorites

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
PORT = int(os.environ.get("PORT", 10000))

if not TELEGRAM_API_KEY or not RENDER_EXTERNAL_HOSTNAME:
    raise ValueError("❌ Не заданы TELEGRAM_API_KEY или RENDER_EXTERNAL_HOSTNAME")

bot = Bot(token=TELEGRAM_API_KEY)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)
app = Flask(__name__)

# Команды

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Привет! Я бот для AI-анализа новостей и поиска недооценённых акций.\n\nНапиши тикер или выбери из кнопок.")
    send_ticker_buttons(update.effective_chat.id)

def send_ticker_buttons(chat_id):
    tickers = ["AAPL", "MSFT", "GOOG", "AMZN"]
    buttons = [[InlineKeyboardButton(ticker, callback_data=f"analyze:{ticker}")] for ticker in tickers]
    markup = InlineKeyboardMarkup(buttons)
    bot.send_message(chat_id=chat_id, text="Выберите тикер:", reply_markup=markup)

def handle_favorites(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    favs = get_favorites(user_id)
    if favs:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Избранные тикеры: " + ", ".join(favs))
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="У вас нет избранных тикеров.")

def handle_delete(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if len(context.args) != 1:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Используйте: /delete <тикер>")
        return
    remove_favorite(user_id, context.args[0])
    context.bot.send_message(chat_id=update.effective_chat.id, text="Удалено.")

def handle_weekly(update: Update, context: CallbackContext):
    stocks = weekly_undervalued_stocks_search()
    if not stocks:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Недооценённых акций не найдено.")
    for stock in stocks:
        msg = f"📉 {stock['ticker']}\nMoS: {stock['mo_safety']}%\nP/E: {stock['pe']}\nPEG: {stock['peg']}\nROE: {stock['roe']}%\nD/E: {stock['de']}"
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

def handle_text(update: Update, context: CallbackContext):
    ticker = update.message.text.strip().upper()
    handle_ticker_analysis(update.effective_chat.id, update.effective_user.id, ticker)

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data.startswith("analyze:"):
        ticker = query.data.split(":")[1]
        handle_ticker_analysis(query.message.chat.id, query.from_user.id, ticker)

def handle_ticker_analysis(chat_id, user_id, ticker):
    add_favorite(user_id, ticker)
    bot.send_message(chat_id=chat_id, text=f"🔍 Ищу новости по {ticker}...")
    articles = fetch_news_for_ticker(ticker)
    if not articles:
        bot.send_message(chat_id=chat_id, text="Новостей не найдено.")
        return
    for article in articles:
        title = article.get("title", "")
        url = article.get("url", "")
        summary = ai_analyze_news(article)
        message = f"🗞 {title}\n{url}\n\n🤖 AI-анализ:\n{summary}"
        bot.send_message(chat_id=chat_id, text=message)

# Автоуведомления каждые 4 часа

def notify_users():
    for user_id, tickers in get_favorites_all().items():
        for ticker in tickers:
            articles = fetch_news_for_ticker(ticker)
            for article in articles[:1]:
                summary = ai_analyze_news(article)
                msg = f"🕒 Новость по {ticker}:\n{article['title']}\n{article['url']}\n\n🤖 {summary}"
                bot.send_message(chat_id=user_id, text=msg)

def get_favorites_all():
    from memory import user_favorites
    return user_favorites

def scheduler_thread():
    schedule.every(4).hours.do(notify_users)
    while True:
        schedule.run_pending()
        time.sleep(60)

# Webhook и Flask
@app.route(f"/{TELEGRAM_API_KEY}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "ok"

# Регистрация команд

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("favorites", handle_favorites))
dispatcher.add_handler(CommandHandler("delete", handle_delete))
dispatcher.add_handler(CommandHandler("weekly", handle_weekly))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
dispatcher.add_handler(CallbackQueryHandler(handle_callback))

# Запуск
if __name__ == "__main__":
    bot.delete_webhook()
    bot.set_webhook(url=f"https://{RENDER_EXTERNAL_HOSTNAME}/{TELEGRAM_API_KEY}")
    logging.basicConfig(level=logging.INFO)
    logging.info(f"✅ Webhook установлен: https://{RENDER_EXTERNAL_HOSTNAME}/{TELEGRAM_API_KEY}")
    threading.Thread(target=scheduler_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
