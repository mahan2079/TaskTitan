from PyQt6.QtWidgets import (QCalendarWidget, QWidget, QVBoxLayout, QLabel, QGridLayout, 
                          QSizePolicy, QScrollArea, QFrame, QHBoxLayout, QApplication, QToolButton)
from PyQt6.QtWidgets import QDialog, QPushButton, QLineEdit, QComboBox, QTimeEdit, QDialogButtonBox, QFormLayout, QColorDialog
from PyQt6.QtCore import Qt, QDate, QSize, pyqtSignal, QPointF, QTime, QRect
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPalette, QLinearGradient, QFont, QRadialGradient, QFontDatabase
import datetime
import math
import sys

# Import ActivityAddEditDialog for consistency across the application
from app.views.unified_activities_widget import ActivityAddEditDialog

# Corrected Persian Date Conversion
class PersianDate:
    """Utility class for correct Gregorian to Persian date conversion."""
    
    @staticmethod
    def gregorian_to_persian(date):
        """Convert Gregorian date to Persian date using the official Iranian calendar algorithm."""
        year = date.year()
        month = date.month()
        day = date.day()
        
        # Convert Gregorian to Julian Day Number
        a = math.floor((14 - month) / 12)
        y = year + 4800 - a
        m = month + 12 * a - 3
        jdn = day + math.floor((153 * m + 2) / 5) + 365 * y + math.floor(y / 4) - math.floor(y / 100) + math.floor(y / 400) - 32045
        
        # Convert Julian Day Number to Persian
        jdn = jdn - 1948320.5  # Subtract Persian epoch
        
        # Calculate Persian year
        p_year = math.floor((jdn + 0.5) / 365.2421986)
        p_year = p_year + 1  # Add 1 to get the correct year
        
        # Calculate Persian month and day
        p_month = 1
        p_day = 1
        
        # Calculate the number of days since the start of the Persian year
        days_in_year = jdn - PersianDate._persian_to_jdn(p_year, 1, 1)
        
        # Adjust for the one-day offset
        days_in_year = days_in_year + 1
        
        # Determine the Persian month
        if days_in_year < 186:
            p_month = math.floor(days_in_year / 31) + 1
            p_day = days_in_year % 31 + 1
        else:
            days_in_year = days_in_year - 186
            p_month = math.floor(days_in_year / 30) + 7
            p_day = days_in_year % 30 + 1
        
        return (p_year, p_month, p_day)
    
    @staticmethod
    def _persian_to_jdn(year, month, day):
        """Convert Persian date to Julian Day Number."""
        # Calculate the number of days since the Persian epoch
        days = (year - 1) * 365
        days += math.floor((year - 1) / 4)
        days -= math.floor((year - 1) / 100)
        days += math.floor((year - 1) / 400)
        
        # Add days for months
        if month <= 7:
            days += (month - 1) * 31
        else:
            days += 186 + (month - 7) * 30
        
        # Add days
        days += day
        
        # Add Persian epoch
        return days + 1948320.5
    
    @staticmethod
    def get_persian_month_name(month):
        """Get Persian month name."""
        months = [
            "فروردین", "اردیبهشت", "خرداد", 
            "تیر", "مرداد", "شهریور", 
            "مهر", "آبان", "آذر", 
            "دی", "بهمن", "اسفند"
        ]
        if 1 <= month <= 12:
            return months[month-1]
        return ""
    
    @staticmethod
    def get_persian_short_month_name(month):
        """Get Persian month short name (first 3 characters)."""
        full_name = PersianDate.get_persian_month_name(month)
        return full_name[:3] if full_name else ""
    
    @staticmethod
    def get_persian_day_of_week(date):
        """Get Persian day of week name."""
        # In Persian calendar, the week starts on Saturday (unlike Gregorian's Monday)
        # QDate uses 1=Monday, 7=Sunday, Persian uses 0=Saturday, 6=Friday
        gregorian_day_of_week = date.dayOfWeek()
        # Convert to Persian day of week (0=Saturday to 6=Friday)
        persian_day_of_week = (gregorian_day_of_week + 1) % 7
        
        days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
        return days[persian_day_of_week]
    
    @staticmethod
    def get_persian_short_day_of_week(date):
        """Get Persian day of week abbreviation."""
        gregorian_day_of_week = date.dayOfWeek()
        persian_day_of_week = (gregorian_day_of_week + 1) % 7
        
        days = ["ش", "ی", "د", "س", "چ", "پ", "ج"]
        return days[persian_day_of_week]

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

