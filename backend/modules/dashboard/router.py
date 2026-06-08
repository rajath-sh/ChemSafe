from fastapi import APIRouter, Depends

from core.dependencies import get_db, require_role
from core.enums import Role
from core.schemas import CurrentUser
from modules.dashboard.schemas import DashboardSnapshot
from modules.dashboard.repository import get_dashboard_repository
from modules.dashboard.service import DashboardService

router = APIRouter()

def get_dashboard_service(db=Depends(get_db)) -> DashboardService:
    repo = get_dashboard_repository(db)
    return DashboardService(repo)

@router.get("/{lab_id}", response_model=DashboardSnapshot)
def get_dashboard(
    lab_id: str,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    """
    Get a real-time summary snapshot for the main UI dashboard.
    Includes active alerts, open incidents, staff availability, and sensor status.
    """
    return service.get_snapshot(lab_id)
