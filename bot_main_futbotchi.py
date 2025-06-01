# main bot entry point

import os
import logging
import random
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters,
    CallbackContext
)
from storage import storage
from models.team import Team
from handlers.button_handlers import (
    handle_toggle_player,
    handle_support_action,
    create_support_keyboard,
    create_squad_keyboard,
    format_squad_message
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

# Create logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TOKEN:
    raise ValueError("No token found! Make sure you have TELEGRAM_TOKEN in your .env file")

# Debug print
logger.info(f"Starting bot with token: {TOKEN}")

# Constants
PLAYER_COST = 1000  # Стоимость покупки игрока

# Keyboard layouts
MAIN_KEYBOARD = ReplyKeyboardMarkup([
    ['💼 Состав', '💰 Поддержать клуб'],
    ['🎲 Купить игрока', '🏟 Играть матч'],
    ['🏆 Топ', '🧑 Профиль'],
    ['❓ Напомни, что за бот']
], resize_keyboard=True)

def get_bot_info():
    """Возвращает информационное сообщение о боте"""
    return (
        "Добро пожаловать в игру Futbochi! ⚽️\n\n"
        "В этой игре ты создаешь свою футбольную команду:\n"
        "• Покупай новых игроков 📦\n"
        "• Управляй составом 👥\n"
        "• Играй матчи ⚽️\n"
        "• Тренируй игроков 💪\n"
        "• Зарабатывай очки и монеты 🏆\n\n"
        "Основные команды:\n"
        "💼 Состав - управление игроками\n"
        "💰 Поддержать клуб - получить бонусы\n"
        "🎲 Купить игрока - приобрести нового игрока\n"
        "🏟 Играть матч - сыграть против другой команды\n"
        "🏆 Топ - таблица лидеров\n"
        "🧑 Профиль - информация о команде\n"
        "📅 События - специальные мероприятия\n\n"
        "Удачи в создании своей футбольной империи! 🏆"
    )

def start(update: Update, context: CallbackContext):
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
            f"{get_bot_info()}\n\n"
            "Я создал для тебя команду и выдал тебе стартовых игроков:\n"
            f"• {starter_players[0]['name']} (Common)\n"
            f"• {starter_players[1]['name']} (Common)\n"
            f"• {starter_players[2]['name']} (Rare)"
        )
    else:
        welcome_message = (
            f"С возвращением, {user.first_name}! 👋\n\n"
            "Твоя команда ждет тебя! Используй кнопки ниже, чтобы продолжить игру."
        )
    
    # Отправляем приветственное изображение вместе с сообщением
    with open('media/welcome.png', 'rb') as photo:
        update.message.reply_photo(
            photo=photo,
            caption=welcome_message,
            reply_markup=MAIN_KEYBOARD,
            parse_mode='HTML'
        )

def show_squad(update: Update, context: CallbackContext):
    """Показать состав команды"""
    user_id = str(update.effective_user.id)
    team = storage.get_team(user_id)
    if not team:
        update.message.reply_text("Сначала начните игру командой /start")
        return

    squad_message = format_squad_message(team)
    keyboard = create_squad_keyboard(team)
    update.message.reply_text(squad_message, reply_markup=keyboard)

def support_club(update: Update, context: CallbackContext):
    """Поддержать клуб"""
    user_id = str(update.effective_user.id)
    team = storage.get_team(user_id)
    if not team:
        update.message.reply_text("Сначала начните игру командой /start")
        return

    if not team.can_support():
        update.message.reply_text("Подождите 2 минуты перед следующей поддержкой клуба")
        return

    keyboard = create_support_keyboard()
    update.message.reply_text(
        "Выберите действие для поддержки клуба:",
        reply_markup=keyboard
    )

