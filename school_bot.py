import json
import logging
import time
import os
import threading
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

# ========== НАЛАШТУВАННЯ ЛОГУВАННЯ ==========
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__))

# ========== КОНСТАНТИ ==========
TIMEZONE = timezone("Europe/Kiev")
CONFIG_FILE = "config.json"
PENDING_FILE = "pending.json"
APPROVED_FILE = "approved.json"
HOLIDAYS_FILE = "holidays.json"

# ========== РОБОТА З ФАЙЛАМИ ==========
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

def save_json(file: Path, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Завантажуємо конфігурацію з файлу (якщо він є)
config = load_json(Path(CONFIG_FILE), {"token": "", "admin_id": 0})

# Пріоритет: змінні оточення (на Render) -> файл config.json (локально)
BOT_TOKEN = os.environ.get("BOT_TOKEN") or config.get("token")
ADMIN_ID = int(os.environ.get("ADMIN_ID") or config.get("admin_id", 0))

if not BOT_TOKEN:
    raise ValueError("❌ Токен не знайдено! Вкажи його в config.json або в змінній оточення BOT_TOKEN")

# Завантажуємо списки
approved_users = load_json(Path(APPROVED_FILE), [])
holidays = load_json(Path(HOLIDAYS_FILE), {})

# ========== РОЗКЛАД УРОКІВ ІЗ ТВОЇМИ ПОСИЛАННЯМИ ==========
schedule = {
    0: [  # Понеділок
        (dt_time(9, 0),   "📚 Хімія // Географія", "https://us04web.zoom.us/j/7430647043?pwd=CLpdFoqSVh0X1s79xVF1m8w4J4MjYo.1"),
        (dt_time(10, 0),  "🇬🇧 Англійська", "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"),
        (dt_time(11, 0),  "🇬🇧 Іноземна мова (англійська)", "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"),
        (dt_time(12, 0),  "📖 Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        (dt_time(13, 0),  "🌍 Всесвітня історія", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        (dt_time(14, 0),  "💻 Інформатика // Мистецтво", "https://us05web.zoom.us/j/3778676851?pwd=llSnb5K3NkdhTaVbaWaiWOnhzQaNbT.1"),
        (dt_time(15, 0),  "📐 Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
    ],
    1: [  # Вівторок
        (dt_time(9, 0),   "🧮 Алгебра", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        (dt_time(10, 0),  "📖 Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        (dt_time(11, 0),  "🧬 Біологія і екологія", "https://us05web.zoom.us/j/81300275025?pwd=xNzRsLtAf4TYeszH5yWAHMbutUCGbz.1"),
        (dt_time(12, 0),  "⚛ Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"),
        (dt_time(13, 0),  "🇬🇧 Іноземна мова (англійська)", "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"),
        (dt_time(14, 0),  "📐 Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        (dt_time(15, 0),  "📚 Українська література", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
    ],
    2: [  # Середа
        (dt_time(9, 0),   "💻 Інформатика", "https://us05web.zoom.us/j/3778676851?pwd=llSnb5K3NkdhTaVbaWaiWOnhzQaNbT.1"),
        (dt_time(10, 0),  "🌏 Географія", "https://us05web.zoom.us/j/7372874110?pwd=MUJaQUJsOUNHYUowUkswcEoxV09IUT09&omn=85468090096"),
        (dt_time(11, 0),  "📖 Зарубіжна література", "https://us04web.zoom.us/j/9721960165?pwd=yYQs8qczfNK9soiSgiSHFXOLXEi2al.1"),
        (dt_time(12, 0),  "🧮 Алгебра і початки аналізу", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        (dt_time(13, 0),  "🎨 Мистецтво", "https://us05web.zoom.us/j/3669615047?pwd=bWFXY3lHcHZTYzBlS2Q2MitjaTY0Zz09"),
        (dt_time(14, 0),  "⚛ Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"),
        (dt_time(15, 0),  "🏃 Фізична культура", "https://us04web.zoom.us/j/9199278785?pwd=V"),
    ],
    3: [  # Четвер
        (dt_time(9, 0),   "🏛 Громадянська освіта", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        (dt_time(10, 0),  "🏛 Громадянська освіта", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        (dt_time(11, 0),  "📖 Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        (dt_time(12, 0),  "🧬 Біологія і екологія", "https://us05web.zoom.us/j/81300275025?pwd=xNzRsLtAf4TYeszH5yWAHMbutUCGbz.1"),
        (dt_time(13, 0),  "📐 Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        (dt_time(14, 0),  "🛡 Захист України", None),
        (dt_time(15, 0),  "🛡 Захист України", None),
    ],
    4: [  # П'ятниця
        (dt_time(9, 0),   "📚 Хімія", "https://us04web.zoom.us/j/7430647043?pwd=CLpdFoqSVh0X1s79xVF1m8w4J4MjYo.1"),
        (dt_time(10, 0),  "📚 Українська література", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        (dt_time(11, 0),  "📜 Історія України", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        (dt_time(12, 0),  "🧮 Алгебра і початки аналізу", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        (dt_time(13, 0),  "⚛ Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"),
        (dt_time(14, 0),  "🏃 Фізична культура", "https://us04web.zoom.us/j/9199278785?pwd=V"),
        (dt_time(15, 0),  "📜 Історія України", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
    ],
    5: [],  # Субота
    6: [],  # Неділя
}

# ========== ДОПОМІЖНІ ФУНКЦІЇ ==========
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def is_approved(user_id: int) -> bool:
    return user_id in approved_users

def add_to_pending(user_id: int, real_name: str, tg_first_name: str, username: str = ""):
    pending = load_json(Path(PENDING_FILE), [])
    if is_approved(user_id):
        return False
    for p in pending:
        if p["user_id"] == user_id:
            return False
    pending.append({
        "user_id": user_id,
        "real_name": real_name,
        "tg_first_name": tg_first_name,
        "username": username,
        "date": datetime.now().isoformat()
    })
    save_json(Path(PENDING_FILE), pending)
    return True

def approve_user(user_id: int):
    global approved_users
    pending = load_json(Path(PENDING_FILE), [])
    pending = [p for p in pending if p["user_id"] != user_id]
    save_json(Path(PENDING_FILE), pending)
    if user_id not in approved_users:
        approved_users.append(user_id)
        save_json(Path(APPROVED_FILE), approved_users)

def reject_user(user_id: int):
    pending = load_json(Path(PENDING_FILE), [])
    pending = [p for p in pending if p["user_id"] != user_id]
    save_json(Path(PENDING_FILE), pending)

def set_holiday(user_id: int, days: int):
    holiday_end = date.today() + timedelta(days=days)
    holidays[str(user_id)] = holiday_end.isoformat()
    save_json(Path(HOLIDAYS_FILE), holidays)

def clear_holiday(user_id: int):
    if str(user_id) in holidays:
        del holidays[str(user_id)]
        save_json(Path(HOLIDAYS_FILE), holidays)

def is_on_holiday(user_id: int) -> bool:
    end_str = holidays.get(str(user_id))
    if not end_str:
        return False
    end_date = date.fromisoformat(end_str)
    return date.today() <= end_date

# ========== ЗАХИСТ ВІД ФЛУДУ ==========
user_last_command = {}
def rate_limit(seconds=3):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            now = time.time()
            last = user_last_command.get(user_id, 0)
            if now - last < seconds:
                await update.message.reply_text(
                    f"⏳ *Зачекайте {seconds} секунд* між командами.",
                    parse_mode="Markdown"
                )
                return
            user_last_command[user_id] = now
            return await func(update, context)
        return wrapper
    return decorator

# ========== КЛАВІАТУРИ ==========
def get_main_reply_keyboard():
    keyboard = [
        [KeyboardButton("📅 Розклад на сьогодні")],
        [KeyboardButton("📆 Розклад на завтра")],
        [KeyboardButton("⏭ Наступний урок")],
        [KeyboardButton("🏖 Канікули")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== ОБРОБНИКИ КОМАНД ==========
@rate_limit(3)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if is_admin(user_id):
        await update.message.reply_text(
            "👋 *Вітаю, адміністраторе!*\n\n"
            "Використовуйте /admin для керування заявками.",
            parse_mode="Markdown"
        )
        return

    if is_approved(user_id):
        await update.message.reply_text(
            f"👋 *Вітаю, {user.first_name}!*\n\n"
            "Обери дію за допомогою кнопок нижче 👇",
            parse_mode="Markdown",
            reply_markup=get_main_reply_keyboard()
        )
        return

    context.user_data['awaiting_name'] = True
    await update.message.reply_text(
        "👋 *Доброго дня!*\n\n"
        "Будь ласка, напиши своє *ім'я та прізвище* (наприклад, `Іван Петренко`), "
        "щоб адміністратор міг тебе ідентифікувати.\n\n"
        "_Це потрібно для безпеки та підтвердження доступу до розкладу._",
        parse_mode="Markdown"
    )

@rate_limit(3)
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "⛔ *Доступ заборонено!*",
            parse_mode="Markdown"
        )
        return

    pending = load_json(Path(PENDING_FILE), [])
    if not pending:
        await update.message.reply_text(
            "📭 *Немає нових заявок.*",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        "📋 *Список охочих приєднатися:*\n",
        parse_mode="Markdown"
    )

    for p in pending:
        user_id = p["user_id"]
        real_name = p["real_name"]
        tg_name = p["tg_first_name"]
        username = p.get("username", "")
        date_str = p.get("date", "")[:10]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Прийняти", callback_data=f"approve_{user_id}"),
             InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_{user_id}")]
        ])
        await update.message.reply_text(
            f"🆔 *ID:* `{user_id}`\n"
            f"👤 *Введене ім'я:* {real_name}\n"
            f"📱 *Telegram ім'я:* {tg_name}\n"
            f"🔗 *Username:* @{username}\n"
            f"📅 *Дата заявки:* {date_str}",
            parse_mode="Markdown",
            reply_markup=kb
        )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_approved(user_id) and not is_admin(user_id):
        await update.message.reply_text(
            "❌ Спочатку напиши /start для реєстрації.",
            parse_mode="Markdown"
        )
        return
    await update.message.reply_text(
        "📋 *Головне меню:*\nОберіть дію нижче 👇",
        parse_mode="Markdown",
        reply_markup=get_main_reply_keyboard()
    )

# ========== ОБРОБНИК ТЕКСТОВИХ ПОВІДОМЛЕНЬ ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text

    # Якщо очікуємо введення імені
    if context.user_data.get('awaiting_name'):
        context.user_data['awaiting_name'] = False

        added = add_to_pending(
            user_id=user_id,
            real_name=text.strip(),
            tg_first_name=user.first_name,
            username=user.username or ""
        )

        if added:
            # Сповістити адміністратора
            if ADMIN_ID:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Прийняти", callback_data=f"approve_{user_id}"),
                     InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_{user_id}")]
                ])
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🆕 *Нова заявка на приєднання!*\n\n"
                         f"👤 *Введене ім'я:* {text}\n"
                         f"📱 *Telegram ім'я:* {user.first_name}\n"
                         f"🔗 *Username:* @{user.username}\n"
                         f"🆔 *ID:* `{user_id}`",
                    parse_mode="Markdown",
                    reply_markup=kb
                )
            await update.message.reply_text(
                "✅ *Дякуємо!* Ваше ім'я отримано.\n\n"
                "⏳ Очікуйте на підтвердження адміністратора. "
                "Про результат ми повідомимо окремо.",
                parse_mode="Markdown"
            )
        else:
            if is_approved(user_id):
                await update.message.reply_text(
                    "👋 Ви вже *підтверджений учень*! Напишіть /start для доступу.",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    "⏳ Ваша заявка вже *на розгляді*. Очікуйте, будь ласка.",
                    parse_mode="Markdown"
                )
        return

    # Якщо не очікуємо імені, але користувач не підтверджений – нагадаємо про /start
    if not is_approved(user_id) and not is_admin(user_id):
        await update.message.reply_text(
            "❌ Спочатку напиши /start для реєстрації.",
            parse_mode="Markdown"
        )
        return

    # Обробка кнопок меню
    if text == "📅 Розклад на сьогодні":
        await show_today_schedule(update, context)
    elif text == "📆 Розклад на завтра":
        await show_tomorrow_schedule(update, context)
    elif text == "⏭ Наступний урок":
        await show_next_lesson(update, context)
    elif text == "🏖 Канікули":
        await show_holiday_menu(update, context)

async def show_today_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weekday = datetime.now(TIMEZONE).weekday()
    text = get_schedule_for_day(weekday)
    await update.message.reply_text(text, parse_mode="Markdown")

async def show_tomorrow_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tomorrow = datetime.now(TIMEZONE) + timedelta(days=1)
    weekday = tomorrow.weekday()
    text = get_schedule_for_day(weekday)
    await update.message.reply_text(text, parse_mode="Markdown")

async def show_next_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)
    today_weekday = now.weekday()
    current_time = now.time()

    lessons_today = schedule.get(today_weekday, [])
    next_lesson = None
    for t, name, link in lessons_today:
        if t > current_time:
            next_lesson = (t, name, link)
            break

    if next_lesson:
        t, name, link = next_lesson
        text = f"⏭ *Наступний урок сьогодні:*\n\n⏰ {t.strftime('%H:%M')} – {name}"
    else:
        tomorrow_weekday = (today_weekday + 1) % 7
        lessons_tomorrow = schedule.get(tomorrow_weekday, [])
        if lessons_tomorrow:
            t, name, link = lessons_tomorrow[0]
            text = f"📅 На сьогодні уроків більше немає.\n\n⏭ *Завтра перший урок:*\n⏰ {t.strftime('%H:%M')} – {name}"
        else:
            text = "🎉 Найближчих уроків немає (можливо, вихідні). Відпочивай!"

    await update.message.reply_text(text, parse_mode="Markdown")

async def show_holiday_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏖 7 днів", callback_data="holiday_7")],
        [InlineKeyboardButton("🏖 14 днів", callback_data="holiday_14")],
        [InlineKeyboardButton("❌ Скасувати канікули", callback_data="holiday_end")],
    ])
    await update.message.reply_text(
        "🏖 *Встановлення канікул*\n\n"
        "Оберіть тривалість канікул (нагадування будуть призупинені):",
        parse_mode="Markdown",
        reply_markup=kb
    )

def get_schedule_for_day(weekday: int) -> str:
    days_ua = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]
    lessons = schedule.get(weekday, [])
    if not lessons:
        return f"📅 *{days_ua[weekday]}* – вихідний або уроків немає. 🎉"
    lines = [f"📅 *{days_ua[weekday]}*"]
    for t, name, link in lessons:
        lines.append(f"⏰ {t.strftime('%H:%M')} – {name}")
    return "\n".join(lines)

# ========== ОБРОБНИК INLINE-КНОПОК ==========
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # Кнопки адміна (прийняти/відхилити)
    if data.startswith("approve_"):
        if not is_admin(user_id):
            await query.edit_message_text(
                "⛔ *Недостатньо прав!*",
                parse_mode="Markdown"
            )
            return
        target_id = int(data.split("_")[1])
        approve_user(target_id)
        await query.edit_message_text(
            f"✅ *Користувача з ID {target_id} прийнято!*",
            parse_mode="Markdown"
        )
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="✅ *Вітаю!* Адміністратор підтвердив вашу заявку.\n\n"
                     "Тепер ви можете користуватись ботом. Напишіть /start, щоб побачити меню.",
                parse_mode="Markdown"
            )
        except Exception:
            pass
        return

    if data.startswith("reject_"):
        if not is_admin(user_id):
            await query.edit_message_text(
                "⛔ *Недостатньо прав!*",
                parse_mode="Markdown"
            )
            return
        target_id = int(data.split("_")[1])
        reject_user(target_id)
        await query.edit_message_text(
            f"❌ *Користувача з ID {target_id} відхилено.*",
            parse_mode="Markdown"
        )
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="❌ *На жаль*, адміністратор відхилив вашу заявку.",
                parse_mode="Markdown"
            )
        except Exception:
            pass
        return

    # Канікули (доступно тільки підтвердженим або адміну)
    if not is_approved(user_id) and not is_admin(user_id):
        await query.edit_message_text(
            "⛔ *У вас немає доступу!*",
            parse_mode="Markdown"
        )
        return

    if data.startswith("holiday_"):
        if data == "holiday_7":
            set_holiday(user_id, 7)
            await query.edit_message_text(
                "🏖 *Канікули встановлено на 7 днів!*\n\n"
                "Нагадування про уроки не надходитимуть.",
                parse_mode="Markdown"
            )
        elif data == "holiday_14":
            set_holiday(user_id, 14)
            await query.edit_message_text(
                "🏖 *Канікули встановлено на 14 днів!*\n\n"
                "Нагадування про уроки не надходитимуть.",
                parse_mode="Markdown"
            )
        elif data == "holiday_end":
            clear_holiday(user_id)
            await query.edit_message_text(
                "✅ *Канікули скасовано!*\n\n"
                "Нагадування відновлено.",
                parse_mode="Markdown"
            )
        return

# ========== ПЛАНУВАЛЬНИК УРОКІВ (НАГАДУВАННЯ) ==========
async def send_lesson_notification(context: ContextTypes.DEFAULT_TYPE):
    """Надсилає гарне нагадування про урок із кнопкою для приєднання."""
    job = context.job
    lesson_time, lesson_name, lesson_link = job.data

    for uid in approved_users:
        if is_on_holiday(uid):
            continue

        # Формуємо гарне повідомлення
        message_text = (
            f"⏰ *Почався урок!*\n\n"
            f"📚 *{lesson_name}*\n\n"
            f"Час: {lesson_time.strftime('%H:%M')}"
        )

        reply_markup = None
        if lesson_link:
            keyboard = [[InlineKeyboardButton("🔗 Приєднатися до уроку", url=lesson_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message_text += "\n\nНатисни кнопку нижче, щоб приєднатися 👇"

        try:
            await context.bot.send_message(
                chat_id=uid,
                text=message_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Не вдалося надіслати сповіщення користувачу {uid}: {e}")

def schedule_all_lessons(app: Application):
    """Планує всі уроки."""
    for day, lessons in schedule.items():
        for lesson_time, lesson_name, lesson_link in lessons:
            tz_time = dt_time(hour=lesson_time.hour, minute=lesson_time.minute, tzinfo=TIMEZONE)
            app.job_queue.run_daily(
                send_lesson_notification,
                time=tz_time,
                days=(day,),
                data=(lesson_time, lesson_name, lesson_link)
            )
    logger.info("✅ Усі уроки заплановано.")

# ========== ОСНОВНА ФУНКЦІЯ ЗАПУСКУ БОТА ==========
def main():
    if not BOT_TOKEN:
        logger.error("❌ Токен не задано. Заповніть config.json або змінні оточення")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Команди
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("menu", menu_command))

    # Обробник текстових повідомлень (має бути після команд)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Інлайн-кнопки
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Планування уроків
    schedule_all_lessons(app)

    logger.info("🚀 Бот успішно запущено!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

# ========== ДЛЯ ХОСТИНГУ НА RENDER ==========
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Бот працює!"

@flask_app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

def run_bot():
    print("🟢 Запускаю поток бота...")
    main()

if __name__ == "__main__":
    # Запускаємо Flask в окремому потоці (демон, щоб закривався разом із ботом)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    # Запускаємо бота в головному потоці
    run_bot()

