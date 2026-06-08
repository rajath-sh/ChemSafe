from abc import ABC, abstractmethod
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from core.models_sql import (
    SensorModel, 
    AlertModel, 
    IncidentModel, 
    ChemicalModel, 
    UserModel
)
from core.config import settings
from core.enums import AlertStatus, IncidentStatus, SensorStatus, StaffAvailability, Role

class DashboardRepository(ABC):
    @abstractmethod
    def get_sensors(self, lab_id: str) -> List[SensorModel]: ...
    @abstractmethod
    def get_active_alerts(self, lab_id: str) -> List[AlertModel]: ...
    @abstractmethod
    def get_open_incidents(self, lab_id: str) -> List[IncidentModel]: ...
    @abstractmethod
    def get_chemical_count(self, lab_id: str) -> int: ...
    @abstractmethod
    def get_available_staff_count(self) -> int: ...
    @abstractmethod
    def get_staff_name(self, user_id: str) -> str: ...
    @abstractmethod
    def get_location_name(self, lab_id: str) -> str: ...


class DashboardRepositorySQLite(DashboardRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_sensors(self, lab_id: str) -> List[SensorModel]:
        query = select(SensorModel)
        if lab_id != 'ALL': query = query.where(SensorModel.lab_id == lab_id)
        return list(self.db.execute(query.order_by(SensorModel.last_updated.desc())).scalars().all())

    def get_active_alerts(self, lab_id: str) -> List[AlertModel]:
        query = select(AlertModel).where(AlertModel.status == AlertStatus.ACTIVE)
        if lab_id != 'ALL': query = query.where(AlertModel.lab_id == lab_id)
        return list(self.db.execute(
            query.order_by(AlertModel.created_at.desc()).limit(10)
        ).scalars().all())

    def get_open_incidents(self, lab_id: str) -> List[IncidentModel]:
        query = select(IncidentModel).where(IncidentModel.status == IncidentStatus.OPEN)
        if lab_id != 'ALL': query = query.where(IncidentModel.lab_id == lab_id)
        return list(self.db.execute(
            query.order_by(IncidentModel.created_at.desc()).limit(10)
        ).scalars().all())

    def get_chemical_count(self, lab_id: str) -> int:
        return self.db.execute(
            select(func.count()).select_from(ChemicalModel)
        ).scalar() or 0

    def get_available_staff_count(self) -> int:
        return self.db.execute(
            select(func.count()).select_from(UserModel).where(
                UserModel.role == Role.STAFF,
                UserModel.availability == StaffAvailability.AVAILABLE
            )
        ).scalar() or 0

    def get_staff_name(self, user_id: str) -> str:
        user = self.db.execute(select(UserModel).where(UserModel.user_id == user_id)).scalar_one_or_none()
        return user.name if user else "Unknown"

    def get_location_name(self, lab_id: str) -> str:
        from core.models_sql import LaboratoryModel
        lab = self.db.execute(select(LaboratoryModel).where(LaboratoryModel.lab_id == lab_id)).scalar_one_or_none()
        return lab.lab_name if lab else f"Location ({lab_id})"


class DashboardRepositoryFirestore(DashboardRepository):
    def __init__(self, db):
        self.db = db

    def get_sensors(self, lab_id: str) -> List[SensorModel]:
        ref = self.db.collection('sensors')
        if lab_id != 'ALL': ref = ref.where('lab_id', '==', lab_id)
        docs = ref.order_by('last_updated', direction="DESCENDING").get()
        return [SensorModel(**d.to_dict()) for d in docs]

    def get_active_alerts(self, lab_id: str) -> List[AlertModel]:
        ref = self.db.collection('alerts').where('status', '==', AlertStatus.ACTIVE.value)
        if lab_id != 'ALL': ref = ref.where('lab_id', '==', lab_id)
        docs = ref.order_by('created_at', direction="DESCENDING").limit(10).get()
        return [AlertModel(**d.to_dict()) for d in docs]

    def get_open_incidents(self, lab_id: str) -> List[IncidentModel]:
        ref = self.db.collection('incidents').where('status', '==', IncidentStatus.OPEN.value)
        if lab_id != 'ALL': ref = ref.where('lab_id', '==', lab_id)
        docs = ref.order_by('created_at', direction="DESCENDING").limit(10).get()
        return [IncidentModel(**d.to_dict()) for d in docs]

    def get_chemical_count(self, lab_id: str) -> int:
        # Note: In production Firestore, use count() aggregation. For SDK parity here:
        docs = self.db.collection('chemicals').get()
        return len(docs)

    def get_available_staff_count(self) -> int:
        docs = self.db.collection('users') \
            .where('role', '==', Role.STAFF.value) \
            .where('availability', '==', StaffAvailability.AVAILABLE.value).get()
        return len(docs)

    def get_staff_name(self, user_id: str) -> str:
        doc = self.db.collection('users').document(user_id).get()
        return doc.to_dict().get("name", "Unknown") if doc.exists else "Unknown"

    def get_location_name(self, lab_id: str) -> str:
        doc = self.db.collection('laboratories').document(lab_id).get()
        return doc.to_dict().get("lab_name", f"Location ({lab_id})") if doc.exists else f"Location ({lab_id})"


def get_dashboard_repository(db) -> DashboardRepository:
    if settings.is_sqlite:
        return DashboardRepositorySQLite(db)
    else:
        return DashboardRepositoryFirestore(db)
