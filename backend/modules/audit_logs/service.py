import logging
from typing import List, Optional, Dict, Any

from modules.audit_logs.repository import AuditLogRepository
from core.models_sql import AuditLogModel
from core.event_bus import event_bus, Events

logger = logging.getLogger(__name__)

class AuditLogService:
    def __init__(self, repo: AuditLogRepository):
        self.repo = repo

    def create_log(self, user_id: str, action: str, entity_type: str, entity_id: str, details: Optional[str] = None) -> AuditLogModel:
        return self.repo.create(user_id, action, entity_type, entity_id, details)

    def list_logs(self, entity_type: Optional[str] = None, user_id: Optional[str] = None) -> List[AuditLogModel]:
        return self.repo.list_logs(entity_type, user_id)


# ═══════════════════════════════════════════════════════════════
# Internal Event Handlers
# ═══════════════════════════════════════════════════════════════

def _handle_inventory_updated(payload: Dict[str, Any]):
    """
    Listens for Events.INVENTORY_UPDATED.
    Creates an immutable audit log entry.
    """
    try:
        chemical_id = payload.get("chemical_id")
        action = payload.get("action")  # created, updated, deleted
        user_id = payload.get("user_id")
        
        if not chemical_id or not action or not user_id:
            return

        from core.database import get_sqlite_session, get_firestore_client
        from core.config import settings
        from modules.audit_logs.repository import get_audit_log_repository

        db = None
        session_generator = None
        if settings.is_sqlite:
            session_generator = get_sqlite_session()
            db = next(session_generator)
        else:
            db = get_firestore_client()

        try:
            repo = get_audit_log_repository(db)
            service = AuditLogService(repo)
            
            details = f"Chemical {chemical_id} was {action} by user {user_id}."
            service.create_log(
                user_id=user_id,
                action=f"chemical_{action}",
                entity_type="chemical",
                entity_id=chemical_id,
                details=details
            )
            logger.info("Audit log created for chemical %s", chemical_id)
        finally:
            if session_generator:
                try:
                    next(session_generator)
                except StopIteration:
                    pass
    except Exception:
        logger.exception("Failed to auto-generate audit log for inventory update")


# Subscribe to the event bus
event_bus.subscribe(Events.INVENTORY_UPDATED, _handle_inventory_updated)
