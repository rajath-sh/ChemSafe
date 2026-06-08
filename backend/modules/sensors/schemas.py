from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from core.enums import SensorType, SensorStatus
from core.schemas import TimestampMixin

# ── Laboratory (Helper for testing) ──
class LabCreate(BaseModel):
    lab_name: str = Field(..., min_length=2)
    location: Optional[str] = None
    description: Optional[str] = None

class LabOut(TimestampMixin):
    lab_id: str
    lab_name: str
    location: Optional[str]
    description: Optional[str]

# ── Sensors ──
class SensorCreate(BaseModel):
    lab_id: str
    sensor_type: SensorType
    status: SensorStatus = SensorStatus.ONLINE

class SensorUpdate(BaseModel):
    status: Optional[SensorStatus] = None

class SensorOut(BaseModel):
    sensor_id: str
    lab_id: str
    sensor_type: SensorType
    status: SensorStatus
    last_reading: Optional[float]
    last_updated: Optional[datetime]

# ── Thresholds ──
class ThresholdCreate(BaseModel):
    lab_id: str
    sensor_type: SensorType
    warning_value: float
    critical_value: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None

class ThresholdOut(BaseModel):
    threshold_id: str
    lab_id: str
    sensor_type: SensorType
    warning_value: float
    critical_value: float
    min_value: Optional[float]
    max_value: Optional[float]

# ── Readings (Historical) ──
class SensorReadingOut(BaseModel):
    reading_id: str
    lab_id: str
    temperature: Optional[float]
    humidity: Optional[float]
    gas: Optional[float]
    light: Optional[float]
    vibration: Optional[float]
    timestamp: datetime
