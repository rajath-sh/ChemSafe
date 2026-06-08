from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SensorSummary(BaseModel):
    sensor_id: str
    node_id: Optional[str] = None
    lab_id: Optional[str] = None
    location_name: Optional[str] = None
    type: str
    status: str
    last_reading: Optional[float]
    last_updated: Optional[datetime]

class ActiveAlertSummary(BaseModel):
    alert_id: str
    type: str
    severity: str
    message: Optional[str]

class OpenIncidentSummary(BaseModel):
    incident_id: str
    title: str
    severity: str
    assigned_staff_name: Optional[str]

class DashboardSnapshot(BaseModel):
    lab_id: str
    total_active_sensors: int
    total_chemicals: int
    available_staff: int
    active_alerts: List[ActiveAlertSummary]
    open_incidents: List[OpenIncidentSummary]
    sensors: List[SensorSummary]
    generated_at: datetime
