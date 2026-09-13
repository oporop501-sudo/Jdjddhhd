import os, sqlite3, telebot, threading, http.server, socketserver
from telebot import types

# Фейковый порт для Render
def run_fake_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()
threading.Thread(target=run_fake_server, daemon=True).start()

TOKEN = '8846255632:AAFTuQcgY_u5WOM1FOjeg6ldANc9k3qnvFo'
bot = telebot.TeleBot(TOKEN)
ADMIN_USERNAME = "BlazingSerafim"
ADMIN_ID = 8846255632  # Твой ID для получения тикетов заказа

db_path = "bot_users.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# Создаем правильную структуру БД
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        points INTEGER DEFAULT 0
    )
''')
conn.commit()

def save_user_data(user_id, username):
    try:
        uname = username.lower() if username else ""
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            if uname: cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (uname, user_id))
        else:
            cursor.execute("INSERT INTO users (user_id, username, points) VALUES (?, ?, 0)", (user_id, uname))
        conn.commit()
    except: pass

@bot.message_handler(commands=['start'])
def start_command(message):
    save_user_data(message.chat.id, message.from_user.username)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"), types.InlineKeyboardButton("👤 Профиль", callback_data="profile"))
    
    welcome = (
        "👋 Привет, дорогой мой друг!\n\n"
        "🏪 Добро пожаловать в мой магазин по игре **Five Nights Tower Defense**!\n\n"
        "У нас в наличии есть самые ценные ресурсы:\n"
        "✨ **Souls** (Души) и 💎 **Units** (Юниты)\n\n"
        "А также топовые редкости для твоей коллекции:\n"
        "💀 **Forgotten** | 🔮 **Apex** | 😈 **Nightmare**\n\n"
        "💬 **Обратная связь:**\n"
        "По поводу покупки товаров, сотрудничества или по любым вопросам пишите владельцу: @BlazingSerafim 👑\n\n"
        "Выбирай нужный раздел на кнопках ниже 👇"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not message.from_user.username or message.from_user.username.lower() != ADMIN_USERNAME.lower(): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Выдать баллы", callback_data="adm_add"))
    markup.add(types.InlineKeyboardButton("➖ Списать баллы", callback_data="adm_take"))
    bot.send_message(message.chat.id, "👑 **Панель администратора магазина**", reply_markup=markup, parse_mode='Markdown') @bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    save_user_data(chat_id, call.from_user.username)

    if call.data == "adm_add":
        bot.edit_message_text("✏️ Введите никнейм и количество баллов через пробел (Пример: `Ivan_Fnaf 50`):", chat_id, msg_id)
        bot.register_next_step_handler_by_chat_id(chat_id, process_admin_add)
    elif call.data == "adm_take":
        bot.edit_message_text("✏️ Введите никнейм и количество баллов через пробел (Пример: `Ivan_Fnaf 30`):", chat_id, msg_id)
        bot.register_next_step_handler_by_chat_id(chat_id, process_admin_take)
    elif call.data == "shop":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Купить souls", callback_data="buy_souls"), types.InlineKeyboardButton("📦 Наличие юнитов", callback_data="check_stock"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))
        text = "🛒 **Выбери категорию товара для автоматического оформления заказа:**\n\n📊 **Новый актуальный курс душ:**\n• 1 000 ✨ = 0.3 ₽ (1к/0.3)\n\n🔥 За каждую покупку тебе начисляется **6% кэшбэка** баллами, которыми можно оплатить до 50% следующих заказов!"
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode='Markdown')
    elif call.data == "profile":
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (chat_id,))
        res = cursor.fetchone()
        points = res[0] if res else 0
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ В меню", callback_data="back_to_main"))
        text = f"👤 **Профиль покупателя**\n\n🏷 Ник: @{call.from_user.username}\n💎 **Бонусы:** {points} баллов\n\n🔥 Баллами можно оплатить до 50% заказа у админа! Сообщите о желании потратить баллы при подтверждении заказа."
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode='Markdown')
    elif call.data == "back_to_main":
        start_command(call.message)
    elif call.data == "buy_souls":
        bot.edit_message_text("📥 **Напишите в чат, сколько Souls вы хотите заказать (числом от 10 000 шт.):**", chat_id, msg_id, parse_mode='Markdown')
        bot.register_next_step_handler_by_chat_id(chat_id, process_souls_order)
    elif call.data == "check_stock":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔮 Заказать Apex персонажа (250₽)", callback_data="ord_apex"))
        markup.add(types.InlineKeyboardButton("⬅️ В магазин", callback_data="shop"))
        bot.edit_message_text("📦 **Доступные юниты в наличии:**\n\n• 🔮 Apex персонаж (Случайный) — 250 ₽\n• 💀 Forgotten — временно нет\n• 😈 Nightmare — временно нет", chat_id, msg_id, reply_markup=markup, parse_mode='Markdown')
    elif call.data == "ord_apex":
        send_ticket_to_admin(call.from_user, "🔮 Случайный Apex персонаж", 250.00)
        bot.edit_message_text("✅ **Тикет заказа успешно отправлен владельцу магазина!**\n\nАдминистратор @BlazingSerafim уже получил уведомление. Ожидайте, он скоро напишет вам в личку для подтверждения заказа и приёма оплаты!", chat_id, msg_id, parse_mode='Markdown')

def process_souls_order(message):
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🛒 В магазин", callback_data="shop"))
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, введите количество цифрами!", reply_markup=markup)
        return
    amount = int(message.text)
    if amount < 10000:
        bot.send_message(message.chat.id, "❌ Минимальный заказ от 10 000 душ!", reply_markup=markup)
        return
    # Расчет по новому курсу 1к = 0.3р (1 душа = 0.0003р)
    price = amount * 0.0003
    send_ticket_to_admin(message.from_user, f"✨ {amount:,} Souls", price)
    bot.send_message(message.chat.id, f"✅ **Тикет вашего заказа успешно отправлен!**\n\n🛍 Товар: {amount:,} Souls\n💵 Сумма к оплате: {price:.2f} ₽\n\nВладелец магазина @BlazingSerafim свяжется с вами в личке для приёма оплаты (ОЗОН Банк)!", reply_markup=markup, parse_mode='Markdown')

def send_ticket_to_admin(user, item_name, price):
    cursor.execute("SELECT points FROM users WHERE username = ?", (user.username.lower() if user.username else "",))
    res = cursor.fetchone()
    user_points = res[0] if res else 0
    # Расчет кэшбэка ровно 6% от суммы в рублях
    recommended_cashback = int(price * 0.06)
    
    ticket = (
        f"📦 🚨 **ПОСТУПИЛ НОВЫЙ ТИКЕТ ЗАКАЗА!**\n\n"
        f"👤 **Покупатель:** @{user.username if user.username else 'Нет никнейма'}\n"
        f"🆔 ID: `{user.id}`\n"
        f"🛍 **Товар:** {item_name}\n"
        f"💵 **Сумма к оплате:** `{price:.2f}` ₽\n"
        f"💎 **Баллы в профиле клиента:** {user_points} б.\n\n"
        f"🎁 *Рекомендуемый кэшбэк (6%):* `+{recommended_cashback}` баллов.\n\n"
        f"📱 **Реквизиты для выдачи клиенту:** `+79994457208` (ОЗОН Банк).\n"
        f"⚠️ Напомните клиенту, что при переводе на Сбербанк возвращается только 50% от суммы!\n\n"
        f"👉 Кликните на никнейм покупателя выше, чтобы подтвердить заказ в личке."
    )
    bot.send_message(ADMIN_ID, ticket, parse_mode='Markdown')

def process_admin_add(message):
    try:
        parts = message.text.split()
        target = parts[0].replace("@", "").lower().strip()
        amount = int(parts[1])
        cursor.execute("SELECT user_id, points FROM users WHERE username = ?", (target,))
        user = cursor.fetchone()
        if not user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{target} не найден.")
            return
        new_bal = user[1] + amount
        cursor.execute("UPDATE users SET points = ? WHERE username = ?", (new_bal, target))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ Начислено {amount} б. для @{target}!")
        try: bot.send_message(user[0], f"🎉 Твой баланс пополнен на *{amount}* баллов! Проверь профиль.")
        except: pass
    except: bot.send_message(message.chat.id, "⚠️ Ошибка. Формат: ник число")

def process_admin_take(message):
    try:
        parts = message.text.split()
        target = parts[0].replace("@", "").lower().strip()
        amount = int(parts[1])
        cursor.execute("SELECT user_id, points FROM users WHERE username = ?", (target,))
        user = cursor.fetchone()
        if not user or user[1] < amount: return
        new_bal = user[1] - amount
        cursor.execute("UPDATE users SET points = ? WHERE username = ?", (new_bal, target))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ Списано {amount} б. у @{target}!")
        try: bot.send_message(user[0], f"📉 С твоего бонусного баланса списано *{amount}* баллов.")
        except: pass
    except: bot.send_message(message.chat.id, "⚠️ Ошибка.")

@bot.message_handler(commands=['update'])
def auto_update_broadcast(message):
    if not message.from_user.username or message.from_user.username.lower() != ADMIN_USERNAME.lower(): return
    cursor.execute("SELECT user_id, username FROM users")
    all_users = cursor.fetchall()
    text = "🔔 **Внимание! Наличие товара в магазине обновлено!**\n\nЗаходи скорее в меню 🛒 Магазин -> Наличие юнитов! ✨"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🛒 Открыть Магазин", callback_data="shop"))
    for user in all_users:
        if user[1] and user[1].lower() == ADMIN_USERNAME.lower(): continue
        try: bot.send_message(user[0], text, reply_markup=markup, parse_mode='Markdown')
        except: pass

if __name__ == "__main__":
    bot.infinity_polling()
