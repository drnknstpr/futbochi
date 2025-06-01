from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from storage import storage
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)

def create_squad_keyboard(team):
    """Create keyboard for squad management"""
    keyboard = []
    for player in team.squad:
        is_active = player in team.active_players
        status = "✅" if is_active else "➕"
        keyboard.append([InlineKeyboardButton(
            f"{status} {player['name']} ({player['rarity']})",
            callback_data=f"toggle_player_{player['id']}"
        )])
    return InlineKeyboardMarkup(keyboard)

def create_support_keyboard():
    """Create keyboard for club support options"""
    keyboard = [
        [InlineKeyboardButton("💰 Дать денег (+500)", callback_data="support_money")],
        [InlineKeyboardButton("👤 Подписать игрока", callback_data="support_player")],
        [InlineKeyboardButton("📋 Выбрать стратегию", callback_data="support_strategy")]
    ]
    return InlineKeyboardMarkup(keyboard)

def format_power_comparison(old_power, new_power):
    """Format power comparison message with arrows and colors"""
    message = "\n📊 Изменение силы команды:\n"
    
    for stat, new_value in new_power.items():
        old_value = old_power[stat]
        diff = new_value - old_value
        
        if stat == 'speed':
            icon = '⚡️'
            name = 'Скорость'
        elif stat == 'mentality':
            icon = '🧠'
            name = 'Менталка'
        elif stat == 'finishing':
            icon = '⚽️'
            name = 'Удар'
        else:  # defense
            icon = '🛡'
            name = 'Защита'
            
        if diff > 0:
            arrow = '⬆️'
            diff_text = f"+{diff}"
        elif diff < 0:
            arrow = '⬇️'
            diff_text = str(diff)
        else:
            arrow = '➖'
            diff_text = "0"
            
        message += f"{icon} {name}: {old_value} {arrow} {new_value} ({diff_text})\n"
    
    # Добавляем изменение рейтинга команды
    old_rating = calculate_team_rating(old_power)
    new_rating = calculate_team_rating(new_power)
    rating_diff = new_rating - old_rating
    
    if rating_diff > 0:
        rating_arrow = '⬆️'
        rating_diff_text = f"+{rating_diff:.1f}"
    elif rating_diff < 0:
        rating_arrow = '⬇️'
        rating_diff_text = f"{rating_diff:.1f}"
    else:
        rating_arrow = '➖'
        rating_diff_text = "0"
    
    message += f"\n⭐️ Рейтинг: {old_rating:.1f} {rating_arrow} {new_rating:.1f} ({rating_diff_text})"
    
    return message

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

def format_squad_message(team):
    """Format squad message with active and reserve players"""
    message = "👥 Состав команды:\n\n"
    
    # Получаем силу команды и рассчитываем рейтинг
    team_power = team.get_team_power()
    team_rating = calculate_team_rating(team_power)
    
    # Добавляем общий рейтинг команды
    message += f"⭐️ Рейтинг команды: {team_rating}\n"
    message += f"👥 Активных игроков: {len(team.active_players)}/3\n\n"
    
    # Добавляем текущие характеристики команды
    message += "📊 Характеристики команды:\n"
    message += f"⚡️ Скорость: {team_power['speed']}\n"
    message += f"🧠 Менталка: {team_power['mentality']}\n"
    message += f"⚽️ Удар: {team_power['finishing']}\n"
    message += f"🛡 Защита: {team_power['defense']}\n\n"
    
    message += "🌟 Активные игроки:\n"
    
    active_players = team.active_players
    reserve_players = [p for p in team.squad if p not in active_players]
    
    for player in active_players:
        stats = player['stats']
        message += (
            f"• {player['name']} ({player['rarity'].capitalize()})\n"
            f"  ⚡️ {stats['speed']} 🧠 {stats['mentality']} "
            f"⚽️ {stats['finishing']} 🛡 {stats['defense']}\n"
        )
    
    message += "\n🔄 Запасные игроки:\n"
    for player in reserve_players:
        stats = player['stats']
        message += (
            f"• {player['name']} ({player['rarity'].capitalize()})\n"
            f"  ⚡️ {stats['speed']} 🧠 {stats['mentality']} "
            f"⚽️ {stats['finishing']} 🛡 {stats['defense']}\n"
        )
    
    return message

