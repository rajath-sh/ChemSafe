from typing import List
from modules.users.repository import UserRepository
from modules.users.schemas import UserCreate, UserUpdate
from core.models_sql import UserModel
from core.exceptions import ConflictException, NotFoundException

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def create_user(self, data: UserCreate) -> UserModel:
        existing = self.repo.get_by_email(data.email)
        if existing:
            raise ConflictException("User with this email already exists")
        return self.repo.create(data)

    def get_user(self, user_id: str) -> UserModel:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        return user

    def update_user(self, user_id: str, data: UserUpdate) -> UserModel:
        user = self.get_user(user_id)
        return self.repo.update(user, data)

    def list_users(self) -> List[UserModel]:
        return self.repo.list_users()
