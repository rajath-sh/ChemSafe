"""
ChemSafe IoT — Database Engine Factory

Provides the database connection based on DB_MODE:
  • "sqlite"   → SQLAlchemy engine + SessionLocal
  • "firebase" → Firestore client via firebase-admin

Modules never call this directly — they use core.dependencies.get_db().
"""

from __future__ import annotations

import logging
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

from core.config import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# SQLAlchemy Base (shared by all models in models_sql.py)
# ═══════════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


# ═══════════════════════════════════════════════════════════════
# SQLite Engine & Session Factory
# ═══════════════════════════════════════════════════════════════

_engine = None
_SessionLocal = None


def _get_sqlite_engine():
    """Create and cache the SQLite engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.SQLITE_URL,
            connect_args={"check_same_thread": False},  # Required for SQLite
            echo=False,
        )
        # Enable WAL mode and foreign keys for SQLite
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

        logger.info("SQLite engine created: %s", settings.SQLITE_URL)
    return _engine


def get_session_factory() -> sessionmaker:
    """Get the SQLAlchemy SessionLocal factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = _get_sqlite_engine()
        _SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return _SessionLocal


def get_sqlite_session() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and close it after use."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# Firebase Firestore Client
# ═══════════════════════════════════════════════════════════════

_firestore_client = None


def get_firestore_client():
    """
    Initialize and cache the Firestore client.
    Only called when DB_MODE=firebase.
    """
    global _firestore_client
    if _firestore_client is None:
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                "projectId": settings.FIREBASE_PROJECT_ID,
            })
            _firestore_client = firestore.client()
            logger.info("Firestore client initialized for project: %s", settings.FIREBASE_PROJECT_ID)
        except Exception as e:
            logger.error("Failed to initialize Firestore: %s", e)
            raise
    return _firestore_client


# ═══════════════════════════════════════════════════════════════
# Database Initialization
# ═══════════════════════════════════════════════════════════════

def init_database():
    """
    Initialize the database on application startup.
    - SQLite: creates all tables from models_sql.py
    - Firebase: ensures Firestore client is connected
    """
    if settings.is_sqlite:
        from core.models_sql import Base as _  # noqa: F401 — ensure models are imported
        engine = _get_sqlite_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite database initialized — all tables created.")
    else:
        get_firestore_client()
        logger.info("Firestore database connected.")
