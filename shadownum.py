import asyncio
import random
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

# ===================================================
#  КОНФИГ
# ===================================================
API_ID = 33728218
API_HASH = "2c416c3a6e867f9c67169a6c8506990b"
BOT_TOKEN = "8822873604:AAHtY4A6R6zvHAdnOp7AMKbe1RBxl5Wkz38"
ADMIN_ID = 7572600645

# ===================================================
#  БАЗА ДАННЫХ (в памяти)
# ===================================================
users = {}
products = {
    "day":   {"name": "🌅 На 1 день", "price": 100, "desc": "24 часа анонимности"},
    "week":  {"name": "📅 На 7 дней", "price": 500, "desc": "Неделя без следа"},
    "month": {"name": "📆 На 30 дней", "price": 1500, "desc": "Месяц полной тени"}
}
admin_numbers = []
product_counter = 100

def get_user(uid):
    if uid not in users:
        users[uid] = {
            "balance":0,
            "numbers": [],
            "active": 0,
            "orders": 0,
            "username": None,
            "bonus_used": False
        }
    return users[uid]

def fmt(b): return f"{b:,}".replace(",", " ")

def gen_number():
    return f"+888 {random.randint(10,99)} {random.randint(1000,9999)} {random.randint(1000,9999)}"

def add_admin_number(num):
    admin_numbers.append(num)
    return len(admin_numbers)

def remove_admin_number(idx):
    if 0 <= idx < len(admin_numbers):
        return admin_numbers.pop(idx)
    return None

def get_admin_numbers():
    return admin_numbers.copy()

def add_product(name, price):
    global product_counter
    pid = f"custom_{product_counter}"
    products[pid] = {"name": name, "price": price, "desc": "Пользовательский тариф"}
    product_counter += 1
    return pid

def delete_product(pid):
    if pid in products:
        del products[pid]
        return True
    return False

def update_product(pid, name=None, price=None):
    if pid in products:
        if name: products[pid]["name"] = name
        if price is not None: products[pid]["price"] = price
        return True
    return False

def get_all_users():
    return list(users.keys())

# ===================================================
#  КЛАВИАТУРЫ
# ===================================================
def main_menu(uid):
    kb = [
        [InlineKeyboardButton("🛒 Купить номер", callback_data="buy")],
        [InlineKeyboardButton("📋 Мои номера", callback_data="my")],
        [InlineKeyboardButton("💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton("💳 Пополнить", callback_data="deposit")], 
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton("⚡ АДМИН-ПАНЕЛЬ", callback_data="admin_panel")])
    return InlineKeyboardMarkup(kb)

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Товары", callback_data="admin_products")],
        [InlineKeyboardButton("📱 Номера", callback_data="admin_numbers")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ])

def buy_menu(balance):
    kb = []
    for pid, p in products.items():
        kb.append([InlineKeyboardButton(
            f"{p['name']} — {p['price']} ₽",
            callback_data=f"buy_{pid}"
        )])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
    return InlineKeyboardMarkup(kb)

def admin_products_menu():
    kb = []
    for pid, p in products.items():
        kb.append([InlineKeyboardButton(
            f"{p['name']} — {p['price']} ₽",
            callback_data=f"admin_product_{pid}"
        )])
    kb.append([
        InlineKeyboardButton("➕ Добавить", callback_data="admin_add_product"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
    ])
    return InlineKeyboardMarkup(kb)

def admin_product_actions(pid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Цена", callback_data=f"admin_edit_price_{pid}")],
        [InlineKeyboardButton("📝 Название", callback_data=f"admin_edit_name_{pid}")],
        [InlineKeyboardButton("🗑 Удалить", callback_data=f"admin_delete_product_{pid}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_products")]
    ])

def admin_numbers_menu():
    kb = []
    for idx, num in enumerate(get_admin_numbers()):
        kb.append([InlineKeyboardButton(
            f"📱 {num}",
            callback_data=f"admin_delete_number_{idx}"
        )])
    kb.append([
        InlineKeyboardButton("➕ Добавить", callback_data="admin_add_number"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
    ])
    return InlineKeyboardMarkup(kb)

def admin_users_menu():
    kb = []
    for uid in get_all_users()[:20]:
        kb.append([InlineKeyboardButton(f"👤 {uid}", callback_data=f"admin_user_{uid}")])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])
    return InlineKeyboardMarkup(kb)

