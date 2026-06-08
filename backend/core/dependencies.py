"""
ChemSafe IoT — FastAPI Dependencies

Central dependency injection providers.
Modules use these via Depends() — never instantiate DB sessions or
auth checks directly.
"""

from __future__ import annotations

from typing import Any, Generator

from fastapi import Depends

from core.config import settings
from core.schemas import CurrentUser


# ═══════════════════════════════════════════════════════════════
# Database Session / Client
# ═══════════════════════════════════════════════════════════════

def get_db() -> Generator[Any, None, None]:
    """
    Yield the appropriate database handle based on DB_MODE.

    - sqlite:   yields a SQLAlchemy Session (auto-closed)
    - firebase: yields the Firestore client (singleton, not closed)
    """
    if settings.is_sqlite:
        from core.database import get_sqlite_session
        yield from get_sqlite_session()
    else:
        from core.database import get_firestore_client
        yield get_firestore_client()


# ═══════════════════════════════════════════════════════════════
# Re-export auth dependencies for convenience
# ═══════════════════════════════════════════════════════════════
# Modules can import from either core.auth or core.dependencies

from core.auth import get_current_user, require_role  # noqa: E402, F401
