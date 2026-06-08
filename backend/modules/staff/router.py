from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from core.dependencies import get_db, require_role
from core.enums import Role, StaffAvailability
from core.schemas import CurrentUser
from modules.staff.schemas import StaffUpdate, StaffOut
from modules.staff.repository import get_staff_repository
from modules.staff.service import StaffService

router = APIRouter()

def get_staff_service(db=Depends(get_db)) -> StaffService:
    repo = get_staff_repository(db)
    return StaffService(repo)

@router.get("", response_model=List[StaffOut])
def list_staff(
    department: Optional[str] = None,
    availability: Optional[str] = None,
    service: StaffService = Depends(get_staff_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.list_staff(department, availability)

@router.get("/{user_id}", response_model=StaffOut)
def get_staff_member(
    user_id: str,
    service: StaffService = Depends(get_staff_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.get_staff(user_id)

@router.patch("/{user_id}", response_model=StaffOut)
def update_staff(
    user_id: str,
    data: StaffUpdate,
    service: StaffService = Depends(get_staff_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    # Staff can only update their own status unless they are Admin
    if current_user.role != Role.ADMIN and current_user.user_id != user_id:
        from core.exceptions import ForbiddenException
        raise ForbiddenException("You can only update your own availability")
        
    return service.update_staff(user_id, data)
