import logging
import os
import json
import threading
from datetime import datetime, time, timedelta
import pytz
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# ========== НАСТРОЙКИ ==========
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
tz = pytz.timezone('Europe/Kiev')
ADMIN_ID = 1823742969

# Файлы
USERS_FILE = "users.json"
PENDING_FILE = "pending.json"
NAMES_FILE = "names.json"
USERNAMES_FILE = "usernames.json"
BLOCKED_FILE = "blocked.json"

# ========== РАБОТА С JSON ==========
def load_json(file, default):
    try:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки {file}: {e}")
    return default

def save_json(file, data):
    try:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения {file}: {e}")

# Загрузка всех данных
NOTIFY_USERS = load_json(USERS_FILE, [ADMIN_ID])
PENDING_USERS = load_json(PENDING_FILE, [])
USER_NAMES = load_json(NAMES_FILE, {})
USER_USERNAMES = load_json(USERNAMES_FILE, {})
BLOCKED_USERS = load_json(BLOCKED_FILE, [])

# ========== РАСПИСАНИЕ ==========
SCHEDULE = {
    0: [  # Понедельник
        ("09:00", "Хімія // Географія", "https://us04web.zoom.us/j/7430647043?pwd=CLpdFoqSVh0X1s79xVF1m8w4J4MjYo.1"),
        ("10:00", "Англійська", "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"),
        ("11:00", "Іноземна мова (англійська)", "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"),
        ("12:00", "Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        ("13:00", "Всесвітня історія", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        ("14:00", "Інформатика // Мистецтво", "https://us05web.zoom.us/j/3778676851?pwd=llSnb5K3NkdhTaVbaWaiWOnhzQaNbT.1"),
        ("15:00", "Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
    ],
    1: [  # Вторник
        ("09:00", "Алгебра", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        ("10:00", "Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        ("11:00", "Біологія і екологія", "https://us05web.zoom.us/j/81300275025?pwd=xNzRsLtAf4TYeszH5yWAHMbutUCGbz.1"),
        ("12:00", "Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"),
        ("13:00", "Іноземна мова (англійська)", "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"),
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
        ("15:00", "Фізична культура", "https://us04web.zoom.us/j/9199278785?pwd=V"),
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
        ("14:00", "Фізична культура", "https://us04web.zoom.us/j/9199278785?pwd=V"),
        ("15:00", "Історія України", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
    ],
    5: [],  # Суббота
    6: [],  # Воскресенье
}

DAYS_UA = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]

# ========== КЛАВИАТУРЫ ==========
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📅 Сьогодні"), KeyboardButton("📆 Завтра")],
        [KeyboardButton("📋 Тиждень"), KeyboardButton("⏭ Наступний урок")],
        [KeyboardButton("🔗 Посилання на урок")]
    ], resize_keyboard=True)

def admin_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📅 Сьогодні"), KeyboardButton("📆 Завтра")],
        [KeyboardButton("📋 Тиждень"), KeyboardButton("⏭ Наступний урок")],
        [KeyboardButton("🔗 Посилання на урок")],
        [KeyboardButton("👑 Адмін панель")]
    ], resize_keyboard=True)

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    if uid == ADMIN_ID:
        return await update.message.reply_text("👑 Адмін-панель", reply_markup=admin_keyboard())
    
    if uid in NOTIFY_USERS:
        return await update.message.reply_text("👋 Вітаю!", reply_markup=main_keyboard())
    
    for p in PENDING_USERS:
        if p['id'] == uid:
            return await update.message.reply_text("⏳ Заявка розглядається")
    
    context.user_data['awaiting_name'] = True
    await update.message.reply_text("👋 Введіть ваше ім'я та прізвище:")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    
    # Регистрация
    if context.user_data.get('awaiting_name'):
        context.user_data['awaiting_name'] = False
        PENDING_USERS.append({
            'id': uid,
            'name': text,
            'username': update.effective_user.username or "",
            'date': datetime.now().isoformat()
        })
        save_json(PENDING_FILE, PENDING_USERS)
        
        # Уведомление админу
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Прийняти", callback_data=f"a_{uid}"),
            InlineKeyboardButton("❌ Відхилити", callback_data=f"r_{uid}")
        ]])
        await context.bot.send_message(
            ADMIN_ID,
            f"🆕 Нова заявка\nІм'я: {text}\nID: {uid}",
            reply_markup=kb
        )
        return await update.message.reply_text("✅ Ім'я отримано, очікуйте")
    
    # Проверка доступа
    if uid in BLOCKED_USERS:
        return await update.message.reply_text("⛔ Доступ заборонено")
    
    if uid not in NOTIFY_USERS and uid != ADMIN_ID:
        return await update.message.reply_text("⏳ Заявка розглядається")
    
    # Обработка кнопок
    today = datetime.now(tz).weekday()
    
    if text == "📅 Сьогодні":
        await show_day(update, today)
    elif text == "📆 Завтра":
        await show_day(update, (today + 1) % 7)
    elif text == "📋 Тиждень":
        await show_week(update)
    elif text == "⏭ Наступний урок":
        await next_lesson(update, today)
    elif text == "🔗 Посилання на урок":
        await show_links(update, today)
    elif text == "👑 Адмін панель" and uid == ADMIN_ID:
        await admin_panel(update)

