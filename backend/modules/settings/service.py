import logging

from modules.settings.repository import SettingsRepository
from modules.settings.schemas import SystemSettingsOut, SystemSettingsUpdate
from core.event_bus import event_bus

logger = logging.getLogger(__name__)

class SettingsService:
    def __init__(self, repo: SettingsRepository):
        self.repo = repo

    def get_system_settings(self) -> SystemSettingsOut:
        return self.repo.get_settings()

    def update_system_settings(self, data: SystemSettingsUpdate) -> SystemSettingsOut:
        # We can fire an event if needed when settings update (e.g. telling MQTT listener to reconnect)
        updated = self.repo.update_settings(data)
        logger.info("System settings updated")
        return updated