def create_sirena_keyboard(bonus_type: str):
    """Create keyboard for SirenaBet bonus"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎁 Забрать", url="sirena.team")
        ]
    ])
    return keyboard

def buy_player(update: Update, context: CallbackContext):
    """Покупка нового игрока"""
    user = update.effective_user
    user_id = str(user.id)
    
    team = storage.get_team(user_id)
    if not team:
        update.message.reply_text("Сначала создайте команду с помощью /start")
        return

    # Проверка лимита покупок
    if not team.can_buy_player():
        if team.can_use_sirena_player_bonus():
            update.message.reply_text(
                "Трансферный лимит 3 игрока за 10 минут!\n"
                "Но «СиренаБет» спешит на помощь!\n"
                "Нажми по ссылке, сделай депозит, и получи одного игрока.",
                reply_markup=create_sirena_keyboard("player")
            )
            return
        else:
            update.message.reply_text(
                "Достигнут лимит покупок (4 игрока за 10 минут).\n"
                "Подождите некоторое время."
            )
            return

    # Проверка наличия денег
    if team.money < PLAYER_COST:
        if team.can_use_sirena_no_money_bonus():
            update.message.reply_text(
                "Кончились деньги! Но «СиренаБет» спешит на помощь!\n"
                "Нажми по ссылке, сделай депозит, и получи одного игрока.",
                reply_markup=create_sirena_keyboard("nomoney")
            )
            return
        else:
            update.message.reply_text(
                f"Недостаточно монет для покупки игрока.\n"
                f"Нужно: {PLAYER_COST} 🪙\nУ вас есть: {team.money} 🪙"
            )
            return

    # Загружаем базу игроков
    players_db = storage.load_players_database()
    
    # Выбираем случайного игрока с учетом редкости
    rarity = random.choices(
        list(players_db["rarity_chances"].keys()),
        list(players_db["rarity_chances"].values())
    )[0]
    
    available_players = [p for p in players_db["players"] if p["rarity"] == rarity]
    if not available_players:
        update.message.reply_text("Ошибка: не удалось найти подходящего игрока")
        return
    
    player = random.choice(available_players)
    
    # Добавляем игрока в команду
    team.add_player(player)
    team.add_player_purchase()  # Записываем покупку
    team.money -= PLAYER_COST
    
    # Определяем эмодзи для редкости
    rarity_emoji = {
        "common": "⚪️",
        "rare": "🔵",
        "epic": "🟣",
        "legendary": "🟡"
    }
    
    # Формируем сообщение о купленном игроке
    message = f"✅ Вы купили нового игрока:\n\n"
    message += f"{rarity_emoji[player['rarity']]} {player['name']}\n"
    message += f"Редкость: {player['rarity'].capitalize()}\n\n"
    message += "Характеристики:\n"
    message += f"⚡️ Скорость: {player['stats']['speed']}\n"
    message += f"🧠 Менталка: {player['stats']['mentality']}\n"
    message += f"⚽️ Удар: {player['stats']['finishing']}\n"
    message += f"🛡 Защита: {player['stats']['defense']}"
    
    storage.save_team(user_id, team)
    update.message.reply_text(message)

def calculate_team_strength(team_power):
    """Calculate team strength based on stats"""
    # Weights for different stats
    weights = {
        'speed': 0.25,
        'mentality': 0.2,
        'finishing': 0.35,
        'defense': 0.2
    }
    
    # Calculate weighted strength
    strength = sum(team_power[stat] * weight for stat, weight in weights.items())
    return strength / 100  # Convert to 0-1 range

def calculate_team_rating(team_power):
    """Calculate overall team rating based on power stats"""
    # Веса для расчета общего рейтинга
    weights = {
        'speed': 0.25,
        'mentality': 0.2,
        'finishing': 0.35,
        'defense': 0.2
    }
    
    rating = sum(team_power[stat] * weight for stat, weight in weights.items())
    return round(rating, 1)

def generate_match_events(team, opponent, difficulty):
    """Generate match events and calculate the result"""
    try:
        # Load match data
        with open('data/match_data.json', 'r', encoding='utf-8') as f:
            match_data = json.load(f)
        
        # Initialize variables
        events = []
        team_goals = 0
        team_power = team.get_team_power()
        team_rating = calculate_team_rating(team_power)
        
        # Get opponent strength from data
        opponent_strength = opponent['strength']
        opponent_rating = opponent_strength * 10  # Конвертируем в такой же формат как у команды игрока
        
        # Рассчитываем базовую вероятность гола для команды игрока
        # Учитываем параметр удара и общий рейтинг
        finishing_factor = team_power['finishing'] / 100  # 0-1
        rating_factor = team_rating / 10  # 0-1
        
        # Базовый шанс гола зависит от сложности
        difficulty_goal_chance = {
            'easy': 0.4,    # 40% базовый шанс на легком
            'medium': 0.35,  # 35% на среднем
            'hard': 0.3     # 30% на сложном
        }
        
        base_goal_chance = difficulty_goal_chance[difficulty]
        
        # Финальный шанс гола учитывает удар, рейтинг и сложность
        team_goal_chance = base_goal_chance * (0.6 * finishing_factor + 0.4 * rating_factor)
        
        # Для каждой атаки проверяем шанс гола
        num_attacks = 5  # Увеличиваем количество атак
        for _ in range(num_attacks):
            # Выбираем случайного игрока
            player = random.choice(team.active_players)
            
            # Проверяем успешность атаки
            if random.random() < team_goal_chance:
                # Гол!
                action = random.choice([a for a in match_data['match_actions']['positive'] if a['is_goal']])
                team_goals += 1
                events.append(f"{player['name']}... {action['action']}")
            else:
                # Неудачная атака
                if random.random() < 0.7:  # 70% шанс позитивного события
                    action = random.choice([a for a in match_data['match_actions']['positive'] if not a['is_goal']])
                else:
                    action = random.choice(match_data['match_actions']['negative'])
                events.append(f"{player['name']}... {action['action']}")
        
        # Рассчитываем голы соперника
        opponent_goals = 0
        opponent_attacks = 4  # Меньше атак у соперника
        
        # Защита команды влияет на шансы соперника
        defense_factor = team_power['defense'] / 100
        opponent_goal_chance = opponent_strength * (1 - defense_factor * 0.5)  # Защита блокирует до 50% шансов
        
        for _ in range(opponent_attacks):
            if random.random() < opponent_goal_chance:
                opponent_goals += 1
        
        # Генерируем сообщение о результате
        if team_goals > opponent_goals:
            result = f"🎉 Ваша команда обыграла «{opponent['name']}» со счётом {team_goals}:{opponent_goals}!"
        elif team_goals < opponent_goals:
            result = f"😔 Ваша команда проиграла «{opponent['name']}» со счётом {team_goals}:{opponent_goals}"
        else:
            result = f"🤝 Ничья с «{opponent['name']}» {team_goals}:{opponent_goals}"
        
        return {
            'events': events,
            'result': result,
            'team_goals': team_goals,
            'opponent_goals': opponent_goals,
            'team_strength': team_rating / 10,  # Конвертируем обратно в 0-1
            'opponent_strength': opponent_strength,
            'difficulty': difficulty
        }
        
    except Exception as e:
        logger.error(f"Error generating match events: {e}", exc_info=True)
        raise

def create_match_difficulty_keyboard():
    """Create keyboard for match difficulty selection"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚪️ Легкий матч (награда: 200-400 монет)", callback_data="match_easy")],
        [InlineKeyboardButton("🔵 Средний матч (награда: 400-800 монет)", callback_data="match_medium")],
        [InlineKeyboardButton("🔴 Сложный матч (награда: 800-1500 монет)", callback_data="match_hard")]
    ])
    return keyboard

