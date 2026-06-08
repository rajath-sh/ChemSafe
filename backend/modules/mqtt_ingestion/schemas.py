from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ESP32Payload(BaseModel):
    """Expected JSON payload from ESP32."""
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    gas: Optional[float] = None
    light: Optional[float] = None
    vibration: Optional[float] = None
    timestamp: Optional[datetime] = None

class SimulatedPayload(ESP32Payload):
    """For API testing."""
    lab_id: str = Field(..., description="Target laboratory ID")
