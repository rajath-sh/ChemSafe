from pydantic import BaseModel, Field
from typing import Optional

class SystemSettingsOut(BaseModel):
    mqtt_broker_url: str = "localhost"
    global_notifications_enabled: bool = True
    strict_mode_enabled: bool = False
    data_retention_days: int = Field(30, ge=1)
    
class SystemSettingsUpdate(BaseModel):
    mqtt_broker_url: Optional[str] = None
    global_notifications_enabled: Optional[bool] = None
    strict_mode_enabled: Optional[bool] = None
    data_retention_days: Optional[int] = Field(None, ge=1)
