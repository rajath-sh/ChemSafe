import logging
from typing import List, Optional

from modules.inventory.repository import InventoryRepository
from modules.inventory.schemas import ChemicalCreate, ChemicalUpdate, InventoryLocationCreate, InventoryLocationUpdate
from core.models_sql import ChemicalModel, InventoryLocationModel
from core.exceptions import NotFoundException
from core.event_bus import event_bus, Events

logger = logging.getLogger(__name__)

class InventoryService:
    def __init__(self, repo: InventoryRepository):
        self.repo = repo

    # ═══════════════════════════════════════════════════════════════
    # Locations
    # ═══════════════════════════════════════════════════════════════
    def create_location(self, data: InventoryLocationCreate) -> InventoryLocationModel:
        return self.repo.create_location(data)

    def get_location(self, location_id: str) -> InventoryLocationModel:
        loc = self.repo.get_location(location_id)
        if not loc:
            raise NotFoundException("Location", location_id)
        return loc

    def list_locations(self) -> List[InventoryLocationModel]:
        return self.repo.list_locations()

    def update_location(self, location_id: str, data: InventoryLocationUpdate) -> InventoryLocationModel:
        loc = self.get_location(location_id)
        return self.repo.update_location(loc, data)

    def delete_location(self, location_id: str) -> None:
        loc = self.get_location(location_id)
        # Prevent deletion if chemicals are present
        chems = self.repo.list_chemicals(location_id=location_id)
        if chems:
            raise Exception("Cannot delete location that contains chemicals")
        self.repo.delete_location(loc)


    # ═══════════════════════════════════════════════════════════════
    # Chemicals
    # ═══════════════════════════════════════════════════════════════
    def add_chemical(self, data: ChemicalCreate, user_id: str) -> ChemicalModel:
        """Adds a new chemical to the inventory."""
        # Validate location exists
        self.get_location(data.location_id)
        
        chemical = self.repo.create(data, user_id)
        # Notify the system a chemical was added (useful for audit logs later)
        event_bus.publish(Events.INVENTORY_UPDATED, {
            "chemical_id": chemical.chemical_id, 
            "location_id": chemical.location_id,
            "action": "created",
            "user_id": user_id
        })
        return chemical

    def get_chemical(self, chemical_id: str) -> ChemicalModel:
        chemical = self.repo.get_by_id(chemical_id)
        if not chemical:
            raise NotFoundException("Chemical", chemical_id)
        return chemical

    def list_chemicals(self, location_id: Optional[str] = None, hazard_class: Optional[str] = None) -> List[ChemicalModel]:
        return self.repo.list_chemicals(location_id, hazard_class)

    def update_chemical(self, chemical_id: str, data: ChemicalUpdate, user_id: str) -> ChemicalModel:
        chemical = self.get_chemical(chemical_id)
        
        if data.location_id and data.location_id != chemical.location_id:
            self.get_location(data.location_id)
            
        updated_chemical = self.repo.update(chemical, data, user_id)
        
        event_bus.publish(Events.INVENTORY_UPDATED, {
            "chemical_id": updated_chemical.chemical_id, 
            "location_id": updated_chemical.location_id,
            "action": "updated",
            "user_id": user_id
        })
        return updated_chemical

    def delete_chemical(self, chemical_id: str, user_id: str) -> None:
        chemical = self.get_chemical(chemical_id)
        self.repo.delete(chemical)
        
        event_bus.publish(Events.INVENTORY_UPDATED, {
            "chemical_id": chemical.chemical_id, 
            "location_id": chemical.location_id,
            "action": "deleted",
            "user_id": user_id
        })
