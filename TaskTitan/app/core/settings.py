"""
Settings persistence module for TaskTitan.

This module provides functions to persist and retrieve user settings,
integrating with the configuration system.
"""

from typing import Any, Dict, Optional
from app.core.config import ConfigManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SettingsManager:
    """Manages user settings persistence."""
    
    def __init__(self):
        """Initialize settings manager."""
        self.config = ConfigManager.get_instance()
    
    def get_window_size(self) -> tuple[int, int]:
        """Get saved window size."""
        width = self.config.get('window.width', 1200)
        height = self.config.get('window.height', 800)
        return (width, height)
    
    def set_window_size(self, width: int, height: int):
        """Save window size."""
        self.config.set('window.width', width)
        self.config.set('window.height', height)
    
    def get_window_position(self) -> Optional[tuple[int, int]]:
        """Get saved window position."""
        if not self.config.get('window.remember_position', True):
            return None
        
        pos = self.config.get('window.position', None)
        if pos:
            return tuple(pos)
        return None
    
    def set_window_position(self, x: int, y: int):
        """Save window position."""
        if self.config.get('window.remember_position', True):
            self.config.set('window.position', [x, y])
    
    def get_theme(self) -> tuple[str, bool]:
        """Get theme settings."""
        theme = self.config.get('display.theme', 'System (Auto)')
        follow_system = self.config.get('display.follow_system_theme', True)
        return (theme, follow_system)
    
    def set_theme(self, theme: str, follow_system: bool):
        """Save theme settings."""
        self.config.set('display.theme', theme)
        self.config.set('display.follow_system_theme', follow_system)
    
    def get_pomodoro_settings(self) -> Dict[str, Any]:
        """Get Pomodoro timer settings."""
        return self.config.get_section('pomodoro')
    
    def set_pomodoro_settings(self, settings: Dict[str, Any]):
        """Save Pomodoro timer settings."""
        self.config.update_section('pomodoro', settings)
    
    def get_backup_settings(self) -> Dict[str, Any]:
        """Get backup settings."""
        return self.config.get_section('backup')
    
    def set_backup_settings(self, settings: Dict[str, Any]):
        """Save backup settings."""
        self.config.update_section('backup', settings)
    
    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification settings."""
        return self.config.get_section('notifications')
    
    def set_notification_settings(self, settings: Dict[str, Any]):
        """Save notification settings."""
        self.config.update_section('notifications', settings)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings."""
        return self.config.config.copy()
    
    def migrate_old_settings(self):
        """Migrate settings from old format if needed."""
        # This would handle migration from previous settings storage
        # For now, just ensure defaults are set
        logger.debug("Checking for old settings to migrate")
        # Future: Add migration logic here


# Singleton instance
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """Get singleton instance of SettingsManager."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager

