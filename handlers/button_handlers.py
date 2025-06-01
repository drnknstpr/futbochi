from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from storage import storage
import logging

logger = logging.getLogger(__name__)

async def create_squad_keyboard(team):
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

async def create_support_keyboard():
    """Create keyboard for club support options"""
    keyboard = [
        [InlineKeyboardButton("💰 Дать денег (+500)", callback_data="support_money")],
        [InlineKeyboardButton("👤 Подписать игрока", callback_data="support_player")],
        [InlineKeyboardButton("📋 Выбрать стратегию", callback_data="support_strategy")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_toggle_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle player toggle in squad"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    team = storage.get_team(user_id)
    if not team:
        logger.warning(f"Team not found for user {user_id}")
        await query.edit_message_text("Сначала начните игру командой /start")
        return

    try:
        player_id = int(query.data.split('_')[-1])
        logger.info(f"Processing toggle for player {player_id}")
        
        current_active_ids = [p['id'] for p in team.active_players]
        
        if player_id in current_active_ids:
            if len(current_active_ids) <= 1:
                await query.answer("Должен быть хотя бы один активный игрок!", show_alert=True)
                return
            current_active_ids.remove(player_id)
            logger.info(f"Removed player {player_id} from active players")
        else:
            if len(current_active_ids) >= 3:
                await query.answer("Максимум 3 активных игрока!", show_alert=True)
                return
            current_active_ids.append(player_id)
            logger.info(f"Added player {player_id} to active players")
        
        team.set_active_players(current_active_ids)
        storage.save_team(user_id, team)
        
        # Update message with new squad info
        squad_message = format_squad_message(team)
        keyboard = await create_squad_keyboard(team)
        await query.edit_message_text(squad_message, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in handle_toggle_player: {e}")
        await query.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)

async def handle_support_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle support club actions"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    team = storage.get_team(user_id)
    if not team:
        logger.warning(f"Team not found for user {user_id}")
        await query.edit_message_text("Сначала начните игру командой /start")
        return

    try:
        action = query.data.split('_')[1]
        
        if not team.can_support():
            await query.answer("Подождите 12 часов перед следующей поддержкой клуба", show_alert=True)
            return
            
        if action == "money":
            team.add_money(500)
            message = "💰 Вы успешно поддержали клуб! +500 монет"
        elif action == "player":
            # Логика для подписания игрока
            message = "👤 Функция подписания игрока в разработке"
        elif action == "strategy":
            # Логика для выбора стратегии
            message = "📋 Функция выбора стратегии в разработке"
        else:
            message = "❌ Неизвестное действие"
        
        storage.save_team(user_id, team)
        await query.edit_message_text(message)
        
    except Exception as e:
        logger.error(f"Error in handle_support_action: {e}")
        await query.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)

def format_squad_message(team):
    """Format squad message with player stats"""
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
    
    return squad_message 