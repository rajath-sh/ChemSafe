from fastapi import APIRouter, Depends

from core.dependencies import get_db, require_role
from core.enums import Role
from core.schemas import CurrentUser
from modules.settings.schemas import SystemSettingsOut, SystemSettingsUpdate
from modules.settings.repository import get_settings_repository
from modules.settings.service import SettingsService

router = APIRouter()

def get_settings_service(db=Depends(get_db)) -> SettingsService:
    repo = get_settings_repository(db)
    return SettingsService(repo)

@router.get("", response_model=SystemSettingsOut)
def get_system_settings(
    service: SettingsService = Depends(get_settings_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    """Get system-wide settings."""
    return service.get_system_settings()

@router.patch("", response_model=SystemSettingsOut)
def update_system_settings(
    data: SystemSettingsUpdate,
    service: SettingsService = Depends(get_settings_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """
    Update system-wide settings.
    Restricted to Admins.
    """
    return service.update_system_settings(data)
