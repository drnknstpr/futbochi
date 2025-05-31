import json
import random
import os

def load_existing_players():
    with open('data/players.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['players']

def generate_name():
    first_names = [
        "Александр", "Михаил", "Даниил", "Максим", "Артем",
        "Иван", "Дмитрий", "Кирилл", "Андрей", "Матвей",
        "Илья", "Алексей", "Роман", "Сергей", "Николай",
        "Владимир", "Егор", "Денис", "Арсений", "Тимофей"
    ]
    last_names = [
        "Смирнов", "Иванов", "Кузнецов", "Попов", "Соколов",
        "Лебедев", "Козлов", "Новиков", "Морозов", "Петров",
        "Волков", "Соловьев", "Васильев", "Зайцев", "Павлов",
        "Семенов", "Голубев", "Виноградов", "Богданов", "Воробьев"
    ]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_stats(rarity):
    base_stats = {
        "legendary": {"min": 3, "max": 5},
        "epic": {"min": 2, "max": 4},
        "rare": {"min": 2, "max": 3},
        "common": {"min": 1, "max": 2}
    }
    
    stats = {
        "speed": random.randint(base_stats[rarity]["min"], base_stats[rarity]["max"]),
        "mentality": random.randint(base_stats[rarity]["min"], base_stats[rarity]["max"]),
        "finishing": random.randint(base_stats[rarity]["min"], base_stats[rarity]["max"]),
        "defense": random.randint(base_stats[rarity]["min"], base_stats[rarity]["max"])
    }
    
    # Ensure at least one stat is at maximum for the rarity
    max_stat = base_stats[rarity]["max"]
    random_stat = random.choice(list(stats.keys()))
    stats[random_stat] = max_stat
    
    return stats

def generate_player(player_id, rarity):
    return {
        "id": player_id,
        "name": generate_name(),
        "rarity": rarity,
        "stats": generate_stats(rarity)
    }

def main():
    existing_players = load_existing_players()
    last_id = max(player['id'] for player in existing_players)
    new_players = []
    
    # Distribution for remaining players
    rarities = []
    rarities.extend(["legendary"] * 20)  # 5%
    rarities.extend(["epic"] * 40)       # 10%
    rarities.extend(["rare"] * 100)      # 25%
    rarities.extend(["common"] * 240)    # 60%
    
    random.shuffle(rarities)
    
    for i, rarity in enumerate(rarities, start=1):
        player = generate_player(last_id + i, rarity)
        new_players.append(player)
    
    # Combine existing and new players
    all_players = existing_players + new_players
    
    # Save updated players
    data = {
        "players": all_players,
        "rarity_chances": {
            "common": 60,
            "rare": 25,
            "epic": 10,
            "legendary": 5
        }
    }
    
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main() 