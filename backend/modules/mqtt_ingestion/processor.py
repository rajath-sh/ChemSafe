import logging
from typing import Dict, Any

from core.enums import SensorType, AlertType, AlertSeverity
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
        # 1. Save reading
        from core.utils import utc_now
        reading_data = {
            "lab_id": lab_id,
            "temperature": payload.get("temperature"),
            "humidity": payload.get("humidity"),
            "gas": payload.get("gas"),
            "light": payload.get("light"),
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
        self._analyze_sensor(lab_id, SensorType.GAS, payload.get("gas"), threshold_map.get(SensorType.GAS))
        self._analyze_sensor(lab_id, SensorType.LIGHT, payload.get("light"), threshold_map.get(SensorType.LIGHT))
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
                    # Dynamic warning based purely on critical (80%)
                    self.warning_value = self.critical_value * 0.8
                    self.min_value = None
                    self.max_value = None
            threshold = DefaultThreshold(sensor_type)
        else:
            # Enforce dynamic relative scaling! Warning is always 80% of whatever Critical is set to by Admin.
            threshold.warning_value = threshold.critical_value * 0.8

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
            severity = AlertSeverity.HIGH
            if sensor_type == SensorType.VIBRATION:
                message = f"Intrusion Warning: Unusual vibration detected in {lab_id} ({value} Hz)."
            else:
                message = f"{sensor_type.value.title()} reached warning level: {value} (Limit: {threshold.warning_value})"
        # Check ranges (like humidity)
        elif threshold.min_value is not None and value < threshold.min_value:
            severity = AlertSeverity.MEDIUM
            message = f"{sensor_type.value.title()} dropped below minimum: {value} (Min: {threshold.min_value})"
        elif threshold.max_value is not None and value > threshold.max_value:
            severity = AlertSeverity.MEDIUM
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
