from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from core.models_sql import AuditLogModel
from core.config import settings

class AuditLogRepository(ABC):
    @abstractmethod
    def create(self, user_id: str, action: str, entity_type: str, entity_id: str, details: Optional[str] = None) -> AuditLogModel: ...
    
    @abstractmethod
    def list_logs(self, entity_type: Optional[str] = None, user_id: Optional[str] = None) -> List[AuditLogModel]: ...


class AuditLogRepositorySQLite(AuditLogRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, action: str, entity_type: str, entity_id: str, details: Optional[str] = None) -> AuditLogModel:
        log = AuditLogModel(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_logs(self, entity_type: Optional[str] = None, user_id: Optional[str] = None) -> List[AuditLogModel]:
        query = select(AuditLogModel)
        if entity_type:
            query = query.where(AuditLogModel.entity_type == entity_type)
        if user_id:
            query = query.where(AuditLogModel.user_id == user_id)
            
        return list(self.db.execute(query.order_by(AuditLogModel.timestamp.desc())).scalars().all())


class AuditLogRepositoryFirestore(AuditLogRepository):
    def __init__(self, db):
        self.db = db
        self.collection = self.db.collection('audit_logs')

    def create(self, user_id: str, action: str, entity_type: str, entity_id: str, details: Optional[str] = None) -> AuditLogModel:
        from core.utils import generate_id, utc_now
        log_id = generate_id("LOG")
        
        doc_data = {
            "log_id": log_id,
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details,
            "timestamp": utc_now()
        }
        
        self.collection.document(log_id).set(doc_data)
        return AuditLogModel(**doc_data)

    def list_logs(self, entity_type: Optional[str] = None, user_id: Optional[str] = None) -> List[AuditLogModel]:
        query = self.collection
        if entity_type:
            query = query.where('entity_type', '==', entity_type)
        if user_id:
            query = query.where('user_id', '==', user_id)
            
        docs = query.order_by('timestamp', direction="DESCENDING").get()
        return [AuditLogModel(**d.to_dict()) for d in docs]


def get_audit_log_repository(db) -> AuditLogRepository:
    if settings.is_sqlite:
        return AuditLogRepositorySQLite(db)
    else:
        return AuditLogRepositoryFirestore(db)
