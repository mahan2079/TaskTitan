"""
Productivity tracking view for TaskTitan.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ProductivityView(QWidget):
    """Widget for tracking productivity."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        
    def setupUI(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Placeholder label
        label = QLabel("Productivity View - Under Construction")
        label.setStyleSheet("font-size: 18px; color: #6B7280;")
        layout.addWidget(label) 