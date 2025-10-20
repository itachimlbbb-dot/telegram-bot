import logging
import asyncio
import pickle
import os
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

TOKEN = "8324886110:AAEx0B9djsrzGrW-_Wni7GVM6cBe2F_l_1w"

# Foydalanuvchi ma’lumotlarini saqlash fayli
DATA_FILE = "user_data.pkl"

# Logger sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Global foydalanuvchi ma’lumoti
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "rb") as f:
        user_data = pickle.load(f)
else:
    user_data = {}

# Foydalanuvchi ma’lumotlarini saqlovchi funksiya
def save_data():
    with open(DATA_FILE, "wb") as f:
        pickle.dump(user_data, f)

# START komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data.setdefault(user_id, {"early": [], "read": []})
    save_data()

    keyboard = [
        [InlineKeyboardButton("Ha", callback_data="ready_yes")],
        [InlineKeyboardButton("Yo‘q", callback_data="ready_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🧠 Siz o'zingizni butunlay o'zgartirishga tayyormisiz?",
        reply_markup=reply_markup
    )

# Callbacklar (tugma bosilganda)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "ready_yes":
        keyboard = [
            [InlineKeyboardButton("⏰ Erta turish", callback_data="habit_early")],
            [InlineKeyboardButton("📖 Kitob o‘qish", callback_data="habit_read")]
        ]
        await query.edit_message_text("✅ Odatni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "habit_early":
        keyboard = [
            [InlineKeyboardButton("5:00", callback_data="wake_5"),
             InlineKeyboardButton("6:00", callback_data="wake_6")],
            [InlineKeyboardButton("7:00", callback_data="wake_7"),
             InlineKeyboardButton("Boshqa vaqt", callback_data="wake_other")],
        ]
        await query.edit_message_text("Qaysi vaqtda uyg'onmoqchisiz?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("wake_"):
        time = data.replace("wake_", "")
        context.user_data["wake_time"] = time
        keyboard = [
            [InlineKeyboardButton("✅ Bugun erta turdim", callback_data="early_yes")],
            [InlineKeyboardButton("❌ Bugun tura olmadim", callback_data="early_no")]
        ]
        await query.edit_message_text(f"⏰ Siz har kuni soat {time}:00 da turishni tanladingiz.\nBugun chi?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "early_yes":
        user_data[user_id]["early"].append((str(datetime.today().date()), True))
        save_data()
        await query.edit_message_text("✅ Tabriklaymiz! Siz o‘zingizga yangi foydali odat qo‘shyapsiz.\n🎯 Bugungi topshiriqni bajardingiz. Kalendarni ko'rish uchun /calendar ni bosing")
    
    elif data == "early_no":
        user_data[user_id]["early"].append((str(datetime.today().date()), False))
        save_data()
        await query.edit_message_text("❌ Afsus, bugun bajara olmadingiz.\n☀️ Mayli, ertaga harakat qilib ko‘ring! Kalendarni ko'rish uchun /calendar ni bosing")

    elif data == "habit_read":
        keyboard = [
            [InlineKeyboardButton("✅ Bugun o‘qidim", callback_data="read_yes")],
            [InlineKeyboardButton("❌ Bugun o‘qiy olmadim", callback_data="read_no")]
        ]
        await query.edit_message_text("📚 Kuniga 1 bet bo‘lsa ham o‘qing — bu sizning kelajagingiz uchun muhim!\nBugun chi?" , reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "read_yes":
        user_data[user_id]["read"].append((str(datetime.today().date()), True))
        save_data()
        await query.edit_message_text("✅ Ajoyib! Bugungi kitob o‘qish topshirig‘ini bajardingiz. Kalendarni ko'rish uchun /calendar ni bosing")

    elif data == "read_no":
        user_data[user_id]["read"].append((str(datetime.today().date()), False))
        save_data()
        await query.edit_message_text("❌ Bugun o‘qiy olmadingiz.\n📖 Mayli, ertaga harakat qiling. Kalendarni ko'rish uchun /calendar ni bosing")

    elif data == "ready_no":
        await query.edit_message_text("⚠️ Mayli, qachon tayyor bo‘lsangiz, /start buyrug‘ini bosib boshlang!")

# /calendar komandasi
async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        await update.message.reply_text("❌ Sizda hali hech qanday ma’lumot yo‘q.")
        return

    early = user_data[user_id]["early"]
    read = user_data[user_id]["read"]

    text = "📅 Sizning odatlaringiz:\n\n"
    text += "⏰ *Erta turish*\n"
    for date, status in early[-10:]:
        emoji = "✅" if status else "❌"
        text += f"{date}: {emoji}\n"

    text += "\n📖 *Kitob o‘qish*\n"
    for date, status in read[-10:]:
        emoji = "✅" if status else "❌"
        text += f"{date}: {emoji}\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# Botni ishga tushirish
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("calendar", calendar))
    await app.run_polling()

# Event loop muammosi bo‘lsa, nest_asyncio ishlatish kerak
import nest_asyncio
nest_asyncio.apply()

asyncio.get_event_loop().run_until_complete(main())
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom, bot ishlayapti!")

async def main():
    app = ApplicationBuilder().token("8324886110:AAEx0B9djsrzGrW-_Wni7GVM6cBe2F_l_1w").build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    import asyncio
from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Foydalanuvchi chat_id saqlash uchun oddiy ro'yxat
subscribers = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    await update.message.reply_text("Salom! Har kuni ertalab soat 8:00 da sizga xabar yuboraman.")

async def daily_message(app):
    while True:
        now = datetime.now()
        target_time = datetime.combine(now.date(), time(8, 0))  # 8:00 ertalab
        if now > target_time:
            # Keyingi kun 8:00 ga o'tish
            target_time += timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        # Xabar yuborish
        date_str = target_time.strftime("%Y-%m-%d")
        for chat_id in subscribers:
            try:
                await app.bot.send_message(chat_id=chat_id, text=f"Assalomu alaykum! Bugun {date_str}. Ertalab uyg'ondingizmi?")

            except Exception as e:
                print(f"Xabar yuborishda xato: {e}")

async def main():
    app = ApplicationBuilder().token("8324886110:AAEx0B9djsrzGrW-_Wni7GVM6cBe2F_l_1w").build()
    
    app.add_handler(CommandHandler("start", start))
    
    # Background vazifa: har kuni xabar yuborish
    app.create_task(daily_message(app))
    
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

