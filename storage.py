import json
import os

def get_user(user_id):
    path = f"users/{user_id}.json"
    if not os.path.exists(path):
        return {"money": 1000, "points": 0, "squad": [], "bench": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user(user_id, user_data):
    with open(f"users/{user_id}.json", "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)
