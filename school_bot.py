import logging
import os
from datetime import datetime, time, timedelta
import pytz
from telegram import Update
from telegram.ext import Application, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
tz = pytz.timezone('Europe/Kiev')
ADMIN_ID = 1823742969

async def test_callback(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет тестовое сообщение админу"""
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🧪 Тест планировщика: {datetime.now(tz).strftime('%H:%M:%S')}"
        )
        logger.info("Тест отправлен")
    except Exception as e:
        logger.error(f"Ошибка теста: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Запускаем тестовую задачу каждые 60 секунд
    app.job_queue.run_repeating(test_callback, interval=60, first=10)
    
    logger.info("🚀 Тестовый бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
