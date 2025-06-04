import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from news_handler import handle_news
from undervalued_stocks import analyze_undervalued_stocks

# Настройки
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
if not TELEGRAM_API_KEY:
    raise ValueError("❌ TELEGRAM_API_KEY not set")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://ai-invest-bot.onrender.com
PORT = int(os.environ.get("PORT", 10000))

bot = Bot(token=TELEGRAM_API_KEY)

# Flask-приложение
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# Команды
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="🤖 Бот активен. Используй /news или /undervalued")

def news(update, context):
    articles = handle_news()
    for article in articles:
        context.bot.send_message(chat_id=update.effective_chat.id, text=article)

def undervalued(update, context):
    tickers = ["AAPL", "MSFT", "GOOG"]
    results = analyze_undervalued_stocks(tickers)
    if results:
        for stock, pe in results:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"{stock} с P/E {pe}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Нет недооценённых акций.")

# Регистрация команд
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("news", news))
dispatcher.add_handler(CommandHandler("undervalued", undervalued))

# Обработка запроса от Telegram
@app.route(f"/{TELEGRAM_API_KEY}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

# Установка Webhook при запуске
@app.before_first_request
def init_webhook():
    full_url = f"{WEBHOOK_URL}/{TELEGRAM_API_KEY}"
    bot.delete_webhook()
    bot.set_webhook(url=full_url)
    print(f"✅ Webhook установлен: {full_url}")

# Запуск сервера
if __name__ == "__main__":
    print(f"🌐 Запуск Flask на порту {PORT}")
    app.run(host="0.0.0.0", port=PORT)
