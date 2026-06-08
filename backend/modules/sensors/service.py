from typing import List, Optional
from datetime import datetime

from modules.sensors.repository import SensorRepository
from modules.sensors.schemas import SensorCreate, SensorUpdate, ThresholdCreate, LabCreate
from core.models_sql import SensorModel, ThresholdModel, LaboratoryModel, SensorReadingModel
from core.exceptions import NotFoundException
from core.event_bus import event_bus, Events

class SensorService:
    def __init__(self, repo: SensorRepository):
        self.repo = repo

    def create_lab(self, data: LabCreate) -> LaboratoryModel:
        return self.repo.create_lab(data)

    def list_labs(self) -> List[LaboratoryModel]:
        return self.repo.list_labs()

    def delete_lab(self, lab_id: str) -> bool:
        return self.repo.delete_lab(lab_id)

    def create_sensor(self, data: SensorCreate) -> SensorModel:
        return self.repo.create_sensor(data)

    def get_sensor(self, sensor_id: str) -> SensorModel:
        sensor = self.repo.get_sensor(sensor_id)
        if not sensor:
            raise NotFoundException("Sensor", sensor_id)
        return sensor

    def list_sensors(self, lab_id: Optional[str] = None) -> List[SensorModel]:
        return self.repo.list_sensors(lab_id)

    def get_readings(self, lab_id: str, limit: int = 50) -> List[SensorReadingModel]:
        return self.repo.get_readings(lab_id, limit)

    def update_sensor(self, sensor_id: str, data: SensorUpdate) -> SensorModel:
        sensor = self.get_sensor(sensor_id)
        updated = self.repo.update_sensor(sensor, data)
        
        # If status changed, publish command to ESP32
        if data.status:
            from core.mqtt_client import mqtt_client
            topic = f"lab/{sensor.lab_id}/command"
            payload = {
                "target": sensor.sensor_type.value,
                "command": data.status.value
            }
            mqtt_client.publish(topic, payload)
            
        return updated

    def toggle_global_vibration(self, status: str) -> dict:
        """Toggles all vibration sensors to the given status and broadcasts MQTT commands."""
        from core.enums import SensorStatus
        from core.mqtt_client import mqtt_client
        
        target_status = SensorStatus(status)
        all_sensors = self.repo.list_sensors()
        vibration_sensors = [s for s in all_sensors if s.sensor_type.value == "vibration"]
        
        updated_count = 0
        for sensor in vibration_sensors:
            if sensor.status != target_status:
                self.repo.update_sensor(sensor, SensorUpdate(status=target_status))
                updated_count += 1
                
        # To be safe, we broadcast to all labs that have a vibration sensor
        labs_affected = set(s.lab_id for s in vibration_sensors)
        for lab_id in labs_affected:
            topic = f"lab/{lab_id}/command"
            payload = {
                "target": "vibration",
                "command": target_status.value
            }
            mqtt_client.publish(topic, payload)
            
        return {"updated_count": updated_count, "target_status": target_status.value}

    def set_threshold(self, data: ThresholdCreate) -> ThresholdModel:
        # Publish event so mqtt engine knows threshold updated
        threshold = self.repo.set_threshold(data)
        event_bus.publish(Events.THRESHOLD_UPDATED, {"lab_id": data.lab_id, "sensor_type": data.sensor_type})
        return threshold

    def get_thresholds(self, lab_id: str) -> List[ThresholdModel]:
        return self.repo.get_thresholds(lab_id)

    def delete_history(self, before: datetime) -> int:
        return self.repo.delete_history(before)
