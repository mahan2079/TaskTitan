"""
Utility functions for handling resources in TaskTitan.
"""

import os
import sys
import darkdetect
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QPalette, QColor

# Constants - Handle PyInstaller's frozen state
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    RESOURCES_DIR = os.path.join(sys._MEIPASS, 'app', 'resources')
else:
    # Running as script
    RESOURCES_DIR = os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path):
    """
    Get the absolute path to a resource file.
    
    Args:
        relative_path (str): Relative path to the resource from the resources directory
        
    Returns:
        str: Absolute path to the resource
    """
    return os.path.join(RESOURCES_DIR, relative_path)

def is_dark_mode():
    """
    Detect if the system is using dark mode.
    
    Returns:
        bool: True if the system is using dark mode, False otherwise
    """
    return darkdetect.isDark()

def load_stylesheet(stylesheet_name):
    """
    Load a stylesheet from file.
    
    Args:
        stylesheet_name (str): Name of the stylesheet file
        
    Returns:
        str: Content of the stylesheet, or empty string if not found
    """
    try:
        stylesheet_path = os.path.join(RESOURCES_DIR, 'styles', stylesheet_name)
        with open(stylesheet_path, 'r') as f:
            return f.read()
    except (FileNotFoundError, IOError):
        return ""

def get_themes_dir():
    """Get the themes directory path, handling PyInstaller frozen state."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        return os.path.join(sys._MEIPASS, 'app', 'themes')
    else:
        # Running as script
        return os.path.join(os.path.dirname(os.path.dirname(RESOURCES_DIR)), 'themes')

def apply_theme(app, use_dark_theme=None):
    """
    Apply a theme to the application.
    
    Args:
        app (QApplication): The application instance
        use_dark_theme (bool, optional): Whether to use dark theme.
            If None, will detect from system settings.
            
    Returns:
        None
    """
    if use_dark_theme is None:
        use_dark_theme = is_dark_mode()
    
    try:
        themes_dir = get_themes_dir()
        # Choose the appropriate stylesheet
        if use_dark_theme:
            # First check if dark_theme.py is actually a .qss file or a .py file
            dark_qss_path = os.path.join(themes_dir, 'dark_theme.qss')
            dark_py_path = os.path.join(themes_dir, 'dark_theme.py')
            
            if os.path.exists(dark_qss_path):
                with open(dark_qss_path, "r", encoding="utf-8") as f:
                    stylesheet_content = f.read()
            elif os.path.exists(dark_py_path):
                # If it's a .py file, we need to get the string content from it, not execute it
                with open(dark_py_path, "r", encoding="utf-8") as f:
                    stylesheet_content = f.read()
                # Remove Python code if present, keep only the string content
                if "'''" in stylesheet_content or '"""' in stylesheet_content:
                    # Extract string content between triple quotes
                    import re
                    match = re.search(r'(\'\'\'|""")(.+?)(\'\'\'|""")', stylesheet_content, re.DOTALL)
                    if match:
                        stylesheet_content = match.group(2)
            else:
                stylesheet_content = ""
        else:
            style_qss_path = os.path.join(themes_dir, 'style.qss')
            if os.path.exists(style_qss_path):
                with open(style_qss_path, "r", encoding="utf-8") as f:
                    stylesheet_content = f.read()
            else:
                stylesheet_content = ""
        
        # Apply the stylesheet
        app.setStyleSheet(stylesheet_content)
    except Exception as e:
        print(f"Error applying theme: {e}")
        # Fallback to a basic stylesheet if there's an error
        app.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #FFFFFF;
                color: #000000;
            }
        """)

def create_font(family="Segoe UI", size=10, weight=QFont.Weight.Normal):
    """
    Create a font with the specified properties.
    
    Args:
        family (str): Font family name
        size (int): Font size in points
        weight (QFont.Weight): Font weight
        
    Returns:
        QFont: The created font
    """
    font = QFont(family, size)
    font.setWeight(weight)
    return font 
