from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class SensorStats(BaseModel):
    min_value: float
    max_value: float
    avg_value: float

class DailyAggregation(BaseModel):
    date: str
    temperature: Optional[SensorStats] = None
    humidity: Optional[SensorStats] = None

class IncidentStats(BaseModel):
    total: int
    open_count: int
    resolved_count: int
    critical_count: int

class LabAnalyticsOut(BaseModel):
    lab_id: str
    date_range_days: int
    sensor_trends: List[DailyAggregation]
    incident_summary: IncidentStats
