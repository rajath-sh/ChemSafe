import logging
from typing import List, Optional, Any, Dict
from datetime import datetime

from modules.alerts.repository import AlertRepository
from modules.alerts.schemas import AlertCreate, AlertUpdate
from core.models_sql import AlertModel
from core.exceptions import NotFoundException
from core.enums import AlertStatus, AlertSeverity
from core.event_bus import event_bus, Events

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self, repo: AlertRepository):
        self.repo = repo

    def create_alert(self, data: AlertCreate) -> AlertModel:
        alert = self.repo.create(data)
        
        # If it's a critical alert, fire an event so the incidents module can catch it
        if alert.severity == AlertSeverity.CRITICAL:
            event_bus.publish(Events.ALERT_CREATED, {"alert_id": alert.alert_id, "lab_id": alert.lab_id, "severity": "critical"})
            
        return alert

    def get_alert(self, alert_id: str) -> AlertModel:
        alert = self.repo.get_by_id(alert_id)
        if not alert:
            raise NotFoundException("Alert", alert_id)
        return alert

    def list_alerts(self, lab_id: Optional[str] = None, status: Optional[str] = None) -> List[AlertModel]:
        return self.repo.list_alerts(lab_id, status)

    def list_anomalies(self, lab_id: Optional[str] = None) -> List:
        return self.repo.list_anomalies(lab_id)

    def update_status(self, alert_id: str, status: AlertStatus) -> AlertModel:
        alert = self.get_alert(alert_id)
        data = AlertUpdate(status=status)
        alert = self.repo.update(alert, data)
        
        # Publish events based on new status
        if status == AlertStatus.ACKNOWLEDGED:
            event_bus.publish(Events.ALERT_ACKNOWLEDGED, {"alert_id": alert.alert_id})
        elif status == AlertStatus.CLOSED:
            event_bus.publish(Events.ALERT_CLOSED, {
                "alert_id": alert.alert_id,
                "lab_id": alert.lab_id,
                "alert_type": alert.alert_type
            })
            
        return alert

    def delete_history(self, before: datetime) -> int:
        count = self.repo.delete_history(before)
        event_bus.publish(Events.ALERTS_CLEARED, {})
        return count


# ═══════════════════════════════════════════════════════════════
# Internal Event Handlers
# ═══════════════════════════════════════════════════════════════

def _handle_alert_created_event(payload: Dict[str, Any]):
    """
    Listens for Events.ALERT_CREATED published by mqtt_ingestion.
    Saves the new alert to the database.
    """
    try:
        from core.database import get_sqlite_session, get_firestore_client
        from core.config import settings
        from modules.alerts.repository import get_alert_repository

        # This payload came from mqtt_ingestion (raw data dict)
        # Note: If it already has an alert_id, it means it was published by create_alert() above.
        # We only want to process raw hazards from the processor that DON'T have an alert_id yet.
        if "alert_id" in payload:
            return

        db = None
        session_generator = None
        if settings.is_sqlite:
            session_generator = get_sqlite_session()
            db = next(session_generator)
        else:
            db = get_firestore_client()

        try:
            repo = get_alert_repository(db)
            service = AlertService(repo)
            
            alert_data = AlertCreate(**payload)
            service.create_alert(alert_data)
            logger.info("Automatically created alert from MQTT ingestion hazard")
        finally:
            if session_generator:
                try:
                    next(session_generator)
                except StopIteration:
                    pass
    except Exception:
        logger.exception("Failed to handle ALERT_CREATED event in Alerts module")

# Subscribe to the event bus
event_bus.subscribe(Events.ALERT_CREATED, _handle_alert_created_event)