def play_match(update: Update, context: CallbackContext):
    """Показать выбор сложности матча"""
    user_id = str(update.effective_user.id)
    team = storage.get_team(user_id)
    if not team:
        update.message.reply_text("Сначала начните игру командой /start")
        return

    if len(team.active_players) == 0:
        update.message.reply_text("Сначала выберите активных игроков в составе!")
        return

    # Проверка лимита матчей
    if not team.can_play_match():
        if team.can_use_sirena_match_bonus():
            update.message.reply_text(
                "Лимит матчей 3 матча за 10 минут!\n"
                "Но «СиренаБет» спешит на помощь!\n"
                "Нажми по ссылке, сделай депозит, и сыграй еще 1 матч.",
                reply_markup=create_sirena_keyboard("match")
            )
            return
        else:
            update.message.reply_text(
                "Достигнут лимит матчей (3 матча за 10 минут).\n"
                "Подождите некоторое время."
            )
            return

    keyboard = create_match_difficulty_keyboard()
    update.message.reply_text(
        "🏟 Выберите сложность матча:\n\n"
        "⚪️ Легкий матч - против слабых команд\n"
        "🔵 Средний матч - против команд среднего уровня\n"
        "🔴 Сложный матч - против топ-клубов\n\n"
        "Чем сложнее матч, тем больше награда за победу!",
        reply_markup=keyboard
    )

