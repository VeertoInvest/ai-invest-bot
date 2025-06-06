import os
import logging
import pytz
import openai
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler
from apscheduler.schedulers.background import BackgroundScheduler
from news_handler import fetch_news_for_ticker, ai_analyze_news
from undervalued_stocks import weekly_undervalued_stocks_search
from memory import add_favorite_ticker, remove_favorite_ticker, get_favorites

TOKEN = os.getenv("TELEGRAM_API_KEY")
HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")
PORT = int(os.environ.get("PORT", 10000))
openai.api_key = os.getenv("OPENAI_API_KEY")

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)
logging.basicConfig(level=logging.INFO)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Бот работает"

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Отправь /analyze <тикер>, чтобы получить новости и анализ.")

def analyze(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Укажите тикер: /analyze AAPL")
        return

    ticker = context.args[0].upper()
    articles = fetch_news_for_ticker(ticker)

    if not articles:
        update.message.reply_text("Новости не найдены.")
        return

    chat_id = update.effective_chat.id
    for article in articles[:3]:
        try:
            analysis = ai_analyze_news(article)
            text = f"\U0001F4F0 {article['title']}\n{article['url']}\n\n{analysis}"
        except Exception as e:
            logging.error(f"AI анализ не удался: {e}")
            text = f"\U0001F4F0 {article['title']}\n{article['url']}\n\nНе удалось получить анализ новости."

        context.bot.send_message(chat_id=chat_id, text=text)

    keyboard = [[InlineKeyboardButton("Добавить в избранное", callback_data=f"add_{ticker}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(f"Хотите получать новости по {ticker}?", reply_markup=reply_markup)

def handle_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = str(query.from_user.id)
    data = query.data

    if data.startswith("add_"):
        ticker = data.split("_")[1]
        add_favorite_ticker(user_id, ticker)
        query.edit_message_text(f"\u2705 {ticker} добавлен в избранное.")

def favorites(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    tickers = get_favorites(user_id)
    if tickers:
        update.message.reply_text("\u2B50 Избранные тикеры: " + ", ".join(tickers))
    else:
        update.message.reply_text("У вас нет избранных тикеров.")

def delete(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not context.args:
        update.message.reply_text("Укажите тикер для удаления: /delete AAPL")
        return
    ticker = context.args[0].upper()
    remove_favorite_ticker(user_id, ticker)
    update.message.reply_text(f"\U0001F5D1 {ticker} удалён из избранного.")

def notify_news():
    for user_id, tickers in get_favorites().items():
        for ticker in tickers:
            articles = fetch_news_for_ticker(ticker)
            for article in articles[:1]:
                try:
                    analysis = ai_analyze_news(article)
                    text = f"\U0001F4F0 {article['title']}\n{article['url']}\n\n{analysis}"
                except Exception as e:
                    logging.error(f"AI анализ не удался: {e}")
                    text = f"\U0001F4F0 {article['title']}\n{article['url']}\n\nНе удалось получить анализ новости."

                bot.send_message(chat_id=user_id, text=text)

def notify_undervalued():
    results = weekly_undervalued_stocks_search()
    for user_id in get_favorites():
        if results:
            bot.send_message(chat_id=user_id, text="\U0001F4C9 Недооценённые акции недели:")
            for stock in results:
                bot.send_message(chat_id=user_id, text=stock)
        else:
            bot.send_message(chat_id=user_id, text="Недооценённых акций не найдено.")

scheduler = BackgroundScheduler()
scheduler.add_job(notify_news, 'interval', hours=4, timezone=pytz.utc)
scheduler.add_job(notify_undervalued, 'cron', day_of_week='mon', hour=10, timezone=pytz.utc)
scheduler.start()

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("analyze", analyze))
dispatcher.add_handler(CommandHandler("favorites", favorites))
dispatcher.add_handler(CommandHandler("delete", delete))
dispatcher.add_handler(CallbackQueryHandler(handle_buttons))

if __name__ == "__main__":
    bot.set_webhook(url=f"https://{HOST}/{TOKEN}")
    logging.info(f"\u2705 Webhook установлен: https://{HOST}/{TOKEN}")
    app.run(host="0.0.0.0", port=PORT)
