import json
import logging
import time
import os
import threading
import signal
import sys
from datetime import time as dt_time, datetime, date, timedelta
from functools import wraps
from pathlib import Path
from pytz import timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from flask import Flask, jsonify

print("✅ Файл school_bot.py запущен")
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== КОНСТАНТЫ ==========
TIMEZONE = timezone("Europe/Kiev")
CONFIG_FILE = "config.json"
PENDING_FILE = "pending.json"
APPROVED_FILE = "approved.json"
HOLIDAYS_FILE = "holidays.json"

# ========== ЗАГРУЗКА КОНФИГА ==========
def load_json(file: Path, default=None):
    if default is None:
        default = {}
    if file.exists():
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

config = load_json(Path(CONFIG_FILE), {"token": "", "admin_id": 0})
BOT_TOKEN = os.environ.get("BOT_TOKEN") or config.get("token")
ADMIN_ID = int(os.environ.get("ADMIN_ID") or config.get("admin_id", 0))

if not BOT_TOKEN:
    raise ValueError("❌ Токен не найден")

# ВРЕМЕННО: принудительно добавляем твой ID
approved_users = load_json(Path(APPROVED_FILE), [])
YOUR_ID = 1823742969
if YOUR_ID not in approved_users:
    approved_users.append(YOUR_ID)
    logger.info(f"✅ Принудительно добавлен пользователь {YOUR_ID}")

holidays = load_json(Path(HOLIDAYS_FILE), {})

# ========== ТЕСТОВОЕ РАСПИСАНИЕ ==========
# Установи время на ближайшее (например, 13:40)
test_hour = 13
test_minute = 40  # поменяй на 45, если не успеваешь

schedule = {
    datetime.now(TIMEZONE).weekday(): [  # сегодня
        (dt_time(test_hour, test_minute), "🧪 ТЕСТОВЫЙ УРОК", None),
    ]
}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def is_admin(user_id): return user_id == ADMIN_ID
def is_approved(user_id): return user_id in approved_users
def is_on_holiday(user_id): 
    end_str = holidays.get(str(user_id))
    if not end_str: return False
    return date.today() <= date.fromisoformat(end_str)

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if is_admin(user_id):
        await update.message.reply_text("👋 Админ")
    elif is_approved(user_id):
        await update.message.reply_text("👋 Привет, ученик!")
    else:
        await update.message.reply_text("👋 Напиши имя")

# ========== ПЛАНИРОВЩИК ==========
async def send_lesson_notification(context: ContextTypes.DEFAULT_TYPE):
    logger.info("🔥🔥🔥 УРОК НАЧАЛСЯ! 🔥🔥🔥")
    job = context.job
    lesson_time, lesson_name, lesson_link = job.data
    logger.info(f"🔔 Отправка урока: {lesson_name}")
    
    for uid in approved_users:
        if is_on_holiday(uid):
            logger.info(f"   Пользователь {uid} на каникулах")
            continue
        try:
            await context.bot.send_message(chat_id=uid, text=f"⏰ {lesson_name}")
            logger.info(f"   Отправлено пользователю {uid}")
        except Exception as e:
            logger.error(f"   Ошибка отправки {uid}: {e}")

def schedule_all_lessons(app):
    count = 0
    for day, lessons in schedule.items():
        for lesson_time, lesson_name, lesson_link in lessons:
            tz_time = dt_time(hour=lesson_time.hour, minute=lesson_time.minute, tzinfo=TIMEZONE)
            app.job_queue.run_daily(send_lesson_notification, time=tz_time, days=(day,), data=(lesson_time, lesson_name, lesson_link))
            count += 1
    logger.info(f"✅ Запланировано {count} уроков")

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def main():
    logger.info("🟢 main() запущен")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    schedule_all_lessons(app)
    logger.info("🚀 Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

# ========== FLASK ==========
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Бот работает"
@flask_app.route('/health')
def health(): return {"status": "ok"}

def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

def run_bot():
    try:
        main()
    except Exception as e:
        logger.error(f"Ошибка: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
