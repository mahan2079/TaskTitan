from PyQt6.QtCore import Qt, QRect
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont

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
        
        # Create layout and add title label
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # We'll draw the percentage in the paintEvent, directly in the circle
        # Instead, add the title label below the circle
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-size: 14px; color: #64748B; margin-top: 5px;")
        
        # Add spacer at top to position title label below the chart
        layout.addSpacing(120)  # Space for the circle
        layout.addWidget(self.title_label)
        
    def updateValue(self, value):
        """Update the progress value and redraw."""
        self.value = value
        self.percentage = (value / self.max_value) * 100 if self.max_value > 0 else 0
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
        
        # Draw percentage text in the middle of the circle
        percentage_text = f"{int(self.percentage)}%"
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        # Set text color based on progress
        if self.percentage < 30:
            painter.setPen(QColor("#EF4444"))  # Red for low progress
        elif self.percentage < 70:
            painter.setPen(QColor("#F59E0B"))  # Orange/Yellow for medium progress
        else:
            painter.setPen(QColor("#10B981"))  # Green for high progress
            
        # Center the text in the circle
        text_rect = rect
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, percentage_text)
        
        painter.end() 