import os, sqlite3, telebot, threading, http.server, socketserver
from telebot import types

# ФЕЙКОВЫЙ ПОРТ ДЛЯ ХОСТИНГА RENDER
def run_fake_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()
threading.Thread(target=run_fake_server, daemon=True).start()

TOKEN = '8846255632:AAFTuQcgY_u5WOM1FOjeg6ldANc9k3qnvFo'
bot = telebot.TeleBot(TOKEN)
ADMIN_USERNAME = "BlazingSerafim"

db_path = "bot_users.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, points INTEGER DEFAULT 0)')
conn.commit()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
    cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    conn.commit()
except: pass

def save_user_data(user_id, username):
    try:
        uname = username.lower() if username else ""
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            if uname: cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (uname, user_id))
        else:
            cursor.execute("INSERT INTO users (user_id, username, points) VALUES (?, ?, 0)", (user_id, uname))
        conn.commit()
    except Exception as e: print(f"Ошибка БД: {e}")

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
    if not message.from_user.username or message.from_user.username.lower() != ADMIN_USERNAME.lower():
        bot.send_message(message.chat.id, "❌ У тебя нет прав администратора!")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Выдать баллы", callback_data="adm_add"))
    markup.add(types.InlineKeyboardButton("➖ Списать баллы", callback_data="adm_take"))
    markup.add(types.InlineKeyboardButton("📢 Сделать рассылку (/update)", callback_data="adm_update"))
    bot.send_message(message.chat.id, "👑 **Панель администратора магазина**\n\nВыбери нужное действие на кнопках ниже:", reply_markup=markup, parse_mode='Markdown')
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    save_user_data(chat_id, call.from_user.username)

    if call.data == "adm_add":
        bot.edit_message_text("✏️ **Начисление баллов**\n\nВведите никнейм покупателя и количество баллов через пробел.\n*Пример:* `Ivan_Fnaf 50`", chat_id, msg_id, parse_mode='Markdown')
        bot.register_next_step_handler_by_chat_id(chat_id, process_admin_add)
        bot.answer_callback_query(call.id)
    elif call.data == "adm_take":
        bot.edit_message_text("✏️ **Списание баллов**\n\nВведите никнейм покупателя и количество баллов через пробел.\n*Пример:* `Ivan_Fnaf 30`", chat_id, msg_id, parse_mode='Markdown')
        bot.register_next_step_handler_by_chat_id(chat_id, process_admin_take)
        bot.answer_callback_query(call.id)
    elif call.data == "adm_update":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "💡 Для автоматической рассылки об обновлении товара просто используй текстовую команду `/update` в чате.", parse_mode='Markdown')
    elif call.data == "shop":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Купить souls", callback_data="buy_souls"), types.InlineKeyboardButton("📦 Наличие", callback_data="check_stock"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))
        text = (
            "🛒 **Текущее наличие товаров в магазине:**\n\n"
            "✨ **Souls (Души):** 0 шт.\n"
            "💀 **Forgotten:** пока нет в наличии\n"
            "🔮 **Apex:** пока нет в наличии\n"
            "😈 **Nightmare:** пока нет в наличии\n\n"
            "📊 **Актуальный курс душ:**\n"
            "• 1 000 ✨ = 0.5 ₽ (1к / 0.5₽)\n\n"
            "💡 Чтобы узнать точные цены и посмотреть, какие конкретно юниты сейчас есть, просто нажми на кнопку **«Наличие»** ниже 👇"
        )
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    elif call.data == "profile":
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (chat_id,))
        res = cursor.fetchone()
        points = res[0] if res else 0
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ В меню", callback_data="back_to_main"))
        text = (
            f"👤 **Твой личный профиль покупателя**\n\n"
            f"🏷 Никнейм: @{call.from_user.username if call.from_user.username else 'Не указан'}\n"
            f"🆔 Ваш ID: `{chat_id}`\n\n"
            f"💎 **Твой бонусный баланс:** {points} баллов\n\n"
            f"🔥 *Система лояльности магазина:*\n"
            f"Вы можете оплатить накопленными баллами **до 50%** от стоимости любого товара по курсу 1 балл = 1 рубль! Для списания баллов сообщите об этом администратору при оформлении заказа."
        )
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    elif call.data == "back_to_main":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛒 Магазин", callback_data="shop"), types.InlineKeyboardButton("👤 Профиль", callback_data="profile"))
        welcome = (
            "👋 Привет, дорогой мой друг!\n\n"
            "🏪 Добро пожаловать в мой магазин по игре **Five Nights Tower Defense**!\n\n"
            "У нас в наличии есть самые ценные ресурсы:\n"
            "✨ **Souls** (Души) и 💎 **Units** (Юниты)\n\n"
            "💬 **Обратная связь:**\n"
            "По поводу покупки товаров, сотрудничества или по любым вопросам пишите владельцу: @BlazingSerafim 👑"
        )
        bot.edit_message_text(welcome, chat_id, msg_id, reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    elif call.data == "buy_souls":
        bot.edit_message_text("📥 **Введите нужное количество souls (от 10 000 шт.):**\n\n_Просто напишите число в чат (например: 15000)_", chat_id, msg_id, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        bot.register_next_step_handler_by_chat_id(chat_id, process_souls_input)
    elif call.data == "check_stock":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ В магазин", callback_data="shop"))
        bot.edit_message_text("📦 **Текущее наличие юнитов:**\n\nПока пустует, ожидайте обновлений! Скоро здесь появятся лучшие редкости.", chat_id, msg_id, reply_markup=markup)
        bot.answer_callback_query(call.id)

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
        bot.send_message(message.chat.id, f"✅ Успешно начислено *{amount}* баллов для @{target}!", parse_mode='Markdown')
        try: bot.send_message(user[0], f"🎉 Баланс пополнен на *{amount}* баллов! Проверь профиль.")
        except: pass
    except: bot.send_message(message.chat.id, "⚠️ Ошибка ввода. Нужно ввести ник и число через пробел.")

def process_admin_take(message):
    try:
        parts = message.text.split()
        target = parts[0].replace("@", "").lower().strip()
        amount = int(parts[1])
        cursor.execute("SELECT user_id, points FROM users WHERE username = ?", (target,))
        user = cursor.fetchone()
        if not user:
            bot.send_message(message.chat.id, f"❌ Пользователь @{target} не найден.")
            return
        if user[1] < amount:
            bot.send_message(message.chat.id, f"⚠️ У игрока всего {user[1]} баллов. Нельзя списать {amount}!")
            return
        new_bal = user[1] - amount
        cursor.execute("UPDATE users SET points = ? WHERE username = ?", (new_bal, target))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ Успешно списано *{amount}* баллов у @{target}!", parse_mode='Markdown')
        try: bot.send_message(user[0], f"📉 С твоего баланса списано *{amount}* баллов.")
        except: pass
    except: bot.send_message(message.chat.id, "⚠️ Ошибка ввода. Нужно ввести ник и число через пробел.")

@bot.message_handler(commands=['update'])
def auto_update_broadcast(message):
    if not message.from_user.username or message.from_user.username.lower() != ADMIN_USERNAME.lower(): return
    bot.send_message(message.chat.id, "🚀 Запускаю рассылку об обновлении товара...")
    cursor.execute("SELECT user_id, username FROM users")
    all_users = cursor.fetchall()
    success = 0
    text = "🔔 **Внимание! Наличие товара в магазине обновлено!**\n\nЗаходи скорее, чтобы посмотреть новые поступления! ✨"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛒 Открыть Магазин", callback_data="shop"))
    for user in all_users:
        if user[1] and user[1].lower() == ADMIN_USERNAME.lower(): continue
        try:
            bot.send_message(user[0], text, reply_markup=markup, parse_mode='Markdown')
            success += 1
        except: pass
    bot.send_message(message.chat.id, f"✅ Рассылка завершена! Доставлено: {success} покупателям.")

def process_souls_input(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛒 В магазин", callback_data="shop"))
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, введите количество **числом**.", reply_markup=markup, parse_mode='Markdown')
        return
    amount = int(message.text)
    if amount < 10000:
        bot.send_message(message.chat.id, "❌ Минимальный заказ — **от 10 тысяч** душ!", reply_markup=markup, parse_mode='Markdown')
    else:
        price = amount * 0.0005
        max_disc = price * 0.5
        text = (
            f"📊 **Расчёт стоимости заказа:**\n\n"
            f"✨ Количество: {amount} Souls\n"
            f"💵 Базовая цена: {price:.2f} ₽\n\n"
            f"🔥 *Важная информация про баллы:*\n"
            f"Вы можете оплатить баллами до **50%** от стоимости заказа (скидка до {max_disc:.2f} ₽).\n"
            f"⚠️ **Чтобы списать накопленные баллы, обязательно напишите администратору при покупке, что хотите использовать бонусы!**\n\n"
            f"💳 **Реквизиты для оплаты:**\n"
            f"• Номер телефона: `+79994457208`\n"
            f"• Банк: **ОЗОН Банк**\n\n"
            f"⚠️ **СТРОГОЕ ПРАВИЛО:** Перевод делать только на ОЗОН Банк! Если вы отправите деньги на Сбербанк, вам вернётся **только 50% от вашей суммы**, а товар выдан не будет.\n\n"
            f"После оплаты отправьте чек владельцу магазина: @BlazingSerafim"
        )
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

if __name__ == "__main__":
    bot.infinity_polling()
