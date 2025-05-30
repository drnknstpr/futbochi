from telegram import Update
from telegram.ext import ContextTypes
from storage import get_user

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    await update.message.reply_text("Привет! Добро пожаловать в Футботчи ⚽️")

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    name = user.get("name") or update.effective_user.first_name
    money = user.get("money", 0)
    points = user.get("points", 0)
    await update.message.reply_text(f"👤 {name}\nОчки: {points}\nДеньги: {money}₽")
