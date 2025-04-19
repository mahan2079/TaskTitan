from PyQt6.QtWidgets import QCalendarWidget, QWidget, QVBoxLayout, QLabel, QGridLayout, QSizePolicy
from PyQt6.QtCore import Qt, QDate, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPalette

class ModernCalendarWidget(QCalendarWidget):
    """A modern styled calendar widget for TaskTitan."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up modern appearance
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)
        self.setNavigationBarVisible(True)
        self.setDateEditEnabled(False)
        self.setGridVisible(False)
        self.setSelectionMode(QCalendarWidget.SelectionMode.SingleSelection)
        
        # Set default size
        self.setFixedHeight(300)
        
        # Set custom styling
        self.initStyleSheet()
        
        # Mark current date with a different color
        self.setSelectedDate(QDate.currentDate())
        
        # Custom events for this date
        self.events = {}
        
    def initStyleSheet(self):
        """Initialize custom style sheet for calendar."""
        self.setStyleSheet("""
            QCalendarWidget {
                background-color: #ffffff;
                border: none;
            }
            
            QCalendarWidget QToolButton {
                color: #1E293B;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 6px;
                font-size: 14px;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: #EEF2FF;
            }
            
            QCalendarWidget QToolButton:pressed {
                background-color: #C7D2FE;
            }
            
            QCalendarWidget QMenu {
                width: 150px;
                background-color: white;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
            }
            
            QCalendarWidget QMenu::item {
                padding: 6px 12px;
                border-radius: 2px;
            }
            
            QCalendarWidget QMenu::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
            
            QCalendarWidget QSpinBox {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 3px;
                font-size: 14px;
                selection-background-color: #EEF2FF;
                selection-color: #4F46E5;
            }
            
            QCalendarWidget QAbstractItemView:enabled {
                color: #1E293B;
                selection-background-color: #EEF2FF;
                selection-color: #4F46E5;
                outline: 0;
            }
            
            QCalendarWidget QAbstractItemView:disabled {
                color: #9CA3AF;
            }
            
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #ffffff;
                border-bottom: 1px solid #E5E7EB;
                padding: 4px;
            }
        """)
        
    def paintCell(self, painter, rect, date):
        """Custom paint method for calendar cells."""
        # Call the base method to draw the basic cell
        super().paintCell(painter, rect, date)
        
        painter.save()
        
        # Get current date for comparison
        current_date = QDate.currentDate()
        selected_date = self.selectedDate()
        
        # Clear background first
        if date == selected_date:
            # Selected date
            painter.fillRect(rect, QColor("#EEF2FF"))
            painter.setPen(QPen(QColor("#4F46E5")))
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 5, 5)
        elif date == current_date:
            # Today's date
            painter.fillRect(rect, QColor("#F1F5F9"))
            painter.setPen(QPen(QColor("#6366F1")))
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 5, 5)
            
        # Check if this date has events
        date_str = date.toString("yyyy-MM-dd")
        if date_str in self.events:
            event_count = self.events[date_str]
            
            # Draw event indicator dot
            if event_count > 0:
                dot_color = QColor("#6366F1")  # Primary color
                dot_radius = 3
                
                # Position at the bottom of the cell
                center_x = rect.center().x()
                bottom_y = rect.bottom() - 5
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(dot_color))
                painter.drawEllipse(center_x - dot_radius, bottom_y - dot_radius, 
                                   dot_radius * 2, dot_radius * 2)
                
                # If more than one event, draw additional dot(s)
                if event_count > 1:
                    painter.drawEllipse(center_x - dot_radius - 8, bottom_y - dot_radius, 
                                       dot_radius * 2, dot_radius * 2)
                
                if event_count > 2:
                    painter.drawEllipse(center_x - dot_radius + 8, bottom_y - dot_radius, 
                                       dot_radius * 2, dot_radius * 2)
        
        painter.restore()
        
    def setEvents(self, events_data):
        """Set events data for the calendar.
        
        Args:
            events_data: Dictionary with dates as keys (format: 'yyyy-MM-dd') and 
                         number of events as values.
        """
        self.events = events_data
        self.updateCells()
        
    def sizeHint(self):
        """Suggested size for the widget."""
        return QSize(400, 300)
        
    def minimumSizeHint(self):
        """Minimum suggested size for the widget."""
        return QSize(280, 220) 