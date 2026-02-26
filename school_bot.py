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

# ID админа (твой)
ADMIN_ID = 1823742969

# Файлы для хранения данных
USERS_FILE = "users.json"              # ID пользователей
PENDING_FILE = "pending.json"          # Ожидающие подтверждения
USER_NAMES_FILE = "user_names.json"    # Имена пользователей
USER_USERNAMES_FILE = "user_usernames.json"  # Username'ы
BLOCKED_FILE = "blocked.json"          # Заблокированные

# Загрузка пользователей
def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей: {e}")
    return [ADMIN_ID]

def save_users(users):
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователей: {e}")

# Загрузка ожидающих
def load_pending():
    try:
        if os.path.exists(PENDING_FILE):
            with open(PENDING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки ожидающих: {e}")
    return []

def save_pending(pending):
    try:
        with open(PENDING_FILE, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения ожидающих: {e}")

# Загрузка имён пользователей
def load_user_names():
    try:
        if os.path.exists(USER_NAMES_FILE):
            with open(USER_NAMES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки имён: {e}")
    return {}

def save_user_names(names):
    try:
        with open(USER_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(names, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения имён: {e}")

# Загрузка username'ов
def load_user_usernames():
    try:
        if os.path.exists(USER_USERNAMES_FILE):
            with open(USER_USERNAMES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки username'ов: {e}")
    return {}

def save_user_usernames(usernames):
    try:
        with open(USER_USERNAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(usernames, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения username'ов: {e}")

# Загрузка заблокированных
def load_blocked():
    try:
        if os.path.exists(BLOCKED_FILE):
            with open(BLOCKED_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки блокированных: {e}")
    return []

def save_blocked(blocked):
    try:
        with open(BLOCKED_FILE, 'w', encoding='utf-8') as f:
            json.dump(blocked, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения блокированных: {e}")

# Загружаем все данные
NOTIFY_USERS = load_users()
PENDING_USERS = load_pending()
USER_NAMES = load_user_names()
USER_USERNAMES = load_user_usernames()
BLOCKED_USERS = load_blocked()

# Твоё полное расписание со ссылками
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

# Дни недели по-украински
DAYS_UA = {
    "monday": "Понеділок",
    "tuesday": "Вівторок",
    "wednesday": "Середа",
    "thursday": "Четвер",
    "friday": "П'ятниця",
    "saturday": "Субота",
    "sunday": "Неділя"
}

# Соответствие индекса datetime и ключа
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

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Если админ — сразу даём доступ
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👋 *Вітаю, адміністраторе!*\n\nЯ твій шкільний помічник. Обери дію нижче 👇",
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
        return
    
    # Если уже подтверждён — даём доступ
    if user_id in NOTIFY_USERS:
        await update.message.reply_text(
            "👋 *Вітаю!*\n\nЯ твій шкільний помічник. Обери дію нижче 👇",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return
    
    # Если в ожидании — сообщаем
    for pending in PENDING_USERS:
        if pending['user_id'] == user_id:
            await update.message.reply_text(
                "⏳ *Ваша заявка ще розглядається адміністратором.*\n\nОчікуйте, будь ласка.",
                parse_mode="Markdown"
            )
            return
    
    # Новый пользователь — просим имя
    context.user_data['awaiting_name'] = True
    await update.message.reply_text(
        "👋 *Доброго дня!*\n\n"
        "Будь ласка, напиши своє *ім'я та прізвище*, щоб адміністратор міг тебе ідентифікувати.\n\n"
        "_Наприклад: Іван Петренко_",
        parse_mode="Markdown"
    )

# ========== ОБРАБОТКА ТЕКСТА ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # Если ждём имя от нового пользователя
    if context.user_data.get('awaiting_name'):
        context.user_data['awaiting_name'] = False
        
        # Сохраняем в ожидающие
        PENDING_USERS.append({
            'user_id': user_id,
            'name': text,
            'username': update.effective_user.username or "",
            'date': datetime.now().isoformat()
        })
        save_pending(PENDING_USERS)
        
        # Уведомляем админа
        keyboard = [[
            InlineKeyboardButton("✅ Прийняти", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_{user_id}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🆕 *Нова заявка!*\n\n"
                 f"👤 *Ім'я:* {text}\n"
                 f"📱 *Username:* @{update.effective_user.username}\n"
                 f"🆔 *ID:* `{user_id}`",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        await update.message.reply_text(
            "✅ *Дякуємо!* Ваше ім'я отримано.\n\n"
            "⏳ Очікуйте на підтвердження адміністратора.",
            parse_mode="Markdown"
        )
        return
    
    # Проверка на блокировку
    if user_id in BLOCKED_USERS and user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Доступ заборонено.")
        return
    
    # Проверка на подтверждение
    if user_id not in NOTIFY_USERS and user_id != ADMIN_ID:
        await update.message.reply_text(
            "⏳ Ваша заявка ще розглядається. Очікуйте.",
            parse_mode="Markdown"
        )
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

# ========== ФУНКЦИИ РАСПИСАНИЯ ==========
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
                f"⏭ *Наступний урок сьогодні:*\n\n{lesson['time']} – {lesson['name']}",
                parse_mode="Markdown"
            )
            return
    
    tomorrow_idx = (today_idx + 1) % 7
    day_key = DAY_MAP[tomorrow_idx]
    if SCHEDULE[day_key]:
        lesson = SCHEDULE[day_key][0]
        await update.message.reply_text(
            f"📅 Сьогодні уроків більше немає.\n\n⏭ *Завтра перший урок:*\n{lesson['time']} – {lesson['name']}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("🎉 Найближчих уроків немає. Відпочивай!")

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
        await update.message.reply_text("🔗 Сьогодні немає уроків з посиланнями.")
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔗 Оберіть урок:", reply_markup=reply_markup)

# ========== АДМИН ПАНЕЛЬ ==========
async def show_admin_panel(update: Update):
    """Показывает список пользователей"""
    text = "👑 *Адмін панель*\n\n"
    
    # Ожидающие
    if PENDING_USERS:
        text += "*⏳ Очікують підтвердження:*\n"
        keyboard = []
        for pending in PENDING_USERS:
            name = pending['name']
            user_id = pending['user_id']
            username = pending['username']
            text += f"• {name} (@{username}) — `{user_id}`\n"
            keyboard.append([InlineKeyboardButton(
                f"✅ {name}", 
                callback_data=f"approve_{user_id}"
            )])
        text += "\n"
    
    # Подтверждённые
    text += "*✅ Підтверджені користувачі:*\n"
    keyboard = []
    for user_id in NOTIFY_USERS:
        if user_id != ADMIN_ID:
            name = USER_NAMES.get(str(user_id), "Невідомий")
            username = USER_USERNAMES.get(str(user_id), "")
            status = "🔴 Заблокований" if user_id in BLOCKED_USERS else "🟢 Активний"
            text += f"• {name} (@{username}) — `{user_id}` — {status}\n"
            keyboard.append([InlineKeyboardButton(
                f"⚙️ {name}", 
                callback_data=f"user_{user_id}"
            )])
    
    await update.message.reply_text(text, parse_mode="Markdown")

# ========== ОБРАБОТКА ИНЛАЙН-КНОПОК ==========
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    # Обработка подтверждения заявки
    if data.startswith("approve_"):
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ Тільки адмін може підтверджувати.")
            return
        
        target_id = int(data.split("_")[1])
        
        # Находим заявку
        for pending in PENDING_USERS:
            if pending['user_id'] == target_id:
                # Сохраняем имя и username
                USER_NAMES[str(target_id)] = pending['name']
                USER_USERNAMES[str(target_id)] = pending['username']
                save_user_names(USER_NAMES)
                save_user_usernames(USER_USERNAMES)
                
                # Добавляем в подтверждённые
                if target_id not in NOTIFY_USERS:
                    NOTIFY_USERS.append(target_id)
                    save_users(NOTIFY_USERS)
                
                # Удаляем из ожидающих
                PENDING_USERS.remove(pending)
                save_pending(PENDING_USERS)
                
                await query.edit_message_text(f"✅ Користувача *{pending['name']}* підтверджено!", parse_mode="Markdown")
                
                # Уведомляем пользователя
                try:
                    await context.bot.send_message(
                        chat_id=target_id,
                        text="✅ *Вітаю!* Адміністратор підтвердив вашу заявку.\n\n"
                             "Напишіть /start, щоб почати користуватись ботом.",
                        parse_mode="Markdown"
                    )
                except:
                    pass
                return
        
        await query.edit_message_text("❌ Заявку не знайдено.")
        return
    
    # Обработка отклонения заявки
    if data.startswith("reject_"):
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ Тільки адмін може відхиляти.")
            return
        
        target_id = int(data.split("_")[1])
        
        for pending in PENDING_USERS:
            if pending['user_id'] == target_id:
                PENDING_USERS.remove(pending)
                save_pending(PENDING_USERS)
                
                await query.edit_message_text(f"❌ Заявку *{pending['name']}* відхилено.", parse_mode="Markdown")
                
                # Уведомляем пользователя
                try:
                    await context.bot.send_message(
                        chat_id=target_id,
                        text="❌ *На жаль*, адміністратор відхилив вашу заявку.",
                        parse_mode="Markdown"
                    )
                except:
                    pass
                return
        
        await query.edit_message_text("❌ Заявку не знайдено.")
        return
    
    # Обработка ссылок на уроки
    if data.startswith("link_"):
        parts = data.split("_")
        day_idx = int(parts[1])
        lesson_idx = int(parts[2])
        
        day_key = DAY_MAP[day_idx]
        lesson = SCHEDULE[day_key][lesson_idx]
        
        if lesson['link']:
            keyboard = [[InlineKeyboardButton("🔗 Відкрити Zoom", url=lesson['link'])]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"🔗 *{lesson['time']} – {lesson['name']}*\n\nНатисни кнопку нижче, щоб приєднатися:",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(f"❌ Для уроку *{lesson['name']}* немає посилання.", parse_mode="Markdown")

# ========== ПЛАНИРОВЩИК УРОКОВ ==========
async def send_lesson_notification(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет уведомление о начале урока"""
    lesson_name = context.job.data['name']
    lesson_link = context.job.data['link']
    notification_type = context.job.data.get('type', 'start')
    
    for user_id in NOTIFY_USERS:
        if user_id in BLOCKED_USERS:
            continue
            
        if notification_type == 'reminder':
            text = f"⏳ *За 5 хвилин урок:* {lesson_name}"
        else:
            text = f"⏰ *Почався урок:* {lesson_name}"
        
        reply_markup = None
        if lesson_link:
            keyboard = [[InlineKeyboardButton("🔗 Приєднатися до Zoom", url=lesson_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text += "\n\nНатисни кнопку нижче, щоб приєднатися 👇"
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Ошибка отправки {user_id}: {e}")

def schedule_lessons(app: Application):
    """Планирует все уроки (за 5 минут и в начало)"""
    for day_key, lessons in SCHEDULE.items():
        day_num = list(DAY_MAP.keys())[list(DAY_MAP.values()).index(day_key)]
        
        for lesson in lessons:
            if not lesson['time']:
                continue
                
            hour, minute = map(int, lesson['time'].split(':'))
            
            # За 5 минут
            reminder_hour = hour
            reminder_minute = minute - 5
            if reminder_minute < 0:
                reminder_hour -= 1
                reminder_minute += 60
            
            reminder_time = time(hour=reminder_hour, minute=reminder_minute, second=0)
            reminder_job_data = {
                'name': lesson['name'],
                'link': lesson['link'],
                'type': 'reminder'
            }
            app.job_queue.run_daily(
                send_lesson_notification,
                time=reminder_time,
                days=(day_num,),
                data=reminder_job_data
            )
            
            # В начале
            start_time = time(hour=hour, minute=minute, second=0)
            start_job_data = {
                'name': lesson['name'],
                'link': lesson['link'],
                'type': 'start'
            }
            app.job_queue.run_daily(
                send_lesson_notification,
                time=start_time,
                days=(day_num,),
                data=start_job_data
            )
    
    logger.info(f"✅ Все уроки запланированы")

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
    
    logger.info(f"🚀 Бот запущен")
    app.run_polling()

# ========== ДЛЯ RENDER ==========
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    main()
