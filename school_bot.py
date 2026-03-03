import logging
import os
import threading
from datetime import datetime, time, timedelta
import pytz
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# Логирование
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ Токен не найден")
    exit(1)

# Часовой пояс
tz = pytz.timezone('Europe/Kiev')
ADMIN_ID = 1823742969
allowed_users = [ADMIN_ID]

# ========== РАСПИСАНИЕ (ТОЛЬКО ПОНЕДЕЛЬНИК ДЛЯ ТЕСТА) ==========
schedule = {
    0: [  # Понедельник
        ("09:00", "Хімія", "https://us04web.zoom.us/j/7430647043?pwd=CLpdFoqSVh0X1s79xVF1m8w4J4MjYo.1"),
        ("09:00", "Географія", "https://us05web.zoom.us/j/7372874110?pwd=MUJaQUJsOUNHYUowUkswcEoxV09IUT09&omn=85468090096"),
    ]
}

days_ua = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]

# ========== КНОПКИ ==========
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📅 Сьогодні")],
    ], resize_keyboard=True)

# ========== СТАРТ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in allowed_users:
        await update.message.reply_text("👋 Привет!", reply_markup=main_keyboard())
    else:
        await update.message.reply_text("❌ Доступ запрещен.")

# ========== КНОПКИ ==========
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in allowed_users:
        return

    text = update.message.text
    today = datetime.now(tz).weekday()

    if text == "📅 Сьогодні":
        await show_day(update, today)

async def show_day(update, day):
    lessons = schedule[day]
    if not lessons:
        await update.message.reply_text(f"📅 *{days_ua[day]}* – выходной", parse_mode="Markdown")
        return
    text = f"📅 *{days_ua[day]}*\n"
    for t, name, _ in lessons:
        text += f"⏰ {t} – {name}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ========== УВЕДОМЛЕНИЯ ==========
async def send_notification(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    t, name, link = job.data

    for uid in allowed_users:
        try:
            text = f"⏰ *Урок начался:* {name}"
            if link:
                keyboard = [[InlineKeyboardButton("🔗 Присоединиться", url=link)]]
                await context.bot.send_message(uid, text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await context.bot.send_message(uid, text, parse_mode="Markdown")
            logger.info(f"Уведомление для '{name}' отправлено")
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")

def schedule_lessons(app):
    for day, lessons in schedule.items():
        for t, name, link in lessons:
            h, m = map(int, t.split(':'))
            app.job_queue.run_daily(
                send_notification,
                time(h, m, tzinfo=tz),
                days=(day,),
                data=(t, name, link)
            )
    logger.info("✅ Уроки запланированы")

# ========== ЗАПУСК БОТА ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    schedule_lessons(app)
    logger.info("🚀 Бот запущен")
    app.run_polling()

# ========== FLASK ДЛЯ RENDER ==========
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running"

@flask_app.route('/health')
def health():
    return {"status": "ok"}

def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    main()
