import logging
import os
import json
import requests
import threading
from datetime import datetime
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler
from apscheduler.schedulers.background import BackgroundScheduler
from openai import OpenAI
from news_handler import handle_news, ai_analyze_news
from undervalued_stocks import analyze_undervalued_stocks_by_indicators

# --- ЛОГГИРОВАНИЕ ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ---
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
PORT = int(os.getenv("PORT", 10000))

if not TELEGRAM_API_KEY or not RENDER_EXTERNAL_HOSTNAME:
    raise ValueError("❌ Обязательно укажите TELEGRAM_API_KEY и RENDER_EXTERNAL_HOSTNAME в .env")

# --- ИНИЦИАЛИЗАЦИЯ ---
app = Flask(__name__)
bot = Bot(token=TELEGRAM_API_KEY)
dispatcher = Dispatcher(bot, None, workers=1, use_context=True)
favorites = {}  # Память: {user_id: [tickers]}

# --- КОМАНДЫ ---
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("📰 Новости", callback_data="news")],
        [InlineKeyboardButton("📌 Добавить тикер", callback_data="add")],
        [InlineKeyboardButton("❌ Удалить тикер", callback_data="remove")],
        [InlineKeyboardButton("⭐ Избранное", callback_data="favorites")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    if query.data == "news":
        tickers = favorites.get(user_id, [])
        if not tickers:
            query.edit_message_text("У вас нет тикеров. Добавьте сначала.")
            return
        for ticker in tickers:
            send_news_analysis(user_id, ticker)

    elif query.data == "add":
        context.bot.send_message(chat_id=query.message.chat_id, text="Введите тикер для добавления в избранное:")
        context.user_data['awaiting_add'] = True

    elif query.data == "remove":
        user_favs = favorites.get(user_id, [])
        if not user_favs:
            context.bot.send_message(chat_id=query.message.chat_id, text="Список пуст.")
            return
        keyboard = [[InlineKeyboardButton(t, callback_data=f"remove_{t}")] for t in user_favs]
        context.bot.send_message(chat_id=query.message.chat_id, text="Выберите тикер для удаления:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "favorites":
        favs = favorites.get(user_id, [])
        if favs:
            context.bot.send_message(chat_id=query.message.chat_id, text="⭐ Ваши тикеры: " + ", ".join(favs))
        else:
            context.bot.send_message(chat_id=query.message.chat_id, text="Список избранного пуст.")

    elif query.data.startswith("remove_"):
        ticker = query.data.replace("remove_", "")
        favorites[user_id].remove(ticker)
        context.bot.send_message(chat_id=query.message.chat_id, text=f"Удалён: {ticker}")


def text_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.upper()

    if context.user_data.get('awaiting_add'):
        context.user_data['awaiting_add'] = False
        favorites.setdefault(user_id, []).append(text)
        update.message.reply_text(f"✅ {text} добавлен в избранное.")
    else:
        send_news_analysis(user_id, text)

# --- АНАЛИЗ НОВОСТЕЙ ---
def send_news_analysis(user_id: int, ticker: str):
    try:
        raw_news = handle_news(ticker)
        if not raw_news:
            bot.send_message(chat_id=user_id, text=f"Нет новостей по {ticker}")
            return

        for news in raw_news[:3]:
            summary, tone, category, impact, recommendation, historical_reaction = ai_analyze_news(news, ticker)
            bot.send_message(chat_id=user_id, text=f"📰 {news['title']}\n\n💬 {summary}\n📊 Категория: {category}\n🎭 Тон: {tone}\n🔥 Влияние: {impact}\n📈 Реакция в прошлом: {historical_reaction}\n💡 Рекомендация: {recommendation}")
    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        bot.send_message(chat_id=user_id, text="Произошла ошибка при анализе новостей.")

# --- ЕЖЕНЕДЕЛЬНЫЙ АНАЛИЗ АКЦИЙ ---
def send_weekly_undervalued():
    try:
        result = analyze_undervalued_stocks_by_indicators()
        for user_id in favorites:
            if result:
                bot.send_message(chat_id=user_id, text="📉 Недооценённые акции на этой неделе:")
                for stock in result:
                    bot.send_message(chat_id=user_id, text=stock)
            else:
                bot.send_message(chat_id=user_id, text="На этой неделе подходящих акций не найдено.")
    except Exception as e:
        logger.error(f"Ошибка при еженедельном анализе акций: {e}")

# --- ПЕРИОДИЧЕСКИЕ УВЕДОМЛЕНИЯ ---
def send_scheduled_news():
    for user_id, tickers in favorites.items():
        for ticker in tickers:
            send_news_analysis(user_id, ticker)

# --- WEBHOOK ---
@app.route(f"/{TELEGRAM_API_KEY}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

@app.route("/")
def home():
    return "OK"

# --- ЗАПУСК ---
if __name__ == '__main__':
    bot.delete_webhook()
    webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/{TELEGRAM_API_KEY}"
    bot.set_webhook(webhook_url)
    logger.info(f"✅ Webhook установлен: {webhook_url}")

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(handle_callback))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))

    scheduler = BackgroundScheduler()
    scheduler.add_job(send_scheduled_news, 'interval', hours=4)
    scheduler.add_job(send_weekly_undervalued, 'cron', day_of_week='mon', hour=10)
    scheduler.start()

    app.run(host='0.0.0.0', port=PORT)
