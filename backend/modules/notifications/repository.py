from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from core.models_sql import NotificationModel
from modules.notifications.schemas import NotificationCreate
from core.config import settings

class NotificationRepository(ABC):
    @abstractmethod
    def create(self, data: NotificationCreate) -> NotificationModel: ...
    @abstractmethod
    def list_user_notifications(self, user_id: str, unread_only: bool = False) -> List[NotificationModel]: ...
    @abstractmethod
    def get_by_id(self, notification_id: str) -> Optional[NotificationModel]: ...
    @abstractmethod
    def mark_as_read(self, notification: NotificationModel) -> NotificationModel: ...
    @abstractmethod
    def delete_notification(self, notification_id: str) -> bool: ...
    @abstractmethod
    def delete_history(self, before: datetime) -> int: ...


class NotificationRepositorySQLite(NotificationRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: NotificationCreate) -> NotificationModel:
        notification = NotificationModel(**data.model_dump(exclude_unset=True))
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def list_user_notifications(self, user_id: str, unread_only: bool = False) -> List[NotificationModel]:
        query = select(NotificationModel).where(NotificationModel.user_id == user_id)
        if unread_only:
            query = query.where(NotificationModel.is_read == False)
        return list(self.db.execute(query.order_by(NotificationModel.created_at.desc())).scalars().all())

    def get_by_id(self, notification_id: str) -> Optional[NotificationModel]:
        return self.db.execute(select(NotificationModel).where(NotificationModel.notification_id == notification_id)).scalar_one_or_none()

    def mark_as_read(self, notification: NotificationModel) -> NotificationModel:
        notification.is_read = True
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def delete_notification(self, notification_id: str) -> bool:
        notification = self.get_by_id(notification_id)
        if notification:
            self.db.delete(notification)
            self.db.commit()
            return True
        return False

    def delete_history(self, before: datetime) -> int:
        from sqlalchemy import delete
        stmt = delete(NotificationModel).where(NotificationModel.created_at < before)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount


class NotificationRepositoryFirestore(NotificationRepository):
    def __init__(self, db):
        self.db = db
        self.collection = self.db.collection('notifications')

    def create(self, data: NotificationCreate) -> NotificationModel:
        from core.utils import generate_id, utc_now
        notif_id = generate_id("NOT")
        
        doc_data = data.model_dump(exclude_unset=True)
        doc_data['notification_id'] = notif_id
        doc_data['created_at'] = utc_now()
        
        self.collection.document(notif_id).set(doc_data)
        return NotificationModel(**doc_data)

    def list_user_notifications(self, user_id: str, unread_only: bool = False) -> List[NotificationModel]:
        query = self.collection.where('user_id', '==', user_id)
        if unread_only:
            query = query.where('is_read', '==', False)
            
        docs = query.order_by('created_at', direction="DESCENDING").get()
        return [NotificationModel(**d.to_dict()) for d in docs]

    def get_by_id(self, notification_id: str) -> Optional[NotificationModel]:
        doc = self.collection.document(notification_id).get()
        if doc.exists:
            return NotificationModel(**doc.to_dict())
        return None

    def mark_as_read(self, notification: NotificationModel) -> NotificationModel:
        self.collection.document(notification.notification_id).update({'is_read': True})
        notification.is_read = True
        return notification

    def delete_notification(self, notification_id: str) -> bool:
        doc_ref = self.collection.document(notification_id)
        if doc_ref.get().exists:
            doc_ref.delete()
            return True
        return False

    def delete_history(self, before: datetime) -> int:
        docs = self.collection.where('created_at', '<', before).get()
        count = 0
        batch = self.db.batch()
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            if count % 500 == 0:
                batch.commit()
                batch = self.db.batch()
        if count > 0:
            batch.commit()
        return count


def get_notification_repository(db) -> NotificationRepository:
    if settings.is_sqlite:
        return NotificationRepositorySQLite(db)
    else:
        return NotificationRepositoryFirestore(db)
