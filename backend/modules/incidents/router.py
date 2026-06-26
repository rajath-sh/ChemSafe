from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from core.dependencies import get_db, require_role
from core.enums import Role, IncidentStatus
from core.schemas import CurrentUser, MessageResponse, DeleteHistoryResponse
from modules.incidents.schemas import (
    IncidentCreate, IncidentUpdate, IncidentOut,
    IncidentNoteCreate, IncidentNoteOut
)
from modules.incidents.repository import get_incident_repository
from modules.incidents.service import IncidentService

router = APIRouter()

def get_incident_service(db=Depends(get_db)) -> IncidentService:
    repo = get_incident_repository(db)
    return IncidentService(repo)

# ── Incidents ──
@router.post("", response_model=IncidentOut)
def create_incident(
    data: IncidentCreate, 
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """Manually create an incident."""
    return service.create_incident(data)

@router.get("", response_model=List[IncidentOut])
def list_incidents(
    lab_id: Optional[str] = None,
    status: Optional[str] = None,
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.list_incidents(lab_id, status)

@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(
    incident_id: str,
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.get_incident(incident_id)

@router.delete("/{incident_id}")
def delete_incident(
    incident_id: str,
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    success = service.delete_incident(incident_id)
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found")
    return MessageResponse(message="Incident deleted successfully")

@router.patch("/{incident_id}", response_model=IncidentOut)
def update_incident(
    incident_id: str,
    data: IncidentUpdate,
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    return service.update_incident(incident_id, data)

@router.delete("/history", response_model=DeleteHistoryResponse)
def delete_incident_history(
    before: datetime = Query(..., description="Delete incidents before this ISO timestamp"),
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    count = service.delete_history(before)
    return DeleteHistoryResponse(message="Incident history deleted", deleted_count=count)

# ── Notes ──
@router.post("/{incident_id}/notes", response_model=IncidentNoteOut)
def add_incident_note(
    incident_id: str,
    data: IncidentNoteCreate,
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    """Add a note to the incident timeline."""
    return service.add_note(incident_id, current_user.user_id, data)

@router.get("/{incident_id}/notes", response_model=List[IncidentNoteOut])
def get_incident_notes(
    incident_id: str,
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.get_notes(incident_id)
