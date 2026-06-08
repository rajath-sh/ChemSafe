from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ReportRequest(BaseModel):
    report_type: str  # 'safety' or 'inventory'
    lab_id: Optional[str] = None
    location_id: Optional[str] = None
    days: int = 30

class ReportOut(BaseModel):
    report_id: str
    lab_id: Optional[str]
    location_id: Optional[str]
    report_type: str
    generated_at: datetime
    generated_by: str
    data: Dict[str, Any]
