from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from core.models_sql import SensorReadingModel, ThresholdModel, SensorModel
from core.config import settings

class IngestionRepository(ABC):
    @abstractmethod
    def save_reading(self, reading_data: dict) -> SensorReadingModel:
        pass

    @abstractmethod
    def get_thresholds(self, lab_id: str) -> List[ThresholdModel]:
        pass

    def update_sensor_status(self, lab_id: str, sensor_type: str, value: float) -> None:
        pass

    @abstractmethod
    def get_sensor_status(self, lab_id: str, sensor_type: str) -> Optional[str]:
        pass


class IngestionRepositorySQLite(IngestionRepository):
    def __init__(self, db: Session):
        self.db = db

    def save_reading(self, reading_data: dict) -> SensorReadingModel:
        reading = SensorReadingModel(**reading_data)
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        return reading

    def get_thresholds(self, lab_id: str) -> List[ThresholdModel]:
        return list(self.db.execute(
            select(ThresholdModel).where(ThresholdModel.lab_id == lab_id)
        ).scalars().all())

    def update_sensor_status(self, lab_id: str, sensor_type: str, value: float) -> None:
        # Update last_reading and last_updated on the Sensor record
        sensor = self.db.execute(
            select(SensorModel)
            .where(SensorModel.lab_id == lab_id)
            .where(SensorModel.sensor_type == sensor_type)
        ).scalar_one_or_none()
        
        if sensor:
            from core.utils import utc_now
            sensor.last_reading = value
            sensor.last_updated = utc_now()
            self.db.commit()

    def get_sensor_status(self, lab_id: str, sensor_type: str) -> Optional[str]:
        sensor = self.db.execute(
            select(SensorModel)
            .where(SensorModel.lab_id == lab_id)
            .where(SensorModel.sensor_type == sensor_type)
        ).scalar_one_or_none()
        return sensor.status.value if sensor else None


class IngestionRepositoryFirestore(IngestionRepository):
    def __init__(self, db):
        self.db = db

    def save_reading(self, reading_data: dict) -> SensorReadingModel:
        from core.utils import generate_id
        reading_id = generate_id("RDG")
        reading_data['reading_id'] = reading_id
        self.db.collection('sensor_readings').document(reading_id).set(reading_data)
        return SensorReadingModel(**reading_data)

    def get_thresholds(self, lab_id: str) -> List[ThresholdModel]:
        docs = self.db.collection('thresholds').where('lab_id', '==', lab_id).get()
        return [ThresholdModel(**d.to_dict()) for d in docs]

    def update_sensor_status(self, lab_id: str, sensor_type: str, value: float) -> None:
        from core.utils import utc_now
        docs = self.db.collection('sensors').where('lab_id', '==', lab_id).where('sensor_type', '==', sensor_type).limit(1).get()
        for doc in docs:
            self.db.collection('sensors').document(doc.id).update({
                'last_reading': value,
                'last_updated': utc_now()
            })

    def get_sensor_status(self, lab_id: str, sensor_type: str) -> Optional[str]:
        docs = self.db.collection('sensors').where('lab_id', '==', lab_id).where('sensor_type', '==', sensor_type).limit(1).get()
        for doc in docs:
            return doc.to_dict().get('status')
        return None


def get_ingestion_repository(db) -> IngestionRepository:
    if settings.is_sqlite:
        return IngestionRepositorySQLite(db)
    else:
        return IngestionRepositoryFirestore(db)
