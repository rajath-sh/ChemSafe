from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from core.enums import Role, UserStatus, StaffAvailability
from core.schemas import TimestampMixin

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: Role = Role.VIEWER
    phone: Optional[str] = None
    department: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    availability: Optional[StaffAvailability] = StaffAvailability.AVAILABLE

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[Role] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    status: Optional[UserStatus] = None
    availability: Optional[StaffAvailability] = None

class UserOut(TimestampMixin):
    user_id: str
    name: str
    email: str
    role: Role
    phone: Optional[str]
    department: Optional[str]
    status: UserStatus
    availability: Optional[StaffAvailability]
