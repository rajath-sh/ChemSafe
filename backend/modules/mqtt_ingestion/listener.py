import logging
from fastapi import APIRouter, Depends
from typing import Dict, Any

from core.mqtt_client import mqtt_client
from core.dependencies import get_db, require_role
from core.schemas import CurrentUser, MessageResponse
from core.enums import Role
from modules.mqtt_ingestion.repository import get_ingestion_repository
from modules.mqtt_ingestion.processor import SensorProcessor
from modules.mqtt_ingestion.schemas import SimulatedPayload

logger = logging.getLogger(__name__)

router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# MQTT Listener (Background processing)
# ═══════════════════════════════════════════════════════════════

def handle_mqtt_message(topic: str, payload: Dict[str, Any]):
    """
    Callback fired when MQTTClient receives a message on lab/+/sensorData.
    topic format: lab/{labId}/sensorData
    """
    try:
        parts = topic.split('/')
        if len(parts) >= 3 and parts[0] == "lab" and parts[2] == "sensorData":
            lab_id = parts[1]
            
            # Since this runs in a background thread from paho-mqtt, 
            # we need to get our own DB connection context
            from core.database import get_sqlite_session, get_firestore_client
            from core.config import settings
            
            db = None
            session_generator = None
            if settings.is_sqlite:
                session_generator = get_sqlite_session()
                db = next(session_generator)
            else:
                db = get_firestore_client()

            try:
                repo = get_ingestion_repository(db)
                processor = SensorProcessor(repo)
                processor.process_payload(lab_id, payload)
            finally:
                if session_generator:
                    try:
                        next(session_generator)
                    except StopIteration:
                        pass
    except Exception:
        logger.exception("Failed to process MQTT message from topic %s", topic)

# Subscribe to the topic when this module is loaded
# (This assumes mqtt_client.connect() happens in main.py lifespan)
mqtt_client.subscribe("lab/+/sensorData", handle_mqtt_message)


# ═══════════════════════════════════════════════════════════════
# HTTP API Endpoints (For testing without MQTT hardware)
# ═══════════════════════════════════════════════════════════════

@router.post("/simulate", response_model=MessageResponse)
def simulate_sensor_payload(
    payload: SimulatedPayload,
    db = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """
    Simulates an ESP32 sending a payload. 
    Processes it immediately through the threshold engine.
    """
    repo = get_ingestion_repository(db)
    processor = SensorProcessor(repo)
    
    data = payload.model_dump(exclude={"lab_id"}, exclude_unset=True)
    processor.process_payload(payload.lab_id, data)
    
    return MessageResponse(message="Simulated payload processed successfully")
