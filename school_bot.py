import logging
import os
import json
import threading
from datetime import datetime, time, timedelta
import pytz
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен из переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Часовой пояс (Киев)
tz = pytz.timezone('Europe/Kiev')

# ID админа
ADMIN_ID = 1823742969

# Файлы для хранения
USERS_FILE = "users.json"
PENDING_FILE = "pending.json"
USER_NAMES_FILE = "user_names.json"
USER_USERNAMES_FILE = "user_usernames.json"
BLOCKED_FILE = "blocked.json"

# ========== РАБОТА С ФАЙЛАМИ ==========
def load_json(file, default=None):
    try:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки {file}: {e}")
    return default if default is not None else []

def save_json(file, data):
    try:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения {file}: {e}")

# Загружаем все данные
NOTIFY_USERS = load_json(USERS_FILE, [ADMIN_ID])
PENDING_USERS = load_json(PENDING_FILE, [])
USER_NAMES = load_json(USER_NAMES_FILE, {})
USER_USERNAMES = load_json(USER_USERNAMES_FILE, {})
BLOCKED_USERS = load_json(BLOCKED_FILE, [])

# ========== РАСПИСАНИЕ ==========
SCHEDULE = {
    "monday": [
        {"time": "09:00", "name": "Хімія // Географія", "link": "https://us04web.zoom.us/j/7430647043?pwd=CLpdFoqSVh0X1s79xVF1m8w4J4MjYo.1"},
        {"time": "10:00", "name": "Англійська", "link": "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"},
        {"time": "11:00", "name": "Іноземна мова (англійська)", "link": "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"},
        {"time": "12:00", "name": "Українська мова", "link": "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"},
        {"time": "13:00", "name": "Всесвітня історія", "link": "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"},
        {"time": "14:00", "name": "Інформатика // Мистецтво", "link": "https://us05web.zoom.us/j/3778676851?pwd=llSnb5K3NkdhTaVbaWaiWOnhzQaNbT.1"},
        {"time": "15:00", "name": "Геометрія", "link": "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"},
    ],
    "tuesday": [
        {"time": "09:00", "name": "Алгебра", "link": "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"},
        {"time": "10:00", "name": "Українська мова", "link": "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"},
        {"time": "11:00", "name": "Біологія і екологія", "link": "https://us05web.zoom.us/j/81300275025?pwd=xNzRsLtAf4TYeszH5yWAHMbutUCGbz.1"},
        {"time": "12:00", "name": "Фізика", "link": "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"},
        {"time": "13:00", "name": "Іноземна мова (англійська)", "link": "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"},
        {"time": "14:00", "name": "Геометрія", "link": "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"},
        {"time": "15:00", "name": "Українська література", "link": "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"},
    ],
    "wednesday": [
        {"time": "09:00", "name": "Інформатика", "link": "https://us05web.zoom.us/j/3778676851?pwd=llSnb5K3NkdhTaVbaWaiWOnhzQaNbT.1"},
        {"time": "10:00", "name": "Географія", "link": "https://us05web.zoom.us/j/7372874110?pwd=MUJaQUJsOUNHYUowUkswcEoxV09IUT09&omn=85468090096"},
        {"time": "11:00", "name": "Зарубіжна література", "link": "https://us04web.zoom.us/j/9721960165?pwd=yYQs8qczfNK9soiSgiSHFXOLXEi2al.1"},
        {"time": "12:00", "name": "Алгебра і початки аналізу", "link": "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"},
        {"time": "13:00", "name": "Мистецтво", "link": "https://us05web.zoom.us/j/3669615047?pwd=bWFXY3lHcHZTYzBlS2Q2MitjaTY0Zz09"},
        {"time": "14:00", "name": "Фізика", "link": "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"},
        {"time": "15:00", "name": "Фізична культура", "link": "https://us04web.zoom.us/j/9199278785?pwd=V"},
    ],
    "thursday": [
        {"time": "09:00", "name": "Громадянська освіта", "link": "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"},
        {"time": "10:00", "name": "Громадянська освіта", "link": "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"},
        {"time": "11:00", "name": "Українська мова", "link": "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"},
        {"time": "12:00", "name": "Біологія і екологія", "link": "https://us05web.zoom.us/j/81300275025?pwd=xNzRsLtAf4TYeszH5yWAHMbutUCGbz.1"},
        {"time": "13:00", "name": "Геометрія", "link": "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"},
        {"time": "14:00", "name": "Захист України", "link": None},
        {"time": "15:00", "name": "Захист України", "link": None},
    ],
    "friday": [
        {"time": "09:00", "name": "Хімія", "link": "https://us04web.zoom.us/j/7430647043?pwd=CLpdFoqSVh0X1s79xVF1m8w4J4MjYo.1"},
        {"time": "10:00", "name": "Українська література", "link": "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"},
        {"time": "11:00", "name": "Історія України", "link": "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"},
        {"time": "12:00", "name": "Алгебра і початки аналізу", "link": "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"},
        {"time": "13:00", "name": "Фізика", "link": "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"},
        {"time": "14:00", "name": "Фізична культура", "link": "https://us04web.zoom.us/j/9199278785?pwd=V"},
        {"time": "15:00", "name": "Історія України", "link": "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"},
    ],
    "saturday": [],
    "sunday": []
}

