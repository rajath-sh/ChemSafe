import logging
from typing import List, Dict, Any
from datetime import datetime

from modules.notifications.repository import NotificationRepository
from modules.notifications.schemas import NotificationCreate
from core.models_sql import NotificationModel
from core.exceptions import NotFoundException, ForbiddenException
from core.event_bus import event_bus, Events

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    def create_notification(self, data: NotificationCreate) -> NotificationModel:
        """Create a notification and log it."""
        # In a real app, this is where you would hook in Twilio/SendGrid to send SMS or Email.
        logger.info(f"Notification generated for User {data.user_id}: {data.title}")
        return self.repo.create(data)

    def list_my_notifications(self, user_id: str, unread_only: bool = False) -> List[NotificationModel]:
        return self.repo.list_user_notifications(user_id, unread_only)

    def mark_as_read(self, notification_id: str, user_id: str) -> NotificationModel:
        notification = self.repo.get_by_id(notification_id)
        if not notification:
            raise NotFoundException("Notification", notification_id)
        
        if notification.user_id != user_id:
            raise ForbiddenException("You cannot modify someone else's notification")
            
        return self.repo.mark_as_read(notification)

    def delete_history(self, before: datetime) -> int:
        return self.repo.delete_history(before)
        
    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        notification = self.repo.get_by_id(notification_id)
        if not notification:
            return False
            
        # Admins can delete any, but users can only delete their own
        if notification.user_id != user_id:
            from core.exceptions import ForbiddenException
            # Since we don't have role check directly here easily without changing signature, 
            # we'll enforce that the router either passes admin user_id or normal user_id.
            # For simplicity, if they don't own it, deny unless handled at router.
            raise ForbiddenException("You cannot delete someone else's notification")
            
        return self.repo.delete_notification(notification_id)


# ═══════════════════════════════════════════════════════════════
# Internal Event Handlers
# ═══════════════════════════════════════════════════════════════

def _handle_incident_assigned(payload: Dict[str, Any]):
    """
    When an incident is assigned to a staff member, notify them.
    If it was rejected, notify the Admins instead.
    """
    try:
        incident_id = payload.get("incident_id")
        if not incident_id:
            return

        from core.database import get_sqlite_session, get_firestore_client
        from core.config import settings
        from modules.notifications.repository import get_notification_repository
        from sqlalchemy import select
        from core.models_sql import UserModel
        from core.enums import Role

        db = None
        session_generator = None
        if settings.is_sqlite:
            session_generator = get_sqlite_session()
            db = next(session_generator)
        else:
            db = get_firestore_client()

        try:
            repo = get_notification_repository(db)
            service = NotificationService(repo)
            
            is_rejected = payload.get("rejected", False)

            if is_rejected:
                # Notify Admins about the rejection
                admins = []
                if settings.is_sqlite:
                    admins = list(db.execute(select(UserModel).where(UserModel.role == Role.ADMIN)).scalars().all())
                else:
                    docs = db.collection('users').where('role', '==', Role.ADMIN.value).get()
                    admins = [UserModel(**d.to_dict()) for d in docs]
                    
                admin_ids = [a.user_id for a in admins]

                reason = payload.get("reason", "No reason provided")
                from core.email import EmailService
                for admin in admins:
                    notif_data = NotificationCreate(
                        user_id=admin.user_id,
                        title="Assignment Rejected",
                        message=f"Incident {incident_id} assignment was rejected. Reason: {reason}"
                    )
                    service.create_notification(notif_data)
                    EmailService.send_email(admin.email, notif_data.title, notif_data.message)
            else:
                # Notify the assigned staff
                staff_id = payload.get("staff_id")
                if staff_id:
                    if settings.is_sqlite:
                        staff = db.execute(select(UserModel).where(UserModel.user_id == staff_id)).scalar_one_or_none()
                    else:
                        doc = db.collection('users').document(staff_id).get()
                        staff = UserModel(**doc.to_dict()) if doc.exists else None
                        
                    if staff:
                        notif_data = NotificationCreate(
                            user_id=staff.user_id,
                            title="New Incident Assignment",
                            message=f"You have been assigned to handle incident: {incident_id}"
                        )
                        service.create_notification(notif_data)
                        from core.email import EmailService
                        EmailService.send_email(staff.email, notif_data.title, notif_data.message)
        finally:
            if session_generator:
                try:
                    next(session_generator)
                except StopIteration:
                    pass
    except Exception:
        logger.exception("Failed to auto-generate assignment notification")


