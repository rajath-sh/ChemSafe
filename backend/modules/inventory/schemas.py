from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from core.enums import HazardClass
from core.schemas import TimestampMixin

class InventoryLocationCreate(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = None

class InventoryLocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    description: Optional[str] = None

class InventoryLocationOut(TimestampMixin):
    location_id: str
    name: str
    description: Optional[str]

class ChemicalCreate(BaseModel):
    location_id: str
    name: str = Field(..., min_length=2)
    cas_number: Optional[str] = None
    hazard_class: HazardClass
    quantity: float = Field(..., ge=0)
    unit: str
    image_url: Optional[str] = None

class ChemicalUpdate(BaseModel):
    quantity: Optional[float] = Field(None, ge=0)
    location_id: Optional[str] = None
    image_url: Optional[str] = None

class ChemicalOut(TimestampMixin):
    chemical_id: str
    location_id: str
    name: str
    cas_number: Optional[str]
    hazard_class: HazardClass
    quantity: float
    unit: str
    image_url: Optional[str]
    last_updated_by: Optional[str]
