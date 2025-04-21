"""
Resources module for TaskTitan.

This module contains resources such as icons, images, and other assets
used throughout the application.
"""

from app.resources.icons import get_icon, get_pixmap, clear_cache
from app.resources.styles import get_component_style
from app.resources.colors import ColorPalette
from app.resources.utils import apply_theme, is_dark_mode, get_resource_path, create_font
from app.resources.constants import *

# Re-export common functions and classes at package level
__all__ = [
    'get_icon', 
    'get_pixmap', 
    'clear_cache',
    'get_component_style',
    'ColorPalette',
    'apply_theme',
    'is_dark_mode',
    'get_resource_path',
    'create_font',
    'APP_NAME',
    'APP_VERSION',
    'DASHBOARD_VIEW',
    'ACTIVITIES_VIEW',
    'GOALS_VIEW',
    'PRODUCTIVITY_VIEW',
    'POMODORO_VIEW',
    'WEEKLY_VIEW',
    'DAILY_VIEW',
    'SETTINGS_VIEW',
    'VIEW_NAMES'
] 