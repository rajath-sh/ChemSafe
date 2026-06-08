from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from core.models_sql import SensorReadingModel, IncidentModel
from core.config import settings
from core.enums import IncidentStatus, IncidentSeverity

class AnalyticsRepository(ABC):
    @abstractmethod
    def get_readings_since(self, lab_id: str, since: datetime) -> List[Dict[str, Any]]: ...
    
    @abstractmethod
    def get_incidents_since(self, lab_id: str, since: datetime) -> List[IncidentModel]: ...


class AnalyticsRepositorySQLite(AnalyticsRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_readings_since(self, lab_id: str, since: datetime) -> List[Dict[str, Any]]:
        query = select(SensorReadingModel).where(
            and_(
                SensorReadingModel.lab_id == lab_id,
                SensorReadingModel.timestamp >= since
            )
        ).order_by(SensorReadingModel.timestamp.asc())
        
        readings = self.db.execute(query).scalars().all()
        # Convert to dicts for pandas
        return [
            {
                "timestamp": r.timestamp,
                "temperature": r.temperature,
                "humidity": r.humidity,
                "gas": r.gas,
                "light": r.light,
                "vibration": r.vibration
            }
            for r in readings
        ]

    def get_incidents_since(self, lab_id: str, since: datetime) -> List[IncidentModel]:
        query = select(IncidentModel).where(
            and_(
                IncidentModel.lab_id == lab_id,
                IncidentModel.created_at >= since
            )
        )
        return list(self.db.execute(query).scalars().all())


class AnalyticsRepositoryFirestore(AnalyticsRepository):
    def __init__(self, db):
        self.db = db

    def get_readings_since(self, lab_id: str, since: datetime) -> List[Dict[str, Any]]:
        docs = self.db.collection('sensor_readings') \
            .where('lab_id', '==', lab_id) \
            .where('timestamp', '>=', since) \
            .order_by('timestamp') \
            .get()
            
        return [d.to_dict() for d in docs]

    def get_incidents_since(self, lab_id: str, since: datetime) -> List[IncidentModel]:
        docs = self.db.collection('incidents') \
            .where('lab_id', '==', lab_id) \
            .where('created_at', '>=', since) \
            .get()
            
        return [IncidentModel(**d.to_dict()) for d in docs]


def get_analytics_repository(db) -> AnalyticsRepository:
    if settings.is_sqlite:
        return AnalyticsRepositorySQLite(db)
    else:
        return AnalyticsRepositoryFirestore(db)
