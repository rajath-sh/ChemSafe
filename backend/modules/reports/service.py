import logging
from typing import List
from datetime import timedelta

from modules.reports.repository import ReportRepository
from modules.reports.schemas import ReportRequest, ReportOut
from core.enums import IncidentSeverity, AlertSeverity, HazardClass

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, repo: ReportRepository):
        self.repo = repo

    def get_facilities(self) -> List[str]:
        return self.repo.get_facilities()

    def generate_report(self, request: ReportRequest, user_id: str) -> ReportOut:
        from core.utils import generate_id, utc_now
        
        since_date = utc_now() - timedelta(days=request.days)
        report_data = {}
        
        if request.report_type == "safety":
            if not request.lab_id:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="lab_id is required for safety reports")
            incidents = self.repo.get_incidents(request.lab_id, since_date)
            alerts = self.repo.get_alerts(request.lab_id, since_date)
            
            # Fetch users to map staff names
            from modules.users.repository import get_user_repository
            # We don't have db object directly here, but we can access it via repo.db
            user_repo = get_user_repository(self.repo.db)
            users = user_repo.list_users()
            user_map = {u.user_id: u.name for u in users}

            report_data = {
                "summary": "Laboratory Safety Incident & Alert Report",
                "period_days": request.days,
                "total_alerts": len(alerts),
                "critical_alerts": sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL),
                "total_incidents": len(incidents),
                "critical_incidents": sum(1 for i in incidents if i.severity == IncidentSeverity.CRITICAL),
                "incident_details": [
                    {
                        "id": i.incident_id, 
                        "title": i.title, 
                        "status": i.status.value, 
                        "date": i.created_at.isoformat(),
                        "description": i.description,
                        "resolution_summary": i.resolution_summary,
                        "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
                        "resolved_by_name": user_map.get(i.assigned_staff_id, "Unknown/Unassigned") if i.assigned_staff_id else "Unassigned"
                    }
                    for i in incidents
                ]
            }
            
        elif request.report_type == "inventory":
            chemicals = self.repo.get_chemicals(request.location_id)
            
            # Count hazard classes
            hazard_counts = {}
            for c in chemicals:
                h_name = c.hazard_class.value if c.hazard_class else "Unknown"
                hazard_counts[h_name] = hazard_counts.get(h_name, 0) + 1
                
            report_data = {
                "summary": "Chemical Inventory Snapshot",
                "total_chemicals": len(chemicals),
                "hazard_distribution": hazard_counts,
                "inventory_list": [
                    {"name": c.name, "quantity": c.quantity, "unit": c.unit, "hazard": c.hazard_class.value if c.hazard_class else None}
                    for c in chemicals
                ]
            }
            
        else:
            from core.exceptions import BadRequestException
            raise BadRequestException(f"Unsupported report type: {request.report_type}")
 
        return ReportOut(
            report_id=generate_id("REP"),
            lab_id=request.lab_id,
            location_id=request.location_id,
            report_type=request.report_type,
            generated_at=utc_now(),
            generated_by=user_id,
            data=report_data
        )
