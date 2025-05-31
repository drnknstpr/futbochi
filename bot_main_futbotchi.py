# main bot entry point

import os
import logging
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from storage import storage
from models.team import Team

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Constants
PLAYER_COST = 1000  # Стоимость покупки игрока

# Debug print
print(f"Using token: {TOKEN}")

# Keyboard layouts
MAIN_KEYBOARD = ReplyKeyboardMarkup([
    ['💼 Состав', '💰 Поддержать клуб'],
    ['🎲 Купить игрока', '🏟 Играть матч'],
    ['🏆 Топ', '🧑 Профиль'],
    ['📅 События']
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы с ботом"""
    user = update.effective_user
    user_id = str(user.id)
    
    team = storage.get_team(user_id)
    if not team:
        # Создаем новую команду
        team = Team(f"FC {user.first_name}")
        # Добавляем стартовых игроков
        players_db = storage.load_players_database()
        
        # Находим common игроков
        common_players = [p for p in players_db["players"] if p["rarity"] == "common"]
        # Находим rare игроков
        rare_players = [p for p in players_db["players"] if p["rarity"] == "rare"]
        
        # Выбираем случайных игроков
        starter_players = random.sample(common_players, 2) + random.sample(rare_players, 1)
        
        for player in starter_players:
            team.add_player(player)
        team.set_active_players([p["id"] for p in starter_players])
        
        # Сохраняем команду
        storage.save_team(user_id, team)
        
        welcome_message = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Добро пожаловать в игру Futbochi! ⚽️\n\n"
            "Я создал для тебя команду и выдал тебе стартовых игроков:\n"
            f"• {starter_players[0]['name']} (Common)\n"
            f"• {starter_players[1]['name']} (Common)\n"
            f"• {starter_players[2]['name']} (Rare)\n\n"
            "Используй кнопки ниже, чтобы:\n"
            "• Посмотреть свою команду 👥\n"
            "• Открыть паки с новыми игроками 📦\n"
            "• Играть матчи ⚽️\n"
            "• Тренировать игроков 💪\n\n"
            "Удачи в создании своей футбольной империи! 🏆"
        )
    else:
        welcome_message = (
            f"С возвращением, {user.first_name}! 👋\n\n"
            "Твоя команда ждет тебя! Используй кнопки ниже, чтобы продолжить игру."
        )
    
    # Отправляем приветственное изображение вместе с сообщением
    with open('media/welcome.png', 'rb') as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=welcome_message,
            reply_markup=MAIN_KEYBOARD,
            parse_mode='HTML'
        )

async def show_squad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать состав команды"""
    user_id = str(update.effective_user.id)
    team = storage.get_team(user_id)
    if not team:
        await update.message.reply_text("Сначала начните игру командой /start")
        return

    squad_message = "📋 Ваш состав:\n\n"
    squad_message += "⚜️ Характеристики игроков:\n"
    squad_message += "⚡️ Скорость\n"
    squad_message += "🧠 Ментальность\n"
    squad_message += "⚽️ Удар\n"
    squad_message += "🛡 Защита\n\n"
    
    squad_message += "🌟 Активные игроки:\n"
    for player in team.active_players:
        stats = player['stats']
        squad_message += (
            f"• {player['name']} ({player['rarity']})\n"
            f"  ⚡️ {stats['speed']} 🧠 {stats['mentality']} "
            f"⚽️ {stats['finishing']} 🛡 {stats['defense']}\n"
        )
    
    squad_message += "\n📝 Полный состав:\n"
    bench = [p for p in team.squad if p not in team.active_players]
    for player in bench:
        stats = player['stats']
        squad_message += (
            f"• {player['name']} ({player['rarity']})\n"
            f"  ⚡️ {stats['speed']} 🧠 {stats['mentality']} "
            f"⚽️ {stats['finishing']} 🛡 {stats['defense']}\n"
        )

    # Создаем кнопки для управления составом
    keyboard = []
    for player in team.squad:
        is_active = player in team.active_players
        status = "✅" if is_active else "➕"
        keyboard.append([InlineKeyboardButton(
            f"{status} {player['name']} ({player['rarity']})",
            callback_data=f"toggle_player_{player['id']}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(squad_message, reply_markup=reply_markup)

async def toggle_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на игроков в составе"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    team = storage.get_team(user_id)
    if not team:
        await query.edit_message_text("Сначала начните игру командой /start")
        return

    player_id = int(query.data.split('_')[-1])
    current_active_ids = [p['id'] for p in team.active_players]
    
    if player_id in current_active_ids:
        current_active_ids.remove(player_id)
    else:
        if len(current_active_ids) >= 3:
            await query.edit_message_text("Максимум 3 активных игрока!")
            return
        current_active_ids.append(player_id)
    
    team.set_active_players(current_active_ids)
    storage.save_team(user_id, team)
    
    # Обновляем сообщение с составом
    squad_message = "📋 Ваш состав:\n\n"
    squad_message += "⚜️ Характеристики игроков:\n"
    squad_message += "⚡️ Скорость\n"
    squad_message += "🧠 Ментальность\n"
    squad_message += "⚽️ Удар\n"
    squad_message += "🛡 Защита\n\n"
    
    squad_message += "🌟 Активные игроки:\n"
    for player in team.active_players:
        stats = player['stats']
        squad_message += (
            f"• {player['name']} ({player['rarity']})\n"
            f"  ⚡️ {stats['speed']} 🧠 {stats['mentality']} "
            f"⚽️ {stats['finishing']} 🛡 {stats['defense']}\n"
        )
    
    squad_message += "\n📝 Полный состав:\n"
    bench = [p for p in team.squad if p not in team.active_players]
    for player in bench:
        stats = player['stats']
        squad_message += (
            f"• {player['name']} ({player['rarity']})\n"
            f"  ⚡️ {stats['speed']} 🧠 {stats['mentality']} "
            f"⚽️ {stats['finishing']} 🛡 {stats['defense']}\n"
        )

    # Обновляем кнопки
    keyboard = []
    for player in team.squad:
        is_active = player in team.active_players
        status = "✅" if is_active else "➕"
        keyboard.append([InlineKeyboardButton(
            f"{status} {player['name']} ({player['rarity']})",
            callback_data=f"toggle_player_{player['id']}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(squad_message, reply_markup=reply_markup)

async def support_club(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поддержать клуб"""
    user_id = str(update.effective_user.id)
    team = storage.get_team(user_id)
    if not team:
        await update.message.reply_text("Сначала начните игру командой /start")
        return

    if not team.can_support():
        await update.message.reply_text("Подождите 12 часов перед следующей поддержкой клуба")
        return

    keyboard = [
        [InlineKeyboardButton("💰 Дать денег (+500)", callback_data="support_money")],
        [InlineKeyboardButton("👤 Подписать игрока", callback_data="support_player")],
        [InlineKeyboardButton("📋 Выбрать стратегию", callback_data="support_strategy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите действие для поддержки клуба:",
        reply_markup=reply_markup
    )

async def support_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий поддержки клуба"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    team = storage.get_team(user_id)
    if not team:
        await query.edit_message_text("Сначала начните игру командой /start")
        return

    action = query.data.split('_')[1]
    success, message = team.support_club(action)
    
    if success:
        if action == "player":
            # Даем случайного игрока
            players_db = storage.load_players_database()
            rarity = random.choices(
                list(players_db["rarity_chances"].keys()),
                list(players_db["rarity_chances"].values())
            )[0]
            available_players = [p for p in players_db["players"] if p["rarity"] == rarity]
            if available_players:
                player = random.choice(available_players)
                team.add_player(player)
                message = f"Вы подписали {player['name']} ({player['rarity']})!"
        
        storage.save_team(user_id, team)
        await query.edit_message_text(message)
    else:
        await query.edit_message_text("Произошла ошибка. Попробуйте позже.")

async def buy_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка нового игрока"""
    user = update.effective_user
    user_id = str(user.id)
    
    team = storage.get_team(user_id)
    if not team:
        await update.message.reply_text("Сначала создайте команду с помощью /start")
        return

    if team.money < PLAYER_COST:
        await update.message.reply_text(
            f"Недостаточно монет для покупки игрока. Нужно: {PLAYER_COST} 🪙\nУ вас есть: {team.money} 🪙"
        )
        return

    players_db = storage.load_players_database()
    
    # Определяем шансы выпадения для каждой редкости
    rarity_chances = {
        "common": 0.60,    # 60%
        "rare": 0.25,      # 25%
        "epic": 0.10,      # 10%
        "legendary": 0.05  # 5%
    }
    
    # Выбираем редкость на основе шансов
    rarity = random.choices(
        list(rarity_chances.keys()),
        weights=list(rarity_chances.values())
    )[0]
    
    # Фильтруем игроков по выбранной редкости
    available_players = [p for p in players_db["players"] if p["rarity"] == rarity]
    
    if not available_players:
        await update.message.reply_text("Ошибка: не удалось найти подходящего игрока")
        return
    
    # Выбираем случайного игрока из доступных
    player = random.choice(available_players)
    
    # Добавляем игрока в команду
    team.add_player(player)
    team.money -= PLAYER_COST
    storage.save_team(user_id, team)
    
    # Определяем эмодзи для редкости
    rarity_emoji = {
        "common": "⚪️",
        "rare": "🔵",
        "epic": "🟣",
        "legendary": "🟡"
    }
    
    # Формируем сообщение о покупке
    message = f"Поздравляем! Вы купили нового игрока:\n\n{rarity_emoji[player['rarity']]} {player['name']}\n"
    message += f"Редкость: {player['rarity'].capitalize()}\n\n"
    message += "Характеристики:\n"
    message += f"⚡️ Скорость: {player['stats']['speed']}\n"
    message += f"🧠 Мышление: {player['stats']['mentality']}\n"
    message += f"⚽️ Удар: {player['stats']['finishing']}\n"
    message += f"🛡 Защита: {player['stats']['defense']}\n\n"
    message += f"Осталось монет: {team.money} 🪙"
    
    await update.message.reply_text(message)

async def play_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Играть матч"""
    user_id = str(update.effective_user.id)
    team = storage.get_team(user_id)
    if not team:
        await update.message.reply_text("Сначала начните игру командой /start")
        return

    if not team.can_play_match():
        await update.message.reply_text("Подождите 1 час перед следующим матчем")
        return

    if len(team.active_players) == 0:
        await update.message.reply_text("Сначала выберите активных игроков в составе!")
        return

    keyboard = [
        [InlineKeyboardButton("🟢 Легкий матч", callback_data="match_easy")],
        [InlineKeyboardButton("🟡 Средний матч", callback_data="match_medium")],
        [InlineKeyboardButton("🔴 Сложный матч", callback_data="match_hard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "Выберите сложность матча:\n\n"
        "🟢 Легкий: 100 монет, 1 очко\n"
        "🟡 Средний: 300 монет, 3 очка\n"
        "🔴 Сложный: 500 монет, 5 очков\n\n"
        "Сила вашей команды:\n"
        f"⚡️ Скорость: {team.get_team_power()['speed']}\n"
        f"🧠 Ментальность: {team.get_team_power()['mentality']}\n"
        f"⚽️ Удар: {team.get_team_power()['finishing']}\n"
        f"🛡 Защита: {team.get_team_power()['defense']}"
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def match_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора сложности матча"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    team = storage.get_team(user_id)
    if not team:
        await query.edit_message_text("Сначала начните игру командой /start")
        return

    difficulty = query.data.split('_')[1]
    success, result, money, points = team.play_match(difficulty)
    
    if success:
        message = (
            f"{result}\n"
            f"Получено:\n"
            f"💰 {money} монет\n"
            f"🏆 {points} очков"
        )
        storage.save_team(user_id, team)
        await query.edit_message_text(message)
    else:
        await query.edit_message_text(result)

async def show_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать таблицу лидеров"""
    teams = storage.get_all_teams()
    sorted_teams = sorted(
        teams.items(),
        key=lambda x: x[1].points,
        reverse=True
    )

    top_message = "🏆 Таблица лидеров:\n\n"
    for i, (user_id, team) in enumerate(sorted_teams[:10], 1):
        top_message += f"{i}. {team.name}: {team.points} очков\n"

    await update.message.reply_text(top_message)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль команды"""
    user_id = str(update.effective_user.id)
    team = storage.get_team(user_id)
    if not team:
        await update.message.reply_text("Сначала начните игру командой /start")
        return

    profile_message = (
        f"🧑 Профиль команды {team.name}\n\n"
        f"💰 Деньги: {team.money}\n"
        f"🏆 Очки: {team.points}\n"
        f"👥 Игроков в составе: {len(team.squad)}/22\n"
        f"🌟 Активных игроков: {len(team.active_players)}/3\n\n"
        "Сила команды:\n"
        f"⚡️ Скорость: {team.get_team_power()['speed']}\n"
        f"🧠 Ментальность: {team.get_team_power()['mentality']}\n"
        f"⚽️ Удар: {team.get_team_power()['finishing']}\n"
        f"🛡 Защита: {team.get_team_power()['defense']}"
    )

    await update.message.reply_text(profile_message)

async def show_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать события"""
    await update.message.reply_text(
        "📅 События в разработке!\n"
        "Следите за обновлениями."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text
    
    if text == "💼 Состав":
        await show_squad(update, context)
    elif text == "💰 Поддержать клуб":
        await support_club(update, context)
    elif text == "🎲 Купить игрока":
        await buy_player(update, context)
    elif text == "🏟 Играть матч":
        await play_match(update, context)
    elif text == "🏆 Топ":
        await show_top(update, context)
    elif text == "🧑 Профиль":
        await show_profile(update, context)
    elif text == "📅 События":
        await show_events(update, context)

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Добавляем обработчики текста
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Добавляем обработчики callback
    application.add_handler(CallbackQueryHandler(toggle_player, pattern="^toggle_player_"))
    application.add_handler(CallbackQueryHandler(support_callback, pattern="^support_"))
    application.add_handler(CallbackQueryHandler(match_callback, pattern="^match_"))

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
