"""
ChemSafe IoT — SQLAlchemy ORM Models

ALL database table models live here (not in individual modules).
This is the single source of truth for the SQLite schema.
Firestore uses these same field names as document keys.

When DB_MODE=sqlite, core.database.init_database() calls
Base.metadata.create_all() to auto-create these tables.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from sqlalchemy import TypeDecorator
from datetime import timezone

class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


from core.database import Base
from core.enums import (
    AlertSeverity,
    AlertStatus,
    AlertType,
    AssignmentPriority,
    AssignmentStatus,
    HazardClass,
    IncidentSeverity,
    IncidentStatus,
    NotificationPriority,
    NotificationStatus,
    RiskLevel,
    Role,
    SensorStatus,
    SensorType,
    StaffAvailability,
    UserStatus,
)
from core.utils import generate_id, utc_now


# ═══════════════════════════════════════════════════════════════
# Users
# ═══════════════════════════════════════════════════════════════

class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(String(32), primary_key=True, default=lambda: generate_id("USR"))
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    role = Column(Enum(Role), nullable=False, default=Role.VIEWER)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    availability = Column(Enum(StaffAvailability), nullable=True, default=StaffAvailability.AVAILABLE)
    created_at = Column(UTCDateTime, nullable=False, default=utc_now)

    # Relationships
    incident_notes = relationship("IncidentNoteModel", back_populates="user")
    notifications = relationship("NotificationModel", back_populates="user")
    audit_logs = relationship("AuditLogModel", back_populates="user")


# ═══════════════════════════════════════════════════════════════
# Laboratories
# ═══════════════════════════════════════════════════════════════

class LaboratoryModel(Base):
    __tablename__ = "laboratories"

    lab_id = Column(String(32), primary_key=True, default=lambda: generate_id("LAB"))
    lab_name = Column(String(100), nullable=False)
    location = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(UTCDateTime, nullable=False, default=utc_now)

    # Relationships
    sensors = relationship("SensorModel", back_populates="laboratory")
    sensor_readings = relationship("SensorReadingModel", back_populates="laboratory")
    alerts = relationship("AlertModel", back_populates="laboratory")
    incidents = relationship("IncidentModel", back_populates="laboratory")
    risk_scores = relationship("RiskScoreModel", back_populates="laboratory")
    anomalies = relationship("AnomalyModel", back_populates="laboratory")
    thresholds = relationship("ThresholdModel", back_populates="laboratory")


# ═══════════════════════════════════════════════════════════════
# Sensors
# ═══════════════════════════════════════════════════════════════

class SensorModel(Base):
    __tablename__ = "sensors"

    sensor_id = Column(String(32), primary_key=True, default=lambda: generate_id("SEN"))
    lab_id = Column(String(32), ForeignKey("laboratories.lab_id"), nullable=False, index=True)
    sensor_type = Column(Enum(SensorType), nullable=False)
    status = Column(Enum(SensorStatus), nullable=False, default=SensorStatus.ONLINE)
    last_reading = Column(Float, nullable=True)
    last_updated = Column(UTCDateTime, nullable=True)

    # Relationships
    laboratory = relationship("LaboratoryModel", back_populates="sensors")


# ═══════════════════════════════════════════════════════════════
# Sensor Readings (time-series data)
# ═══════════════════════════════════════════════════════════════

class SensorReadingModel(Base):
    __tablename__ = "sensor_readings"

    reading_id = Column(String(32), primary_key=True, default=lambda: generate_id("RDG"))
    lab_id = Column(String(32), ForeignKey("laboratories.lab_id"), nullable=False, index=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    gas = Column(Float, nullable=True)
    light = Column(Float, nullable=True)
    vibration = Column(Float, nullable=True)
    timestamp = Column(UTCDateTime, nullable=False, default=utc_now, index=True)

    # Relationships
    laboratory = relationship("LaboratoryModel", back_populates="sensor_readings")


# ═══════════════════════════════════════════════════════════════
# Alerts
# ═══════════════════════════════════════════════════════════════

class AlertModel(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(32), primary_key=True, default=lambda: generate_id("ALR"))
    lab_id = Column(String(32), ForeignKey("laboratories.lab_id"), nullable=False, index=True)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    message = Column(Text, nullable=True)
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE)
    sensor_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    sensor_id = Column(String(32), nullable=True)
    created_at = Column(UTCDateTime, nullable=False, default=utc_now, index=True)

    # Relationships
    laboratory = relationship("LaboratoryModel", back_populates="alerts")


# ═══════════════════════════════════════════════════════════════
# Incidents
# ═══════════════════════════════════════════════════════════════

class IncidentModel(Base):
    __tablename__ = "incidents"

    incident_id = Column(String(32), primary_key=True, default=lambda: generate_id("INC"))
    lab_id = Column(String(32), ForeignKey("laboratories.lab_id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.INFO)
    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN)
    assigned_staff_id = Column(String(32), ForeignKey("users.user_id"), nullable=True)
    alert_id = Column(String(32), nullable=True)  # Source alert if created from alert
    resolution_summary = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)  # Populated if assigned staff rejects
    created_at = Column(UTCDateTime, nullable=False, default=utc_now, index=True)
    resolved_at = Column(UTCDateTime, nullable=True)

    # Relationships
    laboratory = relationship("LaboratoryModel", back_populates="incidents")
    assigned_staff = relationship("UserModel", foreign_keys=[assigned_staff_id])
    notes = relationship("IncidentNoteModel", back_populates="incident")
    assignments = relationship("AssignmentModel", back_populates="incident")


# ═══════════════════════════════════════════════════════════════
# Incident Notes (timeline entries)
# ═══════════════════════════════════════════════════════════════

class IncidentNoteModel(Base):
    __tablename__ = "incident_notes"

    note_id = Column(String(32), primary_key=True, default=lambda: generate_id("NTE"))
    incident_id = Column(String(32), ForeignKey("incidents.incident_id"), nullable=False, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(UTCDateTime, nullable=False, default=utc_now)

    # Relationships
    incident = relationship("IncidentModel", back_populates="notes")
    user = relationship("UserModel", back_populates="incident_notes")


# ═══════════════════════════════════════════════════════════════
# Assignments
# ═══════════════════════════════════════════════════════════════

class AssignmentModel(Base):
    __tablename__ = "assignments"

    assignment_id = Column(String(32), primary_key=True, default=lambda: generate_id("ASN"))
    incident_id = Column(String(32), ForeignKey("incidents.incident_id"), nullable=False, index=True)
    staff_id = Column(String(32), ForeignKey("users.user_id"), nullable=False, index=True)
    status = Column(Enum(AssignmentStatus), nullable=False, default=AssignmentStatus.NEW)
    priority = Column(Enum(AssignmentPriority), nullable=False, default=AssignmentPriority.MEDIUM)
    assigned_at = Column(UTCDateTime, nullable=False, default=utc_now)
    completed_at = Column(UTCDateTime, nullable=True)

    # Relationships
    incident = relationship("IncidentModel", back_populates="assignments")
    staff = relationship("UserModel", foreign_keys=[staff_id])


# ═══════════════════════════════════════════════════════════════
# Chemical Inventory
# ═══════════════════════════════════════════════════════════════

class InventoryLocationModel(Base):
    __tablename__ = "inventory_locations"

    location_id = Column(String(32), primary_key=True, default=lambda: generate_id("LOC"))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(UTCDateTime, nullable=False, default=utc_now)

    # Relationships
    chemicals = relationship("ChemicalModel", back_populates="location")


class ChemicalModel(Base):
    __tablename__ = "chemicals"

    chemical_id = Column(String(32), primary_key=True, default=lambda: generate_id("CHM"))
    location_id = Column(String(32), ForeignKey("inventory_locations.location_id"), nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    formula = Column(String(50), nullable=True)
    cas_number = Column(String(20), nullable=True)
    category = Column(String(100), nullable=True)
    hazard_class = Column(Enum(HazardClass), nullable=True)
    description = Column(Text, nullable=True)
    quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(20), nullable=True, default="mL")
    expiry_date = Column(UTCDateTime, nullable=True)
    image_url = Column(String(500), nullable=True)
    storage_requirements = Column(Text, nullable=True)
    emergency_procedure = Column(Text, nullable=True)
    created_at = Column(UTCDateTime, nullable=False, default=utc_now)
    last_updated_by = Column(String(32), nullable=True)
    updated_at = Column(UTCDateTime, nullable=False, default=utc_now)

    # Relationships
    location = relationship("InventoryLocationModel", back_populates="chemicals")


# ═══════════════════════════════════════════════════════════════
# Notifications
# ═══════════════════════════════════════════════════════════════

class NotificationModel(Base):
    __tablename__ = "notifications"

    notification_id = Column(String(32), primary_key=True, default=lambda: generate_id("NTF"))
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.INFO)
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.UNREAD)
    created_at = Column(UTCDateTime, nullable=False, default=utc_now, index=True)

    # Relationships
    user = relationship("UserModel", back_populates="notifications")


# ═══════════════════════════════════════════════════════════════
# Audit Logs
# ═══════════════════════════════════════════════════════════════

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(32), primary_key=True, default=lambda: generate_id("LOG"))
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True)
    action = Column(String(100), nullable=False)
    module = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(UTCDateTime, nullable=False, default=utc_now, index=True)

    # Relationships
    user = relationship("UserModel", back_populates="audit_logs")


# ═══════════════════════════════════════════════════════════════
# Risk Scores
# ═══════════════════════════════════════════════════════════════

class RiskScoreModel(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(String(32), ForeignKey("laboratories.lab_id"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False, default=0)
    risk_level = Column(Enum(RiskLevel), nullable=False, default=RiskLevel.SAFE)
    generated_at = Column(UTCDateTime, nullable=False, default=utc_now, index=True)

    # Relationships
    laboratory = relationship("LaboratoryModel", back_populates="risk_scores")


# ═══════════════════════════════════════════════════════════════
# Anomalies
# ═══════════════════════════════════════════════════════════════

class AnomalyModel(Base):
    __tablename__ = "anomalies"

    anomaly_id = Column(String(32), primary_key=True, default=lambda: generate_id("ANM"))
    lab_id = Column(String(32), ForeignKey("laboratories.lab_id"), nullable=False, index=True)
    sensor_type = Column(Enum(SensorType), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False, default=AlertSeverity.INFO)
    description = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0)  # 0–100
    timestamp = Column(UTCDateTime, nullable=False, default=utc_now, index=True)

    # Relationships
    laboratory = relationship("LaboratoryModel", back_populates="anomalies")


# ═══════════════════════════════════════════════════════════════
# Threshold Configuration
# ═══════════════════════════════════════════════════════════════

class ThresholdModel(Base):
    __tablename__ = "thresholds"

    threshold_id = Column(String(32), primary_key=True, default=lambda: generate_id("THR"))
    lab_id = Column(String(32), ForeignKey("laboratories.lab_id"), nullable=False, index=True)
    sensor_type = Column(Enum(SensorType), nullable=False)
    warning_value = Column(Float, nullable=False)
    critical_value = Column(Float, nullable=False)
    min_value = Column(Float, nullable=True)  # For humidity range
    max_value = Column(Float, nullable=True)  # For humidity range

    # Relationships
    laboratory = relationship("LaboratoryModel", back_populates="thresholds")
