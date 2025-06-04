import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from news_handler import handle_news
from undervalued_stocks import analyze_undervalued_stocks

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))

if not TELEGRAM_API_KEY or not WEBHOOK_URL:
    raise ValueError("❌ TELEGRAM_API_KEY или WEBHOOK_URL не установлены в переменных окружения.")

bot = Bot(token=TELEGRAM_API_KEY)
app = Flask(__name__)
dispatcher = Dispatcher(bot, update_queue=None, workers=1, use_context=True)

# Команды
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="🤖 Бот активен. Используй /news или /undervalued")

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

# Регистрация
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("news", news))
dispatcher.add_handler(CommandHandler("undervalued", undervalued))

# Webhook обработчик
@app.route(f"/{TELEGRAM_API_KEY}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# Главная страница для Render ping
@app.route("/", methods=["GET"])
def index():
    return "🟢 Telegram Webhook Bot активен", 200

# Установка webhook в момент запуска приложения
def set_webhook():
    url = f"{WEBHOOK_URL}/{TELEGRAM_API_KEY}"
    bot.delete_webhook()
    success = bot.set_webhook(url=url)
    print(f"✅ Webhook {'успешно установлен' if success else 'не удалось установить'}: {url}")

if __name__ == "__main__":
    set_webhook()
    print(f"🚀 Flask-сервер запускается на порту {PORT}")
    app.run(host="0.0.0.0", port=PORT)
