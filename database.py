import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.users: Dict[str, Any] = {}
        self.courses: Dict[str, Any] = {}
        self.load_data()

    def load_data(self):
        try:
            with open("data/users.json", "r", encoding="utf-8") as f:
                self.users = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.users = {}
    
        try:
            with open("data/courses.json", "r", encoding="utf-8") as f:
                self.courses = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.courses = {}

    def save_data(self):
        with open("data/users.json", "w", encoding="utf-8") as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
        with open("data/courses.json", "w", encoding="utf-8") as f:
            json.dump(self.courses, f, ensure_ascii=False, indent=2)

    def get_user(self, user_id: int) -> dict:
        if str(user_id) not in self.users:
            self.users[str(user_id)] = {
                "free_generations": 10,
                "omni_mini_generations": 10,
                "omni_mini_reset_time": None,
                "subscription_until": None,
                "invited_users": [],
                "referred_by": None,
                "completed_lessons": [],
                "premium": False,
                "last_activity": datetime.now().isoformat(),
            }
            self.save_data()
        return self.users[str(user_id)]

    def update_user(self, user_id: int, data: dict):
        self.users[str(user_id)] = data
        self.save_data()

    def get_lesson(self, lesson_number: int) -> Optional[dict]:
        return self.courses.get(str(lesson_number))

    def get_all_lessons(self) -> dict:
        return self.courses

    def add_lesson(self, lesson_data: dict) -> int:
        lesson_number = len(self.courses) + 1
        self.courses[str(lesson_number)] = lesson_data
        self.save_data()
        return lesson_number

    def reset_omni_mini_generations(self, user_id: int):
        user = self.get_user(user_id)
        user['omni_mini_generations'] = 10
        user['omni_mini_reset_time'] = (datetime.now() + timedelta(hours=48)).isoformat()
        self.update_user(user_id, user)

db = Database()