def calculate_match_probabilities(team_rating, opponent_strength):
    """Calculate win/draw/lose probabilities based on team ratings"""
    # Конвертируем силу соперника в рейтинг (примерно такой же алгоритм как у команды игрока)
    opponent_rating = opponent_strength * 10  # Сила 0.8 = рейтинг 8.0
    
    # Разница в рейтинге влияет на вероятности
    rating_diff = team_rating - opponent_rating
    
    # Базовые вероятности
    if rating_diff >= 2:  # Намного сильнее
        win_prob = 0.7
        draw_prob = 0.2
        lose_prob = 0.1
    elif rating_diff >= 1:  # Немного сильнее
        win_prob = 0.5
        draw_prob = 0.3
        lose_prob = 0.2
    elif rating_diff >= -1:  # Примерно равны
        win_prob = 0.35
        draw_prob = 0.3
        lose_prob = 0.35
    elif rating_diff >= -2:  # Немного слабее
        win_prob = 0.2
        draw_prob = 0.3
        lose_prob = 0.5
    else:  # Намного слабее
        win_prob = 0.1
        draw_prob = 0.2
        lose_prob = 0.7
    
    return {
        'win': round(win_prob * 100),
        'draw': round(draw_prob * 100),
        'lose': round(lose_prob * 100)
    }

