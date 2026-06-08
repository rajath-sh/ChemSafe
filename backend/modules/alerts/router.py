from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime

from core.dependencies import get_db, require_role
from core.enums import Role, AlertStatus
from core.schemas import CurrentUser, DeleteHistoryResponse
from modules.alerts.schemas import AlertCreate, AlertUpdate, AlertOut
from modules.alerts.repository import get_alert_repository
from modules.alerts.service import AlertService

router = APIRouter()

def get_alert_service(db=Depends(get_db)) -> AlertService:
    repo = get_alert_repository(db)
    return AlertService(repo)

@router.post("", response_model=AlertOut)
def create_alert(
    data: AlertCreate, 
    service: AlertService = Depends(get_alert_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """Manually create an alert."""
    return service.create_alert(data)

@router.get("", response_model=List[AlertOut])
def list_alerts(
    lab_id: Optional[str] = None,
    status: Optional[str] = None,
    service: AlertService = Depends(get_alert_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.list_alerts(lab_id, status)

@router.get("/anomalies")
def list_anomalies(
    lab_id: Optional[str] = None,
    service: AlertService = Depends(get_alert_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    # Returns List of AnomalyModel dictionaries (no specific schema defined yet)
    return service.list_anomalies(lab_id)

@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: str,
    service: AlertService = Depends(get_alert_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.get_alert(alert_id)

@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(
    alert_id: str,
    service: AlertService = Depends(get_alert_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    return service.update_status(alert_id, AlertStatus.ACKNOWLEDGED)

@router.patch("/{alert_id}/convert", response_model=AlertOut)
def convert_alert_to_incident(
    alert_id: str,
    service: AlertService = Depends(get_alert_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """
    Mark alert as converted. 
    (The Incidents module will handle actual incident creation).
    """
    return service.update_status(alert_id, AlertStatus.CONVERTED)

@router.patch("/{alert_id}/close", response_model=AlertOut)
def close_alert(
    alert_id: str,
    service: AlertService = Depends(get_alert_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    return service.update_status(alert_id, AlertStatus.CLOSED)

@router.delete("/history", response_model=DeleteHistoryResponse)
def delete_alert_history(
    before: datetime = Query(..., description="Delete alerts before this ISO timestamp"),
    service: AlertService = Depends(get_alert_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    count = service.delete_history(before)
    return DeleteHistoryResponse(message="Alert history deleted", deleted_count=count)
