"""
ChemSafe IoT — Custom Exceptions

Standardized HTTP error responses used across all modules.
"""

from __future__ import annotations

from fastapi import HTTPException, status


# ═══════════════════════════════════════════════════════════════
# 4xx Client Errors
# ═══════════════════════════════════════════════════════════════

class NotFoundException(HTTPException):
    """Resource not found (404)."""

    def __init__(self, resource: str = "Resource", resource_id: str = ""):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} '{resource_id}' not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenException(HTTPException):
    """Insufficient permissions (403)."""

    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)


class UnauthorizedException(HTTPException):
    """Authentication required or failed (401)."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class BadRequestException(HTTPException):
    """Invalid request data (400)."""

    def __init__(self, message: str = "Invalid request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


class ConflictException(HTTPException):
    """Resource already exists or state conflict (409)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=message)


# ═══════════════════════════════════════════════════════════════
# 5xx Server Errors
# ═══════════════════════════════════════════════════════════════

class DatabaseException(HTTPException):
    """Database operation failed (500)."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
        )


class MQTTException(HTTPException):
    """MQTT operation failed (503)."""

    def __init__(self, message: str = "MQTT service unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
        )