def handle_match_difficulty(update: Update, context: CallbackContext):
    """Handle match difficulty selection"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    difficulty = query.data.split('_')[1]  # match_easy -> easy
    
    logger.info(f"Starting match with difficulty: {difficulty} for user: {user_id}")
    
    team = storage.get_team(user_id)
    if not team:
        logger.error(f"Team not found for user {user_id}")
        query.answer("Ошибка: команда не найдена")
        return
    
    try:
        # Load match data
        logger.info("Loading match data...")
        with open('data/match_data.json', 'r', encoding='utf-8') as f:
            match_data = json.load(f)
        
        # Select random opponent based on difficulty
        logger.info(f"Selecting opponent for difficulty: {difficulty}")
        if difficulty not in match_data['opponent_teams']:
            logger.error(f"Invalid difficulty level: {difficulty}")
            raise ValueError(f"Invalid difficulty level: {difficulty}")
            
        opponent = random.choice(match_data['opponent_teams'][difficulty])
        logger.info(f"Selected opponent: {opponent['name']}")
        
        # Calculate team rating and probabilities
        logger.info("Calculating team power and probabilities...")
        team_power = team.get_team_power()
        team_rating = calculate_team_rating(team_power)
        probabilities = calculate_match_probabilities(team_rating, opponent['strength'])
        
        # Edit message to show match preview
        preview_message = (
            f"⚔️ Предматчевая информация:\n\n"
            f"👥 {team.name}\n"
            f"⭐️ Рейтинг: {team_rating}\n\n"
            f"👥 {opponent['name']}\n"
            f"⭐️ Рейтинг: {round(opponent['strength'] * 10, 1)}\n\n"
            f"📊 Вероятности исхода:\n"
            f"✅ Победа: {probabilities['win']}%\n"
            f"🤝 Ничья: {probabilities['draw']}%\n"
            f"❌ Поражение: {probabilities['lose']}%\n\n"
            f"⏳ Матч начинается..."
        )
        query.edit_message_text(preview_message)
        
        # Generate and process match events
        logger.info("Generating match events...")
        match_result = generate_match_events(team, opponent, difficulty)
        
        # Send match events with delay
        logger.info("Sending match events...")
        for event in match_result['events']:
            context.bot.send_message(chat_id=update.effective_chat.id, text=event)
            time.sleep(2)  # 2-second delay between events
        
        # Send final result
        context.bot.send_message(chat_id=update.effective_chat.id, text=match_result['result'])
        
        # Calculate rewards based on difficulty and opponent strength
        logger.info("Calculating rewards...")
        reward_ranges = {
            'easy': (200, 400),
            'medium': (400, 800),
            'hard': (800, 1500)
        }
        
        base_min, base_max = reward_ranges[difficulty]
        strength_factor = match_result['opponent_strength']
        
        if match_result['team_goals'] > match_result['opponent_goals']:
            # Win reward
            reward = int(base_min + (base_max - base_min) * strength_factor)
            team.add_points(3)
            team.add_money(reward)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"💰 Награда за победу: +{reward} монет"
            )
        elif match_result['team_goals'] == match_result['opponent_goals']:
            # Draw reward
            reward = int((base_min + (base_max - base_min) * strength_factor) * 0.4)  # 40% of win reward
            team.add_points(1)
            team.add_money(reward)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"💰 Награда за ничью: +{reward} монет"
            )
        
        # Записываем сыгранный матч
        logger.info("Saving match result...")
        team.add_match_played()
        storage.save_team(user_id, team)
        logger.info("Match completed successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_match_difficulty: {str(e)}", exc_info=True)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Произошла ошибка во время матча: {str(e)}"
        )

def show_top(update: Update, context: CallbackContext):
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

    update.message.reply_text(top_message)

def show_profile(update: Update, context: CallbackContext):
    """Показать профиль команды"""
    user_id = str(update.effective_user.id)
    team = storage.get_team(user_id)
    if not team:
        update.message.reply_text("Сначала начните игру командой /start")
        return

    profile_message = (
        f"🧑 Профиль команды {team.name}\n\n"
        f"💰 Деньги: {team.money}\n"
        f"🏆 Очки: {team.points}\n"
        f"👥 Игроков в составе: {len(team.squad)}/22\n"
        f"🌟 Активных игроков: {len(team.active_players)}/3\n\n"
        "Сила команды:\n"
        f"⚡️ Скорость: {team.get_team_power()['speed']}\n"
        f"🧠 Менталка: {team.get_team_power()['mentality']}\n"
        f"⚽️ Удар: {team.get_team_power()['finishing']}\n"
        f"🛡 Защита: {team.get_team_power()['defense']}"
    )

    update.message.reply_text(profile_message)

def handle_text(update: Update, context: CallbackContext):
    """Обработка текстовых сообщений"""
    text = update.message.text
    
    if text == "💼 Состав":
        show_squad(update, context)
    elif text == "💰 Поддержать клуб":
        support_club(update, context)
    elif text == "🎲 Купить игрока":
        buy_player(update, context)
    elif text == "🏟 Играть матч":
        play_match(update, context)
    elif text == "🏆 Топ":
        show_top(update, context)
    elif text == "🧑 Профиль":
        show_profile(update, context)
    elif text == "❓ Напомни, что за бот":
        update.message.reply_text(
            get_bot_info(),
            reply_markup=MAIN_KEYBOARD
        )

def handle_sirena_callback(update: Update, context: CallbackContext):
    """Обработка нажатия на кнопку Забрать от SirenaBet"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    action_type = query.data.split('_')[1]  # sirena_player, sirena_match, sirena_nomoney
    
    team = storage.get_team(user_id)
    if not team:
        query.answer("Ошибка: команда не найдена")
        return
    
    try:
        # Проверяем, можно ли использовать бонус
        if action_type == 'match' and not team.can_use_sirena_match_bonus():
            query.answer("Бонус уже был использован")
            return
        elif action_type == 'player' and not team.can_use_sirena_player_bonus():
            query.answer("Бонус уже был использован")
            return
        elif action_type == 'nomoney' and not team.can_use_sirena_no_money_bonus():
            query.answer("Бонус уже был использован")
            return

        if action_type == 'match':
            # Отмечаем использование бонуса на матч
            team.use_sirena_match_bonus()
            storage.save_team(user_id, team)
            
            # Отправляем сообщение об успешном получении бонусного матча
            query.edit_message_text(
                "✅ Вы получили бонусный матч от SirenaBet!\n"
                "Теперь вы можете сыграть еще один матч."
            )
            return

        # Обработка других типов бонусов...
        # Загружаем базу игроков
        players_db = storage.load_players_database()
        
        # Для бонусного игрока выбираем из common или rare
        available_players = [p for p in players_db["players"] if p["rarity"] in ["common", "rare"]]
        if not available_players:
            query.answer("Ошибка: не удалось найти подходящего игрока")
            return
        
        # Выбираем случайного игрока
        player = random.choice(available_players)
        
        # Добавляем игрока в команду
        team.add_player(player)
        
        # Отмечаем использование бонуса
        if action_type == 'player':
            team.use_sirena_player_bonus()
        else:  # nomoney
            team.use_sirena_no_money_bonus()
        
        # Определяем эмодзи для редкости
        rarity_emoji = {
            "common": "⚪️",
            "rare": "🔵",
            "epic": "🟣",
            "legendary": "🟡"
        }
        
        # Формируем сообщение о полученном игроке
        message = f"🎁 Вы получили бонусного игрока от SirenaBet:\n\n"
        message += f"{rarity_emoji[player['rarity']]} {player['name']}\n"
        message += f"Редкость: {player['rarity'].capitalize()}\n\n"
        message += "Характеристики:\n"
        message += f"⚡️ Скорость: {player['stats']['speed']}\n"
        message += f"🧠 Менталка: {player['stats']['mentality']}\n"
        message += f"⚽️ Удар: {player['stats']['finishing']}\n"
        message += f"🛡 Защита: {player['stats']['defense']}"
        
        storage.save_team(user_id, team)
        query.edit_message_text(message)
        
    except Exception as e:
        logger.error(f"Error in handle_sirena_callback: {str(e)}", exc_info=True)
        query.answer("Произошла ошибка при обработке бонуса")

