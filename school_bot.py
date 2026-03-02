import logging
import os
from datetime import datetime, time, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# Логи
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен
BOT_TOKEN = os.environ.get("BOT_TOKEN")
tz = pytz.timezone('Europe/Kiev')
ADMIN_ID = 1823742969

# Кто получает уведомления — ТОЛЬКО ТЫ
allowed_users = [ADMIN_ID]

# ========== ТВОЁ РАСПИСАНИЕ ==========
# Формат: (час:минута, название, ссылка)
# Для спаренных уроков — две отдельные строки с одинаковым временем
schedule = {
    0: [  # Понедельник
        ("09:00", "Хімія", "https://us04web.zoom.us/j/7430647043?pwd=CLpdFoqSVh0X1s79xVF1m8w4J4MjYo.1"),
        ("09:00", "Географія", "https://us05web.zoom.us/j/7372874110?pwd=MUJaQUJsOUNHYUowUkswcEoxV09IUT09&omn=85468090096"),
        ("10:00", "Алгебра", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        ("11:00", "Англійська", "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"),
        ("12:00", "Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        ("13:00", "Всесвітня історія", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        ("14:00", "Інформатика", "https://us05web.zoom.us/j/3778676851?pwd=llSnb5K3NkdhTaVbaWaiWOnhzQaNbT.1"),
        ("14:00", "Мистецтво", "https://us05web.zoom.us/j/3669615047?pwd=bWFXY3lHcHZTYzBlS2Q2MitjaTY0Zz09"),
        ("15:00", "Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
    ],
    1: [  # Вторник
        ("09:00", "Алгебра", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        ("10:00", "Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        ("11:00", "Біологія і екологія", "https://us05web.zoom.us/j/81300275025?pwd=xNzRsLtAf4TYeszH5yWAHMbutUCGbz.1"),
        ("12:00", "Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"),
        ("13:00", "Англійська", "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"),
        ("14:00", "Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        ("15:00", "Українська література", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
    ],
    2: [  # Среда
        ("09:00", "Інформатика", "https://us05web.zoom.us/j/3778676851?pwd=llSnb5K3NkdhTaVbaWaiWOnhzQaNbT.1"),
        ("10:00", "Географія", "https://us05web.zoom.us/j/7372874110?pwd=MUJaQUJsOUNHYUowUkswcEoxV09IUT09&omn=85468090096"),
        ("11:00", "Зарубіжна література", "https://us04web.zoom.us/j/9721960165?pwd=yYQs8qczfNK9soiSgiSHFXOLXEi2al.1"),
        ("12:00", "Алгебра і початки аналізу", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        ("13:00", "Мистецтво", "https://us05web.zoom.us/j/3669615047?pwd=bWFXY3lHcHZTYzBlS2Q2MitjaTY0Zz09"),
        ("14:00", "Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"),
        ("15:00", "Фізкультура", "https://us04web.zoom.us/j/9199278785?pwd=V"),
    ],
    3: [  # Четверг
        ("09:00", "Громадянська освіта", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        ("10:00", "Громадянська освіта", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        ("11:00", "Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        ("12:00", "Біологія і екологія", "https://us05web.zoom.us/j/81300275025?pwd=xNzRsLtAf4TYeszH5yWAHMbutUCGbz.1"),
        ("13:00", "Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        ("14:00", "Захист України", None),
        ("15:00", "Захист України", None),
    ],
    4: [  # Пятница
        ("09:00", "Хімія", "https://us04web.zoom.us/j/7430647043?pwd=CLpdFoqSVh0X1s79xVF1m8w4J4MjYo.1"),
        ("10:00", "Українська література", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        ("11:00", "Історія України", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        ("12:00", "Алгебра і початки аналізу", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        ("13:00", "Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"),
        ("14:00", "Фізкультура", "https://us04web.zoom.us/j/9199278785?pwd=V"),
        ("15:00", "Історія України", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
    ],
    5: [],  # Суббота
    6: [],  # Воскресенье
}

days_ua = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]

# ========== КНОПКИ ==========
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📅 Сьогодні"), KeyboardButton("📆 Завтра")],
        [KeyboardButton("📋 Тиждень"), KeyboardButton("⏭ Наступний урок")],
        [KeyboardButton("🔗 Посилання")]
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
    elif text == "📆 Завтра":
        await show_day(update, (today + 1) % 7)
    elif text == "📋 Тиждень":
        await show_week(update)
    elif text == "⏭ Наступний урок":
        await next_lesson(update, today)
    elif text == "🔗 Посилання":
        await show_links(update, today)

async def show_day(update, day):
    lessons = schedule[day]
    if not lessons:
        await update.message.reply_text(f"📅 *{days_ua[day]}* – выходной", parse_mode="Markdown")
        return
    text = f"📅 *{days_ua[day]}*\n"
    for t, name, _ in lessons:
        text += f"⏰ {t} – {name}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def show_week(update):
    text = "📋 *Неделя*\n\n"
    for day in range(5):
        lessons = schedule[day]
        if lessons:
            text += f"*{days_ua[day]}:*\n"
            for t, name, _ in lessons:
                text += f"  ⏰ {t} – {name}\n"
            text += "\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def next_lesson(update, today):
    now = datetime.now(tz).strftime("%H:%M")
    for t, name, _ in schedule[today]:
        if t > now:
            await update.message.reply_text(f"⏭ *Следующий урок:* {t} – {name}", parse_mode="Markdown")
            return
    tomorrow = (today + 1) % 7
    if schedule[tomorrow]:
        t, name, _ = schedule[tomorrow][0]
        await update.message.reply_text(f"📅 Завтра первый урок: {t} – {name}", parse_mode="Markdown")
    else:
        await update.message.reply_text("🎉 Уроков нет")

async def show_links(update, day):
    lessons = schedule[day]
    if not lessons:
        await update.message.reply_text("📭 Сегодня уроков нет")
        return
    keyboard = []
    for i, (t, name, link) in enumerate(lessons):
        if link:
            keyboard.append([InlineKeyboardButton(f"{t} – {name}", callback_data=f"link_{day}_{i}")])
    if not keyboard:
        await update.message.reply_text("🔗 Сегодня нет ссылок")
        return
    await update.message.reply_text("🔗 Выбери урок:", reply_markup=InlineKeyboardMarkup(keyboard))

# ========== КОЛБЭКИ ==========
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("link_"):
        _, d, i = data.split("_")
        t, name, link = schedule[int(d)][int(i)]
        if link:
            keyboard = [[InlineKeyboardButton("🔗 Присоединиться", url=link)]]
            await query.edit_message_text(
                f"🔗 *{t} – {name}*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

# ========== УВЕДОМЛЕНИЯ ==========
async def send_notification(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    t, name, link, target_day = job.data
    
    today = datetime.now(tz).weekday()
    if today != target_day:
        return
    
    for uid in allowed_users:
        try:
            if job.name == "reminder":
                text = f"⏳ *Через 5 минут:* {name}"
            else:
                text = f"⏰ *Урок начался:* {name}"
            
            if link:
                keyboard = [[InlineKeyboardButton("🔗 Присоединиться", url=link)]]
                await context.bot.send_message(uid, text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await context.bot.send_message(uid, text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Ошибка: {e}")

def schedule_lessons(app):
    for day, lessons in schedule.items():
        for t, name, link in lessons:
            h, m = map(int, t.split(':'))
            
            # За 5 минут
            rh, rm = (h, m-5) if m >= 5 else (h-1, m+55)
            if rh >= 0:
                app.job_queue.run_daily(
                    send_notification,
                    time(rh, rm, tzinfo=tz),
                    days=(day,),
                    data=(t, name, link, day),
                    name="reminder"
                )
            
            # Начало урока
            app.job_queue.run_daily(
                send_notification,
                time(h, m, tzinfo=tz),
                days=(day,),
                data=(t, name, link, day),
                name="start"
            )
    logger.info("✅ Уроки запланированы")

# ========== ЗАПУСК ==========
def main():
    if not BOT_TOKEN:
        logger.error("❌ Нет токена")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    app.add_handler(CallbackQueryHandler(callback))
    
    schedule_lessons(app)
    
    logger.info("🚀 Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
