from fastapi import APIRouter, Depends, Query
from typing import List

from core.dependencies import get_db, require_role
from core.enums import Role
from core.schemas import CurrentUser
from modules.analytics.schemas import LabAnalyticsOut
from modules.analytics.repository import get_analytics_repository
from modules.analytics.service import AnalyticsService

router = APIRouter()

def get_analytics_service(db=Depends(get_db)) -> AnalyticsService:
    repo = get_analytics_repository(db)
    return AnalyticsService(repo)

@router.get("/{lab_id}/summary", response_model=LabAnalyticsOut)
def get_lab_analytics_summary(
    lab_id: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    """
    Generate an analytical summary for a specific laboratory.
    Aggregates sensor data into daily averages and compiles incident statistics.
    Requires Admin or Staff role.
    """
    return service.generate_lab_report(lab_id, days)
