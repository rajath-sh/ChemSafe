import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from modules.incidents.repository import IncidentRepository
from modules.incidents.schemas import IncidentCreate, IncidentUpdate, IncidentNoteCreate
from core.models_sql import IncidentModel, IncidentNoteModel
from core.exceptions import NotFoundException
from core.enums import IncidentStatus, IncidentSeverity
from core.event_bus import event_bus, Events

logger = logging.getLogger(__name__)

class IncidentService:
    def __init__(self, repo: IncidentRepository):
        self.repo = repo

    def create_incident(self, data: IncidentCreate) -> IncidentModel:
        incident = self.repo.create(data)
        # Notify system that an incident was created
        event_bus.publish(Events.INCIDENT_CREATED, {"incident_id": incident.incident_id, "lab_id": incident.lab_id})
        return incident

    def get_incident(self, incident_id: str) -> IncidentModel:
        incident = self.repo.get_by_id(incident_id)
        if not incident:
            raise NotFoundException("Incident", incident_id)
        return incident

    def list_incidents(self, lab_id: Optional[str] = None, status: Optional[str] = None) -> List[IncidentModel]:
        return self.repo.list_incidents(lab_id, status)

    def update_incident(self, incident_id: str, data: IncidentUpdate) -> IncidentModel:
        incident = self.get_incident(incident_id)
        old_status = incident.status
        old_assignee = incident.assigned_staff_id

        # If staff rejects, nullify the assignee so it can be reassigned
        if data.rejection_reason and data.assigned_staff_id is None:
            # We enforce nullifying it in the dict if they provided a rejection reason
            data.assigned_staff_id = None

        if data.status == IncidentStatus.RESOLVED and old_status != IncidentStatus.RESOLVED:
            from core.utils import utc_now
            incident.resolved_at = utc_now()

        updated_incident = self.repo.update(incident, data)

        # Trigger Events
        if data.assigned_staff_id and data.assigned_staff_id != old_assignee:
            event_bus.publish(Events.INCIDENT_ASSIGNED, {
                "incident_id": incident_id, 
                "staff_id": data.assigned_staff_id
            })
            
        if old_assignee and old_assignee != updated_incident.assigned_staff_id:
            event_bus.publish(Events.INCIDENT_UNASSIGNED, {"staff_id": old_assignee})

        if data.rejection_reason and not data.assigned_staff_id:
            event_bus.publish(Events.INCIDENT_ASSIGNED, {
                "incident_id": incident_id, 
                "rejected": True, 
                "reason": data.rejection_reason
            })
            
        if data.status and data.status != old_status:
            if data.status == IncidentStatus.RESOLVED:
                event_bus.publish(Events.INCIDENT_RESOLVED, {"incident_id": incident_id, "lab_id": incident.lab_id, "alert_id": incident.alert_id})
            elif data.status == IncidentStatus.CLOSED:
                event_bus.publish(Events.INCIDENT_CLOSED, {"incident_id": incident_id, "lab_id": incident.lab_id, "alert_id": incident.alert_id})
            elif data.status == IncidentStatus.IN_PROGRESS:
                event_bus.publish(Events.INCIDENT_ESCALATED, {"incident_id": incident_id})
            
        return updated_incident

    def delete_incident(self, incident_id: str) -> bool:
        incident = self.repo.get_by_id(incident_id)
        if not incident:
            return False
        success = self.repo.delete_incident(incident_id)
        if success:
            # Tell the system the incident is gone so debouncing can clear
            event_bus.publish(Events.INCIDENT_CLOSED, {"incident_id": incident_id, "lab_id": incident.lab_id, "alert_id": incident.alert_id})
        return success

    def delete_history(self, before: datetime) -> int:
        count = self.repo.delete_history(before)
        event_bus.publish(Events.INCIDENTS_CLEARED, {})
        return count

    # ── Notes ──
    def add_note(self, incident_id: str, user_id: str, data: IncidentNoteCreate) -> IncidentNoteModel:
        # Verify incident exists
        self.get_incident(incident_id)
        return self.repo.add_note(incident_id, user_id, data)

    def get_notes(self, incident_id: str) -> List[IncidentNoteModel]:
        # Verify incident exists
        self.get_incident(incident_id)
        return self.repo.get_notes(incident_id)


# ═══════════════════════════════════════════════════════════════
# Internal Event Handlers
# ═══════════════════════════════════════════════════════════════

def _handle_critical_alert(payload: Dict[str, Any]):
    """
    Listens for Events.ALERT_CREATED.
    If the alert is CRITICAL and has an alert_id (meaning it was saved to DB),
    we automatically convert it to an incident.
    """
    try:
        # We only care about alerts that have already been processed and saved by the Alerts module
        if "alert_id" not in payload:
            return
            
        if payload.get("severity") != "critical":
            return

        from core.database import get_sqlite_session, get_firestore_client
        from core.config import settings
        from modules.incidents.repository import get_incident_repository

        db = None
        session_generator = None
        if settings.is_sqlite:
            session_generator = get_sqlite_session()
            db = next(session_generator)
        else:
            db = get_firestore_client()

        try:
            repo = get_incident_repository(db)
            service = IncidentService(repo)
            
            incident_data = IncidentCreate(
                lab_id=payload["lab_id"],
                title=f"Critical Alert Escalation: {payload.get('alert_id')}",
                description="Automatically generated from a critical sensor alert.",
                severity=IncidentSeverity.CRITICAL,
                alert_id=payload["alert_id"]
            )
            service.create_incident(incident_data)
            logger.warning("Critical alert %s auto-escalated to an Incident.", payload['alert_id'])
        finally:
            if session_generator:
                try:
                    next(session_generator)
                except StopIteration:
                    pass
    except Exception:
        logger.exception("Failed to auto-create incident from critical alert")

# Subscribe to the event bus
# event_bus.subscribe(Events.ALERT_CREATED, _handle_critical_alert)