def admin_user_actions(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Баланс", callback_data=f"admin_set_balance_{uid}")],
        [InlineKeyboardButton("🗑 Удалить", callback_data=f"admin_delete_user_{uid}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_users")]
    ])

def my_numbers_menu(numbers):
    kb = []
    for idx in range(len(numbers)):
        kb.append([InlineKeyboardButton(
            f"🗑 Удалить {idx+1}",
            callback_data=f"delete_{idx}"
        )])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
    return InlineKeyboardMarkup(kb)

# ===================================================
#  ТЕКСТЫ
# ===================================================
START_TEXT = """
🔥  RENTA +888 БОТ ДЛЯ АРЕНДЫ АНОНИМНЫХ НОМЕРОВ

Анонимные номера **+888** для:
• Красивого оформления профиля
• Придает официальный статус персоне

💰 Баланс: **{} ₽**
📦 Номеров: **{}/5**
⚡ Активных: **{}**

Выбери действие:
"""

BUY_TEXT = """
📱 **ДОСТУПНЫЕ ТАРИФЫ:**

{}
💰 Баланс: **{} ₽**
"""

BUY_SUCCESS = """
✅ **{} активирован!**

📱 `{}`
📌 Тариф: {}
💰 Цена: {} ₽
💳 Остаток: {} ₽
⚡ Активных: **{}**

{}  
"""

NO_NUMBERS = "📭 У тебя пока нет номеров."
MAX_NUMBERS = "❌ Максимум 5 номеров."

HELP_TEXT = """
🔮 **RENTA ANON — бот для покупки анонимного номера**

за покупкой/пополнением баланса обращаться к 
@godmidnight @benetov
"""

PURCHASE_MSGS = [
    "✅ Номер готов к работе!",
    "📱 Активация успешна!",
    "🔓 Доступ открыт!",
    "🎉 Поздравляю!"
]

ADMIN_PANEL_TEXT = """
⚡ панель бати

👥 Пользователей: {}
📦 Покупок: {}
📱 Активных: {}

Выбери действие:
"""

ADMIN_ADD_NUMBER_TEXT = """
📱 **ДОБАВИТЬ НОМЕР**

Введи номер в формате:
`+888 12 3456 7890`
"""

ADMIN_ADD_PRODUCT_TEXT = """
➕ **ДОБАВИТЬ ТОВАР**

Введи название и цену через запятую:
`Название, 500`
"""

BALANCE_TEXT = """
💰 **БАЛАНС:** {} ₽
📦 Номеров: {}
⚡ Активных: {}
"""

