from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from core.models_sql import ChemicalModel, InventoryLocationModel
from modules.inventory.schemas import ChemicalCreate, ChemicalUpdate, InventoryLocationCreate, InventoryLocationUpdate
from core.config import settings

class InventoryRepository(ABC):
    # Locations
    @abstractmethod
    def create_location(self, data: InventoryLocationCreate) -> InventoryLocationModel: ...
    @abstractmethod
    def get_location(self, location_id: str) -> Optional[InventoryLocationModel]: ...
    @abstractmethod
    def list_locations(self) -> List[InventoryLocationModel]: ...
    @abstractmethod
    def update_location(self, location: InventoryLocationModel, data: InventoryLocationUpdate) -> InventoryLocationModel: ...
    @abstractmethod
    def delete_location(self, location: InventoryLocationModel) -> None: ...

    # Chemicals
    @abstractmethod
    def create(self, data: ChemicalCreate, user_id: str) -> ChemicalModel: ...
    @abstractmethod
    def get_by_id(self, chemical_id: str) -> Optional[ChemicalModel]: ...
    @abstractmethod
    def list_chemicals(self, location_id: Optional[str] = None, hazard_class: Optional[str] = None) -> List[ChemicalModel]: ...
    @abstractmethod
    def update(self, chemical: ChemicalModel, data: ChemicalUpdate, user_id: str) -> ChemicalModel: ...
    @abstractmethod
    def delete(self, chemical: ChemicalModel) -> None: ...


class InventoryRepositorySQLite(InventoryRepository):
    def __init__(self, db: Session):
        self.db = db

    # Locations
    def create_location(self, data: InventoryLocationCreate) -> InventoryLocationModel:
        loc = InventoryLocationModel(**data.model_dump(exclude_unset=True))
        self.db.add(loc)
        self.db.commit()
        self.db.refresh(loc)
        return loc

    def get_location(self, location_id: str) -> Optional[InventoryLocationModel]:
        return self.db.execute(select(InventoryLocationModel).where(InventoryLocationModel.location_id == location_id)).scalar_one_or_none()

    def list_locations(self) -> List[InventoryLocationModel]:
        return list(self.db.execute(select(InventoryLocationModel).order_by(InventoryLocationModel.name)).scalars().all())

    def update_location(self, location: InventoryLocationModel, data: InventoryLocationUpdate) -> InventoryLocationModel:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(location, k, v)
        self.db.commit()
        self.db.refresh(location)
        return location

    def delete_location(self, location: InventoryLocationModel) -> None:
        self.db.delete(location)
        self.db.commit()

    # Chemicals
    def create(self, data: ChemicalCreate, user_id: str) -> ChemicalModel:
        chemical = ChemicalModel(
            **data.model_dump(exclude_unset=True),
            last_updated_by=user_id
        )
        self.db.add(chemical)
        self.db.commit()
        self.db.refresh(chemical)
        return chemical

    def get_by_id(self, chemical_id: str) -> Optional[ChemicalModel]:
        return self.db.execute(select(ChemicalModel).where(ChemicalModel.chemical_id == chemical_id)).scalar_one_or_none()

    def list_chemicals(self, location_id: Optional[str] = None, hazard_class: Optional[str] = None) -> List[ChemicalModel]:
        query = select(ChemicalModel)
        if location_id:
            query = query.where(ChemicalModel.location_id == location_id)
        if hazard_class:
            query = query.where(ChemicalModel.hazard_class == hazard_class)
        return list(self.db.execute(query).scalars().all())

    def update(self, chemical: ChemicalModel, data: ChemicalUpdate, user_id: str) -> ChemicalModel:
        updates = data.model_dump(exclude_unset=True)
        updates['last_updated_by'] = user_id
        from core.utils import utc_now
        updates['updated_at'] = utc_now()
        
        for key, value in updates.items():
            setattr(chemical, key, value)
            
        self.db.commit()
        self.db.refresh(chemical)
        return chemical

    def delete(self, chemical: ChemicalModel) -> None:
        self.db.delete(chemical)
        self.db.commit()


class InventoryRepositoryFirestore(InventoryRepository):
    def __init__(self, db):
        self.db = db
        self.collection = self.db.collection('chemicals')
        self.loc_collection = self.db.collection('inventory_locations')

    # Locations
    def create_location(self, data: InventoryLocationCreate) -> InventoryLocationModel:
        from core.utils import generate_id, utc_now
        loc_id = generate_id("LOC")
        doc_data = data.model_dump(exclude_unset=True)
        doc_data['location_id'] = loc_id
        doc_data['created_at'] = utc_now()
        self.loc_collection.document(loc_id).set(doc_data)
        return InventoryLocationModel(**doc_data)

    def get_location(self, location_id: str) -> Optional[InventoryLocationModel]:
        doc = self.loc_collection.document(location_id).get()
        if doc.exists:
            return InventoryLocationModel(**doc.to_dict())
        return None

    def list_locations(self) -> List[InventoryLocationModel]:
        docs = self.loc_collection.get()
        return [InventoryLocationModel(**d.to_dict()) for d in docs]

    def update_location(self, location: InventoryLocationModel, data: InventoryLocationUpdate) -> InventoryLocationModel:
        updates = data.model_dump(exclude_unset=True)
        self.loc_collection.document(location.location_id).update(updates)
        for k, v in updates.items():
            setattr(location, k, v)
        return location

    def delete_location(self, location: InventoryLocationModel) -> None:
        self.loc_collection.document(location.location_id).delete()

    # Chemicals
    def create(self, data: ChemicalCreate, user_id: str) -> ChemicalModel:
        from core.utils import generate_id, utc_now
        chemical_id = generate_id("CHM")
        
        doc_data = data.model_dump(exclude_unset=True)
        doc_data['chemical_id'] = chemical_id
        doc_data['last_updated_by'] = user_id
        doc_data['created_at'] = utc_now()
        doc_data['updated_at'] = doc_data['created_at']
        
        self.collection.document(chemical_id).set(doc_data)
        return ChemicalModel(**doc_data)

    def get_by_id(self, chemical_id: str) -> Optional[ChemicalModel]:
        doc = self.collection.document(chemical_id).get()
        if doc.exists:
            return ChemicalModel(**doc.to_dict())
        return None

    def list_chemicals(self, location_id: Optional[str] = None, hazard_class: Optional[str] = None) -> List[ChemicalModel]:
        query = self.collection
        if location_id:
            query = query.where('location_id', '==', location_id)
        if hazard_class:
            query = query.where('hazard_class', '==', hazard_class)
            
        docs = query.get()
        return [ChemicalModel(**d.to_dict()) for d in docs]

    def update(self, chemical: ChemicalModel, data: ChemicalUpdate, user_id: str) -> ChemicalModel:
        from core.utils import utc_now
        updates = data.model_dump(exclude_unset=True)
        updates['last_updated_by'] = user_id
        updates['updated_at'] = utc_now()
        
        self.collection.document(chemical.chemical_id).update(updates)
        for k, v in updates.items():
            setattr(chemical, k, v)
        return chemical

    def delete(self, chemical: ChemicalModel) -> None:
        self.collection.document(chemical.chemical_id).delete()


def get_inventory_repository(db) -> InventoryRepository:
    if settings.is_sqlite:
        return InventoryRepositorySQLite(db)
    else:
        return InventoryRepositoryFirestore(db)
