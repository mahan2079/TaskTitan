from PyQt6.QtWidgets import QCalendarWidget, QWidget, QVBoxLayout, QLabel, QGridLayout, QSizePolicy, QScrollArea, QFrame, QHBoxLayout
from PyQt6.QtWidgets import QDialog, QPushButton, QLineEdit, QComboBox, QTimeEdit, QDialogButtonBox, QFormLayout, QColorDialog
from PyQt6.QtCore import Qt, QDate, QSize, pyqtSignal, QPointF, QTime
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPalette, QLinearGradient, QFont, QRadialGradient

# Import ActivityAddEditDialog for consistency across the application
from app.views.unified_activities_widget import ActivityAddEditDialog

class EventDialog(QDialog):
    """Dialog for adding or editing calendar events."""
    
    def __init__(self, parent=None, event_date=None):
        super().__init__(parent)
        self.setWindowTitle("Add Event")
        self.resize(420, 350)
        self.setModal(True)  # Make sure dialog is modal and blocks input to other windows
        
        self.event_date = event_date or QDate.currentDate()
        
        # Create a more modern layout
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
            QLabel {
                color: #1E293B;
                font-size: 14px;
            }
            QLineEdit, QTimeEdit, QComboBox {
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 10px;
                background-color: #F8FAFC;
                color: #334155;
                font-size: 14px;
                selection-background-color: #DBEAFE;
            }
            QLineEdit:focus, QTimeEdit:focus, QComboBox:focus {
                border-color: #93C5FD;
                background-color: white;
            }
        """)
        
        # Main layout with padding
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)  # Increase spacing for better readability
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Event title with better styling
        title_label = QLabel("Title:")
        title_label.setStyleSheet("font-weight: bold;")
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter event title")
        self.title_edit.setMinimumHeight(40)  # Make input fields taller
        
        form_layout.addRow(title_label, self.title_edit)
        
        # Event time
        time_label = QLabel("Time:")
        time_label.setStyleSheet("font-weight: bold;")
        
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setMinimumHeight(40)
        
        form_layout.addRow(time_label, self.time_edit)
        
        # Event type/category
        category_label = QLabel("Category:")
        category_label.setStyleSheet("font-weight: bold;")
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Work", "Personal", "Meeting", "Reminder", "Other"])
        self.category_combo.setMinimumHeight(40)
        
        form_layout.addRow(category_label, self.category_combo)
        
        # Event color with improved UI
        color_label = QLabel("Color:")
        color_label.setStyleSheet("font-weight: bold;")
        
        color_container = QWidget()
        color_layout = QHBoxLayout(color_container)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(10)
        
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(120, 40)
        self.current_color = QColor("#6366F1")  # Default color
        self.update_color_button()
        self.color_btn.clicked.connect(self.select_color)
        
        # Add color preview box
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(40, 40)
        self.color_preview.setStyleSheet(f"""
            background-color: {self.current_color.name()};
            border-radius: 8px;
            border: 1px solid #CBD5E1;
        """)
        
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_btn)
        
        form_layout.addRow(color_label, color_container)
        
        # Date display (read-only) with clear styling
        date_label = QLabel("Date:")
        date_label.setStyleSheet("font-weight: bold;")
        
        self.date_display = QLabel(self.event_date.toString("dddd, MMMM d, yyyy"))
        self.date_display.setStyleSheet("""
            font-weight: bold;
            color: #4F46E5;
            background-color: #EEF2FF;
            padding: 10px;
            border-radius: 8px;
        """)
        
        form_layout.addRow(date_label, self.date_display)
        
        # Add form layout to main layout
        main_layout.addLayout(form_layout)
        
        # Add spacer for better layout
        main_layout.addSpacing(10)
        
        # Button container with modern styling
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(15)
        
        # Cancel button with flat modern style
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(45)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #475569;
                border: none;
                border-radius: 8px;
                padding: 12px 25px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
            QPushButton:pressed {
                background-color: #CBD5E1;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        # Save button with gradient
        self.save_btn = QPushButton("Save Event")
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 25px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #7C3AED);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338CA, stop:1 #6D28D9);
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        
        # Add buttons to layout
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addWidget(button_container)
        
        # Set title as initial focus
        self.title_edit.setFocus()
    
    def select_color(self):
        """Open color dialog to select event color."""
        color = QColorDialog.getColor(self.current_color, self, "Select Event Color")
        if color.isValid():
            self.current_color = color
            self.update_color_button()
            # Update the color preview as well
            self.color_preview.setStyleSheet(f"""
                background-color: {self.current_color.name()};
                border-radius: 8px;
                border: 1px solid #CBD5E1;
            """)
    
    def update_color_button(self):
        """Update color button appearance with selected color."""
        self.color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                font-weight: bold;
                color: #334155;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #F8FAFC;
                border-color: #93C5FD;
            }}
        """)
        self.color_btn.setText("Choose Color")
    
    def get_event_data(self):
        """Return the event data."""
        return {
            "title": self.title_edit.text(),
            "time": self.time_edit.time(),
            "category": self.category_combo.currentText(),
            "color": self.current_color,
            "date": self.event_date
        }


class ModernCalendarWidget(QCalendarWidget):
    """A modern styled calendar widget for TaskTitan."""
    
    eventClicked = pyqtSignal(dict)  # Signal emitted when an event is clicked
    dateDoubleClicked = pyqtSignal(QDate)  # Signal emitted when a date is double-clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up modern appearance
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)
        self.setNavigationBarVisible(True)
        self.setDateEditEnabled(False)
        self.setGridVisible(False)
        self.setSelectionMode(QCalendarWidget.SelectionMode.SingleSelection)
        
        # Custom properties
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.today_color = QColor("#6366F1")  # Indigo color for today
        self.weekend_color = QColor("#EEF2FF")  # Light indigo for weekends
        self.selection_color = QColor("#818CF8")  # Light indigo for selection
        self.event_colors = [
            QColor("#F87171"),  # Red
            QColor("#FBBF24"),  # Amber
            QColor("#34D399"),  # Emerald
            QColor("#60A5FA"),  # Blue
            QColor("#A78BFA")   # Purple
        ]
        
        # Set default size
        self.setFixedHeight(550)  # Make calendar even taller
        
        # Set custom styling
        self.initStyleSheet()
        
        # Mark current date with a different color
        self.setSelectedDate(QDate.currentDate())
        
        # Enhanced events dictionary: date_str -> list of event dictionaries
        self.events = {}
        
        # Generate some sample events
        self.generateSampleEvents()
        
        # Connect signals
        self.activated.connect(self.onDateDoubleClicked)
        
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events on the calendar."""
        super().mouseDoubleClickEvent(event)
        # Get the date at the clicked position - more reliable than using selectedDate
        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        date = self.selectedDate()
        self.dateDoubleClicked.emit(date)
        
    def onDateDoubleClicked(self, date):
        """Handle date double click to add a new event."""
        dialog = EventDialog(self, date)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event_data = dialog.get_event_data()
            self.addEvent(event_data)
            
    def addEvent(self, event_data):
        """Add a new event to the calendar.
        
        Args:
            event_data: Dictionary containing event details
        """
        date_str = event_data["date"].toString("yyyy-MM-dd")
        
        if date_str not in self.events:
            self.events[date_str] = []
            
        self.events[date_str].append(event_data)
        self.updateCells()
        
    def generateSampleEvents(self):
        """Generate sample events for the calendar."""
        current_date = QDate.currentDate()
        current_month = current_date.month()
        current_year = current_date.year()
        
        # Create meaningful sample events
        sample_events = [
            {
                "date": QDate(current_year, current_month, 3),
                "title": "Team Meeting",
                "time": QTime(10, 0),
                "category": "Meeting",
                "color": self.event_colors[0]
            },
            {
                "date": QDate(current_year, current_month, 7),
                "title": "Project Deadline",
                "time": QTime(15, 0),
                "category": "Work",
                "color": self.event_colors[1]
            },
            {
                "date": QDate(current_year, current_month, 12),
                "title": "Doctor Appointment",
                "time": QTime(9, 30),
                "category": "Personal",
                "color": self.event_colors[2]
            },
            {
                "date": QDate(current_year, current_month, 15),
                "title": "Birthday Party",
                "time": QTime(18, 0),
                "category": "Personal",
                "color": self.event_colors[3]
            },
            {
                "date": current_date,
                "title": "Complete TaskTitan",
                "time": QTime(14, 0),
                "category": "Work",
                "color": self.event_colors[4]
            }
        ]
        
        # Add events to the calendar
        for event in sample_events:
            date_str = event["date"].toString("yyyy-MM-dd")
            if date_str not in self.events:
                self.events[date_str] = []
            self.events[date_str].append(event)
        
    def initStyleSheet(self):
        """Initialize custom style sheet for calendar."""
        self.setStyleSheet("""
            QCalendarWidget {
                background-color: #ffffff;
                border: none;
            }
            
            QCalendarWidget QToolButton {
                color: #4F46E5;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 8px;
                font-size: 15px;
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
                border-radius: 8px;
            }
            
            QCalendarWidget QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            
            QCalendarWidget QMenu::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
            
            QCalendarWidget QSpinBox {
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 4px;
                font-size: 14px;
                selection-background-color: #EEF2FF;
                selection-color: #4F46E5;
            }
            
            QCalendarWidget QAbstractItemView:enabled {
                color: #1E293B;
                font-size: 14px;
                font-weight: 500;
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
                padding: 8px;
            }
            
            /* Make headers stand out more */
            QCalendarWidget QTableView QHeaderView {
                background-color: #F8FAFC;
            }
            
            QCalendarWidget QTableView QHeaderView::section {
                color: #6366F1; 
                font-weight: bold;
                font-size: 14px;
                padding: 6px;
                background-color: #F1F5F9;
                border: none;
            }
        """)
        
    def paintCell(self, painter, rect, date):
        """Custom paint method for calendar cells."""
        painter.save()
        
        # Get current date for comparison
        current_date = QDate.currentDate()
        selected_date = self.selectedDate()
        
        # Clear background first
        painter.fillRect(rect, QColor(255, 255, 255))
        
        # Handle weekends
        if date.dayOfWeek() >= 6:  # Saturday or Sunday
            gradient = QLinearGradient(
                QPointF(rect.topLeft()), QPointF(rect.bottomRight())
            )
            gradient.setColorAt(0, self.weekend_color.lighter(107))
            gradient.setColorAt(1, self.weekend_color)
            painter.fillRect(rect, gradient)
            
        # Special styling for today
        if date == current_date:
            # Draw gradient background for today
            today_gradient = QLinearGradient(
                QPointF(rect.topLeft()), QPointF(rect.bottomRight())
            )
            today_gradient.setColorAt(0, self.today_color.lighter(130))
            today_gradient.setColorAt(1, self.today_color.lighter(150))
            
            painter.fillRect(rect, today_gradient)
            
            # Draw border with rounded corners
            painter.setPen(QPen(self.today_color, 2))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)
            
            # Set text color
            painter.setPen(QColor(255, 255, 255))
        
        # Selected date styling
        elif date == selected_date:
            # Draw gradient background for selected date
            select_gradient = QLinearGradient(
                QPointF(rect.topLeft()), QPointF(rect.bottomRight())
            )
            select_gradient.setColorAt(0, self.selection_color.lighter(120))
            select_gradient.setColorAt(1, self.selection_color)
            
            painter.fillRect(rect, select_gradient)
            
            # Draw border with rounded corners
            painter.setPen(QPen(self.selection_color.darker(110), 2))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)
            
            # Set text color
            painter.setPen(QColor(255, 255, 255))
            
        else:
            # Default text color
            painter.setPen(QColor(30, 41, 59))  # Default dark color
            
        # Draw the date text with improved font
        font = painter.font()
        font.setPointSize(11)
        
        if date == current_date or date == selected_date:
            font.setBold(True)
            
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(date.day()))
            
        # Check if this date has events
        date_str = date.toString("yyyy-MM-dd")
        if date_str in self.events:
            event_list = self.events[date_str]
            event_count = len(event_list)
            
            # Draw colorful event indicators - improved smaller version
            if event_count > 0:
                # Event dots container at the bottom of the cell
                dot_y = rect.bottom() - 8  # Moved up a bit to be less obtrusive
                
                # Limit to max 5 dots
                displayed_count = min(event_count, 5)
                
                # Calculate width based on number of dots
                total_width = (displayed_count * 5) + ((displayed_count - 1) * 2)  # dots + spaces
                start_x = rect.center().x() - (total_width / 2)
                
                for i in range(displayed_count):
                    # Use the event's color for the dot
                    if i < len(event_list):
                        dot_color = event_list[i].get("color", self.event_colors[i % len(self.event_colors)])
                    else:
                        # Fallback to default colors if we somehow have more events than details
                        color_index = i % len(self.event_colors)
                        dot_color = self.event_colors[color_index]
                    
                    # Create a radial gradient for each dot - smaller, cleaner dots
                    center_x = start_x + (i * 7)  # Tighter spacing
                    center = QPointF(center_x, dot_y)
                    
                    # Smaller dots with subtle border
                    painter.setPen(QPen(dot_color.darker(120), 0.5))
                    dot_gradient = QRadialGradient(center, 2.5)  # Smaller size
                    dot_gradient.setColorAt(0, dot_color.lighter(120))
                    dot_gradient.setColorAt(1, dot_color)
                    
                    # Draw dot
                    painter.setBrush(dot_gradient)
                    painter.drawEllipse(center, 2.5, 2.5)  # Smaller dots
                
                # If we have more events than can be displayed, add a "more" indicator
                if event_count > 5:
                    more_x = start_x + (displayed_count * 7) + 3
                    painter.setPen(QColor(100, 100, 100, 180))
                    painter.drawText(QPointF(more_x, dot_y + 3), "+")
        
        painter.restore()
        
    def setEvents(self, events_data):
        """Set events data for the calendar.
        
        Args:
            events_data: Dictionary with dates as keys (format: 'yyyy-MM-dd') and 
                         list of event dictionaries as values.
        """
        self.events = events_data
        self.updateCells()
        
    def getEvents(self, date):
        """Get events for a specific date.
        
        Args:
            date: QDate object
            
        Returns:
            List of event dictionaries for the date, or empty list if none
        """
        date_str = date.toString("yyyy-MM-dd")
        return self.events.get(date_str, [])
        
    def sizeHint(self):
        """Suggested size for the widget."""
        return QSize(500, 550)
        
    def minimumSizeHint(self):
        """Minimum suggested size for the widget."""
        return QSize(300, 400) 


class CalendarWithEventList(QWidget):
    """Widget combining a calendar with an event list display."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Store reference to main window (if available through parent chain)
        self.main_window = self.findMainWindow()
        
        # Main layout - change to horizontal layout for side-by-side
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Create calendar widget
        self.calendar = ModernCalendarWidget()
        layout.addWidget(self.calendar)
        
        # Create events section - now beside the calendar
        self.events_widget = QWidget()
        self.events_widget.setMinimumWidth(300)  # Ensure events panel has sufficient width
        events_layout = QVBoxLayout(self.events_widget)
        events_layout.setContentsMargins(0, 0, 0, 10)  # Add bottom padding
        
        self.events_header = QLabel("Events")
        self.events_header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #4F46E5;
            margin-bottom: 10px;
            padding-left: 5px;
        """)
        events_layout.addWidget(self.events_header)
        
        # Add a scroll area for events
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #F1F5F9;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #94A3B8;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #64748B;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Container widget for events inside scroll area
        events_container = QWidget()
        self.events_grid = QGridLayout(events_container)
        self.events_grid.setContentsMargins(5, 5, 5, 5)
        self.events_grid.setSpacing(10)
        
        scroll_area.setWidget(events_container)
        events_layout.addWidget(scroll_area)
        
        # Add event button - make it more prominent and modern
        self.add_button = QPushButton("+ Add New Event")
        self.add_button.setMinimumHeight(48)  # Make button taller
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 16px;
                font-weight: bold;
                font-size: 15px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
            QPushButton:pressed {
                background-color: #4338CA;
            }
        """)
        events_layout.addWidget(self.add_button)
        
        layout.addWidget(self.events_widget)
        
        # Adjust size policies for side-by-side layout
        self.calendar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.events_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        # Set the split between calendar and events (approximately 60/40)
        layout.setStretchFactor(self.calendar, 60)
        layout.setStretchFactor(self.events_widget, 40)
        
        # Connect signals
        self.calendar.selectionChanged.connect(self.updateEventsList)
        self.calendar.dateDoubleClicked.connect(self.addEvent)
        self.add_button.clicked.connect(self.addEvent)
        
        # Load synchronized activities initially
        self.syncWithActivitiesManager()
        
        # Initial update
        self.updateEventsList()
        
    def findMainWindow(self):
        """Find the main window by traversing parent hierarchy."""
        parent = self.parent()
        while parent is not None:
            if parent.__class__.__name__ == "TaskTitanApp":
                return parent
            parent = parent.parent()
        return None
    
    def syncWithActivitiesManager(self):
        """Sync events with the activities manager database."""
        if not self.main_window:
            # Use sample events in standalone mode
            return
        
        try:
            # Clear existing events first
            self.calendar.events = {}
            
            # Get activities from the UnifiedActivitiesView
            activities_view = self.main_window.activitiesView
            
            if not hasattr(activities_view, 'activities'):
                print("No activities found in the main system")
                return
                
            # Iterate through all activities
            for activity_type in activities_view.activities:
                for activity in activities_view.activities[activity_type]:
                    # Only process events (type 'event')
                    if activity_type == 'event':
                        # Extract date and convert to QDate
                        if 'date' in activity:
                            # Handle different date formats
                            if isinstance(activity['date'], QDate):
                                date = activity['date']
                            elif isinstance(activity['date'], str):
                                date = QDate.fromString(activity['date'], "yyyy-MM-dd")
                            else:
                                # Skip if date format is unknown
                                continue
                                
                            # Create the calendar event
                            event_data = {
                                "id": activity.get('id', None),
                                "title": activity.get('title', 'Untitled'),
                                "date": date,
                                "time": activity.get('start_time', QTime(0, 0)),
                                "category": activity.get('category', 'Other'),
                                "color": self.getCategoryColor(activity.get('category', 'Other')),
                                "activity_data": activity  # Store original activity data
                            }
                            
                            # Add to the calendar
                            date_str = date.toString("yyyy-MM-dd")
                            if date_str not in self.calendar.events:
                                self.calendar.events[date_str] = []
                            
                            self.calendar.events[date_str].append(event_data)
            
            # Update the calendar display
            self.calendar.updateCells()
            
        except Exception as e:
            print(f"Error syncing with activities manager: {e}")
            
    def sync_with_activities(self, activities_manager):
        """Sync calendar with activities from the provided activities manager.
        
        Args:
            activities_manager: An instance of ActivitiesManager 
        """
        try:
            # Clear existing events first
            self.calendar.events = {}
            
            # Get all activities
            if activities_manager:
                activities = activities_manager.get_all_activities()
                
                # Process activities and add events to calendar
                for activity in activities:
                    # Only process events
                    if activity.get('type') == 'event':
                        # Extract date
                        date = activity.get('date')
                        if isinstance(date, str):
                            date = QDate.fromString(date, "yyyy-MM-dd")
                            
                        # Create calendar event object
                        event_data = {
                            "id": activity.get('id'),
                            "title": activity.get('title', 'Untitled'),
                            "date": date,
                            "time": activity.get('start_time', QTime(0, 0)),
                            "category": activity.get('category', 'Other'),
                            "color": self.getCategoryColor(activity.get('category', 'Other')),
                            "activity_data": activity  # Store original data
                        }
                        
                        # Add to calendar events
                        date_str = date.toString("yyyy-MM-dd")
                        if date_str not in self.calendar.events:
                            self.calendar.events[date_str] = []
                        
                        self.calendar.events[date_str].append(event_data)
            
            # Update calendar display
            self.calendar.updateCells()
            # Update events list if a date is selected
            self.updateEventsList()
            
        except Exception as e:
            print(f"Error syncing calendar with activities: {e}")
    
    def getCategoryColor(self, category):
        """Get color for a specific category."""
        # Basic category to color mapping
        category_colors = {
            "Work": QColor("#F87171"),  # Red
            "Personal": QColor("#FBBF24"),  # Amber
            "Meeting": QColor("#34D399"),  # Emerald
            "Health": QColor("#60A5FA"),  # Blue
            "Other": QColor("#A78BFA")   # Purple
        }
        
        # Return the color for the category, or default color if not found
        return category_colors.get(category, QColor("#6366F1"))

    def updateEventsList(self):
        """Update the events list for the selected date."""
        selected_date = self.calendar.selectedDate()
        events = self.calendar.getEvents(selected_date)
        
        # Clear current events grid
        while self.events_grid.count():
            item = self.events_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Update header with date
        self.events_header.setText(f"Events for {selected_date.toString('MMMM d, yyyy')}")
        
        if not events:
            # Show a message when no events
            no_events_label = QLabel("No events for this date")
            no_events_label.setStyleSheet("""
                color: #94A3B8;
                font-style: italic;
                padding: 10px;
                font-size: 14px;
            """)
            no_events_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.events_grid.addWidget(no_events_label, 0, 0, 1, 4)
            return
        
        # Add events to grid
        for row, event in enumerate(events, 1):
            # Create a modern card-style container for each event
            event_card = QFrame()
            event_card.setObjectName("event-card")
            event_card.setStyleSheet("""
                #event-card {
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #E2E8F0;
                    margin: 2px 0;
                }
                #event-card:hover {
                    border-color: #CBD5E1;
                    background-color: #F8FAFC;
                }
            """)
            
            # Set a maximum height for the card to make it more compact
            event_card.setMaximumHeight(70)
            
            # Use a horizontal layout for the event card content
            card_layout = QHBoxLayout(event_card)
            card_layout.setContentsMargins(8, 5, 8, 5)  # Reduce margins
            card_layout.setSpacing(6)  # Reduce spacing
            
            # Left side with time and color indicator
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(2)  # Reduce spacing
            left_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            
            # Time display
            time_str = event.get("time").toString("hh:mm AP")
            time_label = QLabel(time_str)
            time_label.setStyleSheet("""
                font-weight: bold;
                color: #1E293B;
                font-size: 11px;  /* Reduced font size */
            """)
            
            # Category with color indicator
            color = event.get("color", QColor("#6366F1"))
            category = event.get("category", "")
            
            # Create a frame with the category color
            color_indicator = QFrame()
            color_indicator.setFixedSize(40, 4)  # Smaller indicator
            color_indicator.setStyleSheet(f"""
                background-color: {color.name()};
                border-radius: 2px;
            """)
            
            # Category label
            category_label = QLabel(category)
            category_label.setStyleSheet("""
                color: #64748B;
                font-size: 10px;  /* Reduced font size */
            """)
            
            # Add to left section
            left_layout.addWidget(time_label)
            left_layout.addWidget(color_indicator)
            left_layout.addWidget(category_label)
            
            # Middle section with title
            title_widget = QWidget()
            title_layout = QVBoxLayout(title_widget)
            title_layout.setContentsMargins(0, 0, 0, 0)
            title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            
            title_label = QLabel(event.get("title", ""))
            title_label.setStyleSheet("""
                font-size: 12px;  /* Reduced font size */
                color: #334155;
                font-weight: 500;
            """)
            title_label.setWordWrap(True)
            title_layout.addWidget(title_label)
            
            # Right section with action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(4)  # Reduce spacing
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Edit button
            edit_btn = QPushButton()
            edit_btn.setToolTip("Edit Event")
            edit_btn.setFixedSize(24, 24)  # Smaller button
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #EFF6FF;
                    border: 1px solid #BFDBFE;
                    border-radius: 5px;
                    padding: 1px;
                    font-size: 12px;  /* Reduced font size */
                }
                QPushButton:hover {
                    background-color: #DBEAFE;
                }
            """)
            # Font-based icon as a simple edit pencil
            edit_btn.setText("✎")
            edit_btn.clicked.connect(lambda checked, e=event: self.editEvent(e))
            
            # Delete button
            delete_btn = QPushButton()
            delete_btn.setToolTip("Delete Event")
            delete_btn.setFixedSize(24, 24)  # Smaller button
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 5px;
                    padding: 1px;
                    font-size: 12px;  /* Reduced font size */
                }
                QPushButton:hover {
                    background-color: #FEE2E2;
                }
            """)
            # Font-based icon as a simple X
            delete_btn.setText("✕")
            delete_btn.clicked.connect(lambda checked, e=event: self.deleteEvent(e))
            
            # Add buttons to actions container
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            
            # Add the three sections to the card layout
            card_layout.addWidget(left_widget, 1)
            card_layout.addWidget(title_widget, 2)
            card_layout.addWidget(actions_widget, 1)
            
            # Add event card to the main grid - span all columns
            self.events_grid.addWidget(event_card, row, 0, 1, 4)
    
    def addEvent(self, date=None):
        """Open dialog to add a new event."""
        if not date:
            date = self.calendar.selectedDate()
        
        # Check if connected to main app and use ActivityAddEditDialog for consistency
        if self.main_window and hasattr(self.main_window, 'activities_manager'):
            # Create event activity data with default values
            activity_data = {
                'type': 'event',
                'title': '',
                'date': date,
                'start_time': QTime.currentTime(),
                'end_time': QTime.currentTime().addSecs(3600),  # Default 1 hour duration
                'category': 'Other',
                'color': '#6366F1'  # Default color
            }
            
            # Use the ActivityAddEditDialog for consistency with activities view
            dialog = ActivityAddEditDialog(self, activity_data, edit_mode=False)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get the data from the dialog
                activity_data = dialog.getActivityData()
                
                # 1. Add to activities manager
                activity_id = self.main_window.activities_manager.add_activity(activity_data)
                
                if activity_id:
                    # Add ID to the data
                    activity_data['id'] = activity_id
                    
                    # 2. Add to calendar for immediate visual feedback
                    calendar_event = {
                        'id': activity_id,
                        'title': activity_data['title'],
                        'date': activity_data['date'],
                        'time': activity_data['start_time'],
                        'category': activity_data['category'],
                        'color': QColor(activity_data['color']),
                        'activity_data': activity_data  # Store original data
                    }
                    
                    # Add to calendar events
                    date_str = date.toString("yyyy-MM-dd")
                    if date_str not in self.calendar.events:
                        self.calendar.events[date_str] = []
                    self.calendar.events[date_str].append(calendar_event)
                    
                    # 3. Update the activities view if it exists
                    if hasattr(self.main_window, 'activitiesView'):
                        # If the activities view has its own sync method, call it
                        if hasattr(self.main_window.activitiesView, 'syncWithCalendar'):
                            self.main_window.activitiesView.syncWithCalendar()
                    
                    # Update the events list display
                    self.updateEventsList()
                    # Update the calendar cells
                    self.calendar.updateCells()
                    return True
        else:
            # Fallback to original dialog for standalone mode
            dialog = EventDialog(self, date)
            result = dialog.exec()
            
            # More explicit check for dialog result
            if result == QDialog.DialogCode.Accepted:
                event_data = dialog.get_event_data()
                
                # 1. Add to calendar for immediate visual feedback
                self.calendar.addEvent(event_data)
                
                # 2. If connected to main app, add to activities manager
                if self.main_window and hasattr(self.main_window, 'activities_manager'):
                    try:
                        # Format the data for the activities manager
                        activity_data = {
                            'type': 'event',
                            'title': event_data['title'],
                            'date': event_data['date'],
                            'start_time': event_data['time'],
                            'end_time': QTime(event_data['time'].hour() + 1, event_data['time'].minute()),  # Default 1 hour duration
                            'category': event_data['category'],
                            'color': event_data['color'].name()  # Store color information
                        }
                        
                        # Add directly to activities manager
                        activity_id = self.main_window.activities_manager.add_activity(activity_data)
                        
                        # Also notify the activities view if it exists
                        if hasattr(self.main_window, 'activitiesView'):
                            activity_data['id'] = activity_id
                            self.main_window.activitiesView.activities.append(activity_data)
                            self.main_window.activitiesView.refreshActivitiesList()
                            # Emit the signal
                            self.main_window.onActivityAdded(activity_data)
                    except Exception as e:
                        print(f"Error adding event to activities manager: {e}")
                
                # Update the events list display
                self.updateEventsList()
                return True
        
        return False
        
    def editEvent(self, event):
        """Open dialog to edit an existing event."""
        # Check if it's an existing event with database ID
        is_existing = 'activity_data' in event and 'id' in event['activity_data']
        activity_id = event['activity_data'].get('id') if is_existing else None
        
        if activity_id and self.main_window and hasattr(self.main_window, 'activities_manager'):
            # Get the full activity data from the activities manager
            activity_data = self.main_window.activities_manager.get_activity_by_id(activity_id)
            
            if activity_data:
                # Use the ActivityAddEditDialog from unified_activities_widget
                dialog = ActivityAddEditDialog(self, activity_data, edit_mode=True)
                
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    # Get the updated data
                    updated_data = dialog.getActivityData()
                    
                    # Update in calendar's UI first for immediate visual feedback
                    updated_event = {
                        'id': event['id'],
                        'title': updated_data['title'],
                        'date': updated_data['date'],
                        'time': updated_data['start_time'],
                        'category': updated_data['category'],
                        'color': QColor(updated_data['color']) if 'color' in updated_data else event.get('color', QColor("#6366F1")),
                        'activity_data': event['activity_data']  # Keep original reference
                    }
                    
                    # Update in calendar display
                    date_str = event['date'].toString("yyyy-MM-dd")
                    if date_str in self.calendar.events:
                        for i, e in enumerate(self.calendar.events[date_str]):
                            if e['id'] == event['id']:
                                self.calendar.events[date_str][i] = updated_event
                                break
                    
                    # 2. If connected to main app, update in activities manager
                    if self.main_window and hasattr(self.main_window, 'activities_manager') and activity_id:
                        try:
                            # Update in activities manager
                            self.main_window.activities_manager.update_activity(activity_id, updated_data)
                            
                            # Also update in activities view if it exists
                            if hasattr(self.main_window, 'activitiesView'):
                                # If the activities view has its own sync method, call it
                                if hasattr(self.main_window.activitiesView, 'syncWithCalendar'):
                                    self.main_window.activitiesView.syncWithCalendar()
                        except Exception as e:
                            print(f"Error updating event in activities manager: {e}")
                    
                    # Update the events list display
                    self.updateEventsList()
                    # Update the calendar cells
                    self.calendar.updateCells()
                    return True
        else:
            # Fallback to original dialog for events not in the database
            # Create a dialog with event data
            dialog = EventDialog(self, event["date"])
            
            # Populate the dialog with event data
            dialog.title_edit.setText(event["title"])
            dialog.time_edit.setTime(event["time"])
            dialog.current_color = event.get("color", QColor("#6366F1"))
            dialog.update_color_button()
            
            # Set the category
            category_index = dialog.category_combo.findText(event["category"])
            if category_index >= 0:
                dialog.category_combo.setCurrentIndex(category_index)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get updated event data
                updated_event = dialog.get_event_data()
                
                # Update the event in the calendar
                date_str = event["date"].toString("yyyy-MM-dd")
                if date_str in self.calendar.events:
                    for i, e in enumerate(self.calendar.events[date_str]):
                        if e["id"] == event["id"]:
                            self.calendar.events[date_str][i] = updated_event
                            break
                
                # Update the events list display
                self.updateEventsList()
                # Update the calendar cells
                self.calendar.updateCells()
                return True
            
        return False
    
    def deleteEvent(self, event):
        """Delete an event from the calendar."""
        # Remove the event from the calendar
        date_str = event["date"].toString("yyyy-MM-dd")
        if date_str in self.calendar.events:
            self.calendar.events[date_str] = [e for e in self.calendar.events[date_str] if e != event]
            if not self.calendar.events[date_str]:
                del self.calendar.events[date_str]
        
        # Get activity type for proper signal emission
        activity_type = "event"
        
        # If connected to main app, also delete from activities manager
        if self.main_window and hasattr(self.main_window, 'activities_manager') and 'activity_data' in event:
            try:
                # Extract the original activity ID
                activity_id = event['activity_data'].get('id', None)
                
                if activity_id is not None:
                    # Delete from activities manager
                    self.main_window.activities_manager.delete_activity(activity_id)
                    
                    # Also update in activities view if it exists
                    if hasattr(self.main_window, 'activitiesView'):
                        # If the activities view has its own sync method, call it
                        if hasattr(self.main_window.activitiesView, 'syncWithCalendar'):
                            self.main_window.activitiesView.syncWithCalendar()
                        
                        # Emit the signal for activity deletion if the main window has it
                        if hasattr(self.main_window, 'onActivityDeleted'):
                            self.main_window.onActivityDeleted(activity_id, activity_type)
            except Exception as e:
                print(f"Error deleting event from activities manager: {e}")
        
        # Refresh the display
        self.updateEventsList()
        self.calendar.updateCells()
        
        return True 