"""
Color resources for TaskTitan.

This module defines the color palette for the application.
"""

from PyQt6.QtGui import QColor

# Main color palette
PRIMARY = QColor("#6366F1")       # Indigo
SECONDARY = QColor("#8B5CF6")     # Purple
ACCENT = QColor("#EC4899")        # Pink
INFO = QColor("#3B82F6")          # Blue
SUCCESS = QColor("#10B981")       # Green
WARNING = QColor("#F59E0B")       # Amber
DANGER = QColor("#EF4444")        # Red

# Background colors
BG_LIGHT = QColor("#F8FAFC")
BG_DARK = QColor("#1E293B")

# Text colors
TEXT_LIGHT = QColor("#F8FAFC")
TEXT_DARK = QColor("#0F172A")
TEXT_MUTED = QColor("#64748B")

# Border colors
BORDER_LIGHT = QColor("#E2E8F0")
BORDER_DARK = QColor("#334155")

class ColorPalette:
    """Color palette for the application."""
    
    def __init__(self, is_dark_mode=False):
        """
        Initialize the color palette.
        
        Args:
            is_dark_mode (bool): Whether to use dark mode colors
        """
        self.is_dark_mode = is_dark_mode
        
    @property
    def background(self):
        """Get the appropriate background color based on the theme."""
        return BG_DARK if self.is_dark_mode else BG_LIGHT
    
    @property
    def text(self):
        """Get the appropriate text color based on the theme."""
        return TEXT_LIGHT if self.is_dark_mode else TEXT_DARK
    
    @property
    def border(self):
        """Get the appropriate border color based on the theme."""
        return BORDER_DARK if self.is_dark_mode else BORDER_LIGHT
    
    @property
    def primary(self):
        """Primary color for buttons and accents."""
        return PRIMARY
    
    @property
    def secondary(self):
        """Secondary color for buttons and accents."""
        return SECONDARY
    
    @property
    def accent(self):
        """Accent color for highlights."""
        return ACCENT
    
    @property
    def info(self):
        """Info color for informational elements."""
        return INFO
    
    @property
    def success(self):
        """Success color for positive feedback."""
        return SUCCESS
    
    @property
    def warning(self):
        """Warning color for cautionary elements."""
        return WARNING
    
    @property
    def danger(self):
        """Danger color for error states."""
        return DANGER
    
    @property
    def text_muted(self):
        """Muted text color for less important text."""
        return TEXT_MUTED
    
    def get_hex(self, color_attr):
        """
        Get a color as a hex string.
        
        Args:
            color_attr (str): Name of the color attribute
            
        Returns:
            str: Hex color code (e.g. "#RRGGBB")
        """
        if hasattr(self, color_attr):
            color = getattr(self, color_attr)
            if isinstance(color, QColor):
                return color.name()
        return None 