from PyQt6.QtCore import Qt, QRect
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush

class CircularProgressChart(QWidget):
    """A circular progress chart widget that displays percentage completion."""
    
    def __init__(self, title, value, max_value=100, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.max_value = max_value
        self.percentage = (value / max_value) * 100 if max_value > 0 else 0
        self.setMinimumSize(140, 180)
        self.setMaximumWidth(200)
        
        # Create layout and add title and value labels
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.value_label = QLabel(f"{int(self.percentage)}%")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4F46E5;")
        
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 14px; color: #64748B;")
        
        # Add spacer at top to position labels below the chart
        layout.addSpacing(100)
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        
    def updateValue(self, value):
        """Update the progress value and redraw."""
        self.value = value
        self.percentage = (value / self.max_value) * 100 if self.max_value > 0 else 0
        self.value_label.setText(f"{int(self.percentage)}%")
        self.update()
        
    def paintEvent(self, event):
        """Draw the circular progress chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Define the rectangle for the chart using QRect instead of QRectF
        rect = QRect(20, 10, 100, 100)
        
        # Calculate the span angle for the progress arc (360 * percentage / 100)
        span_angle = int(360 * self.percentage / 100) * 16  # Qt uses 16ths of a degree
        
        # Draw background circle
        painter.setPen(QPen(QColor("#E2E8F0"), 10, Qt.PenStyle.SolidLine))
        painter.drawArc(rect, 0, 360 * 16)  # Full circle (360 degrees)
        
        # Draw progress arc
        if self.percentage > 0:
            # Use different colors based on completion percentage
            if self.percentage < 30:
                color = QColor("#EF4444")  # Red for low progress
            elif self.percentage < 70:
                color = QColor("#F59E0B")  # Orange/Yellow for medium progress
            else:
                color = QColor("#10B981")  # Green for high progress
                
            painter.setPen(QPen(color, 10, Qt.PenStyle.SolidLine))
            painter.drawArc(rect, 90 * 16, -span_angle)  # Start from top (90 degrees)
        
        painter.end() 