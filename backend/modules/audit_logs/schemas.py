from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuditLogOut(BaseModel):
    log_id: str
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    details: Optional[str]
    timestamp: datetime
