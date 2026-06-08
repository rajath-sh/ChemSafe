from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from core.schemas import TimestampMixin

class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    is_read: bool = False

from pydantic import model_validator
from core.enums import NotificationStatus

class NotificationOut(TimestampMixin):
    notification_id: str
    user_id: str
    title: str
    message: str
    is_read: bool

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def map_status_to_is_read(cls, data):
        # Handle both dicts and ORM objects
        if isinstance(data, dict):
            if 'status' in data and 'is_read' not in data:
                data['is_read'] = data['status'] == NotificationStatus.READ
            elif 'is_read' not in data:
                data['is_read'] = False
        else:
            # It's an ORM object
            if hasattr(data, 'status'):
                status_val = data.status.value if hasattr(data.status, 'value') else data.status
                is_read = status_val == NotificationStatus.READ.value
                # We need to return a dict to allow adding new fields in 'before' mode
                data_dict = {
                    c.name: getattr(data, c.name) for c in data.__table__.columns
                }
                data_dict['is_read'] = is_read
                return data_dict
        return data