def _handle_incident_resolved(payload: Dict[str, Any]):
    """Notify Admins when an incident is resolved by staff."""
    try:
        incident_id = payload.get("incident_id")
        if not incident_id:
            return

        from core.database import get_sqlite_session, get_firestore_client
        from core.config import settings
        from modules.notifications.repository import get_notification_repository
        from sqlalchemy import select
        from core.models_sql import UserModel
        from core.enums import Role

        db = None
        session_generator = None
        if settings.is_sqlite:
            session_generator = get_sqlite_session()
            db = next(session_generator)
        else:
            db = get_firestore_client()

        try:
            repo = get_notification_repository(db)
            service = NotificationService(repo)
            
            admins = []
            if settings.is_sqlite:
                admins = list(db.execute(select(UserModel).where(UserModel.role == Role.ADMIN)).scalars().all())
            else:
                docs = db.collection('users').where('role', '==', Role.ADMIN.value).get()
                admins = [UserModel(**d.to_dict()) for d in docs]

            admin_ids = [a.user_id for a in admins]

            from core.email import EmailService
            for admin in admins:
                notif_data = NotificationCreate(
                    user_id=admin.user_id,
                    title="Incident Resolved",
                    message=f"Incident {incident_id} has been successfully marked as resolved by the responding staff member."
                )
                service.create_notification(notif_data)
                EmailService.send_email(admin.email, notif_data.title, notif_data.message)
        finally:
            if session_generator:
                try:
                    next(session_generator)
                except StopIteration:
                    pass
    except Exception:
        logger.exception("Failed to auto-generate resolution notification")


def _handle_alert_created(payload: Dict[str, Any]):
    """
    When any alert is created, notify Admins.
    """
    try:
        severity = payload.get("severity", "info").upper()
        alert_id = payload.get("alert_id", "Unknown")

        from core.database import get_sqlite_session, get_firestore_client
        from core.config import settings
        from modules.notifications.repository import get_notification_repository
        from sqlalchemy import select
        from core.models_sql import UserModel
        from core.enums import Role

        db = None
        session_generator = None
        if settings.is_sqlite:
            session_generator = get_sqlite_session()
            db = next(session_generator)
        else:
            db = get_firestore_client()

        try:
            repo = get_notification_repository(db)
            service = NotificationService(repo)
            
            # Find all admins to notify
            admins = []
            if settings.is_sqlite:
                admins = list(db.execute(select(UserModel).where(UserModel.role == Role.ADMIN)).scalars().all())
            else:
                docs = db.collection('users').where('role', '==', Role.ADMIN.value).get()
                admins = [UserModel(**d.to_dict()) for d in docs]

            admin_ids = [a.user_id for a in admins]

            for uid in admin_ids:
                alert_msg = payload.get("message")
                if not alert_msg:
                    alert_msg = f"A {severity} alert ({alert_id}) has been triggered by the system."
                
                notif_data = NotificationCreate(
                    user_id=uid,
                    title=f"New {severity} Alert",
                    message=alert_msg
                )
                service.create_notification(notif_data)
        finally:
            if session_generator:
                try:
                    next(session_generator)
                except StopIteration:
                    pass
    except Exception:
        logger.exception("Failed to auto-generate alert notifications")


# Subscribe to the event bus
event_bus.subscribe(Events.INCIDENT_ASSIGNED, _handle_incident_assigned)
event_bus.subscribe(Events.INCIDENT_RESOLVED, _handle_incident_resolved)
event_bus.subscribe(Events.ALERT_CREATED, _handle_alert_created)
