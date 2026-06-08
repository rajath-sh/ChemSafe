from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from core.models_sql import UserModel, IncidentModel
from modules.staff.schemas import StaffUpdate
from core.config import settings
from core.enums import Role

class StaffRepository(ABC):
    @abstractmethod
    def list_staff(self, department: Optional[str] = None, availability: Optional[str] = None) -> List[UserModel]: ...
    
    @abstractmethod
    def get_staff(self, user_id: str) -> Optional[UserModel]: ...
    
    @abstractmethod
    def update_staff(self, user: UserModel, data: StaffUpdate) -> UserModel: ...

    @abstractmethod
    def get_incident_staff_id(self, incident_id: str) -> Optional[str]: ...


class StaffRepositorySQLite(StaffRepository):
    def __init__(self, db: Session):
        self.db = db

    def list_staff(self, department: Optional[str] = None, availability: Optional[str] = None) -> List[UserModel]:
        query = select(UserModel).where(UserModel.role == Role.STAFF)
        if department:
            query = query.where(UserModel.department == department)
        if availability:
            query = query.where(UserModel.availability == availability)
        return list(self.db.execute(query).scalars().all())

    def get_staff(self, user_id: str) -> Optional[UserModel]:
        return self.db.execute(
            select(UserModel).where(UserModel.user_id == user_id, UserModel.role == Role.STAFF)
        ).scalar_one_or_none()

    def update_staff(self, user: UserModel, data: StaffUpdate) -> UserModel:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_incident_staff_id(self, incident_id: str) -> Optional[str]:
        incident = self.db.execute(select(IncidentModel).where(IncidentModel.incident_id == incident_id)).scalar_one_or_none()
        if incident:
            return incident.assigned_staff_id
        return None


class StaffRepositoryFirestore(StaffRepository):
    def __init__(self, db):
        self.db = db
        self.collection = self.db.collection('users')

    def list_staff(self, department: Optional[str] = None, availability: Optional[str] = None) -> List[UserModel]:
        query = self.collection.where('role', '==', Role.STAFF.value)
        if department:
            query = query.where('department', '==', department)
        if availability:
            query = query.where('availability', '==', availability)
            
        docs = query.get()
        return [UserModel(**d.to_dict()) for d in docs]

    def get_staff(self, user_id: str) -> Optional[UserModel]:
        doc = self.collection.document(user_id).get()
        if doc.exists:
            data = doc.to_dict()
            if data.get("role") == Role.STAFF.value:
                return UserModel(**data)
        return None

    def update_staff(self, user: UserModel, data: StaffUpdate) -> UserModel:
        updates = data.model_dump(exclude_unset=True)
        self.collection.document(user.user_id).update(updates)
        for k, v in updates.items():
            setattr(user, k, v)
        return user

    def get_incident_staff_id(self, incident_id: str) -> Optional[str]:
        doc = self.db.collection('incidents').document(incident_id).get()
        if doc.exists:
            return doc.to_dict().get("assigned_staff_id")
        return None


def get_staff_repository(db) -> StaffRepository:
    if settings.is_sqlite:
        return StaffRepositorySQLite(db)
    else:
        return StaffRepositoryFirestore(db)
