import logging
from typing import List, Optional, Dict, Any

from modules.staff.repository import StaffRepository
from modules.staff.schemas import StaffUpdate
from core.models_sql import UserModel
from core.exceptions import NotFoundException
from core.enums import StaffAvailability
from core.event_bus import event_bus, Events

logger = logging.getLogger(__name__)

class StaffService:
    def __init__(self, repo: StaffRepository):
        self.repo = repo

    def list_staff(self, department: Optional[str] = None, availability: Optional[str] = None) -> List[UserModel]:
        return self.repo.list_staff(department, availability)

    def get_staff(self, user_id: str) -> UserModel:
        staff = self.repo.get_staff(user_id)
        if not staff:
            raise NotFoundException("Staff Member", user_id)
        return staff

    def update_staff(self, user_id: str, data: StaffUpdate) -> UserModel:
        staff = self.get_staff(user_id)
        return self.repo.update_staff(staff, data)

    def set_availability(self, user_id: str, availability: StaffAvailability) -> UserModel:
        staff = self.get_staff(user_id)
        data = StaffUpdate(availability=availability)
        return self.repo.update_staff(staff, data)

    def get_incident_staff_id(self, incident_id: str) -> Optional[str]:
        return self.repo.get_incident_staff_id(incident_id)


# ═══════════════════════════════════════════════════════════════
# Internal Event Handlers
# ═══════════════════════════════════════════════════════════════

def _handle_incident_assignment(payload: Dict[str, Any]):
    """
    Listens for Events.INCIDENT_ASSIGNED.
    Automatically marks the staff member as BUSY.
    """
    try:
        staff_id = payload.get("staff_id")
        if not staff_id:
            return

        from core.database import get_sqlite_session, get_firestore_client
        from core.config import settings
        from modules.staff.repository import get_staff_repository

        db = None
        session_generator = None
        if settings.is_sqlite:
            session_generator = get_sqlite_session()
            db = next(session_generator)
        else:
            db = get_firestore_client()

        try:
            repo = get_staff_repository(db)
            service = StaffService(repo)
            
            service.set_availability(staff_id, StaffAvailability.BUSY)
            logger.info("Staff %s marked BUSY due to incident assignment", staff_id)
        finally:
            if session_generator:
                try:
                    next(session_generator)
                except StopIteration:
                    pass
    except Exception:
        logger.exception("Failed to auto-update staff availability on assignment")


def _handle_incident_resolved(payload: Dict[str, Any]):
    """
    Listens for Events.INCIDENT_RESOLVED or Events.INCIDENT_CLOSED.
    Automatically marks the assigned staff member as AVAILABLE.
    """
    try:
        incident_id = payload.get("incident_id")
        if not incident_id:
            return

        from core.database import get_sqlite_session, get_firestore_client
        from core.config import settings
        from modules.staff.repository import get_staff_repository

        db = None
        session_generator = None
        if settings.is_sqlite:
            session_generator = get_sqlite_session()
            db = next(session_generator)
        else:
            db = get_firestore_client()

        try:
            repo = get_staff_repository(db)
            service = StaffService(repo)
            
            # Find out who was assigned
            staff_id = service.get_incident_staff_id(incident_id)
            if staff_id:
                # Need to check if they are BUSY before marking them available (they might be OFF_DUTY)
                staff = service.get_staff(staff_id)
                # Check string value to avoid Enum mismatch bugs
                if hasattr(staff.availability, 'value'):
                    is_busy = staff.availability.value == StaffAvailability.BUSY.value
                else:
                    is_busy = str(staff.availability).lower() == 'busy'
                    
                if is_busy:
                    service.set_availability(staff_id, StaffAvailability.AVAILABLE)
                    logger.info("Staff %s marked AVAILABLE after incident resolution", staff_id)
        finally:
            if session_generator:
                try:
                    next(session_generator)
                except StopIteration:
                    pass
    except Exception:
        logger.exception("Failed to auto-update staff availability on resolution")


def _handle_incident_unassigned(payload: Dict[str, Any]):
    """
    Listens for Events.INCIDENT_UNASSIGNED.
    Automatically marks the unassigned staff member as AVAILABLE.
    """
    try:
        staff_id = payload.get("staff_id")
        if not staff_id:
            return

        from core.database import get_sqlite_session, get_firestore_client
        from core.config import settings
        from modules.staff.repository import get_staff_repository

        db = None
        session_generator = None
        if settings.is_sqlite:
            session_generator = get_sqlite_session()
            db = next(session_generator)
        else:
            db = get_firestore_client()

        try:
            repo = get_staff_repository(db)
            service = StaffService(repo)
            
            staff = service.get_staff(staff_id)
            if hasattr(staff.availability, 'value'):
                is_busy = staff.availability.value == StaffAvailability.BUSY.value
            else:
                is_busy = str(staff.availability).lower() == 'busy'
                
            if is_busy:
                service.set_availability(staff_id, StaffAvailability.AVAILABLE)
                logger.info("Staff %s marked AVAILABLE after being unassigned", staff_id)
        finally:
            if session_generator:
                try:
                    next(session_generator)
                except StopIteration:
                    pass
    except Exception:
        logger.exception("Failed to auto-update staff availability on unassignment")


# Subscribe to the event bus
event_bus.subscribe(Events.INCIDENT_ASSIGNED, _handle_incident_assignment)
event_bus.subscribe(Events.INCIDENT_UNASSIGNED, _handle_incident_unassigned)
event_bus.subscribe(Events.INCIDENT_RESOLVED, _handle_incident_resolved)
event_bus.subscribe(Events.INCIDENT_CLOSED, _handle_incident_resolved)
