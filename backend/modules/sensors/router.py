from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime

from core.dependencies import get_db, require_role
from core.enums import Role
from core.schemas import CurrentUser, DeleteHistoryResponse
from modules.sensors.schemas import (
    SensorCreate, SensorUpdate, SensorOut, 
    ThresholdCreate, ThresholdOut, LabCreate, LabOut
)
from modules.sensors.repository import get_sensor_repository
from modules.sensors.service import SensorService

router = APIRouter()

def get_sensor_service(db=Depends(get_db)) -> SensorService:
    repo = get_sensor_repository(db)
    return SensorService(repo)

# ── Laboratory Helpers (for testing) ──
@router.post("/labs", response_model=LabOut)
def create_lab(
    data: LabCreate, 
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    return service.create_lab(data)

@router.get("/labs", response_model=List[LabOut])
def list_labs(
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.list_labs()

@router.delete("/labs/{lab_id}")
def delete_lab(
    lab_id: str,
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    success = service.delete_lab(lab_id)
    return {"message": "Lab deleted" if success else "Lab not found or deletion failed"}

# ── Sensors ──
@router.post("", response_model=SensorOut)
def create_sensor(
    data: SensorCreate, 
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    return service.create_sensor(data)

@router.get("", response_model=List[SensorOut])
def list_sensors(
    lab_id: Optional[str] = None,
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.list_sensors(lab_id)

@router.patch("/{sensor_id}", response_model=SensorOut)
def update_sensor(
    sensor_id: str,
    data: SensorUpdate,
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    return service.update_sensor(sensor_id, data)

@router.get("/readings/{lab_id}")
def get_sensor_readings(
    lab_id: str,
    limit: int = Query(50, description="Max number of recent readings to fetch"),
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    # Returns List[SensorReadingModel]
    return service.get_readings(lab_id, limit)

from fastapi.responses import StreamingResponse
import io
import csv

@router.get("/readings/{lab_id}/export")
def export_sensor_readings(
    lab_id: str,
    days: int = Query(1, description="Number of days to export"),
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    # Assuming 1 reading every 2 seconds: 30 per min -> 1800 per hr -> 43200 per day
    limit = days * 43200
    readings = service.get_readings(lab_id, limit)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Temperature (°C)", "Humidity (%)", "Gas (PPM)", "Light (Lux)", "Vibration (g)"])
    
    for r in readings:
        writer.writerow([r.timestamp, r.temperature, r.humidity, r.gas, r.light, r.vibration])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=node_{lab_id}_data.csv"}
    )


@router.get("/{sensor_id}", response_model=SensorOut)
def get_sensor(
    sensor_id: str,
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.get_sensor(sensor_id)

@router.post("/vibration/global")
def toggle_global_vibration(
    status: str = Query(..., description="Target status: 'online' or 'offline'"),
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    return service.toggle_global_vibration(status)

from pydantic import BaseModel
class AlarmCommand(BaseModel):
    status: str

@router.post("/nodes/{lab_id}/remote_alarm")
def toggle_remote_alarm(
    lab_id: str,
    data: AlarmCommand,
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    from core.mqtt_client import mqtt_client
    topic = f"lab/{lab_id}/command"
    payload = {"command": "alarm", "state": data.status}
    mqtt_client.publish(topic, payload)
    return {"message": f"Sent {data.status} to {lab_id}"}

@router.patch("/{sensor_id}", response_model=SensorOut)
def update_sensor(
    sensor_id: str,
    data: SensorUpdate,
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    return service.update_sensor(sensor_id, data)

# ── Thresholds ──
@router.post("/thresholds", response_model=ThresholdOut)
def set_threshold(
    data: ThresholdCreate,
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    return service.set_threshold(data)

@router.get("/thresholds/{lab_id}", response_model=List[ThresholdOut])
def get_thresholds(
    lab_id: str,
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.get_thresholds(lab_id)

# ── History Deletion ──
@router.delete("/history", response_model=DeleteHistoryResponse)
def delete_sensor_history(
    before: datetime = Query(..., description="Delete readings before this ISO timestamp"),
    service: SensorService = Depends(get_sensor_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    count = service.delete_history(before)
    return DeleteHistoryResponse(message="History deleted", deleted_count=count)