async def show_day(update, day):
    lessons = SCHEDULE[day]
    if not lessons:
        return await update.message.reply_text(f"📅 {DAYS_UA[day]} – вихідний")
    
    text = f"📅 *{DAYS_UA[day]}*\n"
    for t, name, _ in lessons:
        text += f"⏰ {t} – {name}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def show_week(update):
    text = "📋 *Тиждень*\n\n"
    for day in range(5):
        lessons = SCHEDULE[day]
        if lessons:
            text += f"*{DAYS_UA[day]}:*\n"
            for t, name, _ in lessons:
                text += f"  ⏰ {t} – {name}\n"
            text += "\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def next_lesson(update, today):
    now = datetime.now(tz).strftime("%H:%M")
    
    # Сегодня
    for t, name, _ in SCHEDULE[today]:
        if t > now:
            return await update.message.reply_text(f"⏭ *Наступний урок:* {t} – {name}", parse_mode="Markdown")
    
    # Завтра
    tomorrow = (today + 1) % 7
    if SCHEDULE[tomorrow]:
        t, name, _ = SCHEDULE[tomorrow][0]
        return await update.message.reply_text(f"📅 Завтра перший урок: {t} – {name}")
    
    await update.message.reply_text("🎉 Уроків немає")

async def show_links(update, day):
    lessons = SCHEDULE[day]
    if not lessons:
        return await update.message.reply_text("📭 Сьогодні уроків немає")
    
    kb = []
    for i, (t, name, link) in enumerate(lessons):
        if link:
            kb.append([InlineKeyboardButton(f"{t} – {name}", callback_data=f"l_{day}_{i}")])
    
    if not kb:
        return await update.message.reply_text("🔗 Немає посилань")
    
    await update.message.reply_text("🔗 Оберіть урок:", reply_markup=InlineKeyboardMarkup(kb))

async def admin_panel(update):
    text = "👑 *Адмін панель*\n\n"
    
    if PENDING_USERS:
        text += "*⏳ Очікують:*\n"
        for p in PENDING_USERS:
            text += f"• {p['name']} (@{p['username']}) – `{p['id']}`\n"
        text += "\n"
    
    text += "*✅ Користувачі:*\n"
    for uid in NOTIFY_USERS:
        if uid == ADMIN_ID:
            continue
        name = USER_NAMES.get(str(uid), str(uid))
        username = USER_USERNAMES.get(str(uid), "")
        status = "🔴" if uid in BLOCKED_USERS else "🟢"
        text += f"{status} {name} (@{username}) – `{uid}`\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

# ========== КОЛБЭКИ ==========
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = update.effective_user.id
    
    # Подтверждение заявки
    if data.startswith("a_"):
        if uid != ADMIN_ID:
            return
        target = int(data[2:])
        for p in PENDING_USERS:
            if p['id'] == target:
                USER_NAMES[str(target)] = p['name']
                USER_USERNAMES[str(target)] = p['username']
                save_json(NAMES_FILE, USER_NAMES)
                save_json(USERNAMES_FILE, USER_USERNAMES)
                
                if target not in NOTIFY_USERS:
                    NOTIFY_USERS.append(target)
                    save_json(USERS_FILE, NOTIFY_USERS)
                
                PENDING_USERS.remove(p)
                save_json(PENDING_FILE, PENDING_USERS)
                
                await query.edit_message_text(f"✅ {p['name']} підтверджений")
                try:
                    await context.bot.send_message(target, "✅ Доступ надано! /start")
                except:
                    pass
                return
    
    # Отклонение
    if data.startswith("r_"):
        if uid != ADMIN_ID:
            return
        target = int(data[2:])
        for p in PENDING_USERS:
            if p['id'] == target:
                PENDING_USERS.remove(p)
                save_json(PENDING_FILE, PENDING_USERS)
                await query.edit_message_text(f"❌ {p['name']} відхилений")
                return
    
    # Ссылки
    if data.startswith("l_"):
        _, d, i = data.split("_")
        t, name, link = SCHEDULE[int(d)][int(i)]
        if link:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Відкрити Zoom", url=link)]])
            await query.edit_message_text(f"🔗 *{t} – {name}*", parse_mode="Markdown", reply_markup=kb)

# ========== УВЕДОМЛЕНИЯ ==========
async def notifier(context):
    job = context.job
    t, name, link = job.data
    
    for uid in NOTIFY_USERS:
        if uid in BLOCKED_USERS:
            continue
        
        text = f"⏰ *Почався урок:* {name}" if job.name == "start" else f"⏳ *За 5 хвилин:* {name}"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Приєднатися", url=link)]]) if link else None
        
        try:
            await context.bot.send_message(uid, text, parse_mode="Markdown", reply_markup=kb)
        except:
            pass

def schedule_jobs(app):
    for day, lessons in SCHEDULE.items():
        for t, name, link in lessons:
            h, m = map(int, t.split(':'))
            
            # За 5 минут
            rh, rm = (h, m-5) if m >= 5 else (h-1, m+55)
            if rh >= 0:
                app.job_queue.run_daily(notifier, time(rh, rm), days=(day,), data=(t, name, link), name="reminder")
            
            # Начало
            app.job_queue.run_daily(notifier, time(h, m), days=(day,), data=(t, name, link), name="start")
    
    logger.info("✅ Уроки заплановані")

# ========== ЗАПУСК ==========
def main():
    if not BOT_TOKEN:
        logger.error("❌ Нет токена")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(callback))
    
    schedule_jobs(app)
    
    logger.info("🚀 Бот запущен")
    app.run_polling()

# ========== FLASK ==========
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Бот работает"

def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    main()
