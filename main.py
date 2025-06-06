import os
import logging
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler
from news_handler import handle_news, fetch_news_for_ticker
from undervalued_stocks import analyze_undervalued_stocks
from ai_news_analysis import analyze_news_sentiment

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
PORT = int(os.getenv("PORT", 10000))

if not TELEGRAM_API_KEY or not RENDER_EXTERNAL_HOSTNAME:
    raise ValueError("Не заданы переменные TELEGRAM_API_KEY и RENDER_EXTERNAL_HOSTNAME")

bot = Bot(token=TELEGRAM_API_KEY)
dispatcher = Dispatcher(bot, update_queue=None, workers=4, use_context=True)

user_favorites = {}

# Команда /start
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Новости", callback_data='news')],
        [InlineKeyboardButton("Недооценённые акции", callback_data='undervalued')],
        [InlineKeyboardButton("Мои тикеры", callback_data='favorites')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Привет! Выберите действие:", reply_markup=reply_markup)

# Обработка кнопок

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "news":
        query.edit_message_text("Введите тикер (например: AAPL)")
        context.user_data["expecting_ticker"] = "news"
    elif query.data == "undervalued":
        tickers = ["AAPL", "MSFT", "GOOG"]
        results = analyze_undervalued_stocks(tickers)
        text = "\n".join([f"{t[0]} с P/E {t[1]}" for t in results]) or "Нет недооценённых акций."
        query.edit_message_text(text)
    elif query.data == "favorites":
        user_id = query.from_user.id
        favs = user_favorites.get(user_id, [])
        text = "\n".join(favs) or "Нет любимых тикеров."
        query.edit_message_text(f"Ваши любимые тикеры:\n{text}")

# Команда /favorites

def favorites_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    favs = user_favorites.get(user_id, [])
    text = "\n".join(favs) or "Нет любимых тикеров. Добавьте их, введя тикер."
    update.message.reply_text(f"Ваши любимые тикеры:\n{text}")

# Обработка сообщений

def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip().upper()

    if context.user_data.get("expecting_ticker") == "news":
        news_list = fetch_news_for_ticker(text)
        if not news_list:
            update.message.reply_text("Не найдено новостей по тикеру.")
            return

        user_favorites.setdefault(user_id, []).append(text)
        update.message.reply_text(f"Тикер {text} добавлен в любимые. Анализирую новости...")

        for article in news_list[:3]:
            title = article.get("title", "")
            analysis = analyze_news_sentiment(title)
            summary = (
                f"📰 {title}\n"
                f"📈 Тип: {analysis['type']}\n"
                f"😐 Тональность: {analysis['sentiment']}\n"
                f"💥 Сила воздействия: {analysis['impact']}\n"
                f"💬 Рекомендация: {analysis['recommendation']}\n"
                f"📊 Прошлая реакция цены: {analysis['past_reaction']}"
            )
            update.message.reply_text(summary)
        context.user_data["expecting_ticker"] = None

# Webhook обработчик

@app.route(f"/{TELEGRAM_API_KEY}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Бот работает"

# Регистрируем обработчики

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("favorites", favorites_command))
dispatcher.add_handler(CallbackQueryHandler(button_handler))
dispatcher.add_handler(CommandHandler("help", start))
dispatcher.add_handler(CommandHandler("news", lambda u, c: u.message.reply_text("Введите тикер.")))
dispatcher.add_handler(CommandHandler("undervalued", lambda u, c: u.message.reply_text("Используйте кнопки или введите /start")))
dispatcher.add_handler(CommandHandler("ticker", handle_message))
dispatcher.add_handler(CommandHandler("add", handle_message))
dispatcher.add_handler(CommandHandler("analyze", handle_message))
dispatcher.add_handler(CommandHandler("tickernews", handle_message))
dispatcher.add_handler(CommandHandler("summary", handle_message))
dispatcher.add_handler(CommandHandler("analyze_news", handle_message))
dispatcher.add_handler(CommandHandler("stock", handle_message))
dispatcher.add_handler(CommandHandler("stock_news", handle_message))
dispatcher.add_handler(CommandHandler("analyze_ticker", handle_message))
dispatcher.add_handler(CommandHandler("check", handle_message))
dispatcher.add_handler(CommandHandler("check_news", handle_message))
dispatcher.add_handler(CommandHandler("get_news", handle_message))
dispatcher.add_handler(CommandHandler("recommend", handle_message))
dispatcher.add_handler(CommandHandler("recommendation", handle_message))
dispatcher.add_handler(CommandHandler("reaction", handle_message))
dispatcher.add_handler(CommandHandler("reaction_price", handle_message))
dispatcher.add_handler(CommandHandler("summary_news", handle_message))
dispatcher.add_handler(CommandHandler("full_analysis", handle_message))
dispatcher.add_handler(CommandHandler("price_reaction", handle_message))
dispatcher.add_handler(CommandHandler("ticker_summary", handle_message))
dispatcher.add_handler(CommandHandler("sentiment", handle_message))
dispatcher.add_handler(CommandHandler("sentiment_analysis", handle_message))
dispatcher.add_handler(CommandHandler("impact", handle_message))
dispatcher.add_handler(CommandHandler("impact_analysis", handle_message))
dispatcher.add_handler(CommandHandler("type", handle_message))
dispatcher.add_handler(CommandHandler("news_type", handle_message))
dispatcher.add_handler(CommandHandler("ticker_type", handle_message))
dispatcher.add_handler(CommandHandler("analyze_type", handle_message))
dispatcher.add_handler(CommandHandler("ticker_impact", handle_message))
dispatcher.add_handler(CommandHandler("ticker_sentiment", handle_message))
dispatcher.add_handler(CommandHandler("ticker_recommend", handle_message))
dispatcher.add_handler(CommandHandler("favorite", favorites_command))
dispatcher.add_handler(CommandHandler("add_favorite", handle_message))
dispatcher.add_handler(CommandHandler("remove_favorite", handle_message))
dispatcher.add_handler(CommandHandler("clear_favorites", handle_message))
dispatcher.add_handler(CommandHandler("save_ticker", handle_message))
dispatcher.add_handler(CommandHandler("load_favorites", favorites_command))
dispatcher.add_handler(CommandHandler("list_favorites", favorites_command))
dispatcher.add_handler(CommandHandler("my_tickers", favorites_command))
dispatcher.add_handler(CommandHandler("fav_tickers", favorites_command))
dispatcher.add_handler(CommandHandler("saved", favorites_command))
dispatcher.add_handler(CommandHandler("tickers", favorites_command))
dispatcher.add_handler(CommandHandler("get_favorites", favorites_command))
dispatcher.add_handler(CommandHandler("fav", favorites_command))
dispatcher.add_handler(CommandHandler("tickers_list", favorites_command))
dispatcher.add_handler(CommandHandler("show_tickers", favorites_command))
dispatcher.add_handler(CommandHandler("favorite_list", favorites_command))
dispatcher.add_handler(CommandHandler("ticker_favs", favorites_command))
dispatcher.add_handler(CommandHandler("fav_list", favorites_command))
dispatcher.add_handler(CommandHandler("show_favs", favorites_command))
dispatcher.add_handler(CommandHandler("ticker_favorites", favorites_command))
dispatcher.add_handler(CommandHandler("tickers_favorites", favorites_command))
dispatcher.add_handler(CommandHandler("tickers_saved", favorites_command))
dispatcher.add_handler(CommandHandler("favorite_saved", favorites_command))
dispatcher.add_handler(CommandHandler("tickers_favs", favorites_command))
dispatcher.add_handler(CommandHandler("fav_saved", favorites_command))
dispatcher.add_handler(CommandHandler("favs", favorites_command))
dispatcher.add_handler(CommandHandler("ticker_fav", favorites_command))
dispatcher.add_handler(CommandHandler("favorite_ticker", favorites_command))
dispatcher.add_handler(CommandHandler("tickers_fav", favorites_command))
dispatcher.add_handler(CommandHandler("favs_list", favorites_command))
dispatcher.add_handler(CommandHandler("saved_favs", favorites_command))
dispatcher.add_handler(CommandHandler("fav_stocks", favorites_command))
dispatcher.add_handler(CommandHandler("stocks_favs", favorites_command))
dispatcher.add_handler(CommandHandler("list_favs", favorites_command))
dispatcher.add_handler(CommandHandler("favs_saved", favorites_command))
dispatcher.add_handler(CommandHandler("stock_favs", favorites_command))
dispatcher.add_handler(CommandHandler("favorites_list", favorites_command))
dispatcher.add_handler(CommandHandler("all_favs", favorites_command))
dispatcher.add_handler(CommandHandler("tickers_all", favorites_command))
dispatcher.add_handler(CommandHandler("favorites_all", favorites_command))
dispatcher.add_handler(CommandHandler("tickers_show", favorites_command))
dispatcher.add_handler(CommandHandler("fav_ticker_list", favorites_command))
dispatcher.add_handler(CommandHandler("fav_stocks_list", favorites_command))
dispatcher.add_handler(CommandHandler("tickers_favorites_list", favorites_command))
dispatcher.add_handler(CommandHandler("list_ticker_favs", favorites_command))
dispatcher.add_handler(CommandHandler("ticker_favorites_list", favorites_command))
dispatcher.add_handler(CommandHandler("all_favorite_tickers", favorites_command))
dispatcher.add_handler(CommandHandler("ticker_fav_list", favorites_command))
dispatcher.add_handler(CommandHandler("stock_fav_list", favorites_command))
dispatcher.add_handler(CommandHandler("fav_stock_list", favorites_command))
dispatcher.add_handler(CommandHandler("my_favs", favorites_command))

if __name__ == "__main__":
    webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/{TELEGRAM_API_KEY}"
    bot.set_webhook(url=webhook_url)
    logging.info(f"✅ Webhook установлен: {webhook_url}")
    app.run(host="0.0.0.0", port=PORT)
