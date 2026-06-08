from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from core.enums import AlertType, AlertSeverity, AlertStatus
from core.schemas import TimestampMixin

class AlertCreate(BaseModel):
    lab_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: Optional[str] = None
    sensor_value: Optional[float] = None
    threshold_value: Optional[float] = None
    sensor_id: Optional[str] = None

class AlertUpdate(BaseModel):
    status: AlertStatus

class AlertOut(TimestampMixin):
    alert_id: str
    lab_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: Optional[str]
    status: AlertStatus
    sensor_value: Optional[float]
    threshold_value: Optional[float]
    sensor_id: Optional[str]
