import os
import logging
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from apscheduler.schedulers.background import BackgroundScheduler
from news_handler import fetch_news_for_ticker, ai_analyze_news
from undervalued_stocks import weekly_undervalued_stocks_search
from memory import add_favorite, remove_favorite, get_favorites

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
TOKEN = os.getenv("TELEGRAM_API_KEY")
PORT = int(os.environ.get("PORT", 10000))
HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")

if not TOKEN or not HOST:
    raise ValueError("TELEGRAM_API_KEY и RENDER_EXTERNAL_HOSTNAME должны быть заданы в переменных окружения")

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=1, use_context=True)

# Команды

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("AAPL", callback_data='ticker_AAPL')],
        [InlineKeyboardButton("MSFT", callback_data='ticker_MSFT')],
        [InlineKeyboardButton("GOOG", callback_data='ticker_GOOG')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Привет! Введи тикер или выбери из кнопок ниже:",
        reply_markup=reply_markup
    )

def favorites(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    favs = get_favorites(user_id)
    if favs:
        update.message.reply_text("Ваши любимые тикеры: " + ", ".join(favs))
    else:
        update.message.reply_text("У вас пока нет любимых тикеров. Добавьте их через команды или кнопки.")

def delete(update: Update, context: CallbackContext):
    if context.args:
        ticker = context.args[0].upper()
        removed = remove_favorite(update.effective_user.id, ticker)
        if removed:
            update.message.reply_text(f"Удалён тикер {ticker} из избранного.")
        else:
            update.message.reply_text(f"Тикер {ticker} не найден в избранном.")
    else:
        update.message.reply_text("Укажите тикер: /delete TICKER")

def analyze(update: Update, context: CallbackContext):
    if context.args:
        ticker = context.args[0].upper()
        articles = fetch_news_for_ticker(ticker)
        if not articles:
            update.message.reply_text(f"Нет свежих новостей по {ticker}.")
            return
        add_favorite(update.effective_user.id, ticker)
        for article in articles[:3]:
            analysis = ai_analyze_news(article)
            update.message.reply_text(analysis)
    else:
        update.message.reply_text("Укажите тикер: /analyze TICKER")

def weekly(update: Update, context: CallbackContext):
    update.message.reply_text("Ищу недооценённые акции...")
    result = weekly_undervalued_stocks_search()
    if result:
        for item in result:
            update.message.reply_text(item)
    else:
        update.message.reply_text("На этой неделе подходящих акций не найдено.")

def handle_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data.startswith("ticker_"):
        ticker = query.data.split("_")[1]
        update.effective_chat.send_message(f"Запускаю анализ новостей по {ticker}...")
        articles = fetch_news_for_ticker(ticker)
        if not articles:
            query.edit_message_text(f"Нет новостей по {ticker}")
            return
        add_favorite(query.from_user.id, ticker)
        for article in articles[:3]:
            summary = ai_analyze_news(article)
            update.effective_chat.send_message(summary)

# Планировщик уведомлений
scheduler = BackgroundScheduler()

def send_periodic_news():
    for user_id, tickers in get_favorites().items():
        for ticker in tickers:
            articles = fetch_news_for_ticker(ticker)
            for article in articles[:1]:
                summary = ai_analyze_news(article)
                bot.send_message(chat_id=user_id, text=f"📈 {ticker}: {summary}")

scheduler.add_job(send_periodic_news, 'interval', hours=4)
scheduler.start()

# Регистрация обработчиков

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("favorites", favorites))
dispatcher.add_handler(CommandHandler("delete", delete))
dispatcher.add_handler(CommandHandler("analyze", analyze))
dispatcher.add_handler(CommandHandler("weekly", weekly))
dispatcher.add_handler(CallbackQueryHandler(handle_buttons))

# Webhook endpoint
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Бот работает!"

if __name__ == "__main__":
    bot.set_webhook(f"https://{HOST}/{TOKEN}")
    logger.info(f"✅ Webhook установлен: https://{HOST}/{TOKEN}")
    app.run(host="0.0.0.0", port=PORT)
