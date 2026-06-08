from fastapi import APIRouter, Depends

from core.dependencies import get_db, require_role
from core.enums import Role
from core.schemas import CurrentUser
from modules.reports.schemas import ReportOut, ReportRequest
from modules.reports.repository import get_report_repository
from modules.reports.service import ReportService

router = APIRouter()

def get_report_service(db=Depends(get_db)) -> ReportService:
    repo = get_report_repository(db)
    return ReportService(repo)

@router.get("/facilities", response_model=list[dict])
def list_facilities(
    service: ReportService = Depends(get_report_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    """Fetch distinct lab IDs from the incidents table."""
    return service.get_facilities()

@router.post("/generate", response_model=ReportOut)
def generate_report(
    request: ReportRequest,
    service: ReportService = Depends(get_report_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    """
    Generate a formatted report (e.g., 'safety', 'inventory').
    The data payload can be used by the frontend to render a PDF or CSV.
    """
    return service.generate_report(request, current_user.user_id)
