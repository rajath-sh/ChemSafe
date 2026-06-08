from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from core.models_sql import UserModel
from modules.users.schemas import UserCreate, UserUpdate
from core.config import settings

class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[UserModel]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[UserModel]:
        pass

    @abstractmethod
    def list_users(self) -> List[UserModel]:
        pass

    @abstractmethod
    def create(self, user_data: UserCreate) -> UserModel:
        pass

    @abstractmethod
    def update(self, user: UserModel, update_data: UserUpdate) -> UserModel:
        pass


class UserRepositorySQLite(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[UserModel]:
        return self.db.execute(select(UserModel).where(UserModel.user_id == user_id)).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[UserModel]:
        return self.db.execute(select(UserModel).where(UserModel.email == email)).scalar_one_or_none()

    def list_users(self) -> List[UserModel]:
        return list(self.db.execute(select(UserModel)).scalars().all())

    def create(self, user_data: UserCreate) -> UserModel:
        user = UserModel(**user_data.model_dump(exclude_unset=True))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: UserModel, update_data: UserUpdate) -> UserModel:
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user


class UserRepositoryFirestore(UserRepository):
    def __init__(self, db):
        self.db = db
        self.collection = self.db.collection('users')

    def get_by_id(self, user_id: str) -> Optional[UserModel]:
        doc = self.collection.document(user_id).get()
        if doc.exists:
            return UserModel(**doc.to_dict())
        return None

    def get_by_email(self, email: str) -> Optional[UserModel]:
        docs = self.collection.where('email', '==', email).limit(1).get()
        for doc in docs:
            return UserModel(**doc.to_dict())
        return None

    def list_users(self) -> List[UserModel]:
        docs = self.collection.get()
        return [UserModel(**doc.to_dict()) for doc in docs]

    def create(self, user_data: UserCreate) -> UserModel:
        from core.utils import generate_id
        user_id = generate_id("USR")
        data = user_data.model_dump(exclude_unset=True)
        data['user_id'] = user_id
        self.collection.document(user_id).set(data)
        return UserModel(**data)

    def update(self, user: UserModel, update_data: UserUpdate) -> UserModel:
        updates = update_data.model_dump(exclude_unset=True)
        self.collection.document(user.user_id).update(updates)
        for key, value in updates.items():
            setattr(user, key, value)
        return user


def get_user_repository(db) -> UserRepository:
    if settings.is_sqlite:
        return UserRepositorySQLite(db)
    else:
        return UserRepositoryFirestore(db)