# Дни недели
DAYS_UA = {
    "monday": "Понеділок",
    "tuesday": "Вівторок",
    "wednesday": "Середа",
    "thursday": "Четвер",
    "friday": "П'ятниця",
    "saturday": "Субота",
    "sunday": "Неділя"
}

DAY_MAP = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday"
}

# ========== КЛАВИАТУРЫ ==========
def main_keyboard():
    keyboard = [
        [KeyboardButton("📅 Сьогодні"), KeyboardButton("📆 Завтра")],
        [KeyboardButton("📋 Тиждень"), KeyboardButton("⏭ Наступний урок")],
        [KeyboardButton("🔗 Посилання на урок")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_keyboard():
    keyboard = [
        [KeyboardButton("📅 Сьогодні"), KeyboardButton("📆 Завтра")],
        [KeyboardButton("📋 Тиждень"), KeyboardButton("⏭ Наступний урок")],
        [KeyboardButton("🔗 Посилання на урок")],
        [KeyboardButton("👑 Адмін панель")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Админ
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👋 *Вітаю, адміністраторе!*",
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
        return
    
    # Уже подтверждён
    if user_id in NOTIFY_USERS:
        await update.message.reply_text(
            "👋 *Вітаю!*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return
    
    # В ожидании
    for p in PENDING_USERS:
        if p['user_id'] == user_id:
            await update.message.reply_text("⏳ Ваша заявка розглядається.")
            return
    
    # Новый пользователь
    context.user_data['awaiting_name'] = True
    await update.message.reply_text(
        "👋 *Доброго дня!*\n\nНапишіть своє ім'я та прізвище:",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # Если ждём имя
    if context.user_data.get('awaiting_name'):
        context.user_data['awaiting_name'] = False
        
        # Сохраняем в ожидающие
        PENDING_USERS.append({
            'user_id': user_id,
            'name': text,
            'username': update.effective_user.username or "",
            'date': datetime.now().isoformat()
        })
        save_json(PENDING_FILE, PENDING_USERS)
        
        # Уведомляем админа
        keyboard = [[
            InlineKeyboardButton("✅ Прийняти", callback_data=f"approve_{user_id}"),
            InKeyboardButton("❌ Відхилити", callback_data=f"reject_{user_id}")
        ]]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🆕 *Нова заявка*\n\nІм'я: {text}\nID: `{user_id}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        await update.message.reply_text("✅ Ім'я отримано. Очікуйте підтвердження.")
        return
    
    # Проверка доступа
    if user_id in BLOCKED_USERS:
        await update.message.reply_text("⛔ Доступ заборонено.")
        return
    
    if user_id not in NOTIFY_USERS and user_id != ADMIN_ID:
        await update.message.reply_text("⏳ Ваша заявка розглядається.")
        return
    
    # Обработка кнопок
    today_idx = datetime.now(tz).weekday()
    
    if text == "📅 Сьогодні":
        await show_day(update, today_idx)
    elif text == "📆 Завтра":
        await show_day(update, (today_idx + 1) % 7)
    elif text == "📋 Тиждень":
        await show_week(update)
    elif text == "⏭ Наступний урок":
        await next_lesson(update, today_idx)
    elif text == "🔗 Посилання на урок":
        await show_links_keyboard(update, today_idx)
    elif text == "👑 Адмін панель" and user_id == ADMIN_ID:
        await show_admin_panel(update)

async def show_day(update: Update, day_idx: int):
    day_key = DAY_MAP[day_idx]
    lessons = SCHEDULE[day_key]
    day_name = DAYS_UA[day_key]
    
    if not lessons:
        await update.message.reply_text(f"📅 *{day_name}* – вихідний 🎉", parse_mode="Markdown")
        return
    
    text = f"📅 *{day_name}*\n"
    for lesson in lessons:
        text += f"⏰ {lesson['time']} – {lesson['name']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def show_week(update: Update):
    text = "📋 *Розклад на тиждень*\n\n"
    for day_key, day_name in DAYS_UA.items():
        lessons = SCHEDULE[day_key]
        if lessons:
            text += f"*{day_name}:*\n"
            for lesson in lessons:
                text += f"  ⏰ {lesson['time']} – {lesson['name']}\n"
            text += "\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def next_lesson(update: Update, today_idx: int):
    now = datetime.now(tz)
    current_time = now.strftime("%H:%M")
    
    day_key = DAY_MAP[today_idx]
    for lesson in SCHEDULE[day_key]:
        if lesson['time'] > current_time:
            await update.message.reply_text(
                f"⏭ *Наступний урок сьогодні:*\n{lesson['time']} – {lesson['name']}",
                parse_mode="Markdown"
            )
            return
    
    tomorrow_idx = (today_idx + 1) % 7
    day_key = DAY_MAP[tomorrow_idx]
    if SCHEDULE[day_key]:
        lesson = SCHEDULE[day_key][0]
        await update.message.reply_text(
            f"📅 Сьогодні уроків немає.\n\n⏭ *Завтра перший урок:*\n{lesson['time']} – {lesson['name']}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("🎉 Вихідний")

async def show_links_keyboard(update: Update, day_idx: int):
    day_key = DAY_MAP[day_idx]
    lessons = SCHEDULE[day_key]
    
    if not lessons:
        await update.message.reply_text("📭 Сьогодні уроків немає.")
        return
    
    keyboard = []
    for i, lesson in enumerate(lessons):
        if lesson['link']:
            keyboard.append([InlineKeyboardButton(
                f"{lesson['time']} – {lesson['name']}", 
                callback_data=f"link_{day_idx}_{i}"
            )])
    
    if not keyboard:
        await update.message.reply_text("🔗 Немає уроків з посиланнями.")
        return
    
    await update.message.reply_text(
        "🔗 Оберіть урок:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_admin_panel(update: Update):
    text = "👑 *Адмін панель*\n\n"
    
    if PENDING_USERS:
        text += "*⏳ Очікують:*\n"
        for p in PENDING_USERS:
            text += f"• {p['name']} (@{p['username']}) — `{p['user_id']}`\n"
        text += "\n"
    
    text += "*✅ Підтверджені:*\n"
    for uid in NOTIFY_USERS:
        if uid != ADMIN_ID:
            name = USER_NAMES.get(str(uid), str(uid))
            username = USER_USERNAMES.get(str(uid), "")
            status = "🔴" if uid in BLOCKED_USERS else "🟢"
            text += f"{status} {name} (@{username}) — `{uid}`\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

# ========== ОБРАБОТКА ИНЛАЙН-КНОПОК ==========
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    # Подтверждение заявки
    if data.startswith("approve_"):
        if user_id != ADMIN_ID:
            return
        
        target_id = int(data.split("_")[1])
        for p in PENDING_USERS:
            if p['user_id'] == target_id:
                USER_NAMES[str(target_id)] = p['name']
                USER_USERNAMES[str(target_id)] = p['username']
                save_json(USER_NAMES_FILE, USER_NAMES)
                save_json(USER_USERNAMES_FILE, USER_USERNAMES)
                
                if target_id not in NOTIFY_USERS:
                    NOTIFY_USERS.append(target_id)
                    save_json(USERS_FILE, NOTIFY_USERS)
                
                PENDING_USERS.remove(p)
                save_json(PENDING_FILE, PENDING_USERS)
                
                await query.edit_message_text(f"✅ {p['name']} підтверджений!")
                
                try:
                    await context.bot.send_message(
                        target_id,
                        "✅ *Вітаю!* Адміністратор підтвердив вашу заявку.\nНапишіть /start"
                    )
                except:
                    pass
                return
    
    # Отклонение заявки
    if data.startswith("reject_"):
        if user_id != ADMIN_ID:
            return
        
        target_id = int(data.split("_")[1])
        for p in PENDING_USERS:
            if p['user_id'] == target_id:
                PENDING_USERS.remove(p)
                save_json(PENDING_FILE, PENDING_USERS)
                await query.edit_message_text(f"❌ {p['name']} відхилений!")
                return
    
    # Ссылки на уроки
    if data.startswith("link_"):
        parts = data.split("_")
        day_idx = int(parts[1])
        lesson_idx = int(parts[2])
        
        lesson = SCHEDULE[DAY_MAP[day_idx]][lesson_idx]
        if lesson['link']:
            keyboard = [[InlineKeyboardButton("🔗 Відкрити Zoom", url=lesson['link'])]]
            await query.edit_message_text(
                f"🔗 *{lesson['time']} – {lesson['name']}*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

# ========== ПЛАНИРОВЩИК ==========
async def send_lesson_notification(context: ContextTypes.DEFAULT_TYPE):
    lesson = context.job.data
    for uid in NOTIFY_USERS:
        if uid in BLOCKED_USERS:
            continue
        
        text = f"⏰ *Почався урок:* {lesson['name']}" if lesson['type'] == 'start' else f"⏳ *За 5 хвилин:* {lesson['name']}"
        
        reply_markup = None
        if lesson['link']:
            reply_markup = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔗 Приєднатися", url=lesson['link'])
            ]])
        
        try:
            await context.bot.send_message(uid, text, parse_mode="Markdown", reply_markup=reply_markup)
        except:
            pass

def schedule_lessons(app):
    for day_key, lessons in SCHEDULE.items():
        day_num = list(DAY_MAP.keys())[list(DAY_MAP.values()).index(day_key)]
        
        for lesson in lessons:
            if not lesson['time']:
                continue
            
            h, m = map(int, lesson['time'].split(':'))
            
            # За 5 минут
            rh, rm = (h, m-5) if m>=5 else (h-1, m+55)
            if rh >= 0:
                app.job_queue.run_daily(
                    send_lesson_notification,
                    time=time(rh, rm),
                    days=(day_num,),
                    data={**lesson, 'type': 'reminder'}
                )
            
            # Начало
            app.job_queue.run_daily(
                send_lesson_notification,
                time=time(h, m),
                days=(day_num,),
                data={**lesson, 'type': 'start'}
            )
    
    logger.info("✅ Уроки заплановані")

# ========== ЗАПУСК ==========
def main():
    if not BOT_TOKEN:
        logger.error("❌ Токен не найден")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    schedule_lessons(app)
    
    logger.info("🚀 Бот запущен")
    app.run_polling()

# ========== FLASK ДЛЯ RENDER ==========
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    main()
