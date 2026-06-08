"""
ChemSafe IoT — Authentication & Authorization

Handles:
  1. Firebase Auth JWT token verification
  2. Dev-mode bypass (AUTH_DISABLED=true)
  3. Role-based access control via require_role()

Every protected endpoint uses Depends(get_current_user) or require_role().
"""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings
from core.enums import Role
from core.exceptions import ForbiddenException, UnauthorizedException
from core.schemas import CurrentUser

logger = logging.getLogger(__name__)

# Bearer token extractor (optional=True so we can handle missing tokens ourselves)
_bearer_scheme = HTTPBearer(auto_error=False)


# ═══════════════════════════════════════════════════════════════
# Token Verification
# ═══════════════════════════════════════════════════════════════

def _verify_firebase_token(token: str) -> dict:
    """
    Verify a Firebase Auth ID token and return the decoded claims.
    Only called when AUTH_DISABLED=false.
    """
    try:
        from firebase_admin import auth as firebase_auth
        decoded = firebase_auth.verify_id_token(token)
        return decoded
    except Exception as e:
        logger.warning("Firebase token verification failed: %s", e)
        raise UnauthorizedException("Invalid or expired authentication token")


# ═══════════════════════════════════════════════════════════════
# Dev-Mode Default User
# ═══════════════════════════════════════════════════════════════

_DEV_USER = CurrentUser(
    user_id="DEV-admin-001",
    email="admin@chemsafe.dev",
    name="Dev Admin",
    role=Role.ADMIN,
)


# ═══════════════════════════════════════════════════════════════
# Main Dependency: get_current_user
# ═══════════════════════════════════════════════════════════════

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    """
    FastAPI dependency that extracts and validates the current user.

    - AUTH_DISABLED=true  → returns a dev admin user (no token needed)
    - AUTH_DISABLED=false → verifies Firebase Auth JWT token
    """
    # ── Dev mode bypass ───────────────────────────────────────
    if settings.AUTH_DISABLED:
        # Check for optional X-Dev-Role and X-Dev-User-Id header to test different roles
        dev_role = request.headers.get("X-Dev-Role", "admin")
        dev_user_id = request.headers.get("X-Dev-User-Id")
        
        try:
            role = Role(dev_role.lower())
        except ValueError:
            role = Role.ADMIN

        # Try to return the REAL user from the database if provided
        if dev_user_id:
            from core.database import get_sqlite_session, get_firestore_client
            from sqlalchemy import select
            from core.models_sql import UserModel
            
            if settings.is_sqlite:
                session_generator = get_sqlite_session()
                db = next(session_generator)
                db_user = db.execute(select(UserModel).where(UserModel.user_id == dev_user_id)).scalar_one_or_none()
                try:
                    next(session_generator)
                except StopIteration:
                    pass
                
                if db_user:
                    return CurrentUser(
                        user_id=db_user.user_id,
                        email=db_user.email,
                        name=db_user.name,
                        role=db_user.role,
                    )

        # Fallback
        return CurrentUser(
            user_id=dev_user_id or f"DEV-{dev_role}-001",
            email=f"{dev_role}@chemsafe.dev",
            name=f"Dev {dev_role.title()}",
            role=role,
        )

    # ── Production mode ───────────────────────────────────────
    if not credentials:
        raise UnauthorizedException("Missing authentication token")

    decoded = _verify_firebase_token(credentials.credentials)

    return CurrentUser(
        user_id=decoded.get("uid", ""),
        email=decoded.get("email", ""),
        name=decoded.get("name", ""),
        role=Role(decoded.get("role", "viewer")),
    )


# ═══════════════════════════════════════════════════════════════
# Role Guard Factory
# ═══════════════════════════════════════════════════════════════

def require_role(*allowed_roles: Role) -> Callable:
    """
    Create a FastAPI dependency that restricts access to specific roles.

    Usage in a router:
        @router.get("/admin-only")
        def admin_endpoint(user: CurrentUser = Depends(require_role(Role.ADMIN))):
            ...

        @router.get("/staff-or-admin")
        def staff_endpoint(user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))):
            ...
    """
    async def _role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            logger.warning(
                "Access denied: user '%s' (role=%s) tried to access endpoint requiring %s",
                current_user.email,
                current_user.role.value,
                [r.value for r in allowed_roles],
            )
            raise ForbiddenException(
                f"This action requires one of: {', '.join(r.value for r in allowed_roles)}"
            )
        return current_user

    return _role_checker
