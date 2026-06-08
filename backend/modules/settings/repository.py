import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any

from modules.settings.schemas import SystemSettingsOut, SystemSettingsUpdate
from core.config import settings

class SettingsRepository(ABC):
    @abstractmethod
    def get_settings(self) -> SystemSettingsOut: ...
    @abstractmethod
    def update_settings(self, data: SystemSettingsUpdate) -> SystemSettingsOut: ...


class SettingsRepositoryFile(SettingsRepository):
    """Fallback repository using a local JSON file since we can't alter global models."""
    def __init__(self, filepath: str = "system_settings.json"):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            default_settings = SystemSettingsOut().model_dump()
            with open(self.filepath, "w") as f:
                json.dump(default_settings, f, indent=4)

    def get_settings(self) -> SystemSettingsOut:
        with open(self.filepath, "r") as f:
            data = json.load(f)
        return SystemSettingsOut(**data)

    def update_settings(self, data: SystemSettingsUpdate) -> SystemSettingsOut:
        current = self.get_settings().model_dump()
        updates = data.model_dump(exclude_unset=True)
        
        current.update(updates)
        
        with open(self.filepath, "w") as f:
            json.dump(current, f, indent=4)
            
        return SystemSettingsOut(**current)


class SettingsRepositoryFirestore(SettingsRepository):
    def __init__(self, db):
        self.db = db
        self.doc_ref = self.db.collection('system').document('global_settings')

    def get_settings(self) -> SystemSettingsOut:
        doc = self.doc_ref.get()
        if doc.exists:
            return SystemSettingsOut(**doc.to_dict())
        # Return defaults if it doesn't exist yet
        return SystemSettingsOut()

    def update_settings(self, data: SystemSettingsUpdate) -> SystemSettingsOut:
        updates = data.model_dump(exclude_unset=True)
        self.doc_ref.set(updates, merge=True)
        
        # Fetch fresh
        return self.get_settings()


def get_settings_repository(db) -> SettingsRepository:
    if settings.is_sqlite:
        return SettingsRepositoryFile()
    else:
        return SettingsRepositoryFirestore(db)
