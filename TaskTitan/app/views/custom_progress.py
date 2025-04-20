from PyQt6.QtCore import Qt, QRect, QPointF, QRectF
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QLinearGradient, QRadialGradient, QPainterPath

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
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4B5563; margin-top: 5px;")
        
        # Add spacer at top to position title label below the chart
        layout.addSpacing(120)  # Space for the circle
        layout.addWidget(self.title_label)
        
    def updateValue(self, value):
        """Update the progress value and redraw."""
        self.value = value
        self.percentage = (value / self.max_value) * 100 if self.max_value > 0 else 0
        self.update()
        
    def getColorForPercentage(self, percentage):
        """Get vibrant color based on percentage."""
        if percentage < 30:
            return QColor("#FF4444")  # Brighter red
        elif percentage < 70:
            return QColor("#FFBB33")  # Brighter orange/yellow
        else:
            return QColor("#00C851")  # Brighter green
        
    def paintEvent(self, event):
        """Draw the circular progress chart with beautiful gradients."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        # Calculate scaling for responsive sizing
        min_dimension = min(width, height)
        
        # Make the chart 80% of the available space
        chart_size = min_dimension * 0.8
        
        # Create a rectangle for the chart
        rect = QRectF((width - chart_size) / 2, (height - chart_size) / 2, chart_size, chart_size)
        center = QPointF(rect.center())
        
        # Calculate angle span (full circle = 5760)
        span_angle = 5760 * (self.percentage / 100.0)
        
        # Draw background circle
        painter.setPen(QPen(QColor(230, 230, 230), 8))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)
        
        # Draw progress arc if progress > 0
        if self.percentage > 0:
            # Create the base color for progress
            base_color = self.getColorForPercentage(self.percentage)
            
            # Create gradient for progress arc
            progress_gradient = QLinearGradient(
                QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.bottom())
            )
            progress_gradient.setColorAt(0, base_color.lighter(120))
            progress_gradient.setColorAt(1, base_color)
            
            # Create a path for the progress arc
            progress_path = QPainterPath()
            progress_path.moveTo(center)
            # Use QRectF for arcTo
            progress_path.arcTo(rect, 90, -span_angle / 16)
            progress_path.lineTo(center)
            
            # Fill the progress arc with gradient
            painter.setBrush(progress_gradient)
            painter.drawPath(progress_path)
            
            # Add glossy highlight effect
            highlight_rect = QRectF(rect).adjusted(rect.width() * 0.2, rect.height() * 0.2, 
                                                 -rect.width() * 0.6, -rect.height() * 0.2)
            highlight_gradient = QLinearGradient(
                highlight_rect.topLeft(), highlight_rect.bottomRight()
            )
            highlight_gradient.setColorAt(0, QColor(255, 255, 255, 120))
            highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
            
            # Don't draw the highlight over the entire circle, just a portion
            painter.setBrush(highlight_gradient)
            painter.drawEllipse(highlight_rect)
            
        # Inner circle for the percentage text (lighter background)
        inner_circle = QRectF(rect).adjusted(25, 25, -25, -25)
        painter.setPen(Qt.PenStyle.NoPen)
        inner_gradient = QRadialGradient(center, inner_circle.width() / 2)
        inner_gradient.setColorAt(0, QColor(255, 255, 255, 240))
        inner_gradient.setColorAt(1, QColor(255, 255, 255, 180))
        painter.setBrush(inner_gradient)
        painter.drawEllipse(inner_circle)
        
        # Draw percentage text
        percentage_text = f"{int(self.percentage)}%"
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        # Set text color based on progress
        text_color = self.getColorForPercentage(self.percentage)
        painter.setPen(text_color)
            
        # Center the text
        painter.drawText(inner_circle, Qt.AlignmentFlag.AlignCenter, percentage_text)
        
        # Draw a small reflection highlight at the top
        painter.setPen(Qt.PenStyle.NoPen)
        # Create a simple highlight at the top without complex path
        highlight = QRectF(rect.x() + 25, rect.y() + 5, rect.width() - 50, 20)
        highlight_gradient = QRadialGradient(
            QPointF(highlight.center()), highlight.width() / 2
        )
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 70))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(highlight_gradient)
        painter.drawEllipse(highlight)
        
        painter.end() 