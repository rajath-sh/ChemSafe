from pydantic import BaseModel
from typing import Optional

from core.enums import StaffAvailability, Role

class StaffUpdate(BaseModel):
    availability: StaffAvailability
    department: Optional[str] = None
    phone: Optional[str] = None

class StaffOut(BaseModel):
    user_id: str
    name: str
    email: str
    phone: Optional[str]
    department: Optional[str]
    availability: StaffAvailability
