from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from core.models_sql import IncidentModel, IncidentNoteModel
from modules.incidents.schemas import IncidentCreate, IncidentUpdate, IncidentNoteCreate
from core.config import settings

class IncidentRepository(ABC):
    @abstractmethod
    def create(self, data: IncidentCreate) -> IncidentModel: ...
    @abstractmethod
    def get_by_id(self, incident_id: str) -> Optional[IncidentModel]: ...
    @abstractmethod
    def list_incidents(self, lab_id: Optional[str] = None, status: Optional[str] = None) -> List[IncidentModel]: ...
    @abstractmethod
    def update(self, incident: IncidentModel, data: IncidentUpdate) -> IncidentModel: ...
    @abstractmethod
    def delete_incident(self, incident_id: str) -> bool: ...
    @abstractmethod
    def delete_history(self, before: datetime) -> int: ...

    # Notes
    @abstractmethod
    def add_note(self, incident_id: str, user_id: str, data: IncidentNoteCreate) -> IncidentNoteModel: ...
    @abstractmethod
    def get_notes(self, incident_id: str) -> List[IncidentNoteModel]: ...


class IncidentRepositorySQLite(IncidentRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: IncidentCreate) -> IncidentModel:
        incident = IncidentModel(**data.model_dump(exclude_unset=True))
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def get_by_id(self, incident_id: str) -> Optional[IncidentModel]:
        return self.db.execute(select(IncidentModel).where(IncidentModel.incident_id == incident_id)).scalar_one_or_none()

    def list_incidents(self, lab_id: Optional[str] = None, status: Optional[str] = None) -> List[IncidentModel]:
        query = select(IncidentModel)
        if lab_id:
            query = query.where(IncidentModel.lab_id == lab_id)
        if status:
            query = query.where(IncidentModel.status == status)
        return list(self.db.execute(query.order_by(IncidentModel.created_at.desc())).scalars().all())

    def update(self, incident: IncidentModel, data: IncidentUpdate) -> IncidentModel:
        updates = data.model_dump(exclude_unset=True)
        from core.enums import IncidentStatus
        from core.utils import utc_now
        
        # Handle resolution timestamp
        if "status" in updates:
            if updates["status"] == IncidentStatus.RESOLVED and incident.status != IncidentStatus.RESOLVED:
                incident.resolved_at = utc_now()
            elif updates["status"] != IncidentStatus.RESOLVED:
                incident.resolved_at = None

        for key, value in updates.items():
            setattr(incident, key, value)
            
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def delete_incident(self, incident_id: str) -> bool:
        incident = self.get_by_id(incident_id)
        if incident:
            self.db.delete(incident)
            self.db.commit()
            return True
        return False

    def delete_history(self, before: datetime) -> int:
        from sqlalchemy import delete
        stmt = delete(IncidentModel).where(IncidentModel.created_at < before)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def add_note(self, incident_id: str, user_id: str, data: IncidentNoteCreate) -> IncidentNoteModel:
        note = IncidentNoteModel(
            incident_id=incident_id,
            user_id=user_id,
            message=data.message
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def get_notes(self, incident_id: str) -> List[IncidentNoteModel]:
        return list(self.db.execute(
            select(IncidentNoteModel)
            .where(IncidentNoteModel.incident_id == incident_id)
            .order_by(IncidentNoteModel.created_at.asc())
        ).scalars().all())


class IncidentRepositoryFirestore(IncidentRepository):
    def __init__(self, db):
        self.db = db
        self.collection = self.db.collection('incidents')
        self.notes_collection = self.db.collection('incident_notes')

    def create(self, data: IncidentCreate) -> IncidentModel:
        from core.utils import generate_id, utc_now
        from core.enums import IncidentStatus
        
        incident_id = generate_id("INC")
        doc_data = data.model_dump(exclude_unset=True)
        doc_data['incident_id'] = incident_id
        doc_data['created_at'] = utc_now()
        
        if 'status' not in doc_data:
            doc_data['status'] = IncidentStatus.OPEN.value
            
        self.collection.document(incident_id).set(doc_data)
        return IncidentModel(**doc_data)

    def get_by_id(self, incident_id: str) -> Optional[IncidentModel]:
        doc = self.collection.document(incident_id).get()
        if doc.exists:
            return IncidentModel(**doc.to_dict())
        return None

    def list_incidents(self, lab_id: Optional[str] = None, status: Optional[str] = None) -> List[IncidentModel]:
        query = self.collection
        if lab_id:
            query = query.where('lab_id', '==', lab_id)
        if status:
            query = query.where('status', '==', status)
            
        docs = query.order_by('created_at', direction="DESCENDING").get()
        return [IncidentModel(**d.to_dict()) for d in docs]

    def update(self, incident: IncidentModel, data: IncidentUpdate) -> IncidentModel:
        updates = data.model_dump(exclude_unset=True)
        from core.enums import IncidentStatus
        from core.utils import utc_now
        
        if "status" in updates:
            if updates["status"] == IncidentStatus.RESOLVED.value and incident.status != IncidentStatus.RESOLVED:
                updates["resolved_at"] = utc_now()
                incident.resolved_at = updates["resolved_at"]
            elif updates["status"] != IncidentStatus.RESOLVED.value:
                updates["resolved_at"] = None
                incident.resolved_at = None

        self.collection.document(incident.incident_id).update(updates)
        for k, v in updates.items():
            setattr(incident, k, v)
        return incident

    def delete_incident(self, incident_id: str) -> bool:
        doc_ref = self.collection.document(incident_id)
        if doc_ref.get().exists:
            doc_ref.delete()
            return True
        return False

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

    def add_note(self, incident_id: str, user_id: str, data: IncidentNoteCreate) -> IncidentNoteModel:
        from core.utils import generate_id, utc_now
        note_id = generate_id("NTE")
        doc_data = {
            "note_id": note_id,
            "incident_id": incident_id,
            "user_id": user_id,
            "message": data.message,
            "created_at": utc_now()
        }
        self.notes_collection.document(note_id).set(doc_data)
        return IncidentNoteModel(**doc_data)

    def get_notes(self, incident_id: str) -> List[IncidentNoteModel]:
        docs = self.notes_collection.where('incident_id', '==', incident_id).order_by('created_at').get()
        return [IncidentNoteModel(**d.to_dict()) for d in docs]


def get_incident_repository(db) -> IncidentRepository:
    if settings.is_sqlite:
        return IncidentRepositorySQLite(db)
    else:
        return IncidentRepositoryFirestore(db)
