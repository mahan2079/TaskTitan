"""
Daily planning view for TaskTitan.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QDate

class DailyView(QWidget):
    """Widget for daily planning."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate.currentDate()
        self.setupUI()
        
    def setupUI(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Date label
        self.date_label = QLabel(f"Daily View - {self.current_date.toString('MMMM d, yyyy')}")
        self.date_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        layout.addWidget(self.date_label)
        
        # Placeholder label
        self.placeholder_label = QLabel("Under Construction")
        self.placeholder_label.setStyleSheet("font-size: 16px; color: #6B7280;")
        layout.addWidget(self.placeholder_label)
        
        # Add stretch to push content to the top
        layout.addStretch()
    
    def setDate(self, date):
        """Set the current date for the view.
        
        Args:
            date (QDate or datetime.date): The date to display
        """
        if hasattr(date, 'toPyDate'):
            # It's a QDate
            self.current_date = date
            date_str = date.toString('MMMM d, yyyy')
            day_str = date.toString('dddd, MMMM d, yyyy')
        else:
            # It's a datetime.date
            self.current_date = QDate(date.year, date.month, date.day)
            date_str = date.strftime('%B %d, %Y')
            day_str = date.strftime('%A, %B %d, %Y')
        
        self.date_label.setText(f"Daily View - {date_str}")
        
        # In a full implementation, we would reload tasks and events for this date
        self.placeholder_label.setText(f"Daily plan for {day_str} - Under Construction") 