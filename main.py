import os
import logging
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler
from apscheduler.schedulers.background import BackgroundScheduler

from news_handler import fetch_news_for_ticker, ai_analyze_news
from undervalued_stocks import weekly_undervalued_stocks_search
from memory import add_favorite_ticker, get_favorites

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

scheduler = BackgroundScheduler()

def start(update, context):
    if update.message:
        update.message.reply_text("Привет! Отправь команду /analyze <тикер> для анализа новостей.")

def analyze(update, context):
    try:
        if not context.args:
            if update.message:
                update.message.reply_text("Пожалуйста, укажите тикер. Пример: /analyze AAPL")
            return

        ticker = context.args[0].upper()
        articles = fetch_news_for_ticker(ticker)

        if not articles:
            if update.message:
                update.message.reply_text(f"❌ Не удалось найти новости по {ticker}.")
            return

        for article in articles:
            analysis = ai_analyze_news(article)
            text = f"📰 <b>{article.get('title')}</b>\n\n" \
                   f"{article.get('description')}\n\n" \
                   f"<i>{analysis}</i>\n\n" \
                   f"🔗 {article.get('url')}"
            if update.message:
                update.message.reply_text(text, parse_mode="HTML")

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"➕ Добавить {ticker} в избранное", callback_data=f"add_fav_{ticker}")]
        ])
        if update.message:
            update.message.reply_text(f"Хотите получать новости по {ticker}?", reply_markup=reply_markup)

    except Exception as e:
        logging.exception("Ошибка в analyze")
        if update.message:
            update.message.reply_text("Произошла ошибка при анализе.")

def callback_handler(update, context):
    query = update.callback_query
    if not query:
        return

    query.answer()
    data = query.data
    if data.startswith("add_fav_"):
        ticker = data.replace("add_fav_", "")
        user_id = query.from_user.id
        add_favorite_ticker(user_id, ticker)
        query.edit_message_text(f"✅ {ticker} добавлен в избранное!")

def favorites(update, context):
    user_id = update.effective_user.id
    favs = get_favorites(user_id)
    if favs:
        update.message.reply_text("📌 Ваши любимые тикеры:\n" + ", ".join(favs))
    else:
        update.message.reply_text("У вас пока нет любимых тикеров. Добавьте через /analyze.")

def weekly(update, context):
    try:
        undervalued = weekly_undervalued_stocks_search()
        if not undervalued:
            update.message.reply_text("❌ Не удалось найти недооценённые акции.")
            return

        text = "📉 Недооценённые акции недели:\n\n"
        for stock in undervalued:
            text += f"{stock}\n"

        update.message.reply_text(text)
    except Exception as e:
        logging.exception("Ошибка в weekly")
        update.message.reply_text("Произошла ошибка при генерации отчёта.")

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "бот работает"

# Установка webhook при запуске
@app.before_first_request
def setup():
    url = os.getenv("RENDER_EXTERNAL_URL") or "https://ai-invest-bot.onrender.com"
    full_url = f"{url}/{TOKEN}"
    bot.set_webhook(full_url)
    print(f"✅ Webhook установлен: {full_url}")

    # Планировщик
    scheduler.add_job(notify_undervalued, 'interval', hours=4)
    scheduler.start()

def notify_undervalued():
    try:
        undervalued = weekly_undervalued_stocks_search()
        if undervalued:
            text = "📉 Еженедельные недооценённые акции:\n\n" + "\n".join(undervalued)
            # Рассылка по всем пользователям
            for user_id in get_favorites():
                bot.send_message(chat_id=user_id, text=text)
    except Exception as e:
        logging.exception("Ошибка в notify_undervalued")

dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("analyze", analyze))
dispatcher.add_handler(CommandHandler("favorites", favorites))
dispatcher.add_handler(CommandHandler("weekly", weekly))
dispatcher.add_handler(CallbackQueryHandler(callback_handler))

if __name__ == "__main__":
    app.run(port=10000)
