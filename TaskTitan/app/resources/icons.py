"""
Icon resources for TaskTitan.

This module provides functions to access and load icons used throughout the application.
"""

import os
import sys
from PyQt6.QtGui import QIcon, QPixmap

# The resources directory - Handle PyInstaller's frozen state
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    RESOURCES_DIR = os.path.join(sys._MEIPASS, 'app', 'resources')
else:
    # Running as script
    RESOURCES_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(RESOURCES_DIR, 'icons')

# Dictionary to cache loaded icons
_icon_cache = {}

# Define icon paths
ICON_PATHS = {
    'dashboard': os.path.join(ICONS_DIR, 'dashboard.svg'),
    'calendar': os.path.join(ICONS_DIR, 'calendar.svg'),
    'goals': os.path.join(ICONS_DIR, 'goals.svg'),
    'productivity': os.path.join(ICONS_DIR, 'productivity.svg'),
    'pomodoro': os.path.join(ICONS_DIR, 'pomodoro.svg'),
    'settings': os.path.join(ICONS_DIR, 'settings.svg'),
    'tasks': os.path.join(ICONS_DIR, 'tasks.svg'),
    'habits': os.path.join(ICONS_DIR, 'habits.svg'),
    'search': os.path.join(ICONS_DIR, 'search.svg'),
    'user': os.path.join(ICONS_DIR, 'user.svg'),
    'add': os.path.join(ICONS_DIR, 'add.svg'),
    'edit': os.path.join(ICONS_DIR, 'edit.svg'),
    'delete': os.path.join(ICONS_DIR, 'delete.svg'),
    'more': os.path.join(ICONS_DIR, 'more.svg'),
    'task': os.path.join(ICONS_DIR, 'task.svg'),
    'event': os.path.join(ICONS_DIR, 'event.svg'),
    'habit': os.path.join(ICONS_DIR, 'habit.svg'),
    'daily': os.path.join(ICONS_DIR, 'daily.svg'),
    'weekly': os.path.join(ICONS_DIR, 'weekly.svg'),
    'weekly_plan': os.path.join(ICONS_DIR, 'weekly.svg'),
}

def get_icon(name, fallback=None):
    """
    Get an icon by name.
    
    Args:
        name: The name of the icon to get
        fallback: Fallback icon name if the requested icon doesn't exist
        
    Returns:
        A QIcon object, or an empty QIcon if the icon doesn't exist
    """
    if name in ICON_PATHS and os.path.exists(ICON_PATHS[name]):
        return QIcon(ICON_PATHS[name])
    elif fallback in ICON_PATHS and os.path.exists(ICON_PATHS[fallback]):
        return QIcon(ICON_PATHS[fallback])
    else:
        return QIcon()

def get_pixmap(name, fallback=None):
    """
    Get a pixmap by name.
    
    Args:
        name: The name of the pixmap to get
        fallback: Fallback pixmap name if the requested pixmap doesn't exist
        
    Returns:
        A QPixmap object, or an empty QPixmap if the pixmap doesn't exist
    """
    if name in ICON_PATHS and os.path.exists(ICON_PATHS[name]):
        return QPixmap(ICON_PATHS[name])
    elif fallback in ICON_PATHS and os.path.exists(ICON_PATHS[fallback]):
        return QPixmap(ICON_PATHS[fallback])
    else:
        return QPixmap()

def clear_cache():
    """Clear the icon cache."""
    _icon_cache.clear() 