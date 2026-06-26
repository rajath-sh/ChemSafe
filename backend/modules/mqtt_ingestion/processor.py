import logging
from typing import Dict, Any

from core.enums import SensorType, AlertType, AlertSeverity, SensorStatus
from core.event_bus import event_bus, Events
from modules.mqtt_ingestion.repository import IngestionRepository

logger = logging.getLogger(__name__)

# In-memory debounce cache to prevent alert flooding during a continuous event
# Maps (lab_id, sensor_type) -> AlertSeverity
_active_hazards = {}

class SensorProcessor:
    """
    Analyzes incoming sensor data.
    Checks against thresholds and triggers alerts via the EventBus.
    """
    def __init__(self, repo: IngestionRepository):
        self.repo = repo

    def process_payload(self, lab_id: str, payload: Dict[str, Any]):
        """Main processing pipeline for a sensor payload."""
        
        # 0. Check for Keypad Intrusion Alert FIRST (before save_reading)
        if payload.get("keypad_alert") is True:
            message = payload.get("message", "Unauthorized Keypad Access: 3 wrong passwords entered!")
            
            # Use Events.ALERT_CREATED with AlertCreate-compatible payload
            alert_data = {
                "lab_id": lab_id,
                "alert_type": AlertType.SECURITY,
                "severity": AlertSeverity.CRITICAL,
                "message": message,
            }
            logger.warning("Keypad Intrusion Alert: %s", message)
            event_bus.publish(Events.ALERT_CREATED, alert_data)
            return  # This is NOT a sensor reading, don't try to save it
        
        # 1. Save reading
        from core.utils import utc_now
        from core.conversions import mq135_to_ppm, ldr_to_lux

        gas_val = payload.get("gas")
        if gas_val is not None:
            gas_val = mq135_to_ppm(float(gas_val))

        light_val = payload.get("light")
        if light_val is not None:
            light_val = ldr_to_lux(float(light_val))

        reading_data = {
            "lab_id": lab_id,
            "temperature": payload.get("temperature"),
            "humidity": payload.get("humidity"),
            "gas": gas_val,
            "light": light_val,
            "vibration": payload.get("vibration"),
            "timestamp": payload.get("timestamp") or utc_now()
        }
        self.repo.save_reading(reading_data)

        # 2. Get thresholds for this lab
        thresholds = self.repo.get_thresholds(lab_id)
        threshold_map = {t.sensor_type: t for t in thresholds}

        # 3. Analyze each sensor type
        self._analyze_sensor(lab_id, SensorType.TEMPERATURE, payload.get("temperature"), threshold_map.get(SensorType.TEMPERATURE))
        self._analyze_sensor(lab_id, SensorType.HUMIDITY, payload.get("humidity"), threshold_map.get(SensorType.HUMIDITY))
        self._analyze_sensor(lab_id, SensorType.GAS, gas_val, threshold_map.get(SensorType.GAS))
        self._analyze_sensor(lab_id, SensorType.LIGHT, light_val, threshold_map.get(SensorType.LIGHT))
        self._analyze_sensor(lab_id, SensorType.VIBRATION, payload.get("vibration"), threshold_map.get(SensorType.VIBRATION))

        # 5. (Future) Anomaly Detection Engine hook can go here

    def _analyze_sensor(self, lab_id: str, sensor_type: SensorType, value: float | None, threshold):
        if value is None:
            return

        # Update sensor last_reading status
        self.repo.update_sensor_status(lab_id, sensor_type.value, value)

        if not threshold:
            # Fallback to default thresholds if not defined in DB
            class DefaultThreshold:
                def __init__(self, s_type):
                    self.critical_value = (
                        5.0 if s_type == SensorType.VIBRATION else
                        45.0 if s_type == SensorType.TEMPERATURE else
                        85.0 if s_type == SensorType.HUMIDITY else
                        10.0 if s_type == SensorType.GAS else
                        1000.0
                    )
                    self.warning_value = self.critical_value * 0.8
                    self.min_value = None
                    self.max_value = None
            threshold = DefaultThreshold(sensor_type)
        # If threshold exists in DB, we do NOTHING! We respect the user's manual Warning and Critical values perfectly.

        # Fetch the current manual status of this sensor
        sensor_status = self.repo.get_sensor_status(lab_id, sensor_type.value)
        if sensor_status and sensor_status != SensorStatus.ONLINE.value:
            # If sensor is manually marked offline/error, ignore readings and clear active hazard
            if (lab_id, sensor_type) in _active_hazards:
                del _active_hazards[(lab_id, sensor_type)]
            return

        # Threshold logic
        severity = None
        message = ""

        # Check Critical
        if value >= threshold.critical_value:
            severity = AlertSeverity.CRITICAL
            if sensor_type == SensorType.VIBRATION:
                message = f"Intruder Alert: High vibration detected in {lab_id} ({value} Hz). Possible unauthorized entry!"
            else:
                message = f"{sensor_type.value.title()} reached critical level: {value} (Limit: {threshold.critical_value})"
        # Check Warning
        elif value >= threshold.warning_value:
            severity = AlertSeverity.WARNING
            if sensor_type == SensorType.VIBRATION:
                message = f"Intrusion Warning: Unusual vibration detected in {lab_id} ({value} Hz)."
            else:
                message = f"{sensor_type.value.title()} reached warning level: {value} (Limit: {threshold.warning_value})"
        # Check ranges (like humidity)
        elif threshold.min_value is not None and value < threshold.min_value:
            severity = AlertSeverity.INFO
            message = f"{sensor_type.value.title()} dropped below minimum: {value} (Min: {threshold.min_value})"
        elif threshold.max_value is not None and value > threshold.max_value:
            severity = AlertSeverity.INFO
            if sensor_type == SensorType.VIBRATION:
                message = f"Intrusion Warning: Vibration exceeded threshold in {lab_id} ({value} Hz)."
            else:
                message = f"{sensor_type.value.title()} exceeded maximum: {value} (Max: {threshold.max_value})"

        if severity:
            # Check if this is a new event or an escalation in severity
            current_active = _active_hazards.get((lab_id, sensor_type))
            if current_active != severity:
                # New event or severity changed, trigger an alert!
                _active_hazards[(lab_id, sensor_type)] = severity
                self._trigger_alert(lab_id, sensor_type, severity, value, threshold.critical_value, message)
        else:
            # Sensor reading is normal, clear the active hazard state if any exists
            if (lab_id, sensor_type) in _active_hazards:
                del _active_hazards[(lab_id, sensor_type)]

    def _trigger_alert(self, lab_id: str, sensor_type: SensorType, severity: AlertSeverity, value: float, threshold_val: float, message: str):
        """Publishes an alert event. The Alerts module will listen and save it."""
        alert_data = {
            "lab_id": lab_id,
            "alert_type": AlertType(sensor_type.value),
            "severity": severity,
            "message": message,
            "sensor_value": value,
            "threshold_value": threshold_val
        }
        logger.warning("Hazard Detected: %s", message)
        event_bus.publish(Events.ALERT_CREATED, alert_data)


# ═══════════════════════════════════════════════════════════════
# Internal Event Handlers
# ═══════════════════════════════════════════════════════════════

def _handle_alert_closed_event(payload: Dict[str, Any]):
    """
    Listens for Events.ALERT_CLOSED from the alerts module.
    Clears the debouncing cache so a new alert can be generated
    if the sensor reading is still in the hazard zone.
    """
    lab_id = payload.get("lab_id")
    alert_type_str = payload.get("alert_type")
    
    if lab_id and alert_type_str:
        try:
            s_type = SensorType(alert_type_str)
            if (lab_id, s_type) in _active_hazards:
                del _active_hazards[(lab_id, s_type)]
                logger.info(f"Cleared hazard debounce cache for {lab_id} {s_type.value} because alert was closed.")
        except ValueError:
            pass

def _handle_alerts_cleared_event(payload: Dict[str, Any]):
    """
    Listens for Events.ALERTS_CLEARED.
    Clears the entire debouncing cache since all alerts were deleted.
    """
    _active_hazards.clear()
    logger.info("Cleared entire hazard debounce cache because all alerts were cleared.")

def _handle_incident_done_event(payload: Dict[str, Any]):
    """
    Listens for Events.INCIDENT_RESOLVED or Events.INCIDENT_CLOSED.
    Clears the debouncing cache for the specific sensor (if alert_id exists),
    otherwise clears the entire lab so new alerts can generate.
    """
    lab_id = payload.get("lab_id")
    alert_id = payload.get("alert_id")
    
    if not lab_id:
        return
        
    s_type_to_clear = None
    if alert_id:
        try:
            from core.database import get_sqlite_session, get_firestore_client
            from core.config import settings
            from modules.alerts.repository import get_alert_repository
            from core.enums import SensorType
            
            db = None
            session_generator = None
            if settings.is_sqlite:
                session_generator = get_sqlite_session()
                db = next(session_generator)
            else:
                db = get_firestore_client()
                
            try:
                repo = get_alert_repository(db)
                alert = repo.get_by_id(alert_id)
                if alert:
                    s_type_to_clear = SensorType(alert.alert_type)
            finally:
                if session_generator:
                    try:
                        next(session_generator)
                    except StopIteration:
                        pass
        except Exception as e:
            logger.error("Failed to fetch alert_type for incident clear cache: %s", e)
            
    if s_type_to_clear:
        # Clear only the specific sensor
        if (lab_id, s_type_to_clear) in _active_hazards:
            del _active_hazards[(lab_id, s_type_to_clear)]
            logger.info(f"Cleared hazard debounce cache for lab {lab_id} sensor {s_type_to_clear.value} because incident was resolved/closed.")
    else:
        # Fallback: clear the whole lab
        keys_to_delete = [k for k in _active_hazards.keys() if k[0] == lab_id]
        for k in keys_to_delete:
            del _active_hazards[k]
        if keys_to_delete:
            logger.info(f"Cleared ENTIRE hazard debounce cache for lab {lab_id} because an incident was resolved/closed (no specific sensor).")

event_bus.subscribe(Events.ALERT_CLOSED, _handle_alert_closed_event)
event_bus.subscribe(Events.ALERTS_CLEARED, _handle_alerts_cleared_event)
event_bus.subscribe(Events.INCIDENT_RESOLVED, _handle_incident_done_event)
event_bus.subscribe(Events.INCIDENT_CLOSED, _handle_incident_done_event)
event_bus.subscribe(Events.INCIDENTS_CLEARED, _handle_alerts_cleared_event) # Can reuse the same "clear all" handler
