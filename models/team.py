from typing import List, Dict
import json
from datetime import datetime, timedelta
import random

class Team:
    def __init__(self, name: str):
        self.name = name
        self.money = 1000
        self.points = 0
        self.active_players = []  # до 3 активных игроков
        self.squad = []  # до 22 игроков всего
        self.last_support_time = None
        self.last_match_time = None
        self.strategy = None

    def can_play_match(self) -> bool:
        """Проверка возможности играть матч (кулдаун 1 час)"""
        if not self.last_match_time:
            return True
        cooldown = timedelta(hours=1)
        return datetime.now() - self.last_match_time >= cooldown

    def can_support(self) -> bool:
        """Проверка возможности поддержать клуб (кулдаун 12 часов)"""
        if not self.last_support_time:
            return True
        cooldown = timedelta(hours=12)
        return datetime.now() - self.last_support_time >= cooldown

    def add_player(self, player: Dict) -> bool:
        """Добавить игрока в команду"""
        if len(self.squad) >= 22:
            return False
        self.squad.append(player)
        return True

    def remove_player(self, player_id: int) -> bool:
        """Удалить игрока из команды"""
        for player in self.squad:
            if player['id'] == player_id:
                self.squad.remove(player)
                if player in self.active_players:
                    self.active_players.remove(player)
                return True
        return False

    def set_active_players(self, player_ids: List[int]) -> bool:
        """Установить активных игроков"""
        if len(player_ids) > 3:
            return False
        
        active = []
        for pid in player_ids:
            for player in self.squad:
                if player['id'] == pid:
                    active.append(player)
                    break
        
        if len(active) == len(player_ids):
            self.active_players = active
            return True
        return False

    def get_team_power(self) -> Dict[str, int]:
        """Получить суммарную силу активных игроков по параметрам"""
        power = {
            "speed": 0,
            "mentality": 0,
            "finishing": 0,
            "defense": 0
        }
        
        for player in self.active_players:
            for param, value in player['stats'].items():
                if param in power:
                    power[param] += value
        
        return power

    def support_club(self, action: str) -> tuple[bool, str]:
        """Поддержать клуб одним из действий"""
        if not self.can_support():
            return False, "Подождите 12 часов перед следующей поддержкой клуба"

        if action == "money":
            self.money += 500
            msg = "Получено 500 монет"
        elif action == "player":
            # Логика получения случайного игрока будет в handler
            msg = "Готовы подписать игрока"
        elif action == "strategy":
            msg = "Выберите стратегию"
        else:
            return False, "Неверное действие"

        self.last_support_time = datetime.now()
        return True, msg

    def play_match(self, difficulty: str) -> tuple[bool, str, int, int]:
        """Играть матч"""
        if not self.can_play_match():
            return False, "Подождите перед следующим матчем", 0, 0

        if len(self.active_players) == 0:
            return False, "Сначала выберите активных игроков!", 0, 0

        # Рассчитываем силу команды
        team_power = self.get_team_power()
        total_power = sum(team_power.values()) / 4  # Среднее значение всех характеристик

        # Настройки сложности
        difficulties = {
            "easy": {"required_power": 50, "money": 200, "points": 1, "win_chance": 0.7},
            "medium": {"required_power": 65, "money": 400, "points": 3, "win_chance": 0.5},
            "hard": {"required_power": 80, "money": 600, "points": 5, "win_chance": 0.3}
        }

        settings = difficulties[difficulty]
        
        # Увеличиваем шанс победы в зависимости от силы команды
        power_bonus = max(0, (total_power - settings["required_power"]) / 100)
        win_chance = min(0.9, settings["win_chance"] + power_bonus)

        # Определяем исход матча
        if random.random() < win_chance:
            self.money += settings["money"]
            self.points += settings["points"]
            self.last_match_time = datetime.now()
            
            # Бонус за большую разницу в силе
            if total_power > settings["required_power"] + 20:
                bonus_money = int((total_power - settings["required_power"]) * 2)
                bonus_points = 1 if difficulty == "hard" else 0
                self.money += bonus_money
                self.points += bonus_points
                return True, f"🏆 Победа!\n\n💪 Бонус за сильную команду:\n+{bonus_money} монет\n+{bonus_points} очков", settings["money"] + bonus_money, settings["points"] + bonus_points
            
            return True, "🏆 Победа!", settings["money"], settings["points"]
        else:
            consolation_money = settings["money"] // 4
            self.money += consolation_money
            self.last_match_time = datetime.now()
            return True, f"😔 Поражение\n\nУтешительный приз: {consolation_money} монет", consolation_money, 0

    def to_dict(self) -> Dict:
        """Конвертировать данные команды в словарь для сохранения"""
        return {
            "name": self.name,
            "money": self.money,
            "points": self.points,
            "active_players": self.active_players,
            "squad": self.squad,
            "last_support_time": self.last_support_time.isoformat() if self.last_support_time else None,
            "last_match_time": self.last_match_time.isoformat() if self.last_match_time else None,
            "strategy": self.strategy
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Team':
        """Создать команду из словаря"""
        team = cls(data["name"])
        team.money = data["money"]
        team.points = data["points"]
        team.active_players = data["active_players"]
        team.squad = data["squad"]
        team.last_support_time = datetime.fromisoformat(data["last_support_time"]) if data["last_support_time"] else None
        team.last_match_time = datetime.fromisoformat(data["last_match_time"]) if data["last_match_time"] else None
        team.strategy = data["strategy"]
        return team 