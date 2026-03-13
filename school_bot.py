import os
import json
import time
import threading
import requests
from datetime import datetime, timedelta
import pytz
from flask import Flask

# ========== УНИВЕРСАЛЬНЫЙ ЗАГРУЗЧИК КОНФИГА ==========
BOT_TOKEN = None
allowed_users = []

# Сначала пробуем взять из переменных окружения (Render)
if os.environ.get("BOT_TOKEN"):
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    admin_ids_str = os.environ.get("ADMIN_IDS", "")
    if admin_ids_str:
        allowed_users = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
    print("✅ Загружено из переменных окружения (Render)")

# Если не получилось — пробуем из config.json (локально)
if not BOT_TOKEN or not allowed_users:
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            BOT_TOKEN = config.get('token')
            if 'admin_ids' in config:
                allowed_users = config['admin_ids']
            elif 'admin_id' in config:
                allowed_users = [config['admin_id']]
        print("✅ Загружено из config.json (локально)")
    except FileNotFoundError:
        print("❌ Файл config.json не найден")
    except Exception as e:
        print(f"❌ Ошибка загрузки config.json: {e}")

if not BOT_TOKEN:
    print("❌ Ошибка: BOT_TOKEN не найден")
    exit(1)

if not allowed_users:
    print("❌ Ошибка: Не указаны ID пользователей")
    exit(1)

print(f"🤖 Токен: {BOT_TOKEN[:10]}...")
print(f"👤 Разрешённые пользователи: {allowed_users}")

# ========== НАСТРОЙКИ ==========
tz = pytz.timezone('Europe/Kiev')

# Файл для хранения настроек пользователей (важные уроки или нет)
SETTINGS_FILE = "user_settings.json"

def load_user_settings():
    """Загружает настройки пользователей из файла"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки настроек: {e}")
    return {}

def save_user_settings(settings):
    """Сохраняет настройки пользователей в файл"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения настроек: {e}")

# Загружаем настройки: для каждого user_id храним True (только важные) или False (все)
user_settings = load_user_settings()

