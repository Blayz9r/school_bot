import os
import json
import time
import threading
import requests
from datetime import datetime, timedelta
import pytz
from flask import Flask

# ========== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

if not BOT_TOKEN or not ADMIN_ID:
    print("❌ Ошибка: BOT_TOKEN и ADMIN_ID должны быть заданы в переменных окружения")
    exit(1)

# ========== НАСТРОЙКИ ==========
tz = pytz.timezone('Europe/Kiev')
allowed_users = [ADMIN_ID]

# ========== РАСПИСАНИЕ ==========
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
        ("11:00", "Біологія", "https://us05web.zoom.us/j/81300275025?pwd=xNzRsLtAf4TYeszH5yWAHMbutUCGbz.1"),
        ("12:00", "Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"),
        ("13:00", "Англійська", "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09"),
        ("14:00", "Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        ("15:00", "Українська література", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
    ],
    2: [  # Среда
        ("09:00", "Інформатика", "https://us05web.zoom.us/j/3778676851?pwd=llSnb5K3NkdhTaVbaWaiWOnhzQaNbT.1"),
        ("10:00", "Географія", "https://us05web.zoom.us/j/7372874110?pwd=MUJaQUJsOUNHYUowUkswcEoxV09IUT09&omn=85468090096"),
        ("11:00", "Зарубіжна література", "https://us04web.zoom.us/j/9721960165?pwd=yYQs8qczfNK9soiSgiSHFXOLXEi2al.1"),
        ("12:00", "Алгебра", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        ("13:00", "Мистецтво", "https://us05web.zoom.us/j/3669615047?pwd=bWFXY3lHcHZTYzBlS2Q2MitjaTY0Zz09"),
        ("14:00", "Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"),
        ("15:00", "Фізкультура", "https://us04web.zoom.us/j/9199278785?pwd=V"),
    ],
    3: [  # Четверг
        ("09:00", "Громадянська освіта", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        ("10:00", "Громадянська освіта", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        ("11:00", "Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        ("12:00", "Біологія", "https://us05web.zoom.us/j/81300275025?pwd=xNzRsLtAf4TYeszH5yWAHMbutUCGbz.1"),
        ("13:00", "Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        ("14:00", "Захист України", None),
        ("15:00", "Захист України", None),
    ],
    4: [  # Пятница
        ("09:00", "Хімія", "https://us04web.zoom.us/j/7430647043?pwd=CLpdFoqSVh0X1s79xVF1m8w4J4MjYo.1"),
        ("10:00", "Українська література", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1"),
        ("11:00", "Історія України", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
        ("12:00", "Алгебра", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1"),
        ("13:00", "Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1"),
        ("14:00", "Фізкультура", "https://us04web.zoom.us/j/9199278785?pwd=V"),
        ("15:00", "Історія України", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09"),
    ],
    5: [],  # Суббота
    6: [],  # Воскресенье
}

days_ua = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]

# ========== ФУНКЦИИ ОТПРАВКИ ==========
def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if keyboard:
        data["reply_markup"] = json.dumps(keyboard)
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def send_notification(lesson_name, lesson_link, notification_type):
    """Отправляет уведомление о уроке"""
    for uid in allowed_users:
        if notification_type == "reminder":
            text = f"⏳ *Через 5 минут:* {lesson_name}"
        else:
            text = f"⏰ *Урок начался:* {lesson_name}"
        
        keyboard = None
        if lesson_link:
            keyboard = {
                "inline_keyboard": [[
                    {"text": "🔗 Присоединиться", "url": lesson_link}
                ]]
            }
        send_message(uid, text, keyboard)

# ========== ПЛАНИРОВЩИК ==========
def check_lessons():
    """Проверяет каждую минуту, не пора ли отправить уведомление"""
    while True:
        try:
            now = datetime.now(tz)
            current_time = now.strftime("%H:%M")
            today = now.weekday()
            
            for t, name, link in schedule.get(today, []):
                # Проверяем начало урока
                if t == current_time:
                    send_notification(name, link, "start")
                    print(f"[{current_time}] Отправлено начало: {name}")
                
                # Проверяем за 5 минут до урока
                h, m = map(int, t.split(':'))
                reminder_time = (now.replace(hour=h, minute=m, second=0) - timedelta(minutes=5)).strftime("%H:%M")
                if reminder_time == current_time:
                    send_notification(name, link, "reminder")
                    print(f"[{current_time}] Отправлено напоминание: {name}")
        except Exception as e:
            print(f"Ошибка в планировщике: {e}")
        
        time.sleep(60)

# ========== ОБРАБОТКА КОМАНД ==========
def handle_updates():
    """Получает и обрабатывает обновления от Telegram"""
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"timeout": 30, "offset": offset}
            
            r = requests.get(url, params=params, timeout=35)
            updates = r.json().get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                
                if "message" not in update:
                    continue
                
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")
                
                # Проверка доступа
                if chat_id not in allowed_users:
                    send_message(chat_id, "❌ Доступ запрещен.")
                    continue
                
                today = datetime.now(tz).weekday()
                
                # Обработка команд
                if text == "/start":
                    keyboard = {
                        "keyboard": [
                            [{"text": "📅 Сьогодні"}, {"text": "📆 Завтра"}],
                            [{"text": "📋 Тиждень"}, {"text": "⏭ Наступний урок"}],
                            [{"text": "🔗 Посилання"}]
                        ],
                        "resize_keyboard": True
                    }
                    send_message(chat_id, "👋 Привет!", keyboard)
                    print(f"Пользователь {chat_id} запустил бота")
                
                elif text == "📅 Сьогодні":
                    show_day(chat_id, today)
                elif text == "📆 Завтра":
                    show_day(chat_id, (today + 1) % 7)
                elif text == "📋 Тиждень":
                    show_week(chat_id)
                elif text == "⏭ Наступний урок":
                    show_next_lesson(chat_id, today)
                elif text == "🔗 Посилання":
                    show_links(chat_id, today)
        
        except Exception as e:
            print(f"Ошибка в обработчике: {e}")
            time.sleep(5)

def show_day(chat_id, day):
    lessons = schedule.get(day, [])
    if not lessons:
        send_message(chat_id, f"📅 *{days_ua[day]}* – выходной")
        return
    
    text = f"📅 *{days_ua[day]}*\n"
    for t, name, _ in lessons:
        text += f"⏰ {t} – {name}\n"
    send_message(chat_id, text)

def show_week(chat_id):
    text = "📋 *Неделя*\n\n"
    for day in range(5):
        lessons = schedule.get(day, [])
        if lessons:
            text += f"*{days_ua[day]}:*\n"
            for t, name, _ in lessons:
                text += f"  ⏰ {t} – {name}\n"
            text += "\n"
    send_message(chat_id, text)

def show_next_lesson(chat_id, today):
    now = datetime.now(tz).strftime("%H:%M")
    for t, name, _ in schedule.get(today, []):
        if t > now:
            send_message(chat_id, f"⏭ *Следующий урок:* {t} – {name}")
            return
    tomorrow = (today + 1) % 7
    if schedule.get(tomorrow, []):
        t, name, _ = schedule[tomorrow][0]
        send_message(chat_id, f"📅 Завтра первый урок: {t} – {name}")
    else:
        send_message(chat_id, "🎉 Уроков нет")

def show_links(chat_id, day):
    lessons = schedule.get(day, [])
    if not lessons:
        send_message(chat_id, "📭 Сегодня уроков нет")
        return
    
    keyboard = {"inline_keyboard": []}
    for i, (t, name, link) in enumerate(lessons):
        if link:
            keyboard["inline_keyboard"].append([
                {"text": f"{t} – {name}", "callback_data": f"link_{day}_{i}"}
            ])
    
    if not keyboard["inline_keyboard"]:
        send_message(chat_id, "🔗 Сегодня нет ссылок")
        return
    
    send_message(chat_id, "🔗 Выбери урок:", keyboard)

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

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 Бот запускается...")
    print(f"🤖 Токен: {BOT_TOKEN[:10]}...")
    print(f"👤 Admin ID: {ADMIN_ID}")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask запущен на порту 10000")
    
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=check_lessons, daemon=True)
    scheduler_thread.start()
    print("⏰ Планировщик запущен")
    
    # Запускаем обработчик команд (главный поток)
    print("📨 Обработчик команд запущен")
    handle_updates()
