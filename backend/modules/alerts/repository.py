from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from core.models_sql import AlertModel
from modules.alerts.schemas import AlertCreate, AlertUpdate
from core.config import settings

class AlertRepository(ABC):
    @abstractmethod
    def create(self, data: AlertCreate) -> AlertModel: ...
    @abstractmethod
    def get_by_id(self, alert_id: str) -> Optional[AlertModel]: ...
    @abstractmethod
    @abstractmethod
    def list_alerts(self, lab_id: Optional[str] = None, status: Optional[str] = None) -> List[AlertModel]: ...
    @abstractmethod
    def list_anomalies(self, lab_id: Optional[str] = None) -> List: ...
    @abstractmethod
    def update(self, alert: AlertModel, data: AlertUpdate) -> AlertModel: ...
    @abstractmethod
    def delete_history(self, before: datetime) -> int: ...

class AlertRepositorySQLite(AlertRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: AlertCreate) -> AlertModel:
        alert = AlertModel(**data.model_dump(exclude_unset=True))
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_by_id(self, alert_id: str) -> Optional[AlertModel]:
        return self.db.execute(select(AlertModel).where(AlertModel.alert_id == alert_id)).scalar_one_or_none()

    def list_alerts(self, lab_id: Optional[str] = None, status: Optional[str] = None) -> List[AlertModel]:
        query = select(AlertModel)
        if lab_id:
            query = query.where(AlertModel.lab_id == lab_id)
        if status:
            query = query.where(AlertModel.status == status)
        return list(self.db.execute(query.order_by(AlertModel.created_at.desc())).scalars().all())

    def list_anomalies(self, lab_id: Optional[str] = None) -> List:
        from core.models_sql import AnomalyModel
        query = select(AnomalyModel)
        if lab_id:
            query = query.where(AnomalyModel.lab_id == lab_id)
        return list(self.db.execute(query.order_by(AnomalyModel.timestamp.desc())).scalars().all())

    def update(self, alert: AlertModel, data: AlertUpdate) -> AlertModel:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(alert, key, value)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def delete_history(self, before: datetime) -> int:
        from sqlalchemy import delete
        stmt = delete(AlertModel).where(AlertModel.created_at < before)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

class AlertRepositoryFirestore(AlertRepository):
    def __init__(self, db):
        self.db = db
        self.collection = self.db.collection('alerts')

    def create(self, data: AlertCreate) -> AlertModel:
        from core.utils import generate_id
        alert_id = generate_id("ALR")
        doc_data = data.model_dump(exclude_unset=True)
        doc_data['alert_id'] = alert_id
        
        # We need a fallback status if it isn't in data
        from core.enums import AlertStatus
        if 'status' not in doc_data:
            doc_data['status'] = AlertStatus.ACTIVE.value
            
        from core.utils import utc_now
        doc_data['created_at'] = utc_now()
        
        self.collection.document(alert_id).set(doc_data)
        return AlertModel(**doc_data)

    def get_by_id(self, alert_id: str) -> Optional[AlertModel]:
        doc = self.collection.document(alert_id).get()
        if doc.exists:
            return AlertModel(**doc.to_dict())
        return None

    def list_alerts(self, lab_id: Optional[str] = None, status: Optional[str] = None) -> List[AlertModel]:
        query = self.collection
        if lab_id:
            query = query.where('lab_id', '==', lab_id)
        if status:
            query = query.where('status', '==', status)
        
        docs = query.order_by('created_at', direction="DESCENDING").get()
        return [AlertModel(**d.to_dict()) for d in docs]

    def list_anomalies(self, lab_id: Optional[str] = None) -> List:
        from core.models_sql import AnomalyModel
        query = self.db.collection('anomalies')
        if lab_id:
            query = query.where('lab_id', '==', lab_id)
        docs = query.order_by('timestamp', direction="DESCENDING").get()
        return [AnomalyModel(**d.to_dict()) for d in docs]

    def update(self, alert: AlertModel, data: AlertUpdate) -> AlertModel:
        updates = data.model_dump(exclude_unset=True)
        self.collection.document(alert.alert_id).update(updates)
        for k, v in updates.items():
            setattr(alert, k, v)
        return alert

    def delete_history(self, before: datetime) -> int:
        docs = self.collection.where('created_at', '<', before).get()
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

def get_alert_repository(db) -> AlertRepository:
    if settings.is_sqlite:
        return AlertRepositorySQLite(db)
    else:
        return AlertRepositoryFirestore(db)
