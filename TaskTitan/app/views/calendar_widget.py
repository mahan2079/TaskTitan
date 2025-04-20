from PyQt6.QtWidgets import QCalendarWidget, QWidget, QVBoxLayout, QLabel, QGridLayout, QSizePolicy, QScrollArea, QFrame, QHBoxLayout
from PyQt6.QtWidgets import QDialog, QPushButton, QLineEdit, QComboBox, QTimeEdit, QDialogButtonBox, QFormLayout, QColorDialog
from PyQt6.QtCore import Qt, QDate, QSize, pyqtSignal, QPointF, QTime
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPalette, QLinearGradient, QFont, QRadialGradient

class EventDialog(QDialog):
    """Dialog for adding or editing calendar events."""
    
    def __init__(self, parent=None, event_date=None):
        super().__init__(parent)
        self.setWindowTitle("Add Event")
        self.resize(400, 300)
        self.setModal(True)  # Make sure dialog is modal and blocks input to other windows
        
        self.event_date = event_date or QDate.currentDate()
        
        # Create form layout
        layout = QFormLayout(self)
        layout.setSpacing(12)  # Increase spacing for better readability
        
        # Event title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter event title")
        self.title_edit.setMinimumHeight(30)  # Make input fields taller
        layout.addRow("Title:", self.title_edit)
        
        # Event time
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setMinimumHeight(30)
        layout.addRow("Time:", self.time_edit)
        
        # Event type/category
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Work", "Personal", "Meeting", "Reminder", "Other"])
        self.category_combo.setMinimumHeight(30)
        layout.addRow("Category:", self.category_combo)
        
        # Event color
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(100, 30)
        self.current_color = QColor("#6366F1")  # Default color
        self.update_color_button()
        self.color_btn.clicked.connect(self.select_color)
        
        color_label = QLabel("Choose Color:")
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_btn)
        layout.addRow(color_layout)
        
        # Date display (read-only)
        self.date_label = QLabel(self.event_date.toString("dddd, MMMM d, yyyy"))
        self.date_label.setStyleSheet("font-weight: bold; color: #4F46E5;")
        layout.addRow("Date:", self.date_label)
        
        # Add some space
        spacer = QWidget()
        spacer.setFixedHeight(15)
        layout.addRow("", spacer)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #334155;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #CBD5E1;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        # Save button
        self.save_btn = QPushButton("Save Event")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addRow("", button_layout)
        
        # Set title as initial focus
        self.title_edit.setFocus()
    
    def select_color(self):
        """Open color dialog to select event color."""
        color = QColorDialog.getColor(self.current_color, self, "Select Event Color")
        if color.isValid():
            self.current_color = color
            self.update_color_button()
    
    def update_color_button(self):
        """Update color button appearance with selected color."""
        self.color_btn.setStyleSheet(f"""
            background-color: {self.current_color.name()};
            border: 1px solid #ccc;
            border-radius: 4px;
            font-weight: bold;
            color: {'white' if self.current_color.lightness() < 128 else 'black'};
            text-align: center;
        """)
        self.color_btn.setText("Color")
    
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
            
            # Draw colorful event indicators
            if event_count > 0:
                # Event dots container
                dot_y = rect.bottom() - 12
                total_width = (event_count * 6) + ((event_count - 1) * 2)  # dots + spaces
                start_x = rect.center().x() - (total_width / 2)
                
                for i in range(event_count):
                    # Use the event's color for the dot
                    if i < len(event_list):
                        dot_color = event_list[i].get("color", self.event_colors[i % len(self.event_colors)])
                    else:
                        # Fallback to default colors if we somehow have more events than details
                        color_index = i % len(self.event_colors)
                        dot_color = self.event_colors[color_index]
                    
                    # Create a radial gradient for each dot
                    center_x = start_x + (i * 8)
                    center = QPointF(center_x, dot_y)
                    
                    dot_gradient = QRadialGradient(center, 3)
                    dot_gradient.setColorAt(0, dot_color.lighter(120))
                    dot_gradient.setColorAt(1, dot_color)
                    
                    # Draw dot
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(dot_gradient)
                    painter.drawEllipse(center, 3, 3)
        
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
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Create calendar widget
        self.calendar = ModernCalendarWidget()
        layout.addWidget(self.calendar)
        
        # Create events section
        self.events_widget = QWidget()
        events_layout = QVBoxLayout(self.events_widget)
        
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
        
        # Add event button - make it more prominent
        self.add_button = QPushButton("+ Add New Event")
        self.add_button.setMinimumHeight(40)  # Make button taller
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
                margin-top: 10px;
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
        
        # Set size policies
        self.calendar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.events_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Connect signals
        self.calendar.selectionChanged.connect(self.updateEventsList)
        self.calendar.dateDoubleClicked.connect(self.addEvent)
        self.add_button.clicked.connect(self.addEvent)
        
        # Set the split between calendar and events (approximately 60/40)
        layout.setStretchFactor(self.calendar, 60)
        layout.setStretchFactor(self.events_widget, 40)
        
        # Initial update
        self.updateEventsList()
        
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
            """)
            no_events_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.events_grid.addWidget(no_events_label, 0, 0, 1, 3)
            return
        
        # Column headers
        time_header = QLabel("Time")
        time_header.setStyleSheet("font-weight: bold; color: #4F46E5;")
        
        type_header = QLabel("Type")
        type_header.setStyleSheet("font-weight: bold; color: #4F46E5;")
        
        title_header = QLabel("Title")
        title_header.setStyleSheet("font-weight: bold; color: #4F46E5;")
        
        self.events_grid.addWidget(time_header, 0, 0)
        self.events_grid.addWidget(type_header, 0, 1)
        self.events_grid.addWidget(title_header, 0, 2)
        
        # Add events to grid
        for row, event in enumerate(events, 1):
            # Event container frame for better styling
            event_frame = QFrame()
            event_frame.setStyleSheet("""
                background-color: #F8FAFC;
                border-radius: 4px;
                border: 1px solid #E2E8F0;
                padding: 4px;
            """)
            event_layout = QGridLayout(event_frame)
            event_layout.setContentsMargins(5, 5, 5, 5)
            event_layout.setSpacing(5)
            
            # Time
            time_str = event.get("time").toString("hh:mm AP")
            time_label = QLabel(time_str)
            time_label.setStyleSheet("font-weight: bold;")
            
            # Category with color indicator
            color = event.get("color", QColor("#6366F1"))
            category = event.get("category", "")
            category_label = QLabel(f" {category}")
            category_label.setStyleSheet(f"""
                padding-left: 15px;
                background: qlineargradient(x1:0, y1:0.5, x2:0.2, y2:0.5,
                                           stop:0 {color.name()}, stop:0.2 {color.name()},
                                           stop:0.2 transparent);
                border-radius: 2px;
            """)
            
            # Title
            title_label = QLabel(event.get("title", ""))
            title_label.setStyleSheet("font-size: 13px;")
            title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            
            # Add to event layout
            event_layout.addWidget(time_label, 0, 0)
            event_layout.addWidget(category_label, 0, 1)
            event_layout.addWidget(title_label, 0, 2)
            
            # Add event frame to main grid - span all columns
            self.events_grid.addWidget(event_frame, row, 0, 1, 3)
    
    def addEvent(self, date=None):
        """Open dialog to add a new event."""
        if not date:
            date = self.calendar.selectedDate()
            
        dialog = EventDialog(self, date)
        result = dialog.exec()
        
        # More explicit check for dialog result
        if result == QDialog.DialogCode.Accepted:
            event_data = dialog.get_event_data()
            self.calendar.addEvent(event_data)
            self.updateEventsList()
            return True
        return False 