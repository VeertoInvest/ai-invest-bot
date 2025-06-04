import os
import schedule
import time
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from keep_alive import keep_alive  # добавлено
from news_handler import handle_news
from undervalued_stocks import analyze_undervalued_stocks

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")

bot = Bot(token=TELEGRAM_API_KEY)
updater = Updater(token=TELEGRAM_API_KEY, use_context=True)
dispatcher = updater.dispatcher

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Бот активен!")

def news(update, context):
    articles = handle_news()
    for article in articles:
        context.bot.send_message(chat_id=update.effective_chat.id, text=article)

def undervalued(update, context):
    tickers = ["AAPL", "MSFT", "GOOG"]
    stocks = analyze_undervalued_stocks(tickers)
    if stocks:
        for stock, pe in stocks:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"{stock} с P/E {pe}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Нет недооценённых акций.")

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("news", news))
dispatcher.add_handler(CommandHandler("undervalued", undervalued))

# 🟢 ВАЖНО: запускаем Flask-сервер
keep_alive()

# 🟢 Запускаем Telegram-бота
print("✅ Bot started and keep_alive active.")
updater.start_polling()
updater.idle()
