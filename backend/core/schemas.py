"""
ChemSafe IoT — Shared Pydantic Schemas

Response/request models used across multiple modules.
Module-specific schemas go in their own schemas.py file.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from core.enums import Role

T = TypeVar("T")


# ═══════════════════════════════════════════════════════════════
# User (shared across auth, dependencies, and every module)
# ═══════════════════════════════════════════════════════════════

class CurrentUser(BaseModel):
    """Represents the authenticated user extracted from the JWT token."""
    user_id: str
    email: str
    name: str = ""
    role: Role = Role.VIEWER


# ═══════════════════════════════════════════════════════════════
# Pagination
# ═══════════════════════════════════════════════════════════════

class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Wrapper for paginated API responses."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int):
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=max(1, (total + page_size - 1) // page_size),
        )


# ═══════════════════════════════════════════════════════════════
# Standard API Responses
# ═══════════════════════════════════════════════════════════════

class MessageResponse(BaseModel):
    """Simple success message."""
    message: str
    detail: str | None = None


class DeleteHistoryResponse(BaseModel):
    """Response for admin history-delete operations."""
    message: str
    deleted_count: int


class CountResponse(BaseModel):
    """Generic count response."""
    count: int


# ═══════════════════════════════════════════════════════════════
# Timestamp Mixin
# ═══════════════════════════════════════════════════════════════

class TimestampMixin(BaseModel):
    """Mixin that adds created_at to any schema."""
    created_at: datetime | None = None


# ═══════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    """Application health check response."""
    status: str = "ok"
    app_name: str
    version: str
    db_mode: str
    mqtt_connected: bool
