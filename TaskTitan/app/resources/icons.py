"""
Icon resources for TaskTitan.

This module provides functions to access and load icons used throughout the application.
"""

import os
from PyQt6.QtGui import QIcon, QPixmap

# The resources directory
RESOURCES_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(RESOURCES_DIR, 'icons')

# Dictionary to cache loaded icons
_icon_cache = {}

def get_icon(icon_name):
    """
    Get an icon by name.
    
    Args:
        icon_name (str): Name of the icon without extension
        
    Returns:
        QIcon: The icon object, or a default icon if not found
    """
    if icon_name in _icon_cache:
        return _icon_cache[icon_name]
    
    # List of possible extensions to try
    extensions = ['.png', '.svg', '.jpg']
    
    for ext in extensions:
        icon_path = os.path.join(ICONS_DIR, f"{icon_name}{ext}")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            _icon_cache[icon_name] = icon
            return icon
    
    # Return a default icon if the requested icon is not found
    return QIcon()

def get_pixmap(icon_name, size=None):
    """
    Get a pixmap by name.
    
    Args:
        icon_name (str): Name of the icon without extension
        size (tuple, optional): Size (width, height) for the pixmap
        
    Returns:
        QPixmap: The pixmap object, or an empty pixmap if not found
    """
    icon = get_icon(icon_name)
    if icon.isNull():
        return QPixmap()
    
    if size:
        return icon.pixmap(size[0], size[1])
    else:
        return icon.pixmap(icon.availableSizes()[0]) if icon.availableSizes() else QPixmap()

def clear_cache():
    """Clear the icon cache."""
    _icon_cache.clear() 