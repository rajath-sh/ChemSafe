"""
ChemSafe IoT — Utility Helpers

Shared utility functions: ID generation, timestamps, etc.
Every module uses these — no module-specific logic here.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with an optional prefix.

    Examples:
        generate_id()          → "a1b2c3d4e5f6..."
        generate_id("ALR")     → "ALR-a1b2c3d4e5f6..."
        generate_id("INC")     → "INC-a1b2c3d4e5f6..."
    """
    uid = uuid.uuid4().hex[:16]
    return f"{prefix}-{uid}" if prefix else uid


def utc_now() -> datetime:
    """Current UTC timestamp (timezone-aware)."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Current UTC timestamp as ISO 8601 string."""
    return utc_now().isoformat()


def to_iso(dt: datetime | None) -> str | None:
    """Convert a datetime to ISO 8601 string, or return None."""
    if dt is None:
        return None
    return dt.isoformat()


def from_iso(iso_str: str | None) -> datetime | None:
    """Parse an ISO 8601 string to datetime, or return None."""
    if iso_str is None:
        return None
    return datetime.fromisoformat(iso_str)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a numeric value to a range."""
    return max(min_val, min(value, max_val))


def risk_level_from_score(score: float) -> str:
    """
    Convert a 0-100 risk score to a risk level string.
    0–25:  safe
    26–50: low
    51–75: medium
    76–100: high
    """
    if score <= 25:
        return "safe"
    elif score <= 50:
        return "low"
    elif score <= 75:
        return "medium"
    else:
        return "high"
