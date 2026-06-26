"""
ChemSafe IoT — In-Process Event Bus

Decouples modules by providing publish/subscribe communication.
Modules publish events to the bus; other modules subscribe handlers.
No module ever imports from another module — only from core.

Usage:
    # In a module's __init__.py or service.py:
    from core.event_bus import event_bus

    # Subscribe
    event_bus.subscribe("alert.created", handle_new_alert)

    # Publish
    event_bus.publish("alert.created", {"alert_id": "ALR-xxx", ...})
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Type alias for event handler functions
EventHandler = Callable[[dict[str, Any]], None]


class EventBus:
    """
    Simple synchronous in-process event bus.

    Events are string names (e.g. "alert.created").
    Handlers receive a dict payload.
    """

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register a handler for an event."""
        self._handlers[event_name].append(handler)
        logger.debug("EventBus: subscribed %s to '%s'", handler.__name__, event_name)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Remove a handler from an event."""
        if event_name in self._handlers:
            self._handlers[event_name] = [
                h for h in self._handlers[event_name] if h is not handler
            ]

    def publish(self, event_name: str, data: dict[str, Any] | None = None) -> None:
        """
        Publish an event to all subscribed handlers.
        Handlers are called synchronously in registration order.
        Errors in one handler do not block others.
        """
        data = data or {}
        handlers = self._handlers.get(event_name, [])
        if not handlers:
            logger.debug("EventBus: no handlers for '%s'", event_name)
            return

        logger.info("EventBus: publishing '%s' to %d handler(s)", event_name, len(handlers))
        for handler in handlers:
            try:
                handler(data)
            except Exception:
                logger.exception(
                    "EventBus: error in handler '%s' for event '%s'",
                    handler.__name__,
                    event_name,
                )

    def clear(self) -> None:
        """Remove all subscriptions (useful for testing)."""
        self._handlers.clear()

    @property
    def registered_events(self) -> list[str]:
        """List all events that have at least one handler."""
        return [k for k, v in self._handlers.items() if v]


# ── Singleton instance ────────────────────────────────────────
event_bus = EventBus()


# ═══════════════════════════════════════════════════════════════
# Standard Event Names (constants for consistency)
# ═══════════════════════════════════════════════════════════════

class Events:
    """Canonical event name constants — use these instead of raw strings."""

    # Alerts
    ALERT_CREATED = "alert.created"
    ALERT_ACKNOWLEDGED = "alert.acknowledged"
    ALERT_CLOSED = "alert.closed"
    ALERTS_CLEARED = "alerts.cleared"

    # Incidents
    INCIDENT_CREATED = "incident.created"
    INCIDENT_ASSIGNED = "incident.assigned"
    INCIDENT_UNASSIGNED = "incident.unassigned"
    INCIDENT_ESCALATED = "incident.escalated"
    INCIDENT_RESOLVED = "incident.resolved"
    INCIDENT_CLOSED = "incident.closed"
    INCIDENTS_CLEARED = "incidents.cleared"

    # Assignments
    ASSIGNMENT_CREATED = "assignment.created"
    ASSIGNMENT_ACCEPTED = "assignment.accepted"
    ASSIGNMENT_COMPLETED = "assignment.completed"

    # Sensors
    SENSOR_DATA_RECEIVED = "sensor.data_received"
    SENSOR_OFFLINE = "sensor.offline"
    SENSOR_ONLINE = "sensor.online"

    # Inventory
    CHEMICAL_ADDED = "chemical.added"
    CHEMICAL_DELETED = "chemical.deleted"
    CHEMICAL_LOW_STOCK = "chemical.low_stock"
    CHEMICAL_EXPIRING = "chemical.expiring"
    CHEMICAL_EXPIRED = "chemical.expired"
    INVENTORY_UPDATED = "inventory.updated"

    # Anomaly
    ANOMALY_DETECTED = "anomaly.detected"

    # Settings
    THRESHOLD_UPDATED = "threshold.updated"

    # Auth
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