# ===================================================
#  КЛИЕНТ
# ===================================================
app = Client("shadownum", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===================================================
#  КОМАНДЫ
# ===================================================
@app.on_message(filters.command("start"))
async def start_cmd(c, m):
    uid = m.from_user.id
    user = get_user(uid)
    user["username"] = m.from_user.username
    await m.reply_text(
        START_TEXT.format(fmt(user["balance"]), len(user["numbers"]), user["active"]),
        reply_markup=main_menu(uid)
    )

@app.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin_cmd(c, m):
    await m.reply_text(
        ADMIN_PANEL_TEXT.format(
            len(users),
            sum(u["orders"] for u in users.values()),
            sum(u["active"] for u in users.values())
        ),
        reply_markup=admin_menu()
    )

@app.on_message(filters.user(ADMIN_ID) & filters.text)
async def admin_text(c, m):
    uid = m.from_user.id
    
    # Добавление номера
    if m.text.startswith("+888") and len(m.text) > 10:
        add_admin_number(m.text)
        await m.reply_text(f"✅ Номер {m.text} добавлен!")
        return
    
    # Обработка состояний
    if not hasattr(admin_text, "state"):
        admin_text.state = {}
    
    if uid not in admin_text.state:
        return
    
    state = admin_text.state[uid]
    
    if state == "add_product":
        try:
            parts = m.text.rsplit(",", 1)
            if len(parts) != 2:
                await m.reply_text("❌ Формат: Название, 500")
                return
            name = parts[0].strip()
            price = int(parts[1].strip())
            pid = add_product(name, price)
            await m.reply_text(f"✅ Товар добавлен! ID: {pid}")
        except:
            await m.reply_text("❌ Ошибка! Цена должна быть числом.")
        del admin_text.state[uid]
        return
    
    if state.startswith("price_"):
        pid = state.replace("price_", "")
        try:
            price = int(m.text)
            update_product(pid, price=price)
            await m.reply_text(f"✅ Цена изменена на {price} ₽")
        except:
            await m.reply_text("❌ Введите число!")
        del admin_text.state[uid]
        return
    
    if state.startswith("name_"):
        pid = state.replace("name_", "")
        update_product(pid, name=m.text.strip())
        await m.reply_text(f"✅ Название изменено!")
        del admin_text.state[uid]
        return
    
    if state.startswith("balance_"):
        target = int(state.replace("balance_", ""))
        try:
            bal = int(m.text)
            users[target]["balance"] = bal
            await m.reply_text(f"✅ Баланс {target} = {bal} ₽")
        except:
            await m.reply_text("❌ Введите число!")
        del admin_text.state[uid]
        return
    
    if state == "broadcast":
        if m.text.startswith("/cancel"):
            del admin_text.state[uid]
            await m.reply_text("✅ Отменено")
            return
        count = 0
        for uid2 in get_all_users():
            try:
                await app.send_message(uid2, f"📢 **ОБЪЯВЛЕНИЕ:**\n\n{m.text}")
                count += 1
                await asyncio.sleep(0.05)
            except:
                pass
        await m.reply_text(f"✅ Рассылка завершена! Получили: {count}")
        del admin_text.state[uid]
        return

# ===================================================
#  CALLBACK
# ===================================================
@app.on_callback_query()
async def handle_callback(c, q: CallbackQuery):
    uid = q.from_user.id
    user = get_user(uid)
    data = q.data
    
    # ----- НАЗАД -----
    if data == "back":
        await q.message.edit_text(
            START_TEXT.format(fmt(user["balance"]), len(user["numbers"]), user["active"]),
            reply_markup=main_menu(uid)
        )
        await q.answer()
        return
    
    if data == "admin_back":
        await q.message.edit_text(
            ADMIN_PANEL_TEXT.format(
                len(users),
                sum(u["orders"] for u in users.values()),
                sum(u["active"] for u in users.values())
            ),
            reply_markup=admin_menu()
        )
        await q.answer()
        return
    
    # ----- АДМИН-ПАНЕЛЬ -----
    if data == "admin_panel":
        if uid != ADMIN_ID:
            await q.answer("⛔ Доступ запрещён!", show_alert=True)
            return
        await q.message.edit_text(
            ADMIN_PANEL_TEXT.format(
                len(users),
                sum(u["orders"] for u in users.values()),
                sum(u["active"] for u in users.values())
            ),
            reply_markup=admin_menu()
        )
        await q.answer()
        return
    
    # ----- ПОКУПКА -----
    if data == "buy":
        await q.message.edit_text(BUY_TEXT.format(
            "\n".join([f"{p['name']} — {p['price']} ₽" for p in products.values()]),
            fmt(user["balance"])
        ), reply_markup=buy_menu(user["balance"]))
        await q.answer()
        return
    
    if data.startswith("buy_"):
        pid = data.replace("buy_", "")
        if pid not in products:
            await q.answer("❌ Товар не найден", show_alert=True)
            return
        p = products[pid]
        if len(user["numbers"]) >= 5:
            await q.answer(MAX_NUMBERS, show_alert=True)
            return
        if user["balance"] < p["price"]:
            await q.answer("❌ Недостаточно средств!", show_alert=True)
            return
        
        nums = get_admin_numbers()
        if nums:
            num = nums.pop(0)
            remove_admin_number(0)
        else:
            num = gen_number()
        
        user["balance"] -= p["price"]
        user["orders"] += 1
        user["numbers"].append({"number": num, "type": p["name"], "price": p["price"]})
        user["active"] += 1
        
        await q.message.reply_text(
            BUY_SUCCESS.format(
                p["name"], num, p["name"], p["price"],
                fmt(user["balance"]), user["active"],
                random.choice(PURCHASE_MSGS)
            )
        )
        await q.answer("✅ Готово!", show_alert=False)
        return
    
    # ----- МОИ НОМЕРА -----
    if data == "my":
        if not user["numbers"]:
            await q.answer(NO_NUMBERS, show_alert=True)
            return
        text = "📋 **ТВОИ НОМЕРА:**\n\n"
        for i, item in enumerate(user["numbers"], 1):
            text += f"{i}. `{item['number']}` — {item['type']} ({item['price']} ₽)\n"
        text += f"\n⚡ Активных: {user['active']}"
        await q.message.edit_text(text, reply_markup=my_numbers_menu(user["numbers"]))
        await q.answer()
        return
    
    if data.startswith("delete_"):
        idx = int(data.split("_")[1])
        if idx >= len(user["numbers"]):
            await q.answer("❌ Номер не найден", show_alert=True)
            return
        deleted = user["numbers"].pop(idx)
        user["active"] = max(0, user["active"] - 1)
        await q.answer(f"🗑 {deleted['number']} удалён!", show_alert=True)
        if not user["numbers"]:
            await q.message.edit_text(
                START_TEXT.format(fmt(user["balance"]), len(user["numbers"]), user["active"]),
                reply_markup=main_menu(uid)
            )
        else:
            text = "📋 **ТВОИ НОМЕРА:**\n\n"
            for i, item in enumerate(user["numbers"], 1):
                text += f"{i}. `{item['number']}` — {item['type']} ({item['price']} ₽)\n"
            text += f"\n⚡ Активных: {user['active']}"
            await q.message.edit_text(text, reply_markup=my_numbers_menu(user["numbers"]))
        return
    
    # ----- БАЛАНС -----
    if data == "balance":
        await q.answer(
            BALANCE_TEXT.format(fmt(user["balance"]), len(user["numbers"]), user["active"]),
            show_alert=True
        )
        return
    
    # ----- БОНУС -----
    if data == "bonus":
        if user.get("bonus_used", False):
            await q.answer("❌ Бонус уже использован!", show_alert=True)
            return
        user["balance"] += 1000
        user["bonus_used"] = True
        await q.answer("🎁 +1000 ₽ на баланс!", show_alert=True)
        await q.message.edit_text(
            START_TEXT.format(fmt(user["balance"]), len(user["numbers"]), user["active"]),
            reply_markup=main_menu(uid)
        )
        return
    
    # ----- ПОМОЩЬ -----
    if data == "help":
        await q.answer(HELP_TEXT, show_alert=True)
        return
    
    # ==================== АДМИНКА ====================
    if data == "admin_products":
        await q.message.edit_text("📦 **ТОВАРЫ:**", reply_markup=admin_products_menu())
        await q.answer()
        return
    
    if data.startswith("admin_product_"):
        pid = data.replace("admin_product_", "")
        if pid not in products:
            await q.answer("❌ Не найден", show_alert=True)
            return
        p = products[pid]
        await q.message.edit_text(
            f"📦 **{p['name']}**\n💰 {p['price']} ₽\n📝 {p['desc']}",
            reply_markup=admin_product_actions(pid)
        )
        await q.answer()
        return
    
    if data.startswith("admin_edit_price_"):
        pid = data.replace("admin_edit_price_", "")
        if not hasattr(admin_text, "state"): admin_text.state = {}
        admin_text.state[uid] = f"price_{pid}"
        await q.message.edit_text("💰 **ВВЕДИ НОВУЮ ЦЕНУ:**")
        await q.answer()
        return
    
    if data.startswith("admin_edit_name_"):
        pid = data.replace("admin_edit_name_", "")
        if not hasattr(admin_text, "state"): admin_text.state = {}
        admin_text.state[uid] = f"name_{pid}"
        await q.message.edit_text("📝 **ВВЕДИ НОВОЕ НАЗВАНИЕ:**")
        await q.answer()
        return
    
    if data.startswith("admin_delete_product_"):
        pid = data.replace("admin_delete_product_", "")
        delete_product(pid)
        await q.answer("🗑 Удалено!", show_alert=True)
        await q.message.edit_text("📦 **ТОВАРЫ:**", reply_markup=admin_products_menu())
        return
    
    if data == "admin_add_product":
        if not hasattr(admin_text, "state"): admin_text.state = {}
        admin_text.state[uid] = "add_product"
        await q.message.edit_text(ADMIN_ADD_PRODUCT_TEXT)
        await q.answer()
        return
    
    if data == "admin_numbers":
        nums = get_admin_numbers()
        text = "📱 **НОМЕРА В ПРОДАЖЕ:**\n\n"
        if nums:
            for idx, num in enumerate(nums, 1):
                text += f"{idx}. `{num}`\n"
        else:
            text += "Нет номеров.\n"
        text += f"\n📊 Всего: {len(nums)}"
        await q.message.edit_text(text, reply_markup=admin_numbers_menu())
        await q.answer()
        return
    
    if data == "admin_add_number":
        await q.message.edit_text(ADMIN_ADD_NUMBER_TEXT)
        await q.answer()
        return
    
    if data.startswith("admin_delete_number_"):
        idx = int(data.split("_")[3])
        removed = remove_admin_number(idx)
        await q.answer(f"🗑 {removed if removed else 'Ошибка'} удалён!", show_alert=True)
        nums = get_admin_numbers()
        text = "📱 **НОМЕРА В ПРОДАЖЕ:**\n\n"
        if nums:
            for i, num in enumerate(nums, 1):
                text += f"{i}. `{num}`\n"
        else:
            text += "Нет номеров.\n"
        text += f"\n📊 Всего: {len(nums)}"
        await q.message.edit_text(text, reply_markup=admin_numbers_menu())
        return
    
    if data == "admin_users":
        ids = get_all_users()
        text = "👥 **ПОЛЬЗОВАТЕЛИ:**\n\n"
        for uid2 in ids[:20]:
            u = get_user(uid2)
            text += f"🆔 {uid2} — {u.get('username', 'без юзера')} | {fmt(u['balance'])} ₽ | {len(u['numbers'])} номеров\n"
        if len(ids) > 20:
            text += f"\n... и ещё {len(ids)-20}"
        await q.message.edit_text(text, reply_markup=admin_users_menu())
        await q.answer()
        return
    
    if data.startswith("admin_user_"):
        target = int(data.replace("admin_user_", ""))
        u = get_user(target)
        await q.message.edit_text(
            f"👤 **ПОЛЬЗОВАТЕЛЬ:** {target}\n"
            f"👤 @{u.get('username', 'нет')}\n"
            f"💰 {fmt(u['balance'])} ₽\n"
            f"📦 {len(u['numbers'])} номеров\n"
            f"⚡ {u['active']} активных\n"
            f"🛒 {u['orders']} покупок",
            reply_markup=admin_user_actions(target)
        )
        await q.answer()
        return
    
    if data.startswith("admin_set_balance_"):
        target = int(data.replace("admin_set_balance_", ""))
        if not hasattr(admin_text, "state"): admin_text.state = {}
        admin_text.state[uid] = f"balance_{target}"
        await q.message.edit_text(f"💰 **ВВЕДИ НОВЫЙ БАЛАНС ДЛЯ {target}:**")
        await q.answer()
        return
    
    if data.startswith("admin_delete_user_"):
        target = int(data.replace("admin_delete_user_", ""))
        if target in users:
            del users[target]
            await q.answer("🗑 Удалён!", show_alert=True)
        else:
            await q.answer("❌ Не найден", show_alert=True)
        ids = get_all_users()
        text = "👥 **ПОЛЬЗОВАТЕЛИ:**\n\n"
        for uid2 in ids[:20]:
            u = get_user(uid2)
            text += f"🆔 {uid2} — {u.get('username', 'без юзера')} | {fmt(u['balance'])} ₽ | {len(u['numbers'])} номеров\n"
        await q.message.edit_text(text, reply_markup=admin_users_menu())
        return
    
    if data == "admin_broadcast":
        if not hasattr(admin_text, "state"): admin_text.state = {}
        admin_text.state[uid] = "broadcast"
        await q.message.edit_text(
            "📢 **РАССЫЛКА**\n\nВведите текст для рассылки.\n/cancel — отмена"
        )
        await q.answer()
        return
    
    if data == "admin_stats":
        await q.message.edit_text(
            f"📊 **СТАТИСТИКА:**\n\n"
            f"👥 Пользователей: {len(users)}\n"
            f"📦 Покупок: {sum(u['orders'] for u in users.values())}\n"
            f"📱 Активных: {sum(u['active'] for u in users.values())}\n"
            f"💰 Общий баланс: {fmt(sum(u['balance'] for u in users.values()))} ₽\n"
            f"📋 Товаров: {len(products)}\n"
            f"📱 Номеров в продаже: {len(get_admin_numbers())}",
            reply_markup=admin_menu()
        )
        await q.answer()
        return
    
    await q.answer()

# ===================================================
#  ЗАПУСК
# ===================================================
if __name__ == "__main__":
    print("ядерка запущена нахуй")
    print(f"👑 БАТЯ: {ADMIN_ID}")
    app.run()