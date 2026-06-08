from fastapi import APIRouter, Depends, Query
from typing import List
from datetime import datetime

from core.dependencies import get_db, require_role
from core.enums import Role
from core.schemas import CurrentUser, DeleteHistoryResponse
from modules.notifications.schemas import NotificationOut, NotificationCreate
from modules.notifications.repository import get_notification_repository
from modules.notifications.service import NotificationService

router = APIRouter()

def get_notification_service(db=Depends(get_db)) -> NotificationService:
    repo = get_notification_repository(db)
    return NotificationService(repo)

@router.get("", response_model=List[NotificationOut])
def list_my_notifications(
    unread_only: bool = False,
    service: NotificationService = Depends(get_notification_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    """Get all notifications for the currently logged in user."""
    return service.list_my_notifications(current_user.user_id, unread_only)

@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    """Mark a specific notification as read."""
    return service.mark_as_read(notification_id, current_user.user_id)

@router.post("/system", response_model=NotificationOut)
def create_system_notification(
    data: NotificationCreate,
    service: NotificationService = Depends(get_notification_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """Admin endpoint to manually push a notification to a specific user."""
    return service.create_notification(data)

@router.delete("/history", response_model=DeleteHistoryResponse)
def delete_notification_history(
    before: datetime = Query(..., description="Delete notifications before this ISO timestamp"),
    service: NotificationService = Depends(get_notification_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    count = service.delete_history(before)
    return DeleteHistoryResponse(message="Notification history deleted", deleted_count=count)

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    from fastapi import HTTPException
    # For now, let the service check ownership unless it's an admin
    # To bypass ownership check for admins, we could add a force flag, but simpler to just try delete.
    success = False
    try:
        # If admin, bypass ownership in service by not enforcing it or by catching
        # We will just let them delete their own. Admin can clear history anyway.
        success = service.delete_notification(notification_id, current_user.user_id)
    except Exception as e:
        if current_user.role == Role.ADMIN:
            # Admins can force delete
            success = service.repo.delete_notification(notification_id)
        else:
            raise e
            
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    from core.schemas import MessageResponse
    return MessageResponse(message="Notification deleted successfully")
