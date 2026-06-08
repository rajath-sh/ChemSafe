from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from core.models_sql import SensorModel, ThresholdModel, SensorReadingModel, LaboratoryModel
from modules.sensors.schemas import SensorCreate, SensorUpdate, ThresholdCreate, LabCreate
from core.config import settings

class SensorRepository(ABC):
    # Lab Helper
    @abstractmethod
    @abstractmethod
    def create_lab(self, data: LabCreate) -> LaboratoryModel: ...
    @abstractmethod
    def list_labs(self) -> List[LaboratoryModel]: ...
    @abstractmethod
    def delete_lab(self, lab_id: str) -> bool: ...

    # Sensors
    @abstractmethod
    def create_sensor(self, data: SensorCreate) -> SensorModel: ...
    @abstractmethod
    def get_sensor(self, sensor_id: str) -> Optional[SensorModel]: ...
    @abstractmethod
    def list_sensors(self, lab_id: Optional[str] = None) -> List[SensorModel]: ...
    @abstractmethod
    def update_sensor(self, sensor: SensorModel, data: SensorUpdate) -> SensorModel: ...
    @abstractmethod
    def get_readings(self, lab_id: str, limit: int = 50) -> List[SensorReadingModel]: ...

    # Thresholds
    @abstractmethod
    def set_threshold(self, data: ThresholdCreate) -> ThresholdModel: ...
    @abstractmethod
    def get_thresholds(self, lab_id: str) -> List[ThresholdModel]: ...

    # History Deletion
    @abstractmethod
    def delete_history(self, before: datetime) -> int: ...


class SensorRepositorySQLite(SensorRepository):
    def __init__(self, db: Session):
        self.db = db

    def create_lab(self, data: LabCreate) -> LaboratoryModel:
        lab = LaboratoryModel(**data.model_dump(exclude_unset=True))
        self.db.add(lab)
        self.db.commit()
        self.db.refresh(lab)
        return lab

    def list_labs(self) -> List[LaboratoryModel]:
        return list(self.db.execute(select(LaboratoryModel)).scalars().all())

    def delete_lab(self, lab_id: str) -> bool:
        from sqlalchemy import delete
        from core.models_sql import SensorReadingModel, ThresholdModel, AnomalyModel, AlertModel, IncidentModel
        
        # Manually delete child records to avoid FK constraint failures
        self.db.execute(delete(ThresholdModel).where(ThresholdModel.lab_id == lab_id))
        self.db.execute(delete(AnomalyModel).where(AnomalyModel.lab_id == lab_id))
        self.db.execute(delete(SensorReadingModel).where(SensorReadingModel.lab_id == lab_id))
        self.db.execute(delete(SensorModel).where(SensorModel.lab_id == lab_id))
        self.db.execute(delete(AlertModel).where(AlertModel.lab_id == lab_id))
        self.db.execute(delete(IncidentModel).where(IncidentModel.lab_id == lab_id))
        
        result = self.db.execute(delete(LaboratoryModel).where(LaboratoryModel.lab_id == lab_id))
        self.db.commit()
        return result.rowcount > 0

    def create_sensor(self, data: SensorCreate) -> SensorModel:
        sensor = SensorModel(**data.model_dump(exclude_unset=True))
        self.db.add(sensor)
        self.db.commit()
        self.db.refresh(sensor)
        return sensor

    def get_sensor(self, sensor_id: str) -> Optional[SensorModel]:
        return self.db.execute(select(SensorModel).where(SensorModel.sensor_id == sensor_id)).scalar_one_or_none()

    def list_sensors(self, lab_id: Optional[str] = None) -> List[SensorModel]:
        query = select(SensorModel)
        if lab_id:
            query = query.where(SensorModel.lab_id == lab_id)
        return list(self.db.execute(query).scalars().all())

    def update_sensor(self, sensor: SensorModel, data: SensorUpdate) -> SensorModel:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(sensor, key, value)
        self.db.commit()
        self.db.refresh(sensor)
        return sensor

    def get_readings(self, lab_id: str, limit: int = 50) -> List[SensorReadingModel]:
        return list(
            self.db.execute(
                select(SensorReadingModel)
                .where(SensorReadingModel.lab_id == lab_id)
                .order_by(SensorReadingModel.timestamp.desc())
                .limit(limit)
            ).scalars().all()
        )

    def set_threshold(self, data: ThresholdCreate) -> ThresholdModel:
        # Check if exists
        existing = self.db.execute(
            select(ThresholdModel)
            .where(ThresholdModel.lab_id == data.lab_id)
            .where(ThresholdModel.sensor_type == data.sensor_type)
        ).scalar_one_or_none()

        if existing:
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            new_threshold = ThresholdModel(**data.model_dump(exclude_unset=True))
            self.db.add(new_threshold)
            self.db.commit()
            self.db.refresh(new_threshold)
            return new_threshold

    def get_thresholds(self, lab_id: str) -> List[ThresholdModel]:
        return list(self.db.execute(select(ThresholdModel).where(ThresholdModel.lab_id == lab_id)).scalars().all())

    def delete_history(self, before: datetime) -> int:
        from sqlalchemy import delete
        stmt = delete(SensorReadingModel).where(SensorReadingModel.timestamp < before)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount


