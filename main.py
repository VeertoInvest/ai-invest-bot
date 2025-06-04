import os
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from keep_alive import keep_alive
from news_handler import handle_news
from undervalued_stocks import analyze_undervalued_stocks

# Получаем API-ключ из переменных окружения
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")

# Инициализируем бота и апдейтера
bot = Bot(token=TELEGRAM_API_KEY)
updater = Updater(token=TELEGRAM_API_KEY, use_context=True)
dispatcher = updater.dispatcher

# Команда /start
def start(update, context):
    print(f"User {update.effective_user.id} sent /start")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Я бот для анализа новостей и недооцененных акций.")

# Команда /news
def send_news(update, context):
    print(f"User {update.effective_user.id} sent /news")
    articles = handle_news()
    if articles:
        for article in articles:
            context.bot.send_message(chat_id=update.effective_chat.id, text=article)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Нет свежих новостей.")

# Команда /undervalued
def send_undervalued(update, context):
    print(f"User {update.effective_user.id} sent /undervalued")
    tickers = ["AAPL", "MSFT", "GOOG"]
    stocks = analyze_undervalued_stocks(tickers)
    if stocks:
        for stock, pe in stocks:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"{stock} с P/E {pe}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Нет недооценённых акций.")

# Регистрируем команды
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("news", send_news))
dispatcher.add_handler(CommandHandler("undervalued", send_undervalued))

# Запускаем Flask-сервер для Render
keep_alive()

# Запускаем бота
print("✅ Bot started and keep_alive active.")
updater.start_polling()
updater.idle()
