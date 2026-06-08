from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from core.models_sql import IncidentModel, ChemicalModel, AlertModel
from core.config import settings

class ReportRepository(ABC):
    @abstractmethod
    def get_incidents(self, lab_id: str, since: datetime) -> List[IncidentModel]: ...
    
    @abstractmethod
    def get_chemicals(self, location_id: Optional[str] = None) -> List[ChemicalModel]: ...
    
    @abstractmethod
    def get_facilities(self) -> List[str]: ...
    
    @abstractmethod
    def get_alerts(self, lab_id: str, since: datetime) -> List[AlertModel]: ...


class ReportRepositorySQLite(ReportRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_facilities(self) -> List[Dict[str, str]]:
        from core.models_sql import SensorModel, LaboratoryModel
        incidents_labs = self.db.execute(select(IncidentModel.lab_id).distinct()).scalars().all()
        sensors_labs = self.db.execute(select(SensorModel.lab_id).distinct()).scalars().all()
        all_lab_ids = list(set(list(incidents_labs) + list(sensors_labs)))
        
        # Fetch lab names
        if not all_lab_ids:
            return []
            
        labs = self.db.execute(select(LaboratoryModel).where(LaboratoryModel.lab_id.in_(all_lab_ids))).scalars().all()
        lab_map = {l.lab_id: l.lab_name for l in labs}
        
        return [{"id": lid, "name": lab_map.get(lid, f"Facility ({lid})")} for lid in all_lab_ids]

    def get_incidents(self, lab_id: str, since: datetime) -> List[IncidentModel]:
        query = select(IncidentModel).where(
            and_(
                IncidentModel.lab_id == lab_id,
                IncidentModel.created_at >= since
            )
        )
        return list(self.db.execute(query).scalars().all())

    def get_chemicals(self, location_id: Optional[str] = None) -> List[ChemicalModel]:
        query = select(ChemicalModel)
        if location_id:
            query = query.where(ChemicalModel.location_id == location_id)
        return list(self.db.execute(query).scalars().all())

    def get_alerts(self, lab_id: str, since: datetime) -> List[AlertModel]:
        query = select(AlertModel).where(
            and_(
                AlertModel.lab_id == lab_id,
                AlertModel.created_at >= since
            )
        )
        return list(self.db.execute(query).scalars().all())


class ReportRepositoryFirestore(ReportRepository):
    def __init__(self, db):
        self.db = db

    def get_facilities(self) -> List[Dict[str, str]]:
        incidents_docs = self.db.collection('incidents').select(['lab_id']).get()
        sensors_docs = self.db.collection('sensors').select(['lab_id']).get()
        labs = set(d.to_dict().get('lab_id') for d in incidents_docs if d.to_dict().get('lab_id'))
        labs.update(d.to_dict().get('lab_id') for d in sensors_docs if d.to_dict().get('lab_id'))
        return [{"id": lid, "name": f"Facility ({lid})"} for lid in labs]

    def get_incidents(self, lab_id: str, since: datetime) -> List[IncidentModel]:
        docs = self.db.collection('incidents') \
            .where('lab_id', '==', lab_id) \
            .where('created_at', '>=', since) \
            .get()
        return [IncidentModel(**d.to_dict()) for d in docs]

    def get_chemicals(self, location_id: Optional[str] = None) -> List[ChemicalModel]:
        query = self.db.collection('chemicals')
        if location_id:
            query = query.where('location_id', '==', location_id)
        docs = query.get()
        return [ChemicalModel(**d.to_dict()) for d in docs]

    def get_alerts(self, lab_id: str, since: datetime) -> List[AlertModel]:
        docs = self.db.collection('alerts') \
            .where('lab_id', '==', lab_id) \
            .where('created_at', '>=', since) \
            .get()
        return [AlertModel(**d.to_dict()) for d in docs]


def get_report_repository(db) -> ReportRepository:
    if settings.is_sqlite:
        return ReportRepositorySQLite(db)
    else:
        return ReportRepositoryFirestore(db)
