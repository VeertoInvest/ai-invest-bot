import os
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from keep_alive import keep_alive
from news_handler import handle_news
from undervalued_stocks import analyze_undervalued_stocks

# Получаем ключ API из переменной окружения
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")

# Проверка: если токен не найден — не запускаемся
if not TELEGRAM_API_KEY:
    raise ValueError("TELEGRAM_API_KEY is not set in environment variables")

# Настройка бота
bot = Bot(token=TELEGRAM_API_KEY)
updater = Updater(token=TELEGRAM_API_KEY, use_context=True)
dispatcher = updater.dispatcher

# Обработчики команд
def start(update, context):
    print(f"User {update.effective_user.id} sent /start")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Я бот для анализа новостей и недооцененных акций.")

def news(update, context):
    print(f"User {update.effective_user.id} sent /news")
    articles = handle_news()
    for article in articles:
        context.bot.send_message(chat_id=update.effective_chat.id, text=article)

def undervalued(update, context):
    print(f"User {update.effective_user.id} sent /undervalued")
    tickers = ["AAPL", "MSFT", "GOOG"]
    stocks = analyze_undervalued_stocks(tickers)
    if stocks:
        for stock, pe in stocks:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"{stock} с P/E {pe}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Нет недооценённых акций.")

# Регистрация команд
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("news", news))
dispatcher.add_handler(CommandHandler("undervalued", undervalued))

# Запускаем Flask-сервер для Render
keep_alive()

# Запуск бота с отловом ошибок
try:
    print("✅ Starting bot polling...")
    updater.start_polling()
    updater.idle()
except Exception as e:
    print(f"❌ Error starting bot: {e}")
