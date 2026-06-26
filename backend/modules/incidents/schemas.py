from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from core.enums import IncidentStatus, IncidentSeverity
from core.schemas import TimestampMixin

class IncidentNoteCreate(BaseModel):
    message: str = Field(..., min_length=1)

class IncidentNoteOut(TimestampMixin):
    note_id: str
    incident_id: str
    user_id: str
    message: str

class IncidentCreate(BaseModel):
    lab_id: str
    title: str = Field(..., min_length=3)
    description: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.INFO
    alert_id: Optional[str] = None

class IncidentUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[IncidentStatus] = None
    assigned_staff_id: Optional[str] = None
    resolution_summary: Optional[str] = None
    rejection_reason: Optional[str] = None

class IncidentOut(TimestampMixin):
    incident_id: str
    lab_id: str
    title: str
    description: Optional[str]
    severity: IncidentSeverity
    status: IncidentStatus
    assigned_staff_id: Optional[str]
    alert_id: Optional[str]
    resolution_summary: Optional[str]
    rejection_reason: Optional[str] = None
    resolved_at: Optional[datetime]
