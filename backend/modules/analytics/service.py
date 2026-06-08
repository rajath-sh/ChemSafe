import logging
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta

from modules.analytics.repository import AnalyticsRepository
from modules.analytics.schemas import LabAnalyticsOut, DailyAggregation, SensorStats, IncidentStats
from core.enums import IncidentStatus, IncidentSeverity

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, repo: AnalyticsRepository):
        self.repo = repo

    def generate_lab_report(self, lab_id: str, days: int = 7) -> LabAnalyticsOut:
        from core.utils import utc_now
        since_date = utc_now() - timedelta(days=days)
        
        # 1. Fetch raw data
        readings = self.repo.get_readings_since(lab_id, since_date)
        incidents = self.repo.get_incidents_since(lab_id, since_date)
        
        # 2. Process Incidents
        incident_stats = IncidentStats(
            total=len(incidents),
            open_count=sum(1 for i in incidents if i.status == IncidentStatus.OPEN),
            resolved_count=sum(1 for i in incidents if i.status == IncidentStatus.RESOLVED),
            critical_count=sum(1 for i in incidents if i.severity == IncidentSeverity.CRITICAL)
        )
        
        # 3. Process Sensor Readings using Pandas
        daily_trends = []
        if readings:
            df = pd.DataFrame(readings)
            
            # Ensure timestamp is datetime and sort
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Add a 'date' string column for daily grouping
            df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
            
            # Group by Date
            grouped = df.groupby('date')
            
            for date_str, group in grouped:
                trend = DailyAggregation(date=date_str)
                
                if 'temperature' in group.columns and not group['temperature'].isna().all():
                    trend.temperature = SensorStats(
                        min_value=round(group['temperature'].min(), 2),
                        max_value=round(group['temperature'].max(), 2),
                        avg_value=round(group['temperature'].mean(), 2)
                    )
                    
                if 'humidity' in group.columns and not group['humidity'].isna().all():
                    trend.humidity = SensorStats(
                        min_value=round(group['humidity'].min(), 2),
                        max_value=round(group['humidity'].max(), 2),
                        avg_value=round(group['humidity'].mean(), 2)
                    )
                    
                daily_trends.append(trend)

        return LabAnalyticsOut(
            lab_id=lab_id,
            date_range_days=days,
            sensor_trends=daily_trends,
            incident_summary=incident_stats
        )