def main():
    """Start the bot"""
    # Initialize bot and create dispatcher
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.regex('^💼 Состав$'), show_squad))
    dispatcher.add_handler(MessageHandler(Filters.regex('^🎲 Купить игрока$'), buy_player))
    dispatcher.add_handler(MessageHandler(Filters.regex('^🏟 Играть матч$'), play_match))
    dispatcher.add_handler(MessageHandler(Filters.regex('^💰 Поддержать клуб$'), support_club))
    dispatcher.add_handler(MessageHandler(Filters.regex('^❓ Напомни, что за бот$'), get_bot_info))
    
    # Callback handlers
    dispatcher.add_handler(CallbackQueryHandler(handle_toggle_player, pattern='^toggle_player_'))
    dispatcher.add_handler(CallbackQueryHandler(handle_support_action, pattern='^support_'))
    dispatcher.add_handler(CallbackQueryHandler(handle_match_difficulty, pattern='^match_'))
    dispatcher.add_handler(CallbackQueryHandler(handle_sirena_callback, pattern='^sirena_'))

    # Start the bot
    logger.info("Starting bot...")
    updater.start_polling()
    logger.info("Bot is running!")
    
    # Run the bot until you press Ctrl-C
    print("Bot is running! Press Ctrl+C to stop.")
    updater.idle()

if __name__ == "__main__":
    main()
