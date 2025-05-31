from typing import List, Dict
import json
from datetime import datetime, timedelta

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
        """Сыграть матч"""
        if not self.can_play_match():
            return False, "Подождите 1 час перед следующим матчем", 0, 0

        if len(self.active_players) == 0:
            return False, "Нужно выбрать активных игроков для матча", 0, 0

        # Базовые награды за разные сложности
        rewards = {
            "easy": {"money": 100, "points": 1},
            "medium": {"money": 300, "points": 3},
            "hard": {"money": 500, "points": 5}
        }

        if difficulty not in rewards:
            return False, "Неверная сложность матча", 0, 0

        # Здесь будет логика расчёта результата матча
        success = True  # В реальности будет зависеть от силы команды
        
        if success:
            self.money += rewards[difficulty]["money"]
            self.points += rewards[difficulty]["points"]
            self.last_match_time = datetime.now()
            return True, "Победа!", rewards[difficulty]["money"], rewards[difficulty]["points"]
        else:
            self.last_match_time = datetime.now()
            return True, "Поражение", 0, 0

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