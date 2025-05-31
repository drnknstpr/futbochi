import json
import os
from typing import Dict, Optional
from models.team import Team

class Storage:
    def __init__(self):
        self.teams_dir = "teams"
        os.makedirs(self.teams_dir, exist_ok=True)

    def get_team(self, user_id: str) -> Optional[Team]:
        """Получить команду пользователя"""
        path = os.path.join(self.teams_dir, f"{user_id}.json")
        if not os.path.exists(path):
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Team.from_dict(data)

    def save_team(self, user_id: str, team: Team) -> None:
        """Сохранить команду пользователя"""
        path = os.path.join(self.teams_dir, f"{user_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(team.to_dict(), f, ensure_ascii=False, indent=2)

    def get_all_teams(self) -> Dict[str, Team]:
        """Получить все команды для рейтинга"""
        teams = {}
        for filename in os.listdir(self.teams_dir):
            if filename.endswith(".json"):
                user_id = filename[:-5]  # remove .json
                teams[user_id] = self.get_team(user_id)
        return teams

    def load_players_database(self) -> Dict:
        """Загрузить базу данных игроков"""
        with open("data/players.json", "r", encoding="utf-8") as f:
            return json.load(f)

# Создаем глобальный экземпляр хранилища
storage = Storage()
