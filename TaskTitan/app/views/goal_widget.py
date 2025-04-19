"""
Goal management widget for TaskTitan.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class GoalWidget(QWidget):
    """Widget for managing goals."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        
    def setupUI(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Placeholder label
        label = QLabel("Goals Widget - Under Construction")
        label.setStyleSheet("font-size: 18px; color: #6B7280;")
        layout.addWidget(label) 