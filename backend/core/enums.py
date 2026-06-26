"""
ChemSafe IoT — Shared Enumerations

Every enum used across multiple modules lives here.
Modules import from core.enums — never from each other.
"""

from __future__ import annotations

import enum


# ═══════════════════════════════════════════════════════════════
# User & Auth
# ═══════════════════════════════════════════════════════════════

class Role(str, enum.Enum):
    ADMIN = "admin"
    STAFF = "staff"
    VIEWER = "viewer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


# ═══════════════════════════════════════════════════════════════
# Sensors
# ═══════════════════════════════════════════════════════════════

class SensorType(str, enum.Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    GAS = "gas"
    LIGHT = "light"
    VIBRATION = "vibration"


class SensorStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


# ═══════════════════════════════════════════════════════════════
# Alerts
# ═══════════════════════════════════════════════════════════════

class AlertType(str, enum.Enum):
    GAS = "gas"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    LIGHT = "light"
    VIBRATION = "vibration"
    ANOMALY = "anomaly"
    SECURITY = "security"


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    CONVERTED = "converted_to_incident"
    CLOSED = "closed"


# ═══════════════════════════════════════════════════════════════
# Incidents
# ═══════════════════════════════════════════════════════════════

class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ═══════════════════════════════════════════════════════════════
# Assignments
# ═══════════════════════════════════════════════════════════════

class AssignmentStatus(str, enum.Enum):
    NEW = "new"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class AssignmentPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ═══════════════════════════════════════════════════════════════
# Staff
# ═══════════════════════════════════════════════════════════════

class StaffAvailability(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ON_LEAVE = "on_leave"


# ═══════════════════════════════════════════════════════════════
# Notifications
# ═══════════════════════════════════════════════════════════════

class NotificationPriority(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationStatus(str, enum.Enum):
    UNREAD = "unread"
    READ = "read"


# ═══════════════════════════════════════════════════════════════
# Risk
# ═══════════════════════════════════════════════════════════════

class RiskLevel(str, enum.Enum):
    SAFE = "safe"            # 0–25
    LOW = "low"              # 26–50
    MEDIUM = "medium"        # 51–75
    HIGH = "high"            # 76–100


# ═══════════════════════════════════════════════════════════════
# Chemical Inventory
# ═══════════════════════════════════════════════════════════════

class HazardClass(str, enum.Enum):
    FLAMMABLE = "flammable"
    TOXIC = "toxic"
    CORROSIVE = "corrosive"
    OXIDIZER = "oxidizer"
    EXPLOSIVE = "explosive"
    RADIOACTIVE = "radioactive"
    BIOHAZARD = "biohazard"
    IRRITANT = "irritant"
    COMPRESSED_GAS = "compressed_gas"
    ENVIRONMENTAL = "environmental"
    NON_HAZARDOUS = "non_hazardous"
