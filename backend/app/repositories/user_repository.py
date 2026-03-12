import json
from pathlib import Path
from uuid import UUID
from typing import Optional, List

from app.schemas.user import UserInDB


class UserRepository:
    def __init__(self, data_file: Path):
        self.data_file = data_file
        self.users: List[UserInDB] = []
        self._ensure_file()
        self._load_users()

    def _ensure_file(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self.data_file.write_text("[]", encoding="utf-8")

    def _load_users(self):
        users_data = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.users = [UserInDB(**user) for user in users_data]

    def _save_users(self):
        data = [u.model_dump() for u in self.users]
        self.data_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def create_user(self, user: UserInDB) -> UserInDB:
        self.users.append(user)
        self._save_users()
        return user

    def get_user_by_id(self, user_id: UUID) -> Optional[UserInDB]:
        return next((u for u in self.users if u.id == user_id), None)

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        return next((u for u in self.users if u.email.lower() == email.lower()), None)

    def list_users(self) -> List[UserInDB]:
        return self.users.copy()