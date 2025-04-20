"""
Daily planning view for TaskTitan.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QDate, Qt

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

    def onStatusChanged(self, item_id, is_completed):
        """Handle when a task item's status changes."""
        # Update the UI to reflect the status change
        try:
            # Find labels within the item widget
            # Note: findChild returns a single object, so we need to use findChildren to get a list
            labels = self.findChildren(QLabel, "", options=Qt.FindChildOption.FindChildrenRecursively)
            
            # Find the labels associated with this item
            desc_label = None
            for label in labels:
                # Check if this label belongs to the item widget that emitted the signal
                if label.parent() and hasattr(label.parent(), 'property'):
                    item_widget_id = label.parent().property("item_id")
                    if item_widget_id == item_id and not desc_label:
                        desc_label = label
                        break
            
            # Update the label style based on completion status
            if desc_label:
                if is_completed:
                    desc_label.setStyleSheet("text-decoration: line-through; color: #9CA3AF;")
                else:
                    desc_label.setStyleSheet("")
            
            # Update the database
            if hasattr(self, 'conn') and self.conn:
                try:
                    self.cursor.execute(
                        "UPDATE events SET completed = ? WHERE id = ?", 
                        (1 if is_completed else 0, item_id)
                    )
                    self.conn.commit()
                except Exception as e:
                    print(f"Error updating event status in database: {e}")
        except Exception as e:
            print(f"Error in onStatusChanged: {e}") 