"""
ChemSafe IoT — Application Configuration

Loads all settings from .env via Pydantic BaseSettings.
Single source of truth for every configurable value in the system.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration object.
    Values are loaded from .env file automatically.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database Mode ─────────────────────────────────────────
    # Toggle: "sqlite" for local dev, "firebase" for cloud
    DB_MODE: Literal["sqlite", "firebase"] = "sqlite"

    # ── SQLite ────────────────────────────────────────────────
    SQLITE_URL: str = "sqlite:///./chemsafe.db"

    # ── Firebase ──────────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-service-account.json"
    FIREBASE_PROJECT_ID: str = ""

    # ── MQTT (HiveMQ Cloud) ───────────────────────────────────
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 8883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_USE_TLS: bool = True
    MQTT_CLIENT_ID: str = "chemsafe-backend"

    # ── Application ───────────────────────────────────────────
    APP_NAME: str = "ChemSafe IoT"
    APP_VERSION: str = "1.0.0"
    CORS_ORIGINS: str = '["*"]'

    # ── Auth ──────────────────────────────────────────────────
    AUTH_DISABLED: bool = True  # Set False in production

    # ── Email ─────────────────────────────────────────────────
    SMTP_SERVER: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "noreply@chemsafe.local"
    
    # ── AI Assistant ──────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS_ORIGINS JSON string into a list."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000"]

    @property
    def is_firebase(self) -> bool:
        return self.DB_MODE == "firebase"

    @property
    def is_sqlite(self) -> bool:
        return self.DB_MODE == "sqlite"


# ── Singleton instance ────────────────────────────────────────
settings = Settings()