# ========== РАСПИСАНИЕ ==========
schedule = {
    0: [  # Понедельник
        ("09:00", "Хімія", "https://us04web.zoom.us/j/7430647043?pwd=CLpdFoqSVh0X1s79xVF1m8w4J4MjYo.1", False),
        ("09:00", "Географія", "https://us05web.zoom.us/j/7372874110?pwd=MUJaQUJsOUNHYUowUkswcEoxV09IUT09&omn=85468090096", False),
        ("10:00", "Алгебра", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1", True),
        ("11:00", "Англійська", "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09", True),
        ("12:00", "Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1", True),
        ("13:00", "Всесвітня історія", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09", True),
        ("14:00", "Інформатика", "https://us05web.zoom.us/j/3778676851?pwd=llSnb5K3NkdhTaVbaWaiWOnhzQaNbT.1", False),
        ("14:00", "Мистецтво", "https://us05web.zoom.us/j/3669615047?pwd=bWFXY3lHcHZTYzBlS2Q2MitjaTY0Zz09", False),
        ("15:00", "Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1", True),
    ],
    1: [  # Вторник
        ("09:00", "Алгебра", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1", True),
        ("10:00", "Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1", True),
        ("11:00", "Біологія", "https://us05web.zoom.us/j/81300275025?pwd=xNzRsLtAf4TYeszH5yWAHMbutUCGbz.1", False),
        ("12:00", "Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1", False),
        ("13:00", "Англійська", "https://us05web.zoom.us/j/5515598862?pwd=YUZHZk5TVzdjbTVYcFdVanNBZENYdz09", True),
        ("14:00", "Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1", True),
        ("15:00", "Українська література", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1", True),
    ],
    2: [  # Среда
        ("09:00", "Інформатика", "https://us05web.zoom.us/j/3778676851?pwd=llSnb5K3NkdhTaVbaWaiWOnhzQaNbT.1", False),
        ("10:00", "Географія", "https://us05web.zoom.us/j/7372874110?pwd=MUJaQUJsOUNHYUowUkswcEoxV09IUT09&omn=85468090096", False),
        ("11:00", "Зарубіжна література", "https://us04web.zoom.us/j/9721960165?pwd=yYQs8qczfNK9soiSgiSHFXOLXEi2al.1", True),
        ("12:00", "Алгебра", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1", True),
        ("13:00", "Мистецтво", "https://us05web.zoom.us/j/3669615047?pwd=bWFXY3lHcHZTYzBlS2Q2MitjaTY0Zz09", False),
        ("14:00", "Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1", False),
        ("15:00", "Фізкультура", "https://us04web.zoom.us/j/9199278785?pwd=V", False),
    ],
    3: [  # Четверг
        ("09:00", "Громадянська освіта", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09", False),
        ("10:00", "Громадянська освіта", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09", False),
        ("11:00", "Українська мова", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1", True),
        ("12:00", "Біологія", "https://us05web.zoom.us/j/81300275025?pwd=xNzRsLtAf4TYeszH5yWAHMbutUCGbz.1", False),
        ("13:00", "Геометрія", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1", True),
        ("14:00", "Захист України", None, False),
        ("15:00", "Захист України", None, False),
    ],
    4: [  # Пятница
        ("09:00", "Хімія", "https://us04web.zoom.us/j/7430647043?pwd=CLpdFoqSVh0X1s79xVF1m8w4J4MjYo.1", False),
        ("10:00", "Українська література", "https://us04web.zoom.us/j/79053991159?pwd=THuQCb9YeGtubog7sFkXjP2bQJRvGQ.1", True),
        ("11:00", "Історія України", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09", True),
        ("12:00", "Алгебра", "https://us04web.zoom.us/j/72853881538?pwd=5ap1lUemTYVzIS69BmnqXkqUGx4bkV.1", True),
        ("13:00", "Фізика", "https://us04web.zoom.us/j/77206078472?pwd=a8HpuUDfL7OOujuoMcmCzj5U0VZoJo.1", False),
        ("14:00", "Фізкультура", "https://us04web.zoom.us/j/9199278785?pwd=V", False),
        ("15:00", "Історія України", "https://us05web.zoom.us/j/4813057325?pwd=ZWlaR0VtVmZTVCtlZ3pWbldYMmlTZz09", True),
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

def edit_message(chat_id, message_id, text, keyboard=None):
    """Редактирует существующее сообщение"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if keyboard:
        data["reply_markup"] = json.dumps(keyboard)
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"Ошибка редактирования: {e}")

def delete_message(chat_id, message_id):
    """Удаляет сообщение"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
    data = {
        "chat_id": chat_id,
        "message_id": message_id
    }
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"Ошибка удаления: {e}")

# ========== ПЛАНИРОВЩИК С УЧЁТОМ НАСТРОЕК ==========
def check_lessons():
    """Проверяет каждую минуту, не пора ли отправить уведомление"""
    while True:
        try:
            now = datetime.now(tz)
            current_time = now.strftime("%H:%M")
            today = now.weekday()
            
            # Группируем уроки по времени
            lessons_by_time = {}
            for t, name, link, is_important in schedule.get(today, []):
                if t not in lessons_by_time:
                    lessons_by_time[t] = []
                lessons_by_time[t].append((name, link, is_important))
            
            # Проверяем каждое время
            for t, lessons_list in lessons_by_time.items():
                # Проверяем начало урока
                if t == current_time:
                    # Отправляем каждому пользователю согласно его настройкам
                    for uid in allowed_users:
                        # Получаем настройки пользователя (по умолчанию False = все уроки)
                        only_important = user_settings.get(str(uid), False)
                        
                        # Фильтруем уроки согласно настройкам
                        filtered_lessons = []
                        for name, link, is_important in lessons_list:
                            if not only_important or is_important:
                                filtered_lessons.append((name, link))
                        
                        if not filtered_lessons:
                            continue  # Пользователю не придут уведомления об этих уроках
                        
                        if len(filtered_lessons) == 1:
                            name, link = filtered_lessons[0]
                            text = f"⏰ *Урок начался:* {name}"
                            keyboard = None
                            if link:
                                keyboard = {
                                    "inline_keyboard": [[
                                        {"text": "🔗 Присоединиться", "url": link}
                                    ]]
                                }
                            send_message(uid, text, keyboard)
                        else:
                            names = [item[0] for item in filtered_lessons]
                            text = f"⏰ *Урок начался:* {', '.join(names)}"
                            
                            keyboard = {"inline_keyboard": []}
                            for name, link in filtered_lessons:
                                if link:
                                    keyboard["inline_keyboard"].append([
                                        {"text": f"🔗 {name}", "url": link}
                                    ])
                            
                            if keyboard["inline_keyboard"]:
                                send_message(uid, text, keyboard)
                            else:
                                send_message(uid, text)
                
                # Проверяем за 5 минут до урока
                h, m = map(int, t.split(':'))
                reminder_time = (now.replace(hour=h, minute=m, second=0) - timedelta(minutes=5)).strftime("%H:%M")
                if reminder_time == current_time:
                    for uid in allowed_users:
                        only_important = user_settings.get(str(uid), False)
                        
                        filtered_lessons = []
                        for name, link, is_important in lessons_list:
                            if not only_important or is_important:
                                filtered_lessons.append((name, link))
                        
                        if not filtered_lessons:
                            continue
                        
                        if len(filtered_lessons) == 1:
                            name, link = filtered_lessons[0]
                            text = f"⏳ *Через 5 минут:* {name}"
                            keyboard = None
                            if link:
                                keyboard = {
                                    "inline_keyboard": [[
                                        {"text": "🔗 Присоединиться", "url": link}
                                    ]]
                                }
                            send_message(uid, text, keyboard)
                        else:
                            names = [item[0] for item in filtered_lessons]
                            text = f"⏳ *Через 5 минут:* {', '.join(names)}"
                            
                            keyboard = {"inline_keyboard": []}
                            for name, link in filtered_lessons:
                                if link:
                                    keyboard["inline_keyboard"].append([
                                        {"text": f"🔗 {name}", "url": link}
                                    ])
                            
                            if keyboard["inline_keyboard"]:
                                send_message(uid, text, keyboard)
                            else:
                                send_message(uid, text)
        except Exception as e:
            print(f"Ошибка в планировщике: {e}")
        
        time.sleep(60)

# ========== ФУНКЦИИ ДЛЯ РАСПИСАНИЯ ==========
def show_day(chat_id, day):
    lessons = schedule.get(day, [])
    if not lessons:
        send_message(chat_id, f"📅 *{days_ua[day]}* – выходной")
        return
    
    # Получаем настройки пользователя
    only_important = user_settings.get(str(chat_id), False)
    
    # Группируем по времени для вывода
    lessons_by_time = {}
    for t, name, _, is_important in lessons:
        if t not in lessons_by_time:
            lessons_by_time[t] = []
        
        # Если урок важный И пользователь в режиме "только важные" — ставим звёздочку
        if only_important and is_important:
            lessons_by_time[t].append(f"⭐ {name}")
        else:
            lessons_by_time[t].append(name)
    
    text = f"📅 *{days_ua[day]}*\n"
    for t, names in sorted(lessons_by_time.items()):
        text += f"⏰ {t} – {', '.join(names)}\n"
    send_message(chat_id, text)

def show_week(chat_id):
    only_important = user_settings.get(str(chat_id), False)
    text = "📋 *Неделя*\n\n"
    
    for day in range(5):
        lessons = schedule.get(day, [])
        if lessons:
            # Группируем по времени
            lessons_by_time = {}
            for t, name, _, is_important in lessons:
                if t not in lessons_by_time:
                    lessons_by_time[t] = []
                
                # Звёздочка только если важный И режим "только важные"
                if only_important and is_important:
                    lessons_by_time[t].append(f"⭐ {name}")
                else:
                    lessons_by_time[t].append(name)
            
            text += f"*{days_ua[day]}:*\n"
            for t, names in sorted(lessons_by_time.items()):
                text += f"  ⏰ {t} – {', '.join(names)}\n"
            text += "\n"
    
    send_message(chat_id, text)

def show_next_lesson(chat_id, today):
    now = datetime.now(tz).strftime("%H:%M")
    only_important = user_settings.get(str(chat_id), False)
    
    # Сначала ищем сегодня
    lessons_by_time = {}
    for t, name, _, is_important in schedule.get(today, []):
        if t not in lessons_by_time:
            lessons_by_time[t] = []
        
        # Звёздочка только если важный И режим "только важные"
        if only_important and is_important:
            lessons_by_time[t].append(f"⭐ {name}")
        else:
            lessons_by_time[t].append(name)
    
    for t, names in sorted(lessons_by_time.items()):
        if t > now:
            send_message(chat_id, f"⏭ *Следующий урок:* {t} – {', '.join(names)}")
            return
    
    # Если сегодня нет, смотрим завтра
    tomorrow = (today + 1) % 7
    lessons_by_time = {}
    for t, name, _, is_important in schedule.get(tomorrow, []):
        if t not in lessons_by_time:
            lessons_by_time[t] = []
        
        if only_important and is_important:
            lessons_by_time[t].append(f"⭐ {name}")
        else:
            lessons_by_time[t].append(name)
    
    if lessons_by_time:
        t = min(lessons_by_time.keys())
        names = lessons_by_time[t]
        send_message(chat_id, f"📅 Завтра перший урок: {t} – {', '.join(names)}")
    else:
        send_message(chat_id, "🎉 Уроков нет")

def show_links(chat_id, day):
    lessons = schedule.get(day, [])
    if not lessons:
        send_message(chat_id, "📭 Сегодня уроков нет")
        return
    
    only_important = user_settings.get(str(chat_id), False)
    
    # Группируем для показа
    lessons_by_time = {}
    for i, (t, name, link, is_important) in enumerate(lessons):
        if link:
            if t not in lessons_by_time:
                lessons_by_time[t] = []
            
            # Звёздочка только если важный И режим "только важные"
            if only_important and is_important:
                display_name = f"⭐ {name}"
            else:
                display_name = name
            
            lessons_by_time[t].append((i, display_name, link))
    
    if not lessons_by_time:
        send_message(chat_id, "🔗 Сегодня нет ссылок")
        return
    
    keyboard = {"inline_keyboard": []}
    for t, items in sorted(lessons_by_time.items()):
        for i, display_name, link in items:
            keyboard["inline_keyboard"].append([
                {"text": f"{t} – {display_name}", "callback_data": f"link_{day}_{i}"}
            ])
    
    send_message(chat_id, "🔗 Выбери урок:", keyboard)

def show_important_menu(chat_id, message_id=None):
    """Показывает меню настройки важных уроков"""
    current = user_settings.get(str(chat_id), False)
    
    if current:
        status = "✅ Зараз: тільки важливі уроки"
    else:
        status = "✅ Зараз: всі уроки"
    
    text = (
        f"🔔 *Налаштування важливих уроків*\n\n"
        f"{status}\n\n"
        f"*Важливі уроки:*\n"
        f"• Алгебра\n"
        f"• Геометрія\n"
        f"• Англійська\n"
        f"• Зарубіжна література\n"
        f"• Українська мова\n"
        f"• Українська література\n"
        f"• Історія України\n"
        f"• Всесвітня історія\n\n"
        f"Оберіть режим:"
    )
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔴 Тільки важливі", "callback_data": "important_on"}],
            [{"text": "🟢 Всі уроки", "callback_data": "important_off"}],
            [{"text": "❌ Скасувати", "callback_data": "important_cancel"}]
        ]
    }
    
    if message_id:
        edit_message(chat_id, message_id, text, keyboard)
    else:
        send_message(chat_id, text, keyboard)

# ========== ОБРАБОТКА ВСЕХ ОБНОВЛЕНИЙ ==========
def handle_updates():
    """Единый обработчик для всех обновлений (сообщения + callback)"""
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"timeout": 30, "offset": offset}
            
            r = requests.get(url, params=params, timeout=35)
            updates = r.json().get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                
                # Обработка обычных сообщений
                if "message" in update:
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
                                [{"text": "🔗 Посилання"}],
                                [{"text": "🔔 Важливі уроки"}]
                            ],
                            "resize_keyboard": True
                        }
                        send_message(chat_id, "👋 Привет! Обери дію:", keyboard)
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
                    elif text == "🔔 Важливі уроки":
                        show_important_menu(chat_id)
                
                # Обработка callback-запросов (нажатия на inline кнопки)
                elif "callback_query" in update:
                    query = update["callback_query"]
                    chat_id = query["message"]["chat"]["id"]
                    data = query["data"]
                    message_id = query["message"]["message_id"]
                    
                    # Подтверждаем получение callback
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                        data={"callback_query_id": query["id"]}
                    )
                    
                    # Проверка доступа
                    if chat_id not in allowed_users:
                        continue
                    
                    # Обработка важных уроков
                    if data == "important_on":
                        user_settings[str(chat_id)] = True
                        save_user_settings(user_settings)
                        show_important_menu(chat_id, message_id)
                    
                    elif data == "important_off":
                        user_settings[str(chat_id)] = False
                        save_user_settings(user_settings)
                        show_important_menu(chat_id, message_id)
                    
                    elif data == "important_cancel":
                        delete_message(chat_id, message_id)
                    
                    # Обработка ссылок на уроки
                    elif data.startswith("link_"):
                        _, d, i = data.split("_")
                        day, idx = int(d), int(i)
                        t, name, link, is_important = schedule[day][idx]
                        if link:
                            keyboard = {
                                "inline_keyboard": [[
                                    {"text": "🔗 Присоединиться", "url": link}
                                ]]
                            }
                            edit_message(chat_id, message_id, f"🔗 *{t} – {name}*", keyboard)
        
        except Exception as e:
            print(f"Ошибка в обработчике: {e}")
            time.sleep(5)

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
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask запущен на порту 10000")
    
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=check_lessons, daemon=True)
    scheduler_thread.start()
    print("⏰ Планировщик запущен")
    
    # Запускаем единый обработчик (главный поток)
    print("📨 Обработчик команд и кнопок запущен")
    handle_updates()
