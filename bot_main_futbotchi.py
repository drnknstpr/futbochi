# bot_main_futbotchi.py
from telegram.ext import Application, CommandHandler
from storage import get_user, save_user
from basic_handlers import start_handler, profile_handler

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_handler))
app.add_handler(CommandHandler("profile", profile_handler))

if __name__ == "__main__":
    app.run_polling()
