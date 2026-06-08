"""
ChemSafe IoT — FastAPI Application Entry Point

This is the ONLY file that knows about all modules.
It registers every module's router and wires up startup/shutdown events.

To run:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from core.config import settings
from core.database import init_database
from core.mqtt_client import mqtt_client
from core.schemas import HealthResponse

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("chemsafe")


# ═══════════════════════════════════════════════════════════════
# Lifespan (startup + shutdown)
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown logic."""
    # ── Startup ───────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("  ChemSafe IoT — Starting up")
    logger.info("  DB Mode : %s", settings.DB_MODE)
    logger.info("  Auth    : %s", "DISABLED (dev)" if settings.AUTH_DISABLED else "Firebase")
    logger.info("  MQTT    : %s:%d", settings.MQTT_BROKER, settings.MQTT_PORT)
    logger.info("=" * 60)

    # Initialize database (creates tables for SQLite)
    init_database()

    # Connect MQTT (non-blocking — runs in background thread)
    try:
        mqtt_client.connect()
    except Exception:
        logger.warning("MQTT connection failed — continuing without MQTT")

    yield

    # ── Shutdown ──────────────────────────────────────────────
    logger.info("ChemSafe IoT — Shutting down")
    mqtt_client.disconnect()


# ═══════════════════════════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Chemical Laboratory Safety Management Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Files ──────────────────────────────────────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ═══════════════════════════════════════════════════════════════
# API Router Registry
# ═══════════════════════════════════════════════════════════════
# Each module exposes a router in its router.py.
# Import and include them here — this is the ONLY place modules
# are wired into the app.
#
# Uncomment each line as you build the corresponding module.
# ═══════════════════════════════════════════════════════════════

from modules.users.router import router as users_router
from modules.sensors.router import router as sensors_router
from modules.mqtt_ingestion.listener import router as mqtt_router
from modules.alerts.router import router as alerts_router
from modules.incidents.router import router as incidents_router
from modules.staff.router import router as staff_router
from modules.inventory.router import router as inventory_router
from modules.notifications.router import router as notifications_router
from modules.analytics.router import router as analytics_router
from modules.audit_logs.router import router as audit_logs_router
from modules.settings.router import router as settings_router
from modules.reports.router import router as reports_router
from modules.dashboard.router import router as dashboard_router
from modules.ai.router import router as ai_router

app.include_router(users_router,         prefix="/api/users",         tags=["Users"])
app.include_router(sensors_router,       prefix="/api/sensors",       tags=["Sensors"])
app.include_router(mqtt_router,          prefix="/api/mqtt",          tags=["MQTT"])
app.include_router(alerts_router,        prefix="/api/alerts",        tags=["Alerts"])
app.include_router(incidents_router,     prefix="/api/incidents",     tags=["Incidents"])
app.include_router(staff_router,         prefix="/api/staff",         tags=["Staff & Assignments"])
app.include_router(inventory_router,     prefix="/api/inventory",     tags=["Chemical Inventory"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(analytics_router,     prefix="/api/analytics",     tags=["Analytics"])
app.include_router(audit_logs_router,    prefix="/api/audit-logs",    tags=["Audit Logs"])
app.include_router(settings_router,      prefix="/api/settings",      tags=["Settings"])
app.include_router(reports_router,       prefix="/api/reports",       tags=["Reports"])
app.include_router(dashboard_router,     prefix="/api/dashboard",     tags=["Dashboard"])
app.include_router(ai_router,            prefix="/api/ai",            tags=["AI Assistant"])


# ═══════════════════════════════════════════════════════════════
# Root & Health Endpoints
# ═══════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
def root():
    """Root endpoint — confirms the API is running."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Detailed health check for monitoring."""
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        db_mode=settings.DB_MODE,
        mqtt_connected=mqtt_client.is_connected,
    )
