import logging

from modules.dashboard.repository import DashboardRepository
from modules.dashboard.schemas import (
    DashboardSnapshot, 
    SensorSummary, 
    ActiveAlertSummary, 
    OpenIncidentSummary
)
from core.enums import SensorStatus

logger = logging.getLogger(__name__)

class DashboardService:
    def __init__(self, repo: DashboardRepository):
        self.repo = repo

    def get_snapshot(self, lab_id: str) -> DashboardSnapshot:
        from core.utils import utc_now
        
        # Gather all concurrent parts
        sensors = self.repo.get_sensors(lab_id)
        alerts = self.repo.get_active_alerts(lab_id)
        incidents = self.repo.get_open_incidents(lab_id)
        chemical_count = self.repo.get_chemical_count(lab_id)
        available_staff = self.repo.get_available_staff_count()

        # Format sensors
        sensor_summaries = []
        # Cache location names to avoid duplicate queries
        location_cache = {}
        for s in sensors:
            loc_name = "Unknown Location"
            if s.lab_id:
                if s.lab_id not in location_cache:
                    location_cache[s.lab_id] = self.repo.get_location_name(s.lab_id)
                loc_name = location_cache[s.lab_id]
                
            sensor_summaries.append(SensorSummary(
                sensor_id=s.sensor_id,
                lab_id=s.lab_id,
                location_name=loc_name,
                type=s.sensor_type.value,
                status=s.status.value,
                last_reading=s.last_reading,
                last_updated=s.last_updated
            ))
        
        active_sensor_count = sum(1 for s in sensors if s.status == SensorStatus.ONLINE)

        # Format Alerts
        alert_summaries = [
            ActiveAlertSummary(
                alert_id=a.alert_id,
                type=a.alert_type.value,
                severity=a.severity.value,
                message=a.message
            )
            for a in alerts
        ]

        # Format Incidents
        incident_summaries = []
        for i in incidents:
            staff_name = None
            if i.assigned_staff_id:
                staff_name = self.repo.get_staff_name(i.assigned_staff_id)
                
            incident_summaries.append(OpenIncidentSummary(
                incident_id=i.incident_id,
                title=i.title,
                severity=i.severity.value,
                assigned_staff_name=staff_name
            ))

        return DashboardSnapshot(
            lab_id=lab_id,
            total_active_sensors=active_sensor_count,
            total_chemicals=chemical_count,
            available_staff=available_staff,
            active_alerts=alert_summaries,
            open_incidents=incident_summaries,
            sensors=sensor_summaries,
            generated_at=utc_now()
        )