class SensorRepositoryFirestore(SensorRepository):
    def __init__(self, db):
        self.db = db

    def create_lab(self, data: LabCreate) -> LaboratoryModel:
        from core.utils import generate_id
        lab_id = generate_id("LAB")
        doc_data = data.model_dump(exclude_unset=True)
        doc_data['lab_id'] = lab_id
        self.db.collection('laboratories').document(lab_id).set(doc_data)
        return LaboratoryModel(**doc_data)

    def list_labs(self) -> List[LaboratoryModel]:
        docs = self.db.collection('laboratories').get()
        return [LaboratoryModel(**d.to_dict()) for d in docs]

    def delete_lab(self, lab_id: str) -> bool:
        self.db.collection('laboratories').document(lab_id).delete()
        # Delete associated sensors
        sensors = self.db.collection('sensors').where('lab_id', '==', lab_id).get()
        batch = self.db.batch()
        for s in sensors:
            batch.delete(s.reference)
        batch.commit()
        return True

    def create_sensor(self, data: SensorCreate) -> SensorModel:
        from core.utils import generate_id
        sensor_id = generate_id("SEN")
        doc_data = data.model_dump(exclude_unset=True)
        doc_data['sensor_id'] = sensor_id
        self.db.collection('sensors').document(sensor_id).set(doc_data)
        return SensorModel(**doc_data)

    def get_sensor(self, sensor_id: str) -> Optional[SensorModel]:
        doc = self.db.collection('sensors').document(sensor_id).get()
        if doc.exists:
            return SensorModel(**doc.to_dict())
        return None

    def list_sensors(self, lab_id: Optional[str] = None) -> List[SensorModel]:
        query = self.db.collection('sensors')
        if lab_id:
            query = query.where('lab_id', '==', lab_id)
        docs = query.get()
        return [SensorModel(**d.to_dict()) for d in docs]

    def update_sensor(self, sensor: SensorModel, data: SensorUpdate) -> SensorModel:
        updates = data.model_dump(exclude_unset=True)
        if updates:
            self.db.collection('sensors').document(sensor.sensor_id).update(updates)
            for k, v in updates.items():
                setattr(sensor, k, v)
        return sensor

    def get_readings(self, lab_id: str, limit: int = 50) -> List[SensorReadingModel]:
        docs = (
            self.db.collection('sensor_readings')
            .where('lab_id', '==', lab_id)
            .order_by('timestamp', direction='DESCENDING')
            .limit(limit)
            .get()
        )
        return [SensorReadingModel(**d.to_dict()) for d in docs]

    def set_threshold(self, data: ThresholdCreate) -> ThresholdModel:
        from core.utils import generate_id
        # Firebase composite query equivalent
        docs = self.db.collection('thresholds').where('lab_id', '==', data.lab_id).where('sensor_type', '==', data.sensor_type.value).get()
        
        updates = data.model_dump(exclude_unset=True)
        
        if len(docs) > 0:
            doc = docs[0]
            self.db.collection('thresholds').document(doc.id).update(updates)
            final_data = doc.to_dict()
            final_data.update(updates)
            return ThresholdModel(**final_data)
        else:
            tid = generate_id("THR")
            updates['threshold_id'] = tid
            self.db.collection('thresholds').document(tid).set(updates)
            return ThresholdModel(**updates)

    def get_thresholds(self, lab_id: str) -> List[ThresholdModel]:
        docs = self.db.collection('thresholds').where('lab_id', '==', lab_id).get()
        return [ThresholdModel(**d.to_dict()) for d in docs]

    def delete_history(self, before: datetime) -> int:
        # In a real scenario, this would use a batch delete pattern for Firestore
        docs = self.db.collection('sensor_readings').where('timestamp', '<', before).get()
        count = 0
        batch = self.db.batch()
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            if count % 500 == 0:
                batch.commit()
                batch = self.db.batch()
        if count > 0:
            batch.commit()
        return count


def get_sensor_repository(db) -> SensorRepository:
    if settings.is_sqlite:
        return SensorRepositorySQLite(db)
    else:
        return SensorRepositoryFirestore(db)