# Completely redesigned Calendar Widget
class DualCalendarWidget(QCalendarWidget):
    """A modern, elegant calendar widget displaying both Gregorian and Persian calendars."""
    
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
        
        # Enhanced color palette
        self.gregorian_text_color = QColor("#1E293B")  # Dark slate blue for Gregorian dates
        self.persian_text_color = QColor("#FB8C00")    # Orange for Persian dates
        self.today_color = QColor("#6366F1")           # Indigo for today's highlight
        self.weekend_color = QColor("#F9FAFB")         # Light gray for weekend background
        self.selection_color = QColor("#818CF8")       # Light indigo for selection
        self.divider_color = QColor("#E0E7FF")         # Light indigo for divider
        
        # Event colors
        self.event_colors = [
            QColor("#F87171"),  # Red
            QColor("#FBBF24"),  # Amber
            QColor("#34D399"),  # Emerald
            QColor("#60A5FA"),  # Blue
            QColor("#A78BFA")   # Purple
        ]
        
        # Add a Persian font
        # QFontDatabase.addApplicationFont("path/to/persian-font.ttf")  # Could add a Persian font
        self.persian_font = QFont("Arial", 9)  # Fallback
        
        # Sizing for dual calendar
        self.setFixedHeight(680)
        
        # Apply custom styling
        self.initStyleSheet()
        
        # Mark current date
        self.setSelectedDate(QDate.currentDate())
        
        # Events dictionary: date_str -> list of event dictionaries
        self.events = {}
        
        # Generate sample events
        self.generateSampleEvents()
        
        # Connect signals
        self.activated.connect(self.onDateDoubleClicked)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events on the calendar."""
        super().mouseDoubleClickEvent(event)
        date = self.selectedDate()
        self.dateDoubleClicked.emit(date)
        
    def onDateDoubleClicked(self, date):
        """Handle date double click to add a new event."""
        dialog = EventDialog(self, date)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event_data = dialog.get_event_data()
            self.addEvent(event_data)
    
    def addEvent(self, event_data):
        """Add a new event to the calendar."""
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
        """Initialize custom style sheet for modern calendar."""
        self.setStyleSheet("""
            QCalendarWidget {
                background-color: #ffffff;
                border: none;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #F8FAFC;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid #E2E8F0;
                padding: 8px;
                min-height: 50px;
            }
            
            QCalendarWidget QToolButton {
                color: #4F46E5;
                background-color: transparent;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                padding: 8px 12px;
                font-size: 15px;
                margin: 2px;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: #EEF2FF;
            }
            
            QCalendarWidget QToolButton:pressed {
                background-color: #C7D2FE;
            }
            
            QCalendarWidget QToolButton::menu-indicator {
                image: none;
            }
            
            QCalendarWidget QMenu {
                width: 150px;
                background-color: white;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 5px;
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
                outline: 0;
                selection-background-color: transparent;
                background-color: white;
            }
            
            QCalendarWidget QAbstractItemView:disabled {
                color: #9CA3AF;
            }
            
            /* Make headers stand out more */
            QCalendarWidget QTableView QHeaderView {
                background-color: #F8FAFC;
            }
            
            QCalendarWidget QTableView QHeaderView::section {
                color: #FB8C00; 
                font-weight: bold;
                font-size: 16px;
                padding: 10px 6px;
                background-color: #F8FAFC;
                border: none;
                border-bottom: 1px solid #E2E8F0;
                border-radius: 0;
            }
            
            /* Increase the size of cells for the dual calendar */
            QCalendarWidget QTableView {
                selection-background-color: transparent;
                selection-color: #1E293B;
            }
            
            /* Style for the "Today" text in the navigation bar */
            QCalendarWidget QToolButton#qt_calendar_todaybutton {
                color: white;
                background-color: #4F46E5;
                border-radius: 8px;
                padding: 6px 12px;
                margin: 2px;
            }
            
            QCalendarWidget QToolButton#qt_calendar_todaybutton:hover {
                background-color: #4338CA;
            }
            
            QCalendarWidget QToolButton#qt_calendar_prevmonth, 
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                font-size: 18px;
                padding: 0px 8px;
            }
            
            QCalendarWidget QWidget {
                alternate-background-color: #FFFFFF;
            }
        """)
    
    def paintCell(self, painter, rect, date):
        """Paint cell with both Gregorian and Persian calendars with elegant design."""
        painter.save()
        
        # Get current date for comparison
        current_date = QDate.currentDate()
        selected_date = self.selectedDate()
        
        # First clear the cell background
        cell_rect = rect.adjusted(1, 1, -1, -1)
        painter.fillRect(rect, QColor(255, 255, 255))
        
        # Create a rounded rectangle for the cell with shadow effect
        if date.month() == self.monthShown():
            # Current month cells are white with a subtle border
            painter.setPen(QPen(QColor("#E2E8F0"), 0.5))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
        else:
            # Out-of-month cells are slightly grayed out
            painter.setPen(QPen(QColor("#E2E8F0"), 0.5))
            painter.setBrush(QBrush(QColor("#F9FAFB")))
        
        # Handle weekends with lighter background
        if date.dayOfWeek() >= 6:  # Saturday or Sunday
            painter.setBrush(QBrush(self.weekend_color))
        
        # Draw the cell background
        painter.drawRoundedRect(cell_rect, 6, 6)
        
        # Special styling for today's date
        if date == current_date:
            today_rect = rect.adjusted(3, 3, -3, -3)
            painter.setPen(QPen(self.today_color, 0.7))
            painter.setBrush(QBrush(self.today_color.lighter(160)))
            painter.drawRoundedRect(today_rect, 6, 6)
            
            # Set text colors for today
            g_text_color = QColor("#4338CA")  # Darker indigo for Gregorian
            p_text_color = QColor("#FB8C00")  # Orange for Persian
        
        # Special styling for selected date
        elif date == selected_date:
            select_rect = rect.adjusted(3, 3, -3, -3)
            painter.setPen(QPen(self.selection_color, 0.7))
            painter.setBrush(QBrush(self.selection_color.lighter(160)))
            painter.drawRoundedRect(select_rect, 6, 6)
            
            # Set text colors for selected date
            g_text_color = QColor("#4338CA")  # Darker indigo for Gregorian
            p_text_color = QColor("#FB8C00")  # Orange for Persian
        else:
            # Default text colors
            g_text_color = self.gregorian_text_color
            p_text_color = self.persian_text_color
        
        # Get Persian date
        persian_year, persian_month, persian_day = PersianDate.gregorian_to_persian(date)
        
        # Draw divider between Gregorian and Persian dates
        painter.setPen(QPen(self.divider_color, 0.8, Qt.PenStyle.SolidLine))
        painter.drawLine(
            int(rect.left() + 5), 
            int(rect.top() + rect.height() * 0.5), 
            int(rect.right() - 5), 
            int(rect.top() + rect.height() * 0.5)
        )
        
        # Draw Gregorian date
        gregorian_font = painter.font()
        gregorian_font.setPointSize(11)
        gregorian_font.setBold(date == current_date or date == selected_date)
        painter.setFont(gregorian_font)
        painter.setPen(g_text_color)
        
        # Determine text alignment for Gregorian date
        g_text_rect = QRect(
            int(rect.left() + 2),
            int(rect.top() + 5),
            int(rect.width() - 4),
            int(rect.height() / 2 - 5)
        )
        
        # Draw Gregorian date
        if date.month() == self.monthShown():
            # Current month days are shown normally
            painter.drawText(g_text_rect, Qt.AlignmentFlag.AlignCenter, str(date.day()))
        else:
            # Out-of-month days are shown with lighter color
            painter.setPen(QColor(g_text_color).lighter(150))
            painter.drawText(g_text_rect, Qt.AlignmentFlag.AlignCenter, str(date.day()))
        
        # Draw Persian date
        persian_font = self.persian_font
        persian_font.setPointSize(9)
        persian_font.setBold(date == current_date or date == selected_date)
        painter.setFont(persian_font)
        painter.setPen(p_text_color)
        
        # Determine text alignment for Persian date
        p_text_rect = QRect(
            int(rect.left() + 2),
            int(rect.top() + rect.height() / 2 + 2),
            int(rect.width() - 4),
            int(rect.height() / 2 - 7)
        )
        
        # Draw Persian date
        if date.month() == self.monthShown():
            # Current month days are shown normally
            painter.drawText(p_text_rect, Qt.AlignmentFlag.AlignCenter, str(persian_day))
        else:
            # Out-of-month days are shown with lighter color
            painter.setPen(QColor(p_text_color).lighter(150))
            painter.drawText(p_text_rect, Qt.AlignmentFlag.AlignCenter, str(persian_day))
        
        # Check if this date has events
        date_str = date.toString("yyyy-MM-dd")
        if date_str in self.events:
            event_list = self.events[date_str]
            event_count = len(event_list)
            
            # Draw elegant event indicators
            if event_count > 0:
                # Show event indicators at the very bottom of the cell
                indicator_y = rect.bottom() - 6
                
                # Limit to max 5 indicators
                displayed_count = min(event_count, 5)
                
                # Calculate total width of indicators
                dot_size = 5
                dot_spacing = 2
                total_width = (displayed_count * dot_size) + ((displayed_count - 1) * dot_spacing)
                start_x = rect.center().x() - (total_width / 2)
                
                for i in range(displayed_count):
                    # Get event color
                    event_color = event_list[i].get("color", self.event_colors[i % len(self.event_colors)])
                    
                    # Draw a rounded rect indicator
                    indicator_rect = QRect(
                        int(start_x + (i * (dot_size + dot_spacing))),
                        int(indicator_y - dot_size/2),
                        dot_size,
                        dot_size
                    )
                    
                    painter.setPen(QPen(event_color.darker(120), 0.5))
                    painter.setBrush(QBrush(event_color))
                    painter.drawEllipse(indicator_rect)
                
                # If we have more events than can be displayed, add a "more" indicator
                if event_count > 5:
                    more_x = start_x + (displayed_count * (dot_size + dot_spacing)) + 2
                    painter.setPen(QColor(100, 100, 100, 180))
                    painter.drawText(
                        QPointF(more_x, indicator_y + 3), 
                        "+"
                    )
        
        painter.restore()
    
    def setEvents(self, events_data):
        """Set events data for the calendar."""
        self.events = events_data
        self.updateCells()
        
    def getEvents(self, date):
        """Get events for a specific date."""
        date_str = date.toString("yyyy-MM-dd")
        return self.events.get(date_str, [])
        
    def sizeHint(self):
        """Suggested size for the widget."""
        return QSize(520, 680)
        
    def minimumSizeHint(self):
        """Minimum suggested size for the widget."""
        return QSize(400, 500)

# Alias for backward compatibility
CustomCalendarWidget = DualCalendarWidget
ModernCalendarWidget = DualCalendarWidget

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
        self.calendar = CustomCalendarWidget()
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
        
        # Add spacer to push content up
        events_layout.addStretch()
        
        # Add shortcut to activities view
        self.activities_shortcut = QPushButton("Add New Activity")
        self.activities_shortcut.setMinimumHeight(48)
        self.activities_shortcut.setCursor(Qt.CursorShape.PointingHandCursor)
        self.activities_shortcut.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
        """)
        self.activities_shortcut.clicked.connect(self.openActivitiesView)
        events_layout.addWidget(self.activities_shortcut)
        
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
        self.activities_shortcut.clicked.connect(self.openActivitiesView)
        
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
        self.calendar.removeEvent(event)
        self.updateEventsList()
        
    def openActivitiesView(self):
        """Open the activities view and switch to it."""
        main_window = self.findMainWindow()
        if main_window:
            main_window.changePage(1)  # Switch to activities view (index 1)
            # Trigger the add activity dialog
            if hasattr(main_window, 'activities_view'):
                main_window.activities_view.showAddActivityDialog('task')  # Default to task type
        
        return True 