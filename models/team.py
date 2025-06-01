from typing import List, Dict, Tuple
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
        """Проверка возможности играть матч (кулдаун 1 минута)"""
        if not self.last_match_time:
            return True
        cooldown = timedelta(minutes=1)
        return datetime.now() - self.last_match_time >= cooldown

    def can_support(self) -> bool:
        """Проверка возможности поддержать клуб (кулдаун 1 минута)"""
        if not self.last_support_time:
            return True
        cooldown = timedelta(minutes=1)
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
            return False, "Подождите 1 минуту перед следующей поддержкой клуба"

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

    def get_match_commentary(self) -> Tuple[List[str], int]:
        """Генерирует комментарии к матчу и считает голы"""
        with open("data/match_data.json", "r", encoding="utf-8") as f:
            match_data = json.load(f)

        commentary = []
        goals_scored = 0
        
        # Выбираем 3 случайных игрока для комментариев
        players = random.sample(self.active_players, min(3, len(self.active_players)))
        
        for player in players:
            # Определяем, будет ли действие позитивным или негативным
            if random.random() < 0.7:  # 70% шанс позитивного действия
                action = random.choice(match_data["match_actions"]["positive"])
                if action["is_goal"]:
                    goals_scored += 1
            else:
                action = random.choice(match_data["match_actions"]["negative"])
            
            commentary.append(f"{player['name']}... {action['action']}")
        
        return commentary, goals_scored

    def play_match(self, difficulty: str) -> tuple[bool, List[str], int, int]:
        """Играть матч"""
        if not self.can_play_match():
            return False, ["Подождите перед следующим матчем"], 0, 0

        if len(self.active_players) == 0:
            return False, ["Сначала выберите активных игроков!"], 0, 0

        # Загружаем данные о командах
        with open("data/match_data.json", "r", encoding="utf-8") as f:
            match_data = json.load(f)
        
        # Выбираем случайного соперника
        opponent = random.choice(match_data["opponent_teams"])
        
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
        
        # Генерируем комментарии матча
        commentary, goals_scored = self.get_match_commentary()
        
        # Увеличиваем шанс победы в зависимости от силы команды
        power_bonus = max(0, (total_power - settings["required_power"]) / 100)
        win_chance = min(0.9, settings["win_chance"] + power_bonus)

        # Добавляем начальное сообщение
        match_commentary = [f"⚔️ {self.name} против {opponent}"]
        match_commentary.extend(commentary)

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
                
                # Добавляем сообщение о победе
                if goals_scored > 0:
                    match_commentary.append(f"🏆 {self.name} обыграл «{opponent}» со счетом {goals_scored}:0!")
                else:
                    match_commentary.append(f"🏆 {self.name} обыграл «{opponent}» с минимальным счетом 1:0!")
                match_commentary.append(f"💪 Бонус за сильную команду:\n+{bonus_money} монет\n+{bonus_points} очков")
                
                return True, match_commentary, settings["money"] + bonus_money, settings["points"] + bonus_points
            
            # Добавляем сообщение о победе
            if goals_scored > 0:
                match_commentary.append(f"🏆 {self.name} обыграл «{opponent}» со счетом {goals_scored}:0!")
            else:
                match_commentary.append(f"🏆 {self.name} обыграл «{opponent}» с минимальным счетом 1:0!")
            
            return True, match_commentary, settings["money"], settings["points"]
        else:
            consolation_money = settings["money"] // 4
            self.money += consolation_money
            self.last_match_time = datetime.now()
            
            # Добавляем сообщение о поражении
            opponent_goals = random.randint(1, 3)
            match_commentary.append(f"😔 {self.name} проиграл «{opponent}» со счетом {goals_scored}:{opponent_goals}")
            match_commentary.append(f"Утешительный приз: {consolation_money} монет")
            
            return True, match_commentary, consolation_money, 0

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