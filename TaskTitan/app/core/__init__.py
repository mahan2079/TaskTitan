"""
Core module for TaskTitan.

This module provides core functionality including configuration
and settings management.
"""

from app.core.config import ConfigManager, get_config, set_config
from app.core.settings import SettingsManager, get_settings_manager

__all__ = [
    'ConfigManager',
    'get_config',
    'set_config',
    'SettingsManager',
    'get_settings_manager'
]

