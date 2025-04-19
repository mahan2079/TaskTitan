"""
Settings dialog for TaskTitan.
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel

class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        
    def setupUI(self):
        """Set up the UI components."""
        self.setWindowTitle("Settings")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Placeholder label
        label = QLabel("Settings - Under Construction")
        label.setStyleSheet("font-size: 18px; color: #6B7280;")
        layout.addWidget(label) 