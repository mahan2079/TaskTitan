"""
Utility functions for handling resources in TaskTitan.
"""

import os
import darkdetect
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QPalette, QColor

# Constants
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
        # Choose the appropriate stylesheet
        if use_dark_theme:
            # First check if dark_theme.py is actually a .py file or a .qss file
            if os.path.exists("app/themes/dark_theme.qss"):
                with open("app/themes/dark_theme.qss", "r") as f:
                    stylesheet_content = f.read()
            else:
                # If it's a .py file, we need to get the string content from it, not execute it
                with open("app/themes/dark_theme.py", "r") as f:
                    stylesheet_content = f.read()
                # Remove Python code if present, keep only the string content
                if "'''" in stylesheet_content or '"""' in stylesheet_content:
                    # Extract string content between triple quotes
                    import re
                    match = re.search(r'(\'\'\'|""")(.+?)(\'\'\'|""")', stylesheet_content, re.DOTALL)
                    if match:
                        stylesheet_content = match.group(2)
        else:
            with open("app/themes/style.qss", "r") as f:
                stylesheet_content = f.read()
        
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