def handle_toggle_player(update: Update, context: CallbackContext):
    """Handle player toggle in squad"""
    query = update.callback_query
    logger.info(f"Received toggle player callback: {query.data}")
    
    try:
        user_id = str(query.from_user.id)
        team = storage.get_team(user_id)
        if not team:
            logger.warning(f"Team not found for user {user_id}")
            query.answer("Сначала начните игру командой /start", show_alert=True)
            return

        player_id = int(query.data.split('_')[-1])
        logger.info(f"Processing toggle for player {player_id}")
        
        # Сохраняем текущую силу команды
        old_power = team.get_team_power()
        current_active_ids = [p['id'] for p in team.active_players]
        
        if player_id in current_active_ids:
            if len(current_active_ids) <= 1:
                logger.info(f"Attempt to remove last active player {player_id}")
                query.answer("Должен быть хотя бы один активный игрок!", show_alert=True)
                return
            current_active_ids.remove(player_id)
            logger.info(f"Removed player {player_id} from active players")
        else:
            if len(current_active_ids) >= 3:
                logger.info(f"Attempt to add fourth player {player_id}")
                query.answer("Максимум 3 активных игрока!", show_alert=True)
                return
            current_active_ids.append(player_id)
            logger.info(f"Added player {player_id} to active players")
        
        # Обновляем состав
        team.set_active_players(current_active_ids)
        
        # Получаем новую силу команды
        new_power = team.get_team_power()
        
        # Формируем сообщение
        squad_message = format_squad_message(team)
        power_comparison = format_power_comparison(old_power, new_power)
        full_message = squad_message + power_comparison
        
        # Сохраняем изменения и обновляем сообщение
        storage.save_team(user_id, team)
        keyboard = create_squad_keyboard(team)
        query.edit_message_text(full_message, reply_markup=keyboard)
        query.answer()
        
    except Exception as e:
        logger.error(f"Error in handle_toggle_player: {e}", exc_info=True)
        query.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)

def handle_support_action(update: Update, context: CallbackContext):
    """Handle support club actions"""
    query = update.callback_query
    logger.info(f"Received support action callback: {query.data}")
    
    try:
        user_id = str(query.from_user.id)
        team = storage.get_team(user_id)
        if not team:
            logger.warning(f"Team not found for user {user_id}")
            query.answer("Сначала начните игру командой /start", show_alert=True)
            return

        action = query.data.split('_')[1]
        logger.info(f"Processing support action: {action}")
            
        if action == "money":
            team.add_money(500)
            message = "💰 Вы успешно поддержали клуб! +500 монет"
            logger.info(f"Added 500 money to team {user_id}")
            team.last_support_time = datetime.now()
            storage.save_team(user_id, team)
            query.edit_message_text(message)
        elif action == "player":
            # Загружаем базу игроков
            players_db = storage.load_players_database()
            
            # Определяем шансы выпадения редкости
            rarity_chances = {
                "common": 0.5,    # 50% шанс
                "rare": 0.3,      # 30% шанс
                "epic": 0.15,     # 15% шанс
                "legendary": 0.05  # 5% шанс
            }
            
            # Выбираем случайного игрока с учетом редкости
            rarity = random.choices(
                list(rarity_chances.keys()),
                list(rarity_chances.values())
            )[0]
            
            available_players = [p for p in players_db["players"] if p["rarity"] == rarity]
            if not available_players:
                query.answer("Ошибка: не удалось найти подходящего игрока", show_alert=True)
                return
            
            player = random.choice(available_players)
            
            # Добавляем игрока в команду
            if team.add_player(player):
                # Определяем эмодзи для редкости
                rarity_emoji = {
                    "common": "⚪️",
                    "rare": "🔵",
                    "epic": "🟣",
                    "legendary": "🟡"
                }
                
                # Формируем сообщение о полученном игроке
                message = f"✅ Вы получили нового игрока:\n\n"
                message += f"{rarity_emoji[player['rarity']]} {player['name']}\n"
                message += f"Редкость: {player['rarity'].capitalize()}\n\n"
                message += "Характеристики:\n"
                message += f"⚡️ Скорость: {player['stats']['speed']}\n"
                message += f"🧠 Менталка: {player['stats']['mentality']}\n"
                message += f"⚽️ Удар: {player['stats']['finishing']}\n"
                message += f"🛡 Защита: {player['stats']['defense']}"
                
                team.last_support_time = datetime.now()
                storage.save_team(user_id, team)
                query.edit_message_text(message)
            else:
                query.answer("В составе уже максимальное количество игроков (22)", show_alert=True)
        elif action == "strategy":
            # Логика для выбора стратегии
            message = "📋 Функция выбора стратегии в разработке"
            logger.info("Strategy support action not implemented yet")
            query.edit_message_text(message)
        else:
            message = "❌ Неизвестное действие"
            logger.warning(f"Unknown support action: {action}")
            query.edit_message_text(message)
        
        query.answer()
        
    except Exception as e:
        logger.error(f"Error in handle_support_action: {e}", exc_info=True)
        query.answer("Произошла ошибка. Попробуйте позже.", show_alert=True) 