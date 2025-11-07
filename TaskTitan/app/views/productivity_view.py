"""
Daily Tracker View for TaskTitan.

This module provides comprehensive daily time tracking, activity monitoring,
and analytics for productivity improvement.
"""
from datetime import datetime, timedelta, time
import sqlite3
import uuid
import os
from functools import partial

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTimeEdit, QDateEdit, QScrollArea, QFrame, QLineEdit, QGridLayout,
    QSplitter, QTabWidget, QStackedWidget, QMessageBox, QSlider,
    QTextEdit, QDialog, QDialogButtonBox, QSpinBox, QGroupBox, QColorDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QListWidget,
    QListWidgetItem, QSizePolicy, QMenu, QCalendarWidget, QGraphicsDropShadowEffect,
    QFileDialog, QProgressBar, QFormLayout, QInputDialog
)
from PyQt6.QtCore import (
    Qt, QSize, QDate, QTime, QDateTime, pyqtSignal, QTimer,
    QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QIcon, QColor, QFont, QPalette, QBrush, QPainter, QPen, QPixmap,
    QCursor, QAction
)

# Import for charts
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from app.resources import get_icon, ColorPalette
from app.utils.logger import get_logger
from app.utils.error_handler import handle_database_error, handle_file_error

logger = get_logger(__name__)

def find_database_path():
    """Find the path to the database file in the data directory."""
    import os
    
    # Define a central data directory relative to the application root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, 'data')
    
    # Create the data directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    # Full path to the database
    db_path = os.path.join(data_dir, 'tasktitan.db')
    
    return db_path

class TimeEntry:
    """Represents a single time tracking entry."""
    
    def __init__(self, id=None, date=None, start_time=None, end_time=None, 
                 category=None, description=None, energy_level=None, mood_level=None):
        self.id = id if id else str(uuid.uuid4())
        self.date = date if date else QDate.currentDate()
        self.start_time = start_time if start_time else QTime.currentTime()
        self.end_time = end_time
        self.category = category if category else "Work"
        self.description = description if description else ""
        self.energy_level = energy_level
        self.mood_level = mood_level
        
    def duration_minutes(self):
        """Calculate the duration in minutes."""
        if not self.end_time:
            return 0
            
        # Convert QTime to seconds since midnight
        start_secs = self.start_time.hour() * 3600 + self.start_time.minute() * 60 + self.start_time.second()
        end_secs = self.end_time.hour() * 3600 + self.end_time.minute() * 60 + self.end_time.second()
        
        # Handle entries that cross midnight
        if end_secs < start_secs:
            end_secs += 24 * 3600
            
        return (end_secs - start_secs) // 60

class DailyTrackerView(QWidget):
    """Advanced widget for tracking daily productivity and patterns."""
    
    def __init__(self, parent=None):
        """Initialize the DailyTrackerView."""
        super().__init__(parent)
        self.parent = parent  # Store the reference to parent
        self.current_date = QDate.currentDate()  # Default to today's date
        self.active_entry = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_current_timer)
        self.timer.start(1000)  # Update every second
        self.activities = []
        self.tracking_activities = []  # List for multi-tracking items
        
        # Initialize database
        self.connection = None
        self.cursor = None
        self.open_database()
        
        # Initialize UI
        self.setupUI()
        
        # Load activities for current date
        self.load_activities()
        
    def open_database(self):
        """Open the database connection."""
        import sqlite3
        try:
            db_path = find_database_path()
            self.connection = sqlite3.connect(db_path)
            self.cursor = self.connection.cursor()
            
            # Create journal entries table if it doesn't exist
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id TEXT PRIMARY KEY,
                    date TEXT UNIQUE,
                    wins TEXT,
                    challenges TEXT,
                    learnings TEXT,
                    tomorrow TEXT,
                    gratitude TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    name TEXT
                )
            """)
            
            # Make sure to commit the changes
            self.connection.commit()
            
            logger.info(f"Connected to database: {db_path.split('/')[-1]}")
            
        except Exception as e:
            logger.error(f"Error connecting to database: {e}", exc_info=True)
            self.connection = None
            self.cursor = None
        
    def setupUI(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Set minimum width for the entire view
        self.setMinimumWidth(850)
        
        # Header with title and date navigation
        header = QWidget()
        header.setObjectName("dailyTrackerHeader")
        header.setMinimumHeight(120)
        header.setStyleSheet("""
            #dailyTrackerHeader {
                background-color: white;
                border-bottom: 1px solid #E5E7EB;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 15, 25, 15)
        header_layout.setSpacing(20)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(16)
        
        # Add icon
        icon_label = QLabel()
        tracker_icon = get_icon("productivity")
        if not tracker_icon.isNull():
            icon_label.setPixmap(tracker_icon.pixmap(QSize(48, 48)))
        else:
            # Fallback to emoji
            icon_label.setText("⏱️")
            icon_label.setFont(QFont("Arial", 32))
        title_layout.addWidget(icon_label)
        
        # Title text
        title = QLabel("Daily Tracker")
        title.setObjectName("dailyTrackerTitle")
        font = QFont()
        font.setPointSize(28)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet("color: #111827;")
        title_layout.addWidget(title)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch(1)
        
        # Date navigation
        date_layout = QHBoxLayout()
        date_layout.setSpacing(8)
        
        # Previous day button
        self.prev_day_btn = QPushButton()
        prev_icon = get_icon("left-arrow")
        if not prev_icon.isNull():
            self.prev_day_btn.setIcon(prev_icon)
        else:
            self.prev_day_btn.setText("◀")
        self.prev_day_btn.setFixedSize(46, 46)
        self.prev_day_btn.setToolTip("Previous Day")
        # Theme system will handle button styling
        self.prev_day_btn.clicked.connect(self.previous_day)
        date_layout.addWidget(self.prev_day_btn)
        
        # Date picker
        self.date_edit = QDateEdit(self.current_date)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.date_changed)
        self.date_edit.setMinimumWidth(200)
        self.date_edit.setFixedHeight(46)
        self.date_edit.setDisplayFormat("MM/dd/yyyy")
        # Theme system will handle date edit styling
        date_layout.addWidget(self.date_edit)
        
        # Next day button
        self.next_day_btn = QPushButton()
        next_icon = get_icon("right-arrow")
        if not next_icon.isNull():
            self.next_day_btn.setIcon(next_icon)
        else:
            self.next_day_btn.setText("▶")
        self.next_day_btn.setFixedSize(46, 46)
        self.next_day_btn.setToolTip("Next Day")
        # Theme system will handle button styling
        self.next_day_btn.clicked.connect(self.next_day)
        date_layout.addWidget(self.next_day_btn)
        
        header_layout.addLayout(date_layout)
        header_layout.addSpacing(30)
        
        # Add entry button - improved styling
        self.add_entry_btn = QPushButton("+ Add Time Entry")
        self.add_entry_btn.setFixedSize(180, 46)
        # Theme system will handle button styling
        self.add_entry_btn.clicked.connect(self.add_entry)
        header_layout.addWidget(self.add_entry_btn)
        
        # Start tracking button - improved styling
        self.tracking_btn = QPushButton("Start Tracking")
        self.tracking_btn.setFixedSize(180, 46)
        self.tracking_btn.setObjectName("primaryBtn")
        # Theme system will handle button styling
        self.tracking_btn.clicked.connect(self.toggle_tracking)
        header_layout.addWidget(self.tracking_btn)
        
        main_layout.addWidget(header)
        
        # Main content tabs
        self.tab_widget = QTabWidget()
        # Theme system will handle tab widget styling
        main_layout.addWidget(self.tab_widget)
        
        # Time Tracker Tab
        self.setup_tracker_tab()
        
        # Journal Tab
        self.setup_journal_tab()
        
        # Analytics Tab
        self.setup_analytics_tab()
        
        # Reports Tab
        self.setup_reports_tab()
        
        # Apply styles
        self.apply_styles()
        
    def setup_tracker_tab(self):
        """Set up the time tracker tab."""
        tracker_tab = QWidget()
        outer_layout = QVBoxLayout(tracker_tab)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        
        # Create a scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #F9FAFB;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #F3F4F6;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #D1D5DB;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9CA3AF;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Create a container widget for the scroll area
        scroll_content = QWidget()
        tracker_layout = QVBoxLayout(scroll_content)
        tracker_layout.setContentsMargins(30, 30, 30, 30)
        tracker_layout.setSpacing(30)
        
        # Current tracking status - styled card
        status_card = QFrame()
        status_card.setProperty("data-card", "true")
        # Theme system will handle card styling
        status_card_layout = QVBoxLayout(status_card)
        status_card_layout.setContentsMargins(30, 25, 30, 25)
        status_card_layout.setSpacing(15)
        
        # Empty state when no activity is tracked
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(0, 20, 0, 20)
        empty_layout.setSpacing(15)
        
        empty_icon = QLabel()
        empty_pixmap = get_icon("clock").pixmap(QSize(64, 64))
        if not empty_pixmap.isNull():
            empty_icon.setPixmap(empty_pixmap)
        else:
            empty_icon.setText("⏱️")
            empty_icon.setFont(QFont("Arial", 36))
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)
        
        empty_title = QLabel("No Active Tracking")
        empty_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #111827;")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)
        
        empty_desc = QLabel("Start tracking your time or add a new entry manually")
        empty_desc.setStyleSheet("font-size: 15px; color: #6B7280;")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_desc)
        
        # Active tracking state
        self.tracking_widget = QWidget()
        tracking_layout = QVBoxLayout(self.tracking_widget)
        tracking_layout.setContentsMargins(0, 10, 0, 10)
        tracking_layout.setSpacing(10)
        
        self.tracking_status = QLabel("Not tracking any activity")
        self.tracking_status.setStyleSheet("font-size: 20px; font-weight: bold; color: #111827;")
        self.tracking_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tracking_layout.addWidget(self.tracking_status)
        
        # Current tracking time
        self.tracking_time = QLabel("00:00:00")
        self.tracking_time.setObjectName("trackingTime")
        # Theme system will handle label styling via object name
        self.tracking_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tracking_layout.addWidget(self.tracking_time)
        
        # Add buttons in horizontal layout with proper spacing and centering
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()
        
        # Stop button
        stop_btn = QPushButton("Stop")
        stop_btn.setObjectName("stopBtn")
        # Theme system will handle button styling
        stop_btn.clicked.connect(self.toggle_tracking)
        button_layout.addWidget(stop_btn)
        
        # Pause button
        pause_btn = QPushButton("Pause")
        pause_btn.setObjectName("pauseBtn")
        # Theme system will handle button styling
        button_layout.addWidget(pause_btn)
        
        button_layout.addStretch()
        tracking_layout.addLayout(button_layout)
        
        # Default to empty state
        self.tracking_widget.hide()
        status_card_layout.addWidget(self.empty_state)
        status_card_layout.addWidget(self.tracking_widget)
        
        tracker_layout.addWidget(status_card)
        
        # Time entries section - styled card
        entries_card = QFrame()
        entries_card.setProperty("data-card", "true")
        # Theme system will handle card styling
        entries_layout = QVBoxLayout(entries_card)
        entries_layout.setContentsMargins(25, 25, 25, 25)
        entries_layout.setSpacing(20)
        
        # Time entries header with title and category management
        entries_header_layout = QHBoxLayout()
        entries_header_layout.setContentsMargins(0, 0, 0, 10)
        
        entries_title = QLabel("Time Entries")
        # Theme system will handle label styling
        entries_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        entries_header_layout.addWidget(entries_title)
        
        entries_header_layout.addStretch()
        
        # Add Category Management button - improved styling
        manage_categories_btn = QPushButton("Manage Categories")
        # Theme system will handle button styling
        manage_categories_btn.setIcon(get_icon("settings"))
        manage_categories_btn.clicked.connect(self.manage_categories)
        entries_header_layout.addWidget(manage_categories_btn)
        
        entries_layout.addLayout(entries_header_layout)
        
        # Time entries table - improved styling
        self.entries_table = QTableWidget()
        self.entries_table.setColumnCount(6)
        self.entries_table.setHorizontalHeaderLabels(["Start", "End", "Duration", "Category", "Description", "Actions"])
        self.entries_table.setMinimumWidth(1100)
        self.entries_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.entries_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.entries_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.entries_table.setWordWrap(False)
        
        # Set column widths
        self.entries_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.entries_table.setColumnWidth(0, 100)  # Start
        self.entries_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.entries_table.setColumnWidth(1, 100)  # End
        self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.entries_table.setColumnWidth(2, 110)  # Duration
        self.entries_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.entries_table.setColumnWidth(3, 130)  # Category
        self.entries_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.entries_table.setColumnWidth(4, 350)  # Description
        self.entries_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.entries_table.setColumnWidth(5, 180)  # Actions
        
        self.entries_table.verticalHeader().setDefaultSectionSize(50)
        self.entries_table.horizontalHeader().setMinimumSectionSize(80)
        self.entries_table.horizontalHeader().setFixedHeight(44)
        self.entries_table.verticalHeader().setVisible(False)
        self.entries_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setMinimumHeight(320)
        self.entries_table.setMaximumHeight(420)
        # Theme system will handle table styling
        entries_layout.addWidget(self.entries_table)
        
        tracker_layout.addWidget(entries_card)
        
        # Summary section - styled card
        summary_card = QFrame()
        summary_card.setProperty("data-card", "true")
        # Theme system will handle card styling
        summary_layout = QHBoxLayout(summary_card)
        summary_layout.setContentsMargins(30, 25, 30, 25)
        summary_layout.setSpacing(40)
        
        # Total time
        total_time_layout = QVBoxLayout()
        total_time_label = QLabel("Total Time")
        # Theme system will handle label styling
        total_time_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.total_time_value = QLabel("0h 0m")
        # Theme system will handle label styling
        self.total_time_value.setStyleSheet("font-size: 24px; font-weight: bold; margin-top: 5px;")
        total_time_layout.addWidget(total_time_label)
        total_time_layout.addWidget(self.total_time_value)
        summary_layout.addLayout(total_time_layout)
        
        # Add vertical separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #E5E7EB;")
        summary_layout.addWidget(separator)
        
        # Categories breakdown
        for category in ["Work", "Meeting", "Break"]:
            category_layout = QVBoxLayout()
            category_label = QLabel(category)
            category_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4B5563;")
            category_value = QLabel("0h 0m")
            category_value.setStyleSheet("font-size: 20px; color: #111827; margin-top: 5px;")
            category_value.setObjectName(f"category_{category}")
            category_layout.addWidget(category_label)
            category_layout.addWidget(category_value)
            summary_layout.addLayout(category_layout)
        
            # Add separator except after the last category
            if category != "Break":
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                separator.setStyleSheet("color: #E5E7EB;")
                summary_layout.addWidget(separator)
        
        tracker_layout.addWidget(summary_card)
        
        # Set up the scroll area
        scroll_area.setWidget(scroll_content)
        outer_layout.addWidget(scroll_area)
        
        # Add to tab widget
        self.tab_widget.addTab(tracker_tab, "Time Tracker")
        
    def setup_journal_tab(self):
        """Set up the daily journal tab for reflection and notes."""
        journal_tab = QWidget()
        journal_layout = QVBoxLayout(journal_tab)
        journal_layout.setSpacing(0)
        journal_layout.setContentsMargins(0, 0, 0, 0)

        # Make the whole journal tab scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #F9FAFB;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #F3F4F6;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #D1D5DB;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9CA3AF;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(0)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # Modern header with gradient and shadow
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                      stop:0 #4F46E5, 
                                      stop:1 #7C3AED);
            border-radius: 12px;
            padding: 15px;
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 3)
        header_frame.setGraphicsEffect(shadow)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        journal_icon = QLabel()
        journal_pixmap = get_icon("notes").pixmap(QSize(32, 32))
        if not journal_pixmap.isNull():
            journal_icon.setPixmap(journal_pixmap)
        else:
            journal_icon.setText("📝")
        header_layout.addWidget(journal_icon)
        header_label = QLabel("Daily Journal & Reflections")
        header_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(header_label)
        date_label = QLabel()
        self.journal_date_label = date_label  # Store for updating
        date_label.setStyleSheet("color: white; font-size: 16px;")
        header_layout.addStretch()
        header_layout.addWidget(date_label)
        scroll_layout.addWidget(header_frame)
        
        # Main content - split into two panels using QSplitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Left panel - Journal form
        form_widget = QWidget()
        form_widget.setMinimumWidth(600)
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(25)
        form_layout.setContentsMargins(30, 30, 30, 30)
        
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        form_content = QWidget()
        form_content_layout = QVBoxLayout(form_content)
        form_content_layout.setSpacing(30)
        
        # Add header with entry selector for multiple entries
        entry_header = QHBoxLayout()
        
        # Add a title for the form
        form_title = QLabel("Today's Reflection")
        form_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #4F46E5; margin-bottom: 10px;")
        entry_header.addWidget(form_title)
        
        entry_header.addStretch()
        
        # Add entry selector dropdown and buttons
        entry_selector_layout = QHBoxLayout()
        entry_selector_layout.setSpacing(10)
        
        entry_label = QLabel("Entry:")
        entry_label.setStyleSheet("font-size: 14px; color: #4B5563;")
        entry_selector_layout.addWidget(entry_label)
        
        self.entry_selector = QComboBox()
        self.entry_selector.addItem("New Entry")
        self.entry_selector.setMinimumWidth(180)
        self.entry_selector.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 4px 10px;
                border-radius: 6px;
                border: 1px solid #D1D5DB;
                background-color: #F9FAFB;
            }
        """)
        self.entry_selector.currentIndexChanged.connect(self.journal_entry_selected)
        entry_selector_layout.addWidget(self.entry_selector)
        
        # Add "New Entry" button
        new_entry_btn = QPushButton("New")
        new_entry_btn.setStyleSheet("""
            QPushButton {
                background-color: #EFF6FF;
                color: #3B82F6;
                border: 1px solid #BFDBFE;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #DBEAFE;
                border-color: #93C5FD;
            }
        """)
        new_entry_btn.clicked.connect(self.add_new_journal_entry)
        entry_selector_layout.addWidget(new_entry_btn)
        
        # Add "Delete Entry" button
        delete_entry_btn = QPushButton("Delete")
        delete_entry_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEE2E2;
                color: #DC2626;
                border: 1px solid #FECACA;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FECACA;
                border-color: #FCA5A5;
            }
        """)
        delete_entry_btn.clicked.connect(self.delete_journal_entry)
        entry_selector_layout.addWidget(delete_entry_btn)
        
        entry_header.addLayout(entry_selector_layout)
        form_layout.addLayout(entry_header)
        
        # Initialize timestamp for the current entry
        self.current_entry_id = None
        self.current_entry_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add entry name field
        name_layout = QHBoxLayout()
        name_label = QLabel("Entry Name:")
        name_label.setStyleSheet("font-size: 15px; color: #4B5563;")
        name_layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Give this entry a name (optional)")
        self.name_edit.setStyleSheet("""
            QLineEdit {
                font-size: 15px; 
                padding: 8px; 
                border-radius: 6px; 
                border: 1px solid #D1D5DB;
                background-color: white;
            }
        """)
        name_layout.addWidget(self.name_edit)
        
        # Add timestamp display
        self.entry_timestamp = QLabel(f"Created: {self.current_entry_timestamp}")
        self.entry_timestamp.setStyleSheet("font-size: 12px; color: #6B7280;")
        self.entry_timestamp.setAlignment(Qt.AlignmentFlag.AlignRight)
        name_layout.addWidget(self.entry_timestamp)
        
        form_layout.addLayout(name_layout)
        
        # Create tabs for structured and free-form journal
        journal_tabs = QTabWidget()
        journal_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: white;
                padding: 10px;
            }
            QTabBar::tab {
                background-color: #F3F4F6;
                color: #6B7280;
                padding: 8px 16px;
                min-width: 100px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #E5E7EB;
                border-bottom: none;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #4F46E5;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E5E7EB;
            }
        """)
        
        # Tab for structured form
        structured_tab = QWidget()
        structured_layout = QVBoxLayout(structured_tab)
        structured_layout.setContentsMargins(15, 15, 15, 15)
        structured_layout.setSpacing(20)
        
        # --- Add tags input ---
        tags_label = QLabel("Tags (comma separated):")
        tags_label.setStyleSheet("font-size: 15px; color: #4B5563;")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("e.g. focus, gratitude, health")
        self.tags_edit.setStyleSheet("font-size: 15px; padding: 8px; border-radius: 6px; border: 1px solid #D1D5DB;")
        structured_layout.addWidget(tags_label)
        structured_layout.addWidget(self.tags_edit)

        # --- Add mood selector ---
        mood_label = QLabel("Mood:")
        mood_label.setStyleSheet("font-size: 15px; color: #4B5563;")
        self.mood_combo = QComboBox()
        self.mood_combo.addItems(["😊 Happy", "😐 Neutral", "😔 Sad", "😠 Angry", "😴 Tired", "🤩 Excited"])
        self.mood_combo.setStyleSheet("font-size: 15px; padding: 8px; border-radius: 6px; border: 1px solid #D1D5DB;")
        structured_layout.addWidget(mood_label)
        structured_layout.addWidget(self.mood_combo)

        # --- Add quick rating slider ---
        rating_label = QLabel("How was your day? (1-10)")
        rating_label.setStyleSheet("font-size: 15px; color: #4B5563;")
        self.rating_slider = QSlider(Qt.Orientation.Horizontal)
        self.rating_slider.setMinimum(1)
        self.rating_slider.setMaximum(10)
        self.rating_slider.setValue(5)
        self.rating_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.rating_slider.setTickInterval(1)
        self.rating_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 8px; background: #E5E7EB; border-radius: 4px; }
            QSlider::handle:horizontal { background: #4F46E5; border: 2px solid white; width: 16px; height: 16px; margin: -5px 0; border-radius: 9px; }
            QSlider::sub-page:horizontal { background: #C7D2FE; border-radius: 4px; }
        """)
        self.rating_value = QLabel("5")
        self.rating_value.setStyleSheet("font-weight: bold; min-width: 15px;")
        self.rating_slider.valueChanged.connect(lambda v: self.rating_value.setText(str(v)))
        rating_row = QHBoxLayout()
        rating_row.addWidget(self.rating_slider)
        rating_row.addWidget(self.rating_value)
        structured_layout.addWidget(rating_label)
        structured_layout.addLayout(rating_row)

        # --- Add file/image attachment ---
        attach_label = QLabel("Attach a file or image:")
        attach_label.setStyleSheet("font-size: 15px; color: #4B5563;")
        
        attach_container = QWidget()
        attach_layout = QVBoxLayout(attach_container)
        attach_layout.setContentsMargins(0, 0, 0, 0)
        attach_layout.setSpacing(10)
        
        # File selection row
        attach_file_row = QHBoxLayout()
        
        self.attach_btn = QPushButton("Choose File")
        self.attach_btn.setStyleSheet("font-size: 15px; padding: 8px 16px; border-radius: 6px; background: #F3F4F6; border: 1px solid #D1D5DB;")
        self.attach_btn.clicked.connect(self.attach_file)
        self.attached_file_label = QLabel("")
        self.attached_file_label.setStyleSheet("font-size: 14px; color: #6B7280; margin-left: 10px;")
        attach_file_row.addWidget(self.attach_btn)
        attach_file_row.addWidget(self.attached_file_label)
        attach_file_row.addStretch()
        
        attach_layout.addLayout(attach_file_row)
        
        # Category row
        category_row = QHBoxLayout()
        category_label = QLabel("Category:")
        category_label.setStyleSheet("font-size: 14px; color: #4B5563;")
        category_row.addWidget(category_label)
        
        self.attachment_category = QComboBox()
        self.attachment_category.setEditable(True)
        self.attachment_category.setStyleSheet("font-size: 14px; padding: 5px; min-width: 150px;")
        
        # Load existing categories
        from app.utils.db_utils import list_attachment_categories
        categories = list_attachment_categories()
        default_categories = ["Journal", "Images", "Documents", "Notes", "Reference"]
        
        # Combine existing and default categories
        all_categories = list(set(categories + default_categories))
        all_categories.sort()
        self.attachment_category.addItems(all_categories)
        
        category_row.addWidget(self.attachment_category)
        
        # Add a "Manage Categories" button next to the category dropdown
        manage_categories_btn = QPushButton("Manage")
        manage_categories_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 4px 8px;
                border-radius: 4px;
                background: #F3F4F6;
                border: 1px solid #D1D5DB;
            }
            QPushButton:hover {
                background: #E5E7EB;
            }
        """)
        manage_categories_btn.clicked.connect(self.manage_attachment_categories)
        category_row.addWidget(manage_categories_btn)
        
        category_row.addStretch()
        
        attach_layout.addLayout(category_row)
        
        structured_layout.addWidget(attach_label)
        structured_layout.addWidget(attach_container)

        # --- New: List of attached files for the selected date ---
        self.attachments_list_label = QLabel("Attached files for this day:")
        self.attachments_list_label.setStyleSheet("font-size: 15px; color: #4B5563; margin-top: 10px;")
        structured_layout.addWidget(self.attachments_list_label)
        
        # Container for attachments list and controls
        attachments_container = QWidget()
        attachments_layout = QVBoxLayout(attachments_container)
        attachments_layout.setContentsMargins(0, 0, 0, 0)
        attachments_layout.setSpacing(8)
        
        self.attachments_list = QListWidget()
        self.attachments_list.setStyleSheet("font-size: 14px; background: #F9FAFB; border-radius: 6px; border: 1px solid #E5E7EB;")
        self.attachments_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.attachments_list.customContextMenuRequested.connect(self.show_attachment_context_menu)
        self.attachments_list.itemDoubleClicked.connect(self.open_attached_file)
        attachments_layout.addWidget(self.attachments_list)
        
        # Attachment controls
        attachment_controls = QHBoxLayout()
        attachment_controls.setContentsMargins(0, 0, 0, 0)
        
        self.remove_attachment_btn = QPushButton("Remove Selected")
        self.remove_attachment_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 6px 12px;
                border-radius: 6px;
                background: #FEE2E2;
                border: 1px solid #FECACA;
                color: #DC2626;
            }
            QPushButton:hover {
                background: #FECACA;
            }
            QPushButton:disabled {
                background: #F3F4F6;
                color: #9CA3AF;
                border-color: #E5E7EB;
            }
        """)
        self.remove_attachment_btn.clicked.connect(self.remove_selected_attachment)
        self.remove_attachment_btn.setEnabled(False)
        attachment_controls.addWidget(self.remove_attachment_btn)
        
        self.open_attachment_folder_btn = QPushButton("Open Folder")
        self.open_attachment_folder_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 6px 12px;
                border-radius: 6px;
                background: #EFF6FF;
                border: 1px solid #DBEAFE;
                color: #3B82F6;
            }
            QPushButton:hover {
                background: #DBEAFE;
            }
        """)
        self.open_attachment_folder_btn.clicked.connect(self.open_attachments_folder)
        attachment_controls.addWidget(self.open_attachment_folder_btn)
        
        attachment_controls.addStretch()
        
        attachments_layout.addLayout(attachment_controls)
        structured_layout.addWidget(attachments_container)
        
        # Connect selection changed signal
        self.attachments_list.itemSelectionChanged.connect(self.update_attachment_buttons)
        
        # Each section in a card-like frame
        sections = [
            ("Today's Wins & Achievements", "What went well today? What did you accomplish?", "wins_edit"),
            ("Challenges & Obstacles", "What challenges did you face? How did you overcome them?", "challenges_edit"),
            ("Learnings & Insights", "What did you learn today? Any insights or revelations?", "learnings_edit"),
            ("Tomorrow's Focus", "What will you focus on tomorrow? What's your most important task?", "tomorrow_edit"),
            ("Gratitude & Appreciation", "What are you grateful for today?", "gratitude_edit")
        ]
        for title, placeholder, attr_name in sections:
            section_frame = QFrame()
            section_frame.setStyleSheet("""
                background-color: white;
                border-radius: 10px;
                border: 1px solid #E5E7EB;
                padding: 15px;
            """)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setColor(QColor(0, 0, 0, 30))
            shadow.setOffset(0, 2)
            section_frame.setGraphicsEffect(shadow)
            section_layout = QVBoxLayout(section_frame)
            section_layout.setContentsMargins(15, 15, 15, 15)
            section_layout.setSpacing(10)
            section_title = QLabel(title)
            section_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #4B5563;")
            section_layout.addWidget(section_title)
            text_edit = QTextEdit()
            text_edit.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    padding: 8px;
                    background-color: #F9FAFB;
                    font-size: 14px;
                }
                QTextEdit:focus {
                    border: 1px solid #4F46E5;
                    background-color: white;
                }
            """)
            text_edit.setPlaceholderText(placeholder)
            text_edit.setMinimumHeight(100)
            setattr(self, attr_name, text_edit)  # Store the widget as an attribute
            section_layout.addWidget(text_edit)
            structured_layout.addWidget(section_frame)
        
        # Add structured tab to tab widget
        journal_tabs.addTab(structured_tab, "Structured Journal")
        
        # Tab for free-form writing
        freeform_tab = QWidget()
        freeform_layout = QVBoxLayout(freeform_tab)
        freeform_layout.setContentsMargins(15, 15, 15, 15)
        freeform_layout.setSpacing(20)
        
        # Free writing header
        free_writing_header = QHBoxLayout()
        free_writing_title = QLabel("Free Writing")
        free_writing_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4F46E5;")
        free_writing_header.addWidget(free_writing_title)
        
        # Word count
        self.word_count_label = QLabel("0 words")
        self.word_count_label.setStyleSheet("font-size: 14px; color: #6B7280;")
        free_writing_header.addStretch()
        free_writing_header.addWidget(self.word_count_label)
        
        freeform_layout.addLayout(free_writing_header)
        
        # Free writing instructions
        free_writing_instructions = QLabel("Use this space for stream of consciousness writing, daily reflections, or anything else on your mind.")
        free_writing_instructions.setStyleSheet("font-size: 14px; color: #6B7280; margin-bottom: 10px;")
        free_writing_instructions.setWordWrap(True)
        freeform_layout.addWidget(free_writing_instructions)
        
        # Free writing text area
        self.free_writing_edit = QTextEdit()
        self.free_writing_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 15px;
                background-color: #F9FAFB;
                font-size: 15px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border: 1px solid #4F46E5;
                background-color: white;
            }
        """)
        self.free_writing_edit.setPlaceholderText("Start writing here...")
        self.free_writing_edit.setMinimumHeight(400)
        self.free_writing_edit.textChanged.connect(self.update_word_count)
        
        freeform_layout.addWidget(self.free_writing_edit)
        journal_tabs.addTab(freeform_tab, "Free Writing")
        
        # Add the tabs to the form
        form_layout.addWidget(journal_tabs)
        
        # Current entry timestamp display
        timestamp_label = QLabel("")
        timestamp_label.setStyleSheet("font-size: 12px; color: #6B7280; font-style: italic;")
        self.entry_timestamp = timestamp_label
        form_layout.addWidget(timestamp_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Save button with improved styling
        save_btn_layout = QHBoxLayout()
        save_btn_layout.addStretch()
        save_journal_btn = QPushButton("Save Journal Entry")
        save_journal_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #4338CA;
            }
            QPushButton:pressed {
                background-color: #3730A3;
            }
        """)
        save_journal_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_journal_btn.clicked.connect(self.save_journal_entry)
        save_btn_layout.addWidget(save_journal_btn)
        form_content_layout.addLayout(save_btn_layout)
        form_content_layout.addStretch()
        form_scroll.setWidget(form_content)
        form_layout.addWidget(form_scroll)
        
        # Right panel - Calendar and history
        history_widget = QWidget()
        history_widget.setMinimumWidth(350)
        history_widget.setMinimumHeight(900)  # Triple the height
        history_layout = QVBoxLayout(history_widget)
        history_layout.setSpacing(20)
        history_layout.setContentsMargins(20, 30, 20, 30)
        
        # Calendar section with shadow
        calendar_frame = QFrame()
        calendar_frame.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            border: 1px solid #E5E7EB;
            padding: 15px;
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        calendar_frame.setGraphicsEffect(shadow)
        calendar_layout = QVBoxLayout(calendar_frame)
        calendar_title = QLabel("Journal History")
        calendar_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4F46E5; margin-bottom: 10px;")
        calendar_layout.addWidget(calendar_title)
        calendar_subtitle = QLabel("Select a date to view previous entries")
        calendar_subtitle.setStyleSheet("font-size: 14px; color: #6B7280; margin-bottom: 15px;")
        calendar_layout.addWidget(calendar_subtitle)
        self.journal_calendar = QCalendarWidget()
        self.journal_calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border: none;
            }
            QCalendarWidget QToolButton {
                color: #4F46E5;
                background-color: white;
                border-radius: 4px;
            }
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
            }
            QCalendarWidget QSpinBox {
                border: 1px solid #E5E7EB;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #4F46E5;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #111827;
                background-color: white;
                selection-background-color: #E0E7FF;
                selection-color: #4F46E5;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #9CA3AF;
            }
        """)
        self.journal_calendar.clicked.connect(self.load_journal_entry)
        calendar_layout.addWidget(self.journal_calendar)
        history_layout.addWidget(calendar_frame)
        
        # Entry summary section
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            border: 1px solid #E5E7EB;
            padding: 15px;
            margin-top: 15px;
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        summary_frame.setGraphicsEffect(shadow)
        summary_layout = QVBoxLayout(summary_frame)
        summary_title = QLabel("Journal Stats")
        summary_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4F46E5; margin-bottom: 10px;")
        summary_layout.addWidget(summary_title)
        self.journal_stats_label = QLabel()
        self.journal_stats_label.setStyleSheet("font-size: 14px; color: #4B5563;")
        self.journal_stats_label.setWordWrap(True)
        summary_layout.addWidget(self.journal_stats_label)
        insight_label = QLabel("Journal insights will appear here as you add more entries.")
        insight_label.setStyleSheet("font-size: 14px; color: #6B7280; margin-top: 10px;")
        insight_label.setWordWrap(True)
        summary_layout.addWidget(insight_label)
        history_layout.addWidget(summary_frame)
        history_layout.addStretch()
        
        # Add widgets to splitter
        splitter.addWidget(form_widget)
        splitter.addWidget(history_widget)
        splitter.setSizes([700, 350])  # Set initial sizes
        scroll_layout.addWidget(splitter)
        scroll_area.setWidget(scroll_content)
        journal_layout.addWidget(scroll_area)
        
        # Add to tab widget
        self.tab_widget.addTab(journal_tab, "Daily Journal")
        
        # Update date label
        self.update_journal_date_label()
        # Load journal entry for current date
        self.load_journal_entry(self.current_date)
        # Update journal stats
        self.update_journal_stats()
    
    def attach_file(self):
        """Open a file dialog to attach a file/image to the journal entry and save it for the selected date."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Attach File or Image", "", "All Files (*);;Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.attached_file_label.setText(os.path.basename(file_path))
            self.attached_file_path = file_path
            
            # Get category from the dropdown
            category = self.attachment_category.currentText() if self.attachment_category.currentText() else None
            
            # Save attachment to DB with the selected category
            self.save_journal_attachment(self.current_date, file_path, category)
            self.load_journal_attachments(self.current_date)
        else:
            self.attached_file_label.setText("")
            self.attached_file_path = None

    def save_journal_attachment(self, date, file_path, category=None):
        """Save the attached file path for the given date in the database."""
        if not self.cursor:
            return
        try:
            # Create journal_attachments table if it doesn't exist (with category and shortcut_path fields)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    category TEXT,
                    shortcut_path TEXT
                )
            """)
            
            # Format date string
            date_str = date.toString("yyyy-MM-dd")
            
            # Use the category from the dropdown if not provided
            if not category and hasattr(self, 'attachment_category'):
                category = self.attachment_category.currentText()
                
            # Copy the file to the attachments directory
            from app.utils.db_utils import save_attachment
            date_path, shortcut_path = save_attachment(file_path, date_str=date_str, category=category)
            
            if date_path:
                # Store the paths and category in the database
                self.cursor.execute(
                    "INSERT INTO journal_attachments (date, file_path, category, shortcut_path) VALUES (?, ?, ?, ?)",
                    (date_str, date_path, category, shortcut_path)
                )
                self.connection.commit()
                print(f"Successfully saved attachment to {date_path}")
                if shortcut_path:
                    print(f"Created shortcut at {shortcut_path}")
            else:
                print("Failed to save attachment: Could not copy file to date directory")
        except Exception as e:
            print(f"Error saving journal attachment: {e}")
            QMessageBox.warning(self, "Error", f"Could not save attachment: {e}")

    def load_journal_attachments(self, date):
        """Load and display the list of attached files for the given date."""
        self.attachments_list.clear()
        self.update_attachment_buttons()
        
        if not self.cursor:
            return
        try:
            date_str = date.toString("yyyy-MM-dd") if isinstance(date, QDate) else date
            
            # Check if shortcut_path column exists
            try:
                self.cursor.execute(
                    "SELECT id, file_path, category, shortcut_path FROM journal_attachments WHERE date = ?",
                    (date_str,)
                )
                files = self.cursor.fetchall()
                
                shortcut_path_exists = True
            except sqlite3.OperationalError as e:
                if "no such column: shortcut_path" in str(e):
                    # Shortcut_path column doesn't exist, use query without it
                    self.cursor.execute(
                        "SELECT id, file_path, category FROM journal_attachments WHERE date = ?",
                        (date_str,)
                    )
                    files = self.cursor.fetchall()
                    
                    # Add the missing column to the table
                    try:
                        self.cursor.execute("ALTER TABLE journal_attachments ADD COLUMN shortcut_path TEXT")
                        self.connection.commit()
                        print("Added shortcut_path column to journal_attachments table")
                    except Exception as alter_error:
                        print(f"Error adding shortcut_path column: {alter_error}")
                    
                    shortcut_path_exists = False
                else:
                    # Re-raise if it's a different error
                    raise
            
            for file_data in files:
                file_id = file_data[0]
                file_path = file_data[1]
                category = file_data[2]
                shortcut_path = file_data[3] if shortcut_path_exists and len(file_data) > 3 else None
                
                # Check if file exists and determine which path to use for display
                display_path = file_path
                if not os.path.exists(file_path) and shortcut_path and os.path.exists(shortcut_path):
                    display_path = shortcut_path
                
                # Create an item with more detailed display including category
                item_name = os.path.basename(display_path)
                if item_name.endswith('.lnk'):
                    item_name = item_name[:-4]  # Remove .lnk extension for display
                    
                category_str = f" [{category}]" if category else ""
                
                item = QListWidgetItem(f"{item_name}{category_str}")
                
                # Add an icon based on file type
                file_ext = os.path.splitext(item_name)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    icon_name = "image"
                elif file_ext in ['.pdf']:
                    icon_name = "pdf"
                elif file_ext in ['.doc', '.docx', '.txt', '.rtf']:
                    icon_name = "document"
                elif file_ext in ['.xls', '.xlsx', '.csv']:
                    icon_name = "spreadsheet"
                else:
                    icon_name = "attachment"
                
                # Try to get icon
                from app.resources import get_icon
                icon = get_icon(icon_name)
                if not icon.isNull():
                    item.setIcon(icon)
                
                # Set tooltip with full path and category information
                tooltip = f"File: {display_path}"
                if category:
                    tooltip += f"\nCategory: {category}"
                tooltip += f"\nDate: {date_str}"
                item.setToolTip(tooltip)
                
                # Store the file ID and path as user data
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                item.setData(Qt.ItemDataRole.UserRole + 1, file_id)
                item.setData(Qt.ItemDataRole.UserRole + 2, category)
                item.setData(Qt.ItemDataRole.UserRole + 3, shortcut_path)
                
                # Add to list
                self.attachments_list.addItem(item)
        except Exception as e:
            print(f"Error loading journal attachments: {e}")

    def open_attached_file(self, item):
        """Open the attached file using the default system application."""
        if not item:
            return
            
        file_path = item.data(Qt.ItemDataRole.UserRole)
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"The file could not be found: {file_path}")
            return
            
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", file_path])
            else:  # Linux
                subprocess.call(["xdg-open", file_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open the file: {e}")

    def update_journal_stats(self):
        """Update journal statistics display."""
        if not self.cursor:
            return
            
        try:
            # Count total entries
            self.cursor.execute("SELECT COUNT(*) FROM journal_entries")
            total_entries = self.cursor.fetchone()[0]
            
            # Count streak (consecutive days)
            streak = 0
            current_date = QDate.currentDate()
            
            # Get earliest entry date
            self.cursor.execute("SELECT MIN(date) FROM journal_entries")
            min_date_str = self.cursor.fetchone()[0]
            start_date = QDate.fromString(min_date_str, "yyyy-MM-dd") if min_date_str else current_date
            
            # Calculate days since first entry
            days_since_start = start_date.daysTo(current_date) + 1
            
            stats_text = f"Total entries: {total_entries}\n"
            stats_text += f"Days journaling: {days_since_start} days\n"
            
            # Avoid division by zero
            if days_since_start > 0:
                completion_rate = (total_entries / days_since_start * 100)
                stats_text += f"Completion rate: {completion_rate:.1f}% of days"
            
            self.journal_stats_label.setText(stats_text)
            
        except Exception as e:
            print(f"Error updating journal stats: {e}")
            self.journal_stats_label.setText("Unable to load journal statistics.")
    
    def update_journal_date_label(self):
        """Update the date label in the journal tab."""
        self.journal_date_label.setText(f"Entry for {self.current_date.toString('MMMM d, yyyy')}")
    
    def date_changed(self, new_date):
        """Handle date change in the date picker."""
        self.current_date = new_date
        self.load_entries(new_date)
        self.update_journal_date_label()
        self.load_journal_entry(new_date)
        
    def save_journal_entry(self):
        """Save the current journal entry to the database."""
        if not self.cursor:
            QMessageBox.warning(self, "Database Error", "Cannot save journal entry: Database not connected.")
            return
            
        try:
            # Generate a unique ID for new entries
            entry_id = str(uuid.uuid4())
            
            # Prepare data
            date_str = self.current_date.toString("yyyy-MM-dd")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if journal_entries table exists
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_entries'")
            if not self.cursor.fetchone():
                # Create the table if it doesn't exist
                self.cursor.execute("""
                    CREATE TABLE journal_entries (
                        id TEXT PRIMARY KEY,
                        date TEXT,
                        wins TEXT,
                        challenges TEXT,
                        learnings TEXT,
                        tomorrow TEXT,
                        gratitude TEXT,
                        free_writing TEXT,
                        timestamp TEXT,
                        name TEXT
                    )
                """)
            else:
                # Check if journal_entries table has required columns
                try:
                    self.cursor.execute("SELECT free_writing, name FROM journal_entries LIMIT 1")
                except sqlite3.OperationalError:
                    # Add missing columns if they don't exist
                    try:
                        # Check and add free_writing column
                        try:
                            self.cursor.execute("SELECT free_writing FROM journal_entries LIMIT 1")
                        except sqlite3.OperationalError:
                            self.cursor.execute("ALTER TABLE journal_entries ADD COLUMN free_writing TEXT")
                            print("Added free_writing column to journal_entries table")
                            
                        # Check and add name column
                        try:
                            self.cursor.execute("SELECT name FROM journal_entries LIMIT 1")
                        except sqlite3.OperationalError:
                            self.cursor.execute("ALTER TABLE journal_entries ADD COLUMN name TEXT")
                            print("Added name column to journal_entries table")
                            
                    except Exception as alter_error:
                        print(f"Error adding columns: {alter_error}")
                
                # Also check for timestamp column
                try:
                    self.cursor.execute("SELECT timestamp FROM journal_entries LIMIT 1")
                except sqlite3.OperationalError:
                    # Add timestamp column if it doesn't exist
                    try:
                        self.cursor.execute("ALTER TABLE journal_entries ADD COLUMN timestamp TEXT")
                        print("Added timestamp column to journal_entries table")
                    except Exception as alter_error:
                        print(f"Error adding timestamp column: {alter_error}")
                        
                # Remove UNIQUE constraint from date column by recreating the table if needed
                has_unique_constraint = False
                try:
                    self.cursor.execute("INSERT INTO journal_entries (id, date) VALUES (?, ?)", 
                                       (str(uuid.uuid4()), date_str))
                    self.cursor.execute("INSERT INTO journal_entries (id, date) VALUES (?, ?)", 
                                       (str(uuid.uuid4()), date_str))
                    self.connection.rollback()  # Don't actually insert test entries
                except sqlite3.IntegrityError:
                    # UNIQUE constraint exists
                    has_unique_constraint = True
                except Exception as e:
                    print(f"Error testing for UNIQUE constraint: {e}")
                
                if has_unique_constraint:
                    print("Recreating journal_entries table to remove UNIQUE constraint on date...")
                    # Create new table without the UNIQUE constraint
                    self.cursor.execute("""
                        CREATE TABLE IF NOT EXISTS journal_entries_new (
                            id TEXT PRIMARY KEY,
                            date TEXT,
                            wins TEXT,
                            challenges TEXT,
                            learnings TEXT,
                            tomorrow TEXT,
                            gratitude TEXT,
                            free_writing TEXT,
                            timestamp TEXT,
                            name TEXT
                        )
                    """)
                    
                    # Copy data from old table to new table
                    self.cursor.execute("""
                        INSERT INTO journal_entries_new 
                        SELECT id, date, wins, challenges, learnings, tomorrow, gratitude, 
                               free_writing, timestamp, name
                        FROM journal_entries
                    """)
                    
                    # Drop old table and rename new table
                    self.cursor.execute("DROP TABLE journal_entries")
                    self.cursor.execute("ALTER TABLE journal_entries_new RENAME TO journal_entries")
                    
                    self.connection.commit()
                    print("Successfully recreated journal_entries table without UNIQUE constraint")
            
            # Check if this is a new entry or if we're updating an existing one
            if hasattr(self, 'current_entry_id') and self.current_entry_id:
                # Update existing entry
                self.cursor.execute("""
                    UPDATE journal_entries 
                    SET wins = ?, challenges = ?, learnings = ?, tomorrow = ?, 
                        gratitude = ?, free_writing = ?, timestamp = ?, name = ?
                    WHERE id = ?
                """, (
                    self.wins_edit.toPlainText(),
                    self.challenges_edit.toPlainText(),
                    self.learnings_edit.toPlainText(),
                    self.tomorrow_edit.toPlainText(),
                    self.gratitude_edit.toPlainText(),
                    self.free_writing_edit.toPlainText() if hasattr(self, 'free_writing_edit') else None,
                    timestamp,
                    self.name_edit.text() if hasattr(self, 'name_edit') else None,
                    self.current_entry_id
                ))
                entry_id = self.current_entry_id
            else:
                # Insert new entry
                self.cursor.execute("""
                    INSERT INTO journal_entries 
                    (id, date, wins, challenges, learnings, tomorrow, gratitude, free_writing, timestamp, name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry_id,
                    date_str,
                    self.wins_edit.toPlainText(),
                    self.challenges_edit.toPlainText(),
                    self.learnings_edit.toPlainText(),
                    self.tomorrow_edit.toPlainText(),
                    self.gratitude_edit.toPlainText(),
                    self.free_writing_edit.toPlainText() if hasattr(self, 'free_writing_edit') else None,
                    timestamp,
                    self.name_edit.text() if hasattr(self, 'name_edit') else None
                ))
            
            # Commit changes
            self.connection.commit()
            
            # Update current entry ID
            self.current_entry_id = entry_id
            
            # Highlight the date in the calendar
            self.update_journal_calendar()
            
            QMessageBox.information(self, "Success", "Journal entry saved successfully!")
            
        except Exception as e:
            print(f"Error saving journal entry: {e}")
            QMessageBox.warning(self, "Error", f"Could not save journal entry: {e}")
    
    def load_journal_entry(self, date):
        """Load journal entries for the specified date."""
        if not self.cursor:
            return
        
        try:
            # Convert QDate to string
            if isinstance(date, QDate):
                date_str = date.toString("yyyy-MM-dd")
            else:
                date_str = self.current_date.toString("yyyy-MM-dd")
            
            # Load all entries for this date into the dropdown
            self.load_journal_entries_for_date(date if isinstance(date, QDate) else self.current_date)
            
            # If there are entries, load the most recent one
            if self.entry_selector.count() > 1:
                self.entry_selector.setCurrentIndex(1)  # First actual entry
            else:
                # No entries found, clear fields
                self.clear_journal_entry_fields()
                self.current_entry_id = None
                self.entry_selector.setCurrentIndex(0)  # "New Entry"
                self.current_entry_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.entry_timestamp.setText(f"Created: {self.current_entry_timestamp}")
            
            # Load attachments
            self.load_journal_attachments(date)
            
        except Exception as e:
            print(f"Error loading journal entry: {e}")
    
    def update_journal_calendar(self):
        """Update the journal calendar to highlight dates with entries."""
        if not self.cursor:
            return
            
        try:
            # Get all dates with journal entries
            self.cursor.execute("SELECT date FROM journal_entries")
            entry_dates = [QDate.fromString(row[0], "yyyy-MM-dd") for row in self.cursor.fetchall()]
            
            # Custom format for the calendar to highlight dates with journal entries
            class JournalCalendarStyle(QCalendarWidget):
                def __init__(self, parent=None, entry_dates=None):
                    super().__init__(parent)
                    self.entry_dates = entry_dates or []
                
                def paintCell(self, painter, rect, date):
                    super().paintCell(painter, rect, date)
                    
                    if date in self.entry_dates:
                        painter.save()
                        painter.setPen(QColor("#3B82F6"))
                        painter.setBrush(QColor(59, 130, 246, 50))  # Semi-transparent blue
                        painter.drawEllipse(rect.center(), 12, 12)
                        painter.restore()
            
            # Create new calendar widget with entry dates
            old_calendar = self.journal_calendar
            new_calendar = JournalCalendarStyle(entry_dates=entry_dates)
            new_calendar.clicked.connect(self.load_journal_entry)
            
            # Get the parent widget and layout
            parent_layout = old_calendar.parentWidget().layout()
            parent_layout.replaceWidget(old_calendar, new_calendar)
            
            # Update reference and clean up
            self.journal_calendar = new_calendar
            old_calendar.deleteLater()
            
        except Exception as e:
            print(f"Error updating journal calendar: {e}")
        
    def setup_analytics_tab(self):
        """Set up the analytics tab with charts and insights."""
        analytics_tab = QWidget()
        analytics_layout = QVBoxLayout(analytics_tab)
        
        # Date range selection
        date_range_frame = QFrame()
        date_range_layout = QHBoxLayout(date_range_frame)
        
        date_range_layout.addWidget(QLabel("Date Range:"))
        
        self.start_date_edit = QDateEdit(self.current_date.addDays(-7))
        self.start_date_edit.setCalendarPopup(True)
        date_range_layout.addWidget(self.start_date_edit)
        
        date_range_layout.addWidget(QLabel("to"))
        
        self.end_date_edit = QDateEdit(self.current_date)
        self.end_date_edit.setCalendarPopup(True)
        date_range_layout.addWidget(self.end_date_edit)
        
        self.update_analytics_btn = QPushButton("Update Charts")
        self.update_analytics_btn.clicked.connect(self.update_analytics)
        date_range_layout.addWidget(self.update_analytics_btn)
        
        # Quick range buttons
        self.week_btn = QPushButton("This Week")
        self.week_btn.clicked.connect(lambda: self.set_date_range("week"))
        date_range_layout.addWidget(self.week_btn)
        
        self.month_btn = QPushButton("This Month")
        self.month_btn.clicked.connect(lambda: self.set_date_range("month"))
        date_range_layout.addWidget(self.month_btn)
        
        analytics_layout.addWidget(date_range_frame)
        
        # Create subtabs for each chart type
        self.chart_tabs = QTabWidget()
        analytics_layout.addWidget(self.chart_tabs)
        
        if HAS_MATPLOTLIB:
            # Category Distribution Tab
            category_tab = QWidget()
            category_layout = QVBoxLayout(category_tab)
            
            # Add customization options for category chart
            category_options_frame = QFrame()
            category_options_layout = QHBoxLayout(category_options_frame)
            
            category_options_layout.addWidget(QLabel("Chart Type:"))
            self.category_chart_type = QComboBox()
            self.category_chart_type.addItems(["Pie Chart", "Bar Chart", "Donut Chart"])
            self.category_chart_type.currentIndexChanged.connect(lambda: self.update_analytics())
            category_options_layout.addWidget(self.category_chart_type)
            
            category_options_layout.addWidget(QLabel("Color Scheme:"))
            self.category_color_scheme = QComboBox()
            self.category_color_scheme.addItems(["Default", "Pastel", "Bright", "Dark", "Colorblind-friendly"])
            self.category_color_scheme.currentIndexChanged.connect(lambda: self.update_analytics())
            category_options_layout.addWidget(self.category_color_scheme)
            
            # Add sort order option
            sort_label = QLabel("Sort by:")
            category_options_layout.addWidget(sort_label)
            self.category_sort_order = QComboBox()
            self.category_sort_order.addItems(["Time (Descending)", "Time (Ascending)", "Alphabetical"])
            self.category_sort_order.currentIndexChanged.connect(lambda: self.update_analytics())
            category_options_layout.addWidget(self.category_sort_order)
            
            category_options_layout.addStretch()
            
            category_layout.addWidget(category_options_frame)
            
            # Create the figure and canvas
            self.category_figure = Figure(figsize=(6, 5), dpi=100)
            self.category_canvas = FigureCanvas(self.category_figure)
            category_layout.addWidget(self.category_canvas)
            
            # Add to tabs
            self.chart_tabs.addTab(category_tab, "Category Distribution")
            
            # Daily Distribution Tab
            daily_tab = QWidget()
            daily_layout = QVBoxLayout(daily_tab)
            
            # Add customization options for daily chart
            daily_options_frame = QFrame()
            daily_options_layout = QHBoxLayout(daily_options_frame)
            
            daily_options_layout.addWidget(QLabel("Chart Type:"))
            self.daily_chart_type = QComboBox()
            self.daily_chart_type.addItems(["Bar Chart", "Line Chart", "Area Chart"])
            self.daily_chart_type.currentIndexChanged.connect(lambda: self.update_analytics())
            daily_options_layout.addWidget(self.daily_chart_type)
            
            daily_options_layout.addWidget(QLabel("Group by:"))
            self.daily_group_by = QComboBox()
            self.daily_group_by.addItems(["Day", "Week", "Month"])
            self.daily_group_by.currentIndexChanged.connect(lambda: self.update_analytics())
            daily_options_layout.addWidget(self.daily_group_by)
            
            daily_options_layout.addWidget(QLabel("Show Categories:"))
            self.daily_show_categories = QCheckBox()
            self.daily_show_categories.setChecked(False)
            self.daily_show_categories.stateChanged.connect(lambda: self.update_analytics())
            daily_options_layout.addWidget(self.daily_show_categories)
            
            daily_options_layout.addStretch()
            
            daily_layout.addWidget(daily_options_frame)
            
            # Create the figure and canvas
            self.daily_figure = Figure(figsize=(6, 5), dpi=100)
            self.daily_canvas = FigureCanvas(self.daily_figure)
            daily_layout.addWidget(self.daily_canvas)
            
            # Add to tabs
            self.chart_tabs.addTab(daily_tab, "Time Distribution")
            
            # Productivity Patterns Tab
            patterns_tab = QWidget()
            patterns_layout = QVBoxLayout(patterns_tab)
            
            # Add customization options for patterns chart
            patterns_options_frame = QFrame()
            patterns_options_layout = QHBoxLayout(patterns_options_frame)
            
            patterns_options_layout.addWidget(QLabel("Show:"))
            self.patterns_show_energy = QCheckBox("Energy")
            self.patterns_show_energy.setChecked(True)
            self.patterns_show_energy.stateChanged.connect(lambda: self.update_analytics())
            patterns_options_layout.addWidget(self.patterns_show_energy)
            
            self.patterns_show_mood = QCheckBox("Mood")
            self.patterns_show_mood.setChecked(True)
            self.patterns_show_mood.stateChanged.connect(lambda: self.update_analytics())
            patterns_options_layout.addWidget(self.patterns_show_mood)
            
            self.patterns_show_time = QCheckBox("Time")
            self.patterns_show_time.setChecked(True)
            self.patterns_show_time.stateChanged.connect(lambda: self.update_analytics())
            patterns_options_layout.addWidget(self.patterns_show_time)
            
            patterns_options_layout.addStretch()
            
            patterns_layout.addWidget(patterns_options_frame)
            
            # Create the figure and canvas
            self.patterns_figure = Figure(figsize=(6, 5), dpi=100)
            self.patterns_canvas = FigureCanvas(self.patterns_figure)
            patterns_layout.addWidget(self.patterns_canvas)
            
            # Add to tabs
            self.chart_tabs.addTab(patterns_tab, "Productivity Patterns")
            
            # Hourly Heatmap Tab (new chart)
            heatmap_tab = QWidget()
            heatmap_layout = QVBoxLayout(heatmap_tab)
            
            # Add customization options for heatmap
            heatmap_options_frame = QFrame()
            heatmap_options_layout = QHBoxLayout(heatmap_options_frame)
            
            heatmap_options_layout.addWidget(QLabel("Metric:"))
            self.heatmap_metric = QComboBox()
            self.heatmap_metric.addItems(["Time Spent", "Energy Level", "Mood Level"])
            self.heatmap_metric.currentIndexChanged.connect(lambda: self.update_analytics())
            heatmap_options_layout.addWidget(self.heatmap_metric)
            
            heatmap_options_layout.addWidget(QLabel("Color Scheme:"))
            self.heatmap_color_scheme = QComboBox()
            self.heatmap_color_scheme.addItems(["Viridis", "Plasma", "Inferno", "Magma", "Blues", "Reds"])
            self.heatmap_color_scheme.currentIndexChanged.connect(lambda: self.update_analytics())
            heatmap_options_layout.addWidget(self.heatmap_color_scheme)
            
            heatmap_options_layout.addStretch()
            
            heatmap_layout.addWidget(heatmap_options_frame)
            
            # Create the figure and canvas
            self.heatmap_figure = Figure(figsize=(6, 5), dpi=100)
            self.heatmap_canvas = FigureCanvas(self.heatmap_figure)
            heatmap_layout.addWidget(self.heatmap_canvas)
            
            # Add to tabs
            self.chart_tabs.addTab(heatmap_tab, "Time Heatmap")
            
            # Category Comparison Tab (new chart)
            comparison_tab = QWidget()
            comparison_layout = QVBoxLayout(comparison_tab)
            
            # Add customization options for comparison chart
            comparison_options_frame = QFrame()
            comparison_options_layout = QHBoxLayout(comparison_options_frame)
            
            comparison_options_layout.addWidget(QLabel("Comparison Type:"))
            self.comparison_type = QComboBox()
            self.comparison_type.addItems(["Time by Day of Week", "Time by Hour of Day", "Energy/Mood by Category"])
            self.comparison_type.currentIndexChanged.connect(lambda: self.update_analytics())
            comparison_options_layout.addWidget(self.comparison_type)
            
            comparison_options_layout.addWidget(QLabel("Chart Style:"))
            self.comparison_style = QComboBox()
            self.comparison_style.addItems(["Bar Chart", "Radar Chart", "Box Plot"])
            self.comparison_style.currentIndexChanged.connect(lambda: self.update_analytics())
            comparison_options_layout.addWidget(self.comparison_style)
            
            comparison_options_layout.addStretch()
            
            comparison_layout.addWidget(comparison_options_frame)
            
            # Create the figure and canvas
            self.comparison_figure = Figure(figsize=(6, 5), dpi=100)
            self.comparison_canvas = FigureCanvas(self.comparison_figure)
            comparison_layout.addWidget(self.comparison_canvas)
            
            # Add to tabs
            self.chart_tabs.addTab(comparison_tab, "Category Comparison")
            
            # Trend Analysis Tab (new chart)
            trend_tab = QWidget()
            trend_layout = QVBoxLayout(trend_tab)
            
            # Add customization options for trend chart
            trend_options_frame = QFrame()
            trend_options_layout = QHBoxLayout(trend_options_frame)
            
            trend_options_layout.addWidget(QLabel("Trend Metric:"))
            self.trend_metric = QComboBox()
            self.trend_metric.addItems(["Daily Time", "Energy Level", "Mood Level", "Category Balance"])
            self.trend_metric.currentIndexChanged.connect(lambda: self.update_analytics())
            trend_options_layout.addWidget(self.trend_metric)
            
            trend_options_layout.addWidget(QLabel("Show Trend Line:"))
            self.trend_show_line = QCheckBox()
            self.trend_show_line.setChecked(True)
            self.trend_show_line.stateChanged.connect(lambda: self.update_analytics())
            trend_options_layout.addWidget(self.trend_show_line)
            
            trend_options_layout.addStretch()
            
            trend_layout.addWidget(trend_options_frame)
            
            # Create the figure and canvas
            self.trend_figure = Figure(figsize=(6, 5), dpi=100)
            self.trend_canvas = FigureCanvas(self.trend_figure)
            trend_layout.addWidget(self.trend_canvas)
            
            # Add to tabs
            self.chart_tabs.addTab(trend_tab, "Trend Analysis")
            
        else:
            no_charts_label = QLabel("Matplotlib not available. Charts cannot be displayed.")
            no_charts_label.setStyleSheet("color: #EF4444; font-size: 16px; padding: 20px;")
            no_charts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            analytics_layout.addWidget(no_charts_label)
            
        # Add to tab widget
        self.tab_widget.addTab(analytics_tab, "Analytics")
        
    def setup_reports_tab(self):
        """Set up the reports tab with detailed time analysis."""
        reports_tab = QWidget()
        reports_layout = QVBoxLayout(reports_tab)
        
        # Report type selection
        report_type_frame = QFrame()
        report_type_layout = QHBoxLayout(report_type_frame)
        
        report_type_layout.addWidget(QLabel("Report Type:"))
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Daily Summary", 
            "Weekly Summary", 
            "Category Breakdown", 
            "Productivity Patterns",
            "Time Distribution", 
            "Energy & Mood Analysis"
        ])
        self.report_type_combo.currentIndexChanged.connect(self.change_report_type)
        report_type_layout.addWidget(self.report_type_combo)
        
        # Date range for reports
        report_type_layout.addWidget(QLabel("Date Range:"))
        
        self.report_start_date = QDateEdit(self.current_date.addDays(-7))
        self.report_start_date.setCalendarPopup(True)
        report_type_layout.addWidget(self.report_start_date)
        
        report_type_layout.addWidget(QLabel("to"))
        
        self.report_end_date = QDateEdit(self.current_date)
        self.report_end_date.setCalendarPopup(True)
        report_type_layout.addWidget(self.report_end_date)
        
        self.generate_report_btn = QPushButton("Generate Report")
        self.generate_report_btn.clicked.connect(self.generate_report)
        report_type_layout.addWidget(self.generate_report_btn)
        
        reports_layout.addWidget(report_type_frame)
        
        # Report content area
        self.report_content = QTextEdit()
        self.report_content.setReadOnly(True)
        reports_layout.addWidget(self.report_content)
        
        # Export options
        export_frame = QFrame()
        export_layout = QHBoxLayout(export_frame)
        
        export_layout.addStretch()
        
        self.export_pdf_btn = QPushButton("Export to PDF")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        export_layout.addWidget(self.export_pdf_btn)
        
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        export_layout.addWidget(self.export_csv_btn)
        
        reports_layout.addWidget(export_frame)
        
        # Add to tab widget
        self.tab_widget.addTab(reports_tab, "Reports")
        
    def setup_energy_tab(self):
        """Set up the energy and mood tracking tab."""
        energy_tab = QWidget()
        energy_layout = QVBoxLayout(energy_tab)
        
        # Energy and mood tracking section
        tracking_group = QGroupBox("Track Your Energy & Mood")
        tracking_layout = QGridLayout(tracking_group)
        
        # Energy level
        tracking_layout.addWidget(QLabel("Energy Level:"), 0, 0)
        
        self.energy_slider = QSlider(Qt.Orientation.Horizontal)
        self.energy_slider.setMinimum(1)
        self.energy_slider.setMaximum(10)
        self.energy_slider.setValue(5)
        self.energy_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.energy_slider.setTickInterval(1)
        tracking_layout.addWidget(self.energy_slider, 0, 1)
        
        self.energy_value = QLabel("5")
        tracking_layout.addWidget(self.energy_value, 0, 2)
        self.energy_slider.valueChanged.connect(lambda v: self.energy_value.setText(str(v)))
        
        # Mood level
        tracking_layout.addWidget(QLabel("Mood Level:"), 1, 0)
        
        self.mood_slider = QSlider(Qt.Orientation.Horizontal)
        self.mood_slider.setMinimum(1)
        self.mood_slider.setMaximum(10)
        self.mood_slider.setValue(5)
        self.mood_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.mood_slider.setTickInterval(1)
        tracking_layout.addWidget(self.mood_slider, 1, 1)
        
        self.mood_value = QLabel("5")
        tracking_layout.addWidget(self.mood_value, 1, 2)
        self.mood_slider.valueChanged.connect(lambda v: self.mood_value.setText(str(v)))
        
        # Notes
        tracking_layout.addWidget(QLabel("Notes:"), 2, 0)
        
        self.energy_notes = QTextEdit()
        self.energy_notes.setMaximumHeight(100)
        tracking_layout.addWidget(self.energy_notes, 2, 1, 1, 2)
        
        # Log button
        self.log_energy_btn = QPushButton("Log Energy & Mood")
        self.log_energy_btn.clicked.connect(self.log_energy_mood)
        tracking_layout.addWidget(self.log_energy_btn, 3, 1)
        
        energy_layout.addWidget(tracking_group)
        
        # Chart of energy and mood over time
        if HAS_MATPLOTLIB:
            self.energy_chart_widget = QWidget()
            energy_chart_layout = QVBoxLayout(self.energy_chart_widget)
            energy_chart_layout.addWidget(QLabel("Energy & Mood Patterns"))
            
            self.energy_figure = Figure(figsize=(5, 4), dpi=100)
            self.energy_canvas = FigureCanvas(self.energy_figure)
            energy_chart_layout.addWidget(self.energy_canvas)
            
            energy_layout.addWidget(self.energy_chart_widget)
            
            # Pattern analysis section
            pattern_group = QGroupBox("Pattern Analysis")
            pattern_layout = QVBoxLayout(pattern_group)
            
            self.patterns_list = QListWidget()
            pattern_layout.addWidget(self.patterns_list)
            
            energy_layout.addWidget(pattern_group)
        
        # Add to tab widget
        self.tab_widget.addTab(energy_tab, "Energy & Mood")
        
    def apply_styles(self):
        """Apply styles to the Daily Tracker view."""
        self.setStyleSheet("""
            #dailyTrackerHeader {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
                padding: 10px;
            }
            #dailyTrackerTitle {
                color: #111827;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 8px 16px;
                color: #1F2937;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
            QTableWidget {
                border: 1px solid #E5E7EB;
                background-color: #FFFFFF;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
            QFrame {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                background-color: #F9FAFB;
                padding: 10px;
            }
        """)
        
    def date_changed(self, new_date):
        """Handle date change in the date picker."""
        self.current_date = new_date
        self.load_entries(new_date)
        
    def previous_day(self):
        """Navigate to the previous day."""
        self.date_edit.setDate(self.current_date.addDays(-1))
        
    def next_day(self):
        """Navigate to the next day."""
        self.date_edit.setDate(self.current_date.addDays(1))
        
    def toggle_tracking(self):
        """Start or stop time tracking."""
        if self.active_entry:
            # Stop current tracking
            self.active_entry.end_time = QTime.currentTime()
            
            # Save to database
            self.save_entry(self.active_entry)
            
            # Update UI
            self.tracking_btn.setText("Start Tracking")
            track_icon = get_icon("play")
            if not track_icon.isNull():
                self.tracking_btn.setIcon(track_icon)
            
            # Update the tracking display
            self.tracking_widget.hide()
            self.empty_state.show()
            
            # Stop timer
            self.timer.stop()
            
            # Reset active entry
            self.active_entry = None
            
            # Refresh entries
            self.load_entries(self.current_date)
        else:
            # Show dialog to start new tracking
            self.start_tracking()
            
    def start_tracking(self):
        """Start a new time tracking session."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Start Time Tracking")
        dialog.resize(500, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                font-size: 14px;
                color: #4B5563;
            }
            QComboBox, QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 10px;
                background-color: #F9FAFB;
                min-height: 20px;
                min-width: 250px;
                font-size: 14px;
            }
            QComboBox:focus, QLineEdit:focus {
                border-color: #4F46E5;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Dialog title
        title_label = QLabel("Start Tracking")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #111827; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(15)
        
        # Category selection
        category_combo = QComboBox()
        category_combo.addItems(self.categories)
        form_layout.addRow("Category:", category_combo)
        
        # Description
        description_input = QLineEdit()
        description_input.setPlaceholderText("What are you working on?")
        form_layout.addRow("Description:", description_input)
        
        # Energy level
        energy_container = QWidget()
        energy_layout = QHBoxLayout(energy_container)
        energy_layout.setContentsMargins(0, 0, 0, 0)
        energy_layout.setSpacing(10)
        
        energy_slider = QSlider(Qt.Orientation.Horizontal)
        energy_slider.setMinimum(1)
        energy_slider.setMaximum(10)
        energy_slider.setValue(5)
        energy_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        energy_slider.setTickInterval(1)
        energy_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #E5E7EB;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4F46E5;
                border: 2px solid white;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #C7D2FE;
                border-radius: 4px;
            }
        """)
        energy_layout.addWidget(energy_slider)
        
        energy_value = QLabel("5")
        energy_value.setMinimumWidth(30)
        energy_value.setStyleSheet("font-weight: bold;")
        energy_layout.addWidget(energy_value)
        energy_slider.valueChanged.connect(lambda v: energy_value.setText(str(v)))
        
        form_layout.addRow("Energy Level (1-10):", energy_container)
        
        # Mood level
        mood_container = QWidget()
        mood_layout = QHBoxLayout(mood_container)
        mood_layout.setContentsMargins(0, 0, 0, 0)
        mood_layout.setSpacing(10)
        
        mood_slider = QSlider(Qt.Orientation.Horizontal)
        mood_slider.setMinimum(1)
        mood_slider.setMaximum(10)
        mood_slider.setValue(5)
        mood_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        mood_slider.setTickInterval(1)
        mood_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #E5E7EB;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #8B5CF6;
                border: 2px solid white;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #DDD6FE;
                border-radius: 4px;
            }
        """)
        mood_layout.addWidget(mood_slider)
        
        mood_value = QLabel("5")
        mood_value.setMinimumWidth(30)
        mood_value.setStyleSheet("font-weight: bold;")
        mood_layout.addWidget(mood_value)
        mood_slider.valueChanged.connect(lambda v: mood_value.setText(str(v)))
        
        form_layout.addRow("Mood Level (1-10):", mood_container)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #4B5563;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        start_btn = QPushButton("Start Tracking")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #4338CA;
            }
        """)
        start_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(start_btn)
        
        layout.addLayout(button_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Create new time entry
            self.active_entry = TimeEntry(
                date=self.current_date,
                start_time=QTime.currentTime(),
                category=category_combo.currentText(),
                description=description_input.text(),
                energy_level=energy_slider.value(),
                mood_level=mood_slider.value()
            )
            
            # Update UI
            self.tracking_btn.setText("Stop Tracking")
            stop_icon = get_icon("stop")
            if not stop_icon.isNull():
                self.tracking_btn.setIcon(stop_icon)
            
            activity_info = f"{self.active_entry.category}: {self.active_entry.description}"
            self.tracking_status.setText(activity_info)
            
            # Show tracking UI
            self.empty_state.hide()
            self.tracking_widget.show()
            
            # Start timer
            self.timer.start(1000)  # Update every second
            
    def update_current_timer(self):
        """Update the current tracking timer and multi-tracking timers."""
        # Handle single tracking
        if self.active_entry:
            # Calculate elapsed time
            start_time = self.active_entry.start_time
            current_time = QTime.currentTime()
            
            # Convert to seconds
            start_secs = start_time.hour() * 3600 + start_time.minute() * 60 + start_time.second()
            current_secs = current_time.hour() * 3600 + current_time.minute() * 60 + current_time.second()
            
            # Handle crossing midnight
            if current_secs < start_secs:
                current_secs += 24 * 3600
                
            elapsed_secs = current_secs - start_secs
            
            # Format as HH:MM:SS
            hours = elapsed_secs // 3600
            minutes = (elapsed_secs % 3600) // 60
            seconds = elapsed_secs % 60
                
            self.tracking_time.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Update multi-tracking timers
        if hasattr(self, 'tracking_activities'):
            for entry in self.tracking_activities:
                if hasattr(entry, 'elapsed_label'):
                    elapsed_seconds = entry.start_time.secsTo(QTime.currentTime())
                    if elapsed_seconds < 0:  # Handle day change
                        elapsed_seconds += 24 * 3600
                    
                    hours = elapsed_seconds // 3600
                    minutes = (elapsed_seconds % 3600) // 60
                    seconds = elapsed_seconds % 60
                    
                    entry.elapsed_label.setText(f"Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def add_entry(self):
        """Add a new time entry manually."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Time Entry")
        dialog.resize(500, 450)  # Set a reasonable default size
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                font-size: 13px;
                color: #4B5563;
            }
            QLineEdit, QDateEdit, QTimeEdit, QComboBox {
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #F9FAFB;
                min-width: 180px;
                min-height: 20px;
            }
            QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QComboBox:focus {
                border-color: #4F46E5;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Add title and description
        title_label = QLabel("Add New Time Entry")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        description_label = QLabel("Record time spent on activities by filling out the form below.")
        description_label.setStyleSheet("color: #6B7280; margin-bottom: 15px;")
        layout.addWidget(description_label)
        
        # Form layout for better alignment
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(15)
        
        # Date selection (default to current date)
        date_edit = QDateEdit(self.current_date)
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("MMMM d, yyyy")
        form_layout.addRow("Date:", date_edit)
        
        # Time range
        time_container = QWidget()
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(10)
        
        start_time_edit = QTimeEdit(QTime.currentTime().addSecs(-3600))  # Default to 1 hour ago
        start_time_edit.setDisplayFormat("hh:mm AP")
        time_layout.addWidget(start_time_edit)
        
        time_layout.addWidget(QLabel("to"))
        
        end_time_edit = QTimeEdit(QTime.currentTime())
        end_time_edit.setDisplayFormat("hh:mm AP")
        time_layout.addWidget(end_time_edit)
        
        form_layout.addRow("Time Range:", time_container)
        
        # Category with colored icons
        category_combo = QComboBox()
        category_combo.addItems(self.categories)
        form_layout.addRow("Category:", category_combo)
        
        # Description
        description_input = QLineEdit()
        description_input.setPlaceholderText("What did you work on?")
        form_layout.addRow("Description:", description_input)
        
        # Sliders container 
        sliders_container = QWidget()
        sliders_layout = QVBoxLayout(sliders_container)
        sliders_layout.setContentsMargins(0, 0, 0, 0)
        sliders_layout.setSpacing(15)
        
        # Energy level
        energy_container = QWidget()
        energy_layout = QHBoxLayout(energy_container)
        energy_layout.setContentsMargins(0, 0, 0, 0)
        energy_layout.setSpacing(10)
        
        energy_slider = QSlider(Qt.Orientation.Horizontal)
        energy_slider.setMinimum(1)
        energy_slider.setMaximum(10)
        energy_slider.setValue(5)
        energy_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        energy_slider.setTickInterval(1)
        energy_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #E5E7EB;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4F46E5;
                border: 2px solid white;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #C7D2FE;
                border-radius: 4px;
            }
        """)
        energy_layout.addWidget(energy_slider)
        
        energy_value = QLabel("5")
        energy_value.setStyleSheet("font-weight: bold; min-width: 15px;")
        energy_layout.addWidget(energy_value)
        energy_slider.valueChanged.connect(lambda v: energy_value.setText(str(v)))
        
        sliders_layout.addWidget(QLabel("Energy Level (1-10):"))
        sliders_layout.addWidget(energy_container)
        
        # Mood level
        mood_container = QWidget()
        mood_layout = QHBoxLayout(mood_container)
        mood_layout.setContentsMargins(0, 0, 0, 0)
        mood_layout.setSpacing(10)
        
        mood_slider = QSlider(Qt.Orientation.Horizontal)
        mood_slider.setMinimum(1)
        mood_slider.setMaximum(10)
        mood_slider.setValue(5)
        mood_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        mood_slider.setTickInterval(1)
        mood_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #E5E7EB;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #8B5CF6;
                border: 2px solid white;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #DDD6FE;
                border-radius: 4px;
            }
        """)
        mood_layout.addWidget(mood_slider)
        
        mood_value = QLabel("5")
        mood_value.setStyleSheet("font-weight: bold; min-width: 15px;")
        mood_layout.addWidget(mood_value)
        mood_slider.valueChanged.connect(lambda v: mood_value.setText(str(v)))
        
        sliders_layout.addWidget(QLabel("Mood Level (1-10):"))
        sliders_layout.addWidget(mood_container)
        
        layout.addLayout(form_layout)
        layout.addWidget(sliders_container)
        
        # Add spacer
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #4B5563;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Entry")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #4338CA;
            }
            QPushButton:pressed {
                background-color: #3730A3;
            }
        """)
        save_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Create and save the entry
            entry = TimeEntry(
                date=date_edit.date(),
                start_time=start_time_edit.time(),
                end_time=end_time_edit.time(),
                category=category_combo.currentText(),
                description=description_input.text(),
                energy_level=energy_slider.value(),
                mood_level=mood_slider.value()
            )
            
            self.save_entry(entry)
            
            # Refresh if on the same date
            if date_edit.date() == self.current_date:
                self.load_entries(self.current_date)
                
    def save_entry(self, entry):
        """Save a time entry to the database."""
        if not self.cursor:
            return
            
        try:
            date_str = entry.date.toString("yyyy-MM-dd")
            
            self.cursor.execute("""
                INSERT INTO time_entries 
                (id, date, start_time, end_time, category, description, energy_level, mood_level) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                date_str,
                entry.start_time.toString("HH:mm:ss"),
                entry.end_time.toString("HH:mm:ss") if entry.end_time else None,
                entry.category,
                entry.description,
                entry.energy_level,
                entry.mood_level
            ))
            
            self.connection.commit()
            
        except Exception as e:
            print(f"Error saving time entry: {e}")
            
    def update_entry(self, entry):
        """Update an existing time entry in the database."""
        if not self.cursor:
            return
            
        try:
            self.cursor.execute("""
                UPDATE time_entries 
                SET date = ?, start_time = ?, end_time = ?, category = ?, 
                    description = ?, energy_level = ?, mood_level = ?
                WHERE id = ?
            """, (
                entry.date.toString("yyyy-MM-dd"),
                entry.start_time.toString("HH:mm:ss"),
                entry.end_time.toString("HH:mm:ss") if entry.end_time else None,
                entry.category,
                entry.description,
                entry.energy_level,
                entry.mood_level,
                self.name_edit.toPlainText() if hasattr(self, 'name_edit') else None,
                entry.id
            ))
            
            self.connection.commit()
            
        except Exception as e:
            print(f"Error updating time entry: {e}")
            
    def delete_entry(self, entry_id):
        """Delete a time entry from the database."""
        if not self.cursor:
            return
            
        try:
            self.cursor.execute("DELETE FROM time_entries WHERE id = ?", (entry_id,))
            self.connection.commit()
            
        except Exception as e:
            print(f"Error deleting time entry: {e}")
            
    def load_entries(self, date):
        """Load time entries for the given date."""
        if not self.cursor:
            return
            
        try:
            # Clear existing entries
            self.time_entries = []
            
            # Query database
            self.cursor.execute("""
                SELECT id, date, start_time, end_time, category, description, energy_level, mood_level 
                FROM time_entries 
                WHERE date = ?
                ORDER BY start_time
            """, (date.toString("yyyy-MM-dd"),))
            
            rows = self.cursor.fetchall()
            
            for row in rows:
                entry = TimeEntry(
                    id=row[0],
                    date=QDate.fromString(row[1], "yyyy-MM-dd"),
                    start_time=QTime.fromString(row[2], "HH:mm:ss"),
                    end_time=QTime.fromString(row[3], "HH:mm:ss") if row[3] else None,
                    category=row[4],
                    description=row[5],
                    energy_level=row[6],
                    mood_level=row[7]
                )
                self.time_entries.append(entry)
                
            # Refresh the UI
            self.refresh_entries_table()
            self.update_summary()
            
        except Exception as e:
            print(f"Error loading time entries: {e}")
            
    def refresh_entries_table(self):
        """Refresh the time entries table with current data."""
        self.entries_table.setRowCount(0)
        if not self.time_entries:
            self.entries_table.setRowCount(1)
            for col in range(6):
                self.entries_table.setItem(0, col, QTableWidgetItem(""))
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setContentsMargins(10, 20, 10, 20)
            empty_message = QLabel("No time entries for this day. Start tracking or add entries manually.")
            empty_message.setStyleSheet("color: #6B7280; font-size: 16px;")
            empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_message)
            self.entries_table.setSpan(0, 0, 1, 6)
            self.entries_table.setCellWidget(0, 0, empty_widget)
            return
        for entry in self.time_entries:
            row_position = self.entries_table.rowCount()
            self.entries_table.insertRow(row_position)
            self.entries_table.setRowHeight(row_position, 65)
            self.entries_table.setItem(row_position, 0, QTableWidgetItem(entry.start_time.toString("HH:mm")))
            end_time_text = entry.end_time.toString("HH:mm") if entry.end_time else "In progress"
            self.entries_table.setItem(row_position, 1, QTableWidgetItem(end_time_text))
            duration_mins = entry.duration_minutes()
            hours = duration_mins // 60
            mins = duration_mins % 60
            self.entries_table.setItem(row_position, 2, QTableWidgetItem(f"{hours}h {mins}m"))
            self.entries_table.setItem(row_position, 3, QTableWidgetItem(entry.category))
            self.entries_table.setItem(row_position, 4, QTableWidgetItem(entry.description))
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(16)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedSize(70, 25)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #EEF2FF;
                    color: #4F46E5;
                    border: 1px solid #C7D2FE;
                    border-radius: 6px;
                    font-size: 15px;
                    font-weight: bold;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #C7D2FE;
                }
            """)
            edit_btn.clicked.connect(lambda checked, e=entry: self.edit_entry(e))
            actions_layout.addWidget(edit_btn)
            delete_btn = QPushButton("Delete")
            delete_btn.setFixedSize(70, 25)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FEE2E2;
                    color: #EF4444;
                    border: 1px solid #FECACA;
                    border-radius: 6px;
                    font-size: 15px;
                    font-weight: bold;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #FECACA;
                }
            """)
            delete_btn.clicked.connect(lambda checked, e=entry: self.confirm_delete_entry(e))
            actions_layout.addWidget(delete_btn)
            self.entries_table.setCellWidget(row_position, 5, actions_widget)
            
    def update_summary(self):
        """Update the summary section with current data."""
        # Calculate total time
        total_mins = sum(entry.duration_minutes() for entry in self.time_entries)
        total_hours = total_mins // 60
        total_mins_remainder = total_mins % 60
        self.total_time_value.setText(f"{total_hours}h {total_mins_remainder}m")
        
        # Calculate category breakdowns
        category_times = {}
        for entry in self.time_entries:
            category = entry.category
            duration = entry.duration_minutes()
            
            if category in category_times:
                category_times[category] += duration
            else:
                category_times[category] = duration
                
        # Update category labels
        for category in ["Work", "Meeting", "Break"]:
            category_label = self.findChild(QLabel, f"category_{category}")
            if category_label:
                mins = category_times.get(category, 0)
                hours = mins // 60
                mins_remainder = mins % 60
                category_label.setText(f"{hours}h {mins_remainder}m")
                
    def edit_entry(self, entry):
        """Edit an existing time entry."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Time Entry")
        
        layout = QVBoxLayout(dialog)
        
        # Date selection
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date:"))
        
        date_edit = QDateEdit(entry.date)
        date_edit.setCalendarPopup(True)
        date_layout.addWidget(date_edit)
        
        layout.addLayout(date_layout)
        
        # Time range
        time_layout = QHBoxLayout()
        
        time_layout.addWidget(QLabel("Start Time:"))
        start_time_edit = QTimeEdit(entry.start_time)
        time_layout.addWidget(start_time_edit)
        
        time_layout.addWidget(QLabel("End Time:"))
        end_time_edit = QTimeEdit(entry.end_time or QTime.currentTime())
        time_layout.addWidget(end_time_edit)
        
        layout.addLayout(time_layout)
        
        # Category
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        
        category_combo = QComboBox()
        category_combo.addItems(self.categories)
        index = category_combo.findText(entry.category)
        if index >= 0:
            category_combo.setCurrentIndex(index)
        category_layout.addWidget(category_combo)
        
        layout.addLayout(category_layout)
        
        # Description
        description_layout = QHBoxLayout()
        description_layout.addWidget(QLabel("Description:"))
        
        description_input = QLineEdit(entry.description)
        description_layout.addWidget(description_input)
        
        layout.addLayout(description_layout)
        
        # Energy and mood levels
        energy_layout = QHBoxLayout()
        energy_layout.addWidget(QLabel("Energy Level (1-10):"))
        
        energy_slider = QSlider(Qt.Orientation.Horizontal)
        energy_slider.setMinimum(1)
        energy_slider.setMaximum(10)
        energy_slider.setValue(entry.energy_level)
        energy_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        energy_layout.addWidget(energy_slider)
        
        energy_value = QLabel(str(entry.energy_level))
        energy_layout.addWidget(energy_value)
        energy_slider.valueChanged.connect(lambda v: energy_value.setText(str(v)))
        
        layout.addLayout(energy_layout)
        
        mood_layout = QHBoxLayout()
        mood_layout.addWidget(QLabel("Mood Level (1-10):"))
        
        mood_slider = QSlider(Qt.Orientation.Horizontal)
        mood_slider.setMinimum(1)
        mood_slider.setMaximum(10)
        mood_slider.setValue(entry.mood_level)
        mood_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        mood_layout.addWidget(mood_slider)
        
        mood_value = QLabel(str(entry.mood_level))
        mood_layout.addWidget(mood_value)
        mood_slider.valueChanged.connect(lambda v: mood_value.setText(str(v)))
        
        layout.addLayout(mood_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update entry
            entry.date = date_edit.date()
            entry.start_time = start_time_edit.time()
            entry.end_time = end_time_edit.time()
            entry.category = category_combo.currentText()
            entry.description = description_input.text()
            entry.energy_level = energy_slider.value()
            entry.mood_level = mood_slider.value()
            
            # Save to database
            self.update_entry(entry)
            
            # Refresh if on the same date
            if date_edit.date() == self.current_date:
                self.load_entries(self.current_date)
                
    def confirm_delete_entry(self, entry):
        """Confirm and delete a time entry."""
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete this time entry?\n\n{entry.category}: {entry.description}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_entry(entry.id)
            self.load_entries(self.current_date)
            
    def log_energy_mood(self):
        """Log current energy and mood levels."""
        if not self.cursor:
            return
            
        try:
            current_time = QTime.currentTime()
            
            self.cursor.execute("""
                INSERT INTO energy_patterns (date, time, energy_level, mood_level, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.current_date.toString("yyyy-MM-dd"),
                current_time.toString("HH:mm:ss"),
                self.energy_slider.value(),
                self.mood_slider.value(),
                self.energy_notes.toPlainText()
            ))
            
            self.conn.commit()
            
            # Clear form
            self.energy_slider.setValue(5)
            self.mood_slider.setValue(5)
            self.energy_notes.clear()
            
            # Update charts
            if HAS_MATPLOTLIB:
                self.update_energy_chart()
                
            QMessageBox.information(self, "Success", "Energy and mood recorded successfully!")
            
        except Exception as e:
            print(f"Error logging energy and mood: {e}")
            QMessageBox.warning(self, "Error", f"Could not save energy and mood data: {e}")
            
    def set_date_range(self, range_type):
        """Set date range for analytics."""
        end_date = QDate.currentDate()
        
        if range_type == "week":
            # Current week (Monday to Sunday)
            day_of_week = end_date.dayOfWeek()
            start_date = end_date.addDays(-(day_of_week - 1))
        elif range_type == "month":
            # Current month
            start_date = QDate(end_date.year(), end_date.month(), 1)
        else:
            # Default to last 7 days
            start_date = end_date.addDays(-7)
            
        self.start_date_edit.setDate(start_date)
        self.end_date_edit.setDate(end_date)
        self.update_analytics()
        
    # Add placeholder methods for analytics and reports functionality
    def update_analytics(self):
        """Update the analytics charts."""
        if HAS_MATPLOTLIB:
            start_date = self.start_date_edit.date()
            end_date = self.end_date_edit.date()
            
            # Ensure the end date is after or on the start date
            if end_date < start_date:
                QMessageBox.warning(self, "Invalid Date Range", "End date must be after start date.")
                return
            
            # Get the current active tab
            current_tab_index = self.chart_tabs.currentIndex()
            tab_name = self.chart_tabs.tabText(current_tab_index)
            
            # Update only the active tab's chart to improve performance
            if tab_name == "Category Distribution":
                self.update_category_pie_chart(start_date, end_date)
            elif tab_name == "Time Distribution":
                self.update_daily_distribution_chart(start_date, end_date)
            elif tab_name == "Productivity Patterns":
                self.update_productivity_patterns_chart(start_date, end_date)
            elif tab_name == "Time Heatmap":
                self.update_time_heatmap_chart(start_date, end_date)
            elif tab_name == "Category Comparison":
                self.update_category_comparison_chart(start_date, end_date)
            elif tab_name == "Trend Analysis":
                self.update_trend_analysis_chart(start_date, end_date)
    
    def update_category_pie_chart(self, start_date, end_date):
        """Update the category distribution pie chart."""
        if not HAS_MATPLOTLIB or not self.cursor:
            return
        
        try:
            # Clear previous chart
            self.category_figure.clear()
            
            # Create a new axis
            ax = self.category_figure.add_subplot(111)
            
            # Query time entries between the dates, grouped by category
            # Apply sort order based on user selection
            sort_option = self.category_sort_order.currentText()
            if sort_option == "Time (Descending)":
                order_clause = "ORDER BY duration DESC"
            elif sort_option == "Time (Ascending)":
                order_clause = "ORDER BY duration ASC"
            else:  # Alphabetical
                order_clause = "ORDER BY category"
                
            self.cursor.execute(f"""
                SELECT category, SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as duration
                FROM time_entries
                WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
                GROUP BY category
                {order_clause}
            """, (
                start_date.toString("yyyy-MM-dd"),
                end_date.toString("yyyy-MM-dd")
            ))
            
            results = self.cursor.fetchall()
            
            if not results:
                ax.text(0.5, 0.5, "No data available for selected period",
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax.transAxes, fontsize=12, color='gray')
                self.category_canvas.draw()
                return
                
            # Extract categories and durations
            categories = [row[0] for row in results]
            durations = [row[1] for row in results]
            
            # Get category colors
            colors = []
            color_scheme = self.category_color_scheme.currentText()
            
            if color_scheme == "Default":
                # Use colors from database
                for category in categories:
                    # Try to get color from database
                    self.cursor.execute("SELECT color FROM time_categories WHERE name = ?", (category,))
                    result = self.cursor.fetchone()
                    if result:
                        colors.append(result[0])
                    else:
                        # Fallback to a default color
                        colors.append("#6B7280")
            else:
                # Use predefined color schemes
                if color_scheme == "Pastel":
                    cmap = plt.cm.Pastel1
                elif color_scheme == "Bright":
                    cmap = plt.cm.Set1
                elif color_scheme == "Dark":
                    cmap = plt.cm.Dark2
                elif color_scheme == "Colorblind-friendly":
                    cmap = plt.cm.tab10
                else:
                    cmap = plt.cm.Paired
                    
                for i in range(len(categories)):
                    colors.append(cmap(i % cmap.N))
            
            # Choose chart type based on user selection
            chart_type = self.category_chart_type.currentText()
            
            if chart_type == "Pie Chart":
                # Create the pie chart
                wedges, texts, autotexts = ax.pie(
                    durations, 
                    labels=None, 
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': 'white', 'linewidth': 1}
                )
                
                # Customize text properties
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(8)
                
            elif chart_type == "Donut Chart":
                # Create a donut chart (pie chart with a hole)
                wedges, texts, autotexts = ax.pie(
                    durations, 
                    labels=None, 
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': 'white', 'linewidth': 1},
                    pctdistance=0.85
                )
                
                # Draw a white circle at the center to create donut
                centre_circle = plt.Circle((0, 0), 0.70, fc='white')
                ax.add_patch(centre_circle)
                
                # Customize text properties
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(8)
                    
            else:  # Bar Chart
                # Create horizontal bar chart for categories
                y_pos = np.arange(len(categories))
                ax.barh(y_pos, durations, align='center', color=colors)
                ax.set_yticks(y_pos)
                ax.set_yticklabels(categories)
                ax.invert_yaxis()  # Labels read top-to-bottom
                ax.set_xlabel('Minutes')
                
                # Add value labels to bars
                for i, v in enumerate(durations):
                    hours, mins = divmod(int(v), 60)
                    label = f"{hours}h {mins}m"
                    ax.text(v + 5, i, label, va='center')
            
            # Equal aspect ratio for pie charts
            if chart_type != "Bar Chart":
                ax.axis('equal')
            
            # Add legend
            total_minutes = sum(durations)
            legend_labels = [f"{cat} ({self.format_duration(dur)})" 
                            for cat, dur in zip(categories, durations)]
            
            if chart_type != "Bar Chart":
                ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            else:
                # For bar chart, add a title instead
                hours, mins = divmod(int(total_minutes), 60)
                ax.set_title(f"Time by Category (Total: {hours}h {mins}m)")
            
            # Add total time for pie charts
            if chart_type != "Bar Chart":
                hours, mins = divmod(int(total_minutes), 60)
                ax.set_title(f"Total: {hours}h {mins}m", fontsize=10, pad=10)
            
            # Draw the chart
            self.category_canvas.draw()
            
        except Exception as e:
            print(f"Error updating category pie chart: {e}")
    
    def format_duration(self, minutes):
        """Format duration in minutes to hours and minutes."""
        hours, mins = divmod(int(minutes), 60)
        return f"{hours}h {mins}m"
    
    def update_daily_distribution_chart(self, start_date, end_date):
        """Update the daily time distribution chart."""
        if not HAS_MATPLOTLIB or not self.cursor:
            return
        
        try:
            # Clear previous chart
            self.daily_figure.clear()
            
            # Create a new axis
            ax = self.daily_figure.add_subplot(111)
            
            # Determine grouping based on user selection
            group_by = self.daily_group_by.currentText()
            
            if group_by == "Day":
                # Group by individual days
                group_sql = "date"
                format_str = "%Y-%m-%d"
                date_format = "%d %b"
                title_suffix = "by Day"
            elif group_by == "Week":
                # Group by week
                group_sql = "strftime('%W', date)"
                format_str = "%Y-%W"  # Year and week number
                date_format = "Week %W"
                title_suffix = "by Week"
            else:  # Month
                # Group by month
                group_sql = "strftime('%Y-%m', date)"
                format_str = "%Y-%m"
                date_format = "%b %Y"
                title_suffix = "by Month"
            
            # Determine if we should show categories
            show_categories = self.daily_show_categories.isChecked()
            
            if show_categories:
                # Query time entries by category
                self.cursor.execute(f"""
                    SELECT 
                        {group_sql} as time_period,
                        category,
                        SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as duration
                    FROM time_entries
                    WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
                    GROUP BY time_period, category
                    ORDER BY time_period, category
                """, (
                    start_date.toString("yyyy-MM-dd"),
                    end_date.toString("yyyy-MM-dd")
                ))
                
                category_results = self.cursor.fetchall()
                
                if not category_results:
                    ax.text(0.5, 0.5, "No data available for selected period",
                            horizontalalignment='center', verticalalignment='center',
                            transform=ax.transAxes, fontsize=12, color='gray')
                    self.daily_canvas.draw()
                    return
                
                # Process data by category
                time_periods = []
                categories = set()
                data_by_category = {}
                
                for period, category, duration in category_results:
                    if period not in time_periods:
                        time_periods.append(period)
                    categories.add(category)
                    
                    if category not in data_by_category:
                        data_by_category[category] = {}
                    
                    data_by_category[category][period] = duration / 60  # Convert to hours
                
                # Convert to lists for plotting
                categories = sorted(list(categories))
                time_periods = sorted(time_periods)
                
                # Format dates
                if group_by == "Day":
                    formatted_periods = [datetime.strptime(p, format_str).date() for p in time_periods]
                else:
                    formatted_periods = [datetime.strptime(p, format_str) for p in time_periods]
                
                # Create a chart based on selected type
                chart_type = self.daily_chart_type.currentText()
                
                if chart_type == "Bar Chart":
                    # Create a stacked bar chart
                    bottoms = np.zeros(len(time_periods))
                    bar_width = 0.8
                    
                    # Get colors for categories
                    category_colors = []
                    for category in categories:
                        self.cursor.execute("SELECT color FROM time_categories WHERE name = ?", (category,))
                        result = self.cursor.fetchone()
                        if result:
                            category_colors.append(result[0])
                        else:
                            category_colors.append("#6B7280")
                    
                    # Plot each category as a segment of the stacked bar
                    for i, category in enumerate(categories):
                        # Get values for this category across all time periods
                        values = []
                        for period in time_periods:
                            values.append(data_by_category[category].get(period, 0))
                        
                        ax.bar(formatted_periods, values, bar_width, bottom=bottoms, 
                               label=category, color=category_colors[i % len(category_colors)])
                        bottoms += np.array(values)
                    
                    # Add legend
                    ax.legend(title="Categories", loc='upper left')
                    
                elif chart_type == "Line Chart":
                    # Create a multi-line chart
                    for i, category in enumerate(categories):
                        values = []
                        for period in time_periods:
                            values.append(data_by_category[category].get(period, 0))
                        
                        ax.plot(formatted_periods, values, marker='o', label=category)
                    
                    # Add legend
                    ax.legend(title="Categories", loc='upper left')
                    
                else:  # Area Chart
                    # Create a stacked area chart
                    values = np.zeros((len(categories), len(time_periods)))
                    
                    for i, category in enumerate(categories):
                        for j, period in enumerate(time_periods):
                            values[i, j] = data_by_category[category].get(period, 0)
                    
                    ax.stackplot(formatted_periods, values, labels=categories)
                    
                    # Add legend
                    ax.legend(title="Categories", loc='upper left')
                
            else:
                # Query time entries grouped by the selected time period
                self.cursor.execute(f"""
                    SELECT 
                        {group_sql} as time_period,
                        SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as duration
                    FROM time_entries
                    WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
                    GROUP BY time_period
                    ORDER BY time_period
                """, (
                    start_date.toString("yyyy-MM-dd"),
                    end_date.toString("yyyy-MM-dd")
                ))
                
                results = self.cursor.fetchall()
                
                if not results:
                    ax.text(0.5, 0.5, "No data available for selected period",
                            horizontalalignment='center', verticalalignment='center',
                            transform=ax.transAxes, fontsize=12, color='gray')
                    self.daily_canvas.draw()
                    return
                
                # Extract periods and durations
                periods = [row[0] for row in results]
                durations = [row[1] / 60 for row in results]  # Convert to hours
                
                # Format dates based on grouping
                if group_by == "Day":
                    formatted_periods = [datetime.strptime(p, format_str).date() for p in periods]
                else:
                    formatted_periods = [datetime.strptime(p, format_str) for p in periods]
                
                # Create a chart based on selected type
                chart_type = self.daily_chart_type.currentText()
                
                if chart_type == "Bar Chart":
                    # Create the bar chart
                    bars = ax.bar(formatted_periods, durations, width=0.7, color='#4F46E5', alpha=0.8)
                    
                    # Add data values on top of bars
                    for bar in bars:
                        height = bar.get_height()
                        ax.annotate(f'{height:.1f}h',
                                    xy=(bar.get_x() + bar.get_width() / 2, height),
                                    xytext=(0, 3),  # 3 points vertical offset
                                    textcoords="offset points",
                                    ha='center', va='bottom',
                                    fontsize=8)
                                    
                elif chart_type == "Line Chart":
                    # Create line chart
                    ax.plot(formatted_periods, durations, 'o-', color='#4F46E5', linewidth=2)
                    
                    # Add data points
                    for i, (period, value) in enumerate(zip(formatted_periods, durations)):
                        ax.annotate(f'{value:.1f}h',
                                    xy=(period, value),
                                    xytext=(0, 5),
                                    textcoords="offset points",
                                    ha='center',
                                    fontsize=8)
                                    
                else:  # Area Chart
                    # Create area chart
                    ax.fill_between(formatted_periods, durations, color='#4F46E5', alpha=0.5)
                    ax.plot(formatted_periods, durations, color='#4F46E5', linewidth=2)
            
            # Customize appearance
            ax.set_xlabel('Time Period')
            ax.set_ylabel('Hours')
            ax.set_title(f'Time Distribution {title_suffix}')
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Format x-axis with appropriate date format
            if group_by == "Day":
                ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
            elif group_by == "Week":
                # For weeks, use the first day of each week
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: 
                    f"Week {datetime.fromordinal(int(x)).strftime('%W')}"))
            else:
                ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
            
            # Format y-axis with hours
            ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
            
            # Rotate date labels
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
            # Adjust layout
            self.daily_figure.tight_layout()
            
            # Draw the chart
            self.daily_canvas.draw()
            
        except Exception as e:
            print(f"Error updating daily distribution chart: {e}")
    
    def update_productivity_patterns_chart(self, start_date, end_date):
        """Update the productivity patterns chart."""
        if not HAS_MATPLOTLIB or not self.cursor:
            return
        
        try:
            # Clear previous chart
            self.patterns_figure.clear()
            
            # Create a new axis
            ax = self.patterns_figure.add_subplot(111)
            
            # Query time entries with energy and mood levels
            self.cursor.execute("""
                SELECT 
                    time_entries.date, 
                    AVG(time_entries.energy_level) as avg_energy,
                    AVG(time_entries.mood_level) as avg_mood,
                    SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as duration
                FROM time_entries
                WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
                GROUP BY time_entries.date
                ORDER BY time_entries.date
            """, (
                start_date.toString("yyyy-MM-dd"),
                end_date.toString("yyyy-MM-dd")
            ))
            
            results = self.cursor.fetchall()
            
            if not results:
                ax.text(0.5, 0.5, "No data available for selected period",
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax.transAxes, fontsize=12, color='gray')
                self.patterns_canvas.draw()
                return
                
            # Extract dates, energy and mood levels
            dates = [datetime.strptime(row[0], "%Y-%m-%d").date() for row in results]
            energy_levels = [row[1] for row in results]
            mood_levels = [row[2] for row in results]
            durations = [row[3] / 60 for row in results]  # Convert to hours
            
            # Get display options
            show_energy = self.patterns_show_energy.isChecked()
            show_mood = self.patterns_show_mood.isChecked()
            show_time = self.patterns_show_time.isChecked()
            
            # Create the line chart for energy and mood
            if show_energy:
                ax.plot(dates, energy_levels, 'o-', color='#F97316', label='Energy Level', linewidth=2)
            
            if show_mood:
                ax.plot(dates, mood_levels, 'o-', color='#8B5CF6', label='Mood Level', linewidth=2)
            
            # Create second axis for duration if needed
            if show_time:
                ax2 = ax.twinx()
                ax2.bar(dates, durations, alpha=0.2, color='#4F46E5', label='Hours Worked')
                ax2.set_ylabel('Hours')
            
            # Customize appearance
            ax.set_xlabel('Date')
            ax.set_ylabel('Level (1-10)')
            ax.set_title('Productivity Patterns: Energy, Mood & Time')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Set y-axis range for levels
            ax.set_ylim(0, 11)
            
            # Format x-axis with date
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            
            # Rotate date labels
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
            # Combine legends from both axes if needed
            if show_time and (show_energy or show_mood):
                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            else:
                # Only add legend if there are lines to show
                if show_energy or show_mood:
                    ax.legend(loc='upper left')
                if show_time and not (show_energy or show_mood):
                    ax2.legend(loc='upper left')
            
            # Adjust layout
            self.patterns_figure.tight_layout()
            
            # Draw the chart
            self.patterns_canvas.draw()
            
        except Exception as e:
            print(f"Error updating productivity patterns chart: {e}")
            
    def change_report_type(self, index):
        """Change the report type."""
        # Store the current report type index
        self.current_report_type = index
        
        # Update the report when the type changes
        self.generate_report()
        
    def generate_report(self):
        """Generate a report based on selected type and date range."""
        if not self.cursor:
            self.report_content.setHtml("<p>Database not connected. Cannot generate report.</p>")
            return
            
        try:
            # Get date range
            start_date = self.report_start_date.date()
            end_date = self.report_end_date.date()
            
            # Get report type
            report_type = self.report_type_combo.currentText()
            
            # HTML template for report
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #4F46E5; font-size: 24px; }}
                    h2 {{ color: #1F2937; font-size: 18px; margin-top: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                    th, td {{ border: 1px solid #E5E7EB; padding: 8px; text-align: left; }}
                    th {{ background-color: #F3F4F6; color: #1F2937; }}
                    tr:nth-child(even) {{ background-color: #F9FAFB; }}
                    .summary {{ background-color: #EEF2FF; padding: 10px; border-radius: 5px; margin-top: 15px; }}
                    .highlight {{ color: #4F46E5; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>{report_type}</h1>
                <p>Period: {start_date.toString('MMMM d, yyyy')} to {end_date.toString('MMMM d, yyyy')}</p>
            """
            
            # Generate content based on report type
            if report_type == "Daily Summary":
                html += self.generate_daily_summary_report(start_date, end_date)
            elif report_type == "Weekly Summary":
                html += self.generate_weekly_summary_report(start_date, end_date)
            elif report_type == "Category Breakdown":
                html += self.generate_category_breakdown_report(start_date, end_date)
            elif report_type == "Productivity Patterns":
                html += self.generate_productivity_patterns_report(start_date, end_date)
            elif report_type == "Time Distribution":
                html += self.generate_time_distribution_report(start_date, end_date)
            elif report_type == "Energy & Mood Analysis":
                html += self.generate_energy_mood_report(start_date, end_date)
            
            # Close HTML
            html += """
            </body>
            </html>
            """
            
            # Set the HTML content
            self.report_content.setHtml(html)
            
        except Exception as e:
            print(f"Error generating report: {e}")
            self.report_content.setHtml(f"<p>Error generating report: {e}</p>")
            
    def generate_daily_summary_report(self, start_date, end_date):
        """Generate HTML for daily summary report."""
        html = "<h2>Time Entries by Day</h2>"
        
        # Query daily totals
        self.cursor.execute("""
            SELECT 
                date, 
                COUNT(*) as entry_count,
                SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as total_minutes
            FROM time_entries
            WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
            GROUP BY date
            ORDER BY date
        """, (
            start_date.toString("yyyy-MM-dd"),
            end_date.toString("yyyy-MM-dd")
        ))
        
        daily_results = self.cursor.fetchall()
        
        if not daily_results:
            return "<p>No data available for the selected period.</p>"
            
        # Create table for daily summary
        html += """
        <table>
            <tr>
                <th>Date</th>
                <th>Entries</th>
                <th>Total Time</th>
                <th>Categories</th>
            </tr>
        """
        
        total_minutes_overall = 0
        total_entries_overall = 0
        
        for date_str, entry_count, total_minutes in daily_results:
            # Format date
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
            
            # Format duration
            hours, mins = divmod(int(total_minutes), 60)
            duration_str = f"{hours}h {mins}m"
            
            # Get categories for this day
            self.cursor.execute("""
                SELECT DISTINCT category
                FROM time_entries
                WHERE date = ?
            """, (date_str,))
            
            categories = [row[0] for row in self.cursor.fetchall()]
            categories_str = ", ".join(categories)
            
            # Add row to table
            html += f"""
            <tr>
                <td>{formatted_date}</td>
                <td>{entry_count}</td>
                <td>{duration_str}</td>
                <td>{categories_str}</td>
            </tr>
            """
            
            total_minutes_overall += total_minutes
            total_entries_overall += entry_count
        
        html += "</table>"
        
        # Add summary
        hours_overall, mins_overall = divmod(int(total_minutes_overall), 60)
        html += f"""
        <div class="summary">
            <h2>Summary</h2>
            <p>Total time tracked: <span class="highlight">{hours_overall}h {mins_overall}m</span></p>
            <p>Total entries: <span class="highlight">{total_entries_overall}</span></p>
            <p>Average daily time: <span class="highlight">{int(total_minutes_overall / len(daily_results) / 60)}h {int(total_minutes_overall / len(daily_results) % 60)}m</span></p>
        </div>
        """
        
        return html
        
    def generate_weekly_summary_report(self, start_date, end_date):
        """Generate HTML for weekly summary report."""
        html = "<h2>Time by Week</h2>"
        
        # Query data grouped by week
        self.cursor.execute("""
            SELECT 
                strftime('%W', date) as week_num,
                MIN(date) as week_start,
                COUNT(*) as entry_count,
                SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as total_minutes
            FROM time_entries
            WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
            GROUP BY week_num
            ORDER BY week_num
        """, (
            start_date.toString("yyyy-MM-dd"),
            end_date.toString("yyyy-MM-dd")
        ))
        
        weekly_results = self.cursor.fetchall()
        
        if not weekly_results:
            return "<p>No data available for the selected period.</p>"
            
        # Create table for weekly summary
        html += """
        <table>
            <tr>
                <th>Week</th>
                <th>Entries</th>
                <th>Total Time</th>
                <th>Daily Average</th>
                <th>Most Tracked Category</th>
            </tr>
        """
        
        for week_num, week_start, entry_count, total_minutes in weekly_results:
            # Get week date range
            start_obj = datetime.strptime(week_start, "%Y-%m-%d").date()
            # Find week end (Saturday if we consider Sunday as first day of week)
            days_to_end = 6 - start_obj.weekday() if start_obj.weekday() != 6 else 0
            end_obj = start_obj + timedelta(days=days_to_end)
            
            week_range = f"{start_obj.strftime('%b %d')} - {end_obj.strftime('%b %d, %Y')}"
            
            # Calculate daily average (assuming work week of 5 days)
            daily_avg = total_minutes / 5
            hours_avg, mins_avg = divmod(int(daily_avg), 60)
            daily_avg_str = f"{hours_avg}h {mins_avg}m"
            
            # Format total time
            hours, mins = divmod(int(total_minutes), 60)
            duration_str = f"{hours}h {mins}m"
            
            # Find most tracked category for this week
            self.cursor.execute("""
                SELECT 
                    category, 
                    SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as cat_minutes
                FROM time_entries
                WHERE strftime('%W', date) = ? AND date BETWEEN ? AND ? AND end_time IS NOT NULL
                GROUP BY category
                ORDER BY cat_minutes DESC
                LIMIT 1
            """, (
                week_num,
                start_date.toString("yyyy-MM-dd"),
                end_date.toString("yyyy-MM-dd")
            ))
            
            top_category_result = self.cursor.fetchone()
            top_category = top_category_result[0] if top_category_result else "None"
            
            # Add row to table
            html += f"""
            <tr>
                <td>{week_range}</td>
                <td>{entry_count}</td>
                <td>{duration_str}</td>
                <td>{daily_avg_str}</td>
                <td>{top_category}</td>
            </tr>
            """
        
        html += "</table>"
        
        return html
        
    def generate_category_breakdown_report(self, start_date, end_date):
        """Generate HTML for category breakdown report."""
        html = "<h2>Time by Category</h2>"
        
        # Query data grouped by category
        self.cursor.execute("""
            SELECT 
                category,
                COUNT(*) as entry_count,
                SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as total_minutes
            FROM time_entries
            WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
            GROUP BY category
            ORDER BY total_minutes DESC
        """, (
            start_date.toString("yyyy-MM-dd"),
            end_date.toString("yyyy-MM-dd")
        ))
        
        category_results = self.cursor.fetchall()
        
        if not category_results:
            return "<p>No data available for the selected period.</p>"
            
        # Calculate total minutes across all categories
        total_minutes_all = sum(row[2] for row in category_results)
        
        # Create table for category breakdown
        html += """
        <table>
            <tr>
                <th>Category</th>
                <th>Entries</th>
                <th>Total Time</th>
                <th>Percentage</th>
            </tr>
        """
        
        for category, entry_count, total_minutes in category_results:
            # Format duration
            hours, mins = divmod(int(total_minutes), 60)
            duration_str = f"{hours}h {mins}m"
            
            # Calculate percentage
            percentage = (total_minutes / total_minutes_all) * 100 if total_minutes_all > 0 else 0
            
            # Add row to table
            html += f"""
            <tr>
                <td>{category}</td>
                <td>{entry_count}</td>
                <td>{duration_str}</td>
                <td>{percentage:.1f}%</td>
            </tr>
            """
        
        html += "</table>"
        
        # Add summary with top categories
        top_categories = category_results[:3] if len(category_results) >= 3 else category_results
        
        html += """
        <div class="summary">
            <h2>Top Categories</h2>
        """
        
        for i, (category, entries, minutes) in enumerate(top_categories):
            hours, mins = divmod(int(minutes), 60)
            percentage = (minutes / total_minutes_all) * 100 if total_minutes_all > 0 else 0
            
            html += f"""
            <p>{i+1}. <span class="highlight">{category}</span>: {hours}h {mins}m ({percentage:.1f}%)</p>
            """
        
        html += "</div>"
        
        return html
        
    def generate_productivity_patterns_report(self, start_date, end_date):
        """Generate HTML for productivity patterns report."""
        html = "<h2>Energy and Mood Patterns</h2>"
        
        # Query energy and mood data
        self.cursor.execute("""
            SELECT 
                date,
                AVG(energy_level) as avg_energy,
                AVG(mood_level) as avg_mood,
                SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as total_minutes
            FROM time_entries
            WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
            GROUP BY date
            ORDER BY date
        """, (
            start_date.toString("yyyy-MM-dd"),
            end_date.toString("yyyy-MM-dd")
        ))
        
        pattern_results = self.cursor.fetchall()
        
        if not pattern_results:
            return "<p>No data available for the selected period.</p>"
            
        # Create table for patterns
        html += """
        <table>
            <tr>
                <th>Date</th>
                <th>Avg. Energy</th>
                <th>Avg. Mood</th>
                <th>Hours Tracked</th>
            </tr>
        """
        
        total_energy = 0
        total_mood = 0
        days_count = 0
        
        for date_str, avg_energy, avg_mood, total_minutes in pattern_results:
            # Format date
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            formatted_date = date_obj.strftime("%A, %B %d")
            
            # Calculate hours
            hours = total_minutes / 60
            
            # Add row to table
            html += f"""
            <tr>
                <td>{formatted_date}</td>
                <td>{avg_energy:.1f}/10</td>
                <td>{avg_mood:.1f}/10</td>
                <td>{hours:.1f}h</td>
            </tr>
            """
            
            total_energy += avg_energy
            total_mood += avg_mood
            days_count += 1
        
        html += "</table>"
        
        # Add analysis
        if days_count > 0:
            avg_energy_overall = total_energy / days_count
            avg_mood_overall = total_mood / days_count
            
            html += f"""
            <div class="summary">
                <h2>Pattern Analysis</h2>
                <p>Average energy level: <span class="highlight">{avg_energy_overall:.1f}/10</span></p>
                <p>Average mood level: <span class="highlight">{avg_mood_overall:.1f}/10</span></p>
            """
            
            # Correlate energy/mood with productivity
            energy_productivity_corr = self.calculate_correlation(
                [(row[1], row[3]/60) for row in pattern_results]
            )
            
            mood_productivity_corr = self.calculate_correlation(
                [(row[2], row[3]/60) for row in pattern_results]
            )
            
            html += f"""
                <p>Correlation between energy and hours worked: <span class="highlight">{energy_productivity_corr:.2f}</span></p>
                <p>Correlation between mood and hours worked: <span class="highlight">{mood_productivity_corr:.2f}</span></p>
            </div>
            """
        
        return html
        
    def calculate_correlation(self, data_pairs):
        """Calculate Pearson correlation coefficient between two variables."""
        if len(data_pairs) < 2:
            return 0
            
        x_values = [pair[0] for pair in data_pairs]
        y_values = [pair[1] for pair in data_pairs]
        
        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(y_values) / len(y_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator_x = sum((x - x_mean) ** 2 for x in x_values)
        denominator_y = sum((y - y_mean) ** 2 for y in y_values)
        
        if denominator_x == 0 or denominator_y == 0:
            return 0
            
        return numerator / ((denominator_x ** 0.5) * (denominator_y ** 0.5))
        
    def generate_time_distribution_report(self, start_date, end_date):
        """Generate HTML for time distribution report."""
        html = "<h2>Time Distribution by Hour</h2>"
        
        # Query data grouped by hour
        self.cursor.execute("""
            SELECT 
                substr(start_time, 1, 2) as hour,
                COUNT(*) as entry_count,
                SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as total_minutes
            FROM time_entries
            WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
            GROUP BY hour
            ORDER BY hour
        """, (
            start_date.toString("yyyy-MM-dd"),
            end_date.toString("yyyy-MM-dd")
        ))
        
        hour_results = self.cursor.fetchall()
        
        if not hour_results:
            return "<p>No data available for the selected period.</p>"
            
        # Create table for hourly distribution
        html += """
        <table>
            <tr>
                <th>Hour</th>
                <th>Entries</th>
                <th>Total Time</th>
                <th>Percentage</th>
            </tr>
        """
        
        total_minutes_all = sum(row[2] for row in hour_results)
        
        for hour_str, entry_count, total_minutes in hour_results:
            # Format hour
            try:
                hour = int(hour_str)
                if hour < 12:
                    time_label = f"{hour}:00 AM" if hour > 0 else "12:00 AM"
                elif hour == 12:
                    time_label = "12:00 PM"
                else:
                    time_label = f"{hour-12}:00 PM"
            except ValueError:
                time_label = hour_str
                
            # Format duration
            hours, mins = divmod(int(total_minutes), 60)
            duration_str = f"{hours}h {mins}m"
            
            # Calculate percentage
            percentage = (total_minutes / total_minutes_all) * 100 if total_minutes_all > 0 else 0
            
            # Add row to table
            html += f"""
            <tr>
                <td>{time_label}</td>
                <td>{entry_count}</td>
                <td>{duration_str}</td>
                <td>{percentage:.1f}%</td>
            </tr>
            """
        
        html += "</table>"
        
        # Add insights
        html += """
        <div class="summary">
            <h2>Time Distribution Insights</h2>
        """
        
        # Find peak hours (top 3)
        peak_hours = sorted(hour_results, key=lambda x: x[2], reverse=True)[:3]
        
        html += "<p>Peak productivity hours:</p><ol>"
        for hour_str, entries, minutes in peak_hours:
            try:
                hour = int(hour_str)
                if hour < 12:
                    time_label = f"{hour}:00 AM" if hour > 0 else "12:00 AM"
                elif hour == 12:
                    time_label = "12:00 PM"
                else:
                    time_label = f"{hour-12}:00 PM"
            except ValueError:
                time_label = hour_str
                
            hours, mins = divmod(int(minutes), 60)
            percentage = (minutes / total_minutes_all) * 100 if total_minutes_all > 0 else 0
            
            html += f"<li><span class='highlight'>{time_label}</span>: {hours}h {mins}m ({percentage:.1f}%)</li>"
            
        html += "</ol></div>"
        
        return html
        
    def generate_energy_mood_report(self, start_date, end_date):
        """Generate HTML for energy and mood analysis report."""
        html = "<h2>Energy & Mood Analysis</h2>"
        
        # Query energy patterns data
        self.cursor.execute("""
            SELECT 
                date,
                time,
                energy_level,
                mood_level,
                notes
            FROM energy_patterns
            WHERE date BETWEEN ? AND ?
            ORDER BY date, time
        """, (
            start_date.toString("yyyy-MM-dd"),
            end_date.toString("yyyy-MM-dd")
        ))
        
        energy_results = self.cursor.fetchall()
        
        if not energy_results:
            return "<p>No energy and mood data available for the selected period.</p>"
            
        # Create table for energy and mood entries
        html += """
        <table>
            <tr>
                <th>Date & Time</th>
                <th>Energy</th>
                <th>Mood</th>
                <th>Notes</th>
            </tr>
        """
        
        total_energy = 0
        total_mood = 0
        entries_count = 0
        
        for date_str, time_str, energy, mood, notes in energy_results:
            # Format date and time
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
            formatted_datetime = f"{date_obj.strftime('%b %d')} at {time_obj.strftime('%I:%M %p')}"
            
            # Add row to table
            html += f"""
            <tr>
                <td>{formatted_datetime}</td>
                <td>{energy}/10</td>
                <td>{mood}/10</td>
                <td>{notes or "-"}</td>
            </tr>
            """
            
            total_energy += energy
            total_mood += mood
            entries_count += 1
        
        html += "</table>"
        
        # Add analysis
        if entries_count > 0:
            avg_energy = total_energy / entries_count
            avg_mood = total_mood / entries_count
            
            html += f"""
            <div class="summary">
                <h2>Energy & Mood Summary</h2>
                <p>Average energy level: <span class="highlight">{avg_energy:.1f}/10</span></p>
                <p>Average mood level: <span class="highlight">{avg_mood:.1f}/10</span></p>
                <p>Number of entries: <span class="highlight">{entries_count}</span></p>
            </div>
            """
            
            # Group by time of day
            morning_entries = []
            afternoon_entries = []
            evening_entries = []
            
            for date_str, time_str, energy, mood, notes in energy_results:
                time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
                
                if time_obj < time(12, 0):  # Morning
                    morning_entries.append((energy, mood))
                elif time_obj < time(18, 0):  # Afternoon
                    afternoon_entries.append((energy, mood))
                else:  # Evening
                    evening_entries.append((energy, mood))
            
            html += """
            <h2>Time of Day Analysis</h2>
            <table>
                <tr>
                    <th>Time of Day</th>
                    <th>Entries</th>
                    <th>Avg. Energy</th>
                    <th>Avg. Mood</th>
                </tr>
            """
            
            # Morning
            if morning_entries:
                avg_morning_energy = sum(e[0] for e in morning_entries) / len(morning_entries)
                avg_morning_mood = sum(e[1] for e in morning_entries) / len(morning_entries)
                html += f"""
                <tr>
                    <td>Morning (before 12 PM)</td>
                    <td>{len(morning_entries)}</td>
                    <td>{avg_morning_energy:.1f}/10</td>
                    <td>{avg_morning_mood:.1f}/10</td>
                </tr>
                """
            
            # Afternoon
            if afternoon_entries:
                avg_afternoon_energy = sum(e[0] for e in afternoon_entries) / len(afternoon_entries)
                avg_afternoon_mood = sum(e[1] for e in afternoon_entries) / len(afternoon_entries)
                html += f"""
                <tr>
                    <td>Afternoon (12 PM - 6 PM)</td>
                    <td>{len(afternoon_entries)}</td>
                    <td>{avg_afternoon_energy:.1f}/10</td>
                    <td>{avg_afternoon_mood:.1f}/10</td>
                </tr>
                """
            
            # Evening
            if evening_entries:
                avg_evening_energy = sum(e[0] for e in evening_entries) / len(evening_entries)
                avg_evening_mood = sum(e[1] for e in evening_entries) / len(evening_entries)
                html += f"""
                <tr>
                    <td>Evening (after 6 PM)</td>
                    <td>{len(evening_entries)}</td>
                    <td>{avg_evening_energy:.1f}/10</td>
                    <td>{avg_evening_mood:.1f}/10</td>
                </tr>
                """
            
            html += "</table>"
        
        return html
    
    def export_pdf(self):
        """Export current report to PDF."""
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt6.QtGui import QTextDocument
            from app.utils.db_utils import get_exports_dir
            import os
            
            # Create printer
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            
            # Get default file name based on report type
            report_type = self.report_type_combo.currentText()
            start_date = self.report_start_date.date().toString("yyyy-MM-dd")
            end_date = self.report_end_date.date().toString("yyyy-MM-dd")
            
            # Generate filename in exports directory
            exports_dir = get_exports_dir()
            filename = f"TaskTitan_{report_type.replace(' ', '_')}_{start_date}_to_{end_date}.pdf"
            default_filepath = os.path.join(exports_dir, filename)
            
            # Set output filename
            printer.setOutputFileName(default_filepath)
            
            # Optional: Show print dialog
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                # Create document from HTML content
                document = QTextDocument()
                document.setHtml(self.report_content.toHtml())
                
                # Print to PDF
                document.print_(printer)
                
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"Report exported to PDF successfully!\n\nFile: {printer.outputFileName()}"
                )
                
        except ImportError:
            QMessageBox.warning(
                self, 
                "Export Failed", 
                "PDF export requires the QtPrintSupport module which is not available."
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Export Failed", 
                f"Could not export to PDF: {e}"
            )
    
    def export_csv(self):
        """Export current report data to CSV."""
        import csv
        import os
        from PyQt6.QtWidgets import QFileDialog
        from app.utils.db_utils import get_exports_dir
        
        try:
            # Get report type and date range
            report_type = self.report_type_combo.currentText()
            start_date = self.report_start_date.date()
            end_date = self.report_end_date.date()
            
            # Default filename
            exports_dir = get_exports_dir()
            filename = f"TaskTitan_{report_type.replace(' ', '_')}_{start_date.toString('yyyy-MM-dd')}_to_{end_date.toString('yyyy-MM-dd')}.csv"
            default_filepath = os.path.join(exports_dir, filename)
            
            # Get save location from user, suggesting the default location
            filepath, _ = QFileDialog.getSaveFileName(
                self, 
                "Export to CSV", 
                default_filepath, 
                "CSV Files (*.csv)"
            )
            
            if not filepath:
                return  # User cancelled
                
            # Open CSV file for writing
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Generate CSV data based on report type
                if report_type == "Daily Summary":
                    # Write header
                    writer.writerow(["Date", "Number of Entries", "Total Hours", "Total Minutes", "Categories"])
                    
                    # Query data
                    self.cursor.execute("""
                        SELECT 
                            date, 
                            COUNT(*) as entry_count,
                            SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as total_minutes
                        FROM time_entries
                        WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
                        GROUP BY date
                        ORDER BY date
                    """, (
                        start_date.toString("yyyy-MM-dd"),
                        end_date.toString("yyyy-MM-dd")
                    ))
                    
                    daily_results = self.cursor.fetchall()
                    
                    # Write data rows
                    for date_str, entry_count, total_minutes in daily_results:
                        # Calculate hours and minutes
                        hours = int(total_minutes) // 60
                        minutes = int(total_minutes) % 60
                        
                        # Get categories for this day
                        self.cursor.execute("""
                            SELECT GROUP_CONCAT(DISTINCT category, ', ')
                            FROM time_entries
                            WHERE date = ?
                        """, (date_str,))
                        
                        categories = self.cursor.fetchone()[0] or ""
                        
                        # Write row
                        writer.writerow([date_str, entry_count, hours, minutes, categories])
                        
                elif report_type == "Category Breakdown":
                    # Write header
                    writer.writerow(["Category", "Number of Entries", "Total Hours", "Total Minutes", "Percentage"])
                    
                    # Query data
                    self.cursor.execute("""
                        SELECT 
                            category,
                            COUNT(*) as entry_count,
                            SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as total_minutes
                        FROM time_entries
                        WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
                        GROUP BY category
                        ORDER BY total_minutes DESC
                    """, (
                        start_date.toString("yyyy-MM-dd"),
                        end_date.toString("yyyy-MM-dd")
                    ))
                    
                    category_results = self.cursor.fetchall()
                    
                    # Calculate total minutes across all categories
                    total_minutes_all = sum(row[2] for row in category_results)
                    
                    # Write data rows
                    for category, entry_count, total_minutes in category_results:
                        # Calculate hours and minutes
                        hours = int(total_minutes) // 60
                        minutes = int(total_minutes) % 60
                        
                        # Calculate percentage
                        percentage = (total_minutes / total_minutes_all) * 100 if total_minutes_all > 0 else 0
                        
                        # Write row
                        writer.writerow([category, entry_count, hours, minutes, f"{percentage:.2f}%"])
                        
                elif report_type == "Energy & Mood Analysis":
                    # Write header
                    writer.writerow(["Date", "Time", "Energy Level", "Mood Level", "Notes"])
                    
                    # Query data
                    self.cursor.execute("""
                        SELECT 
                            date,
                            time,
                            energy_level,
                            mood_level,
                            notes
                        FROM energy_patterns
                        WHERE date BETWEEN ? AND ?
                        ORDER BY date, time
                    """, (
                        start_date.toString("yyyy-MM-dd"),
                        end_date.toString("yyyy-MM-dd")
                    ))
                    
                    energy_results = self.cursor.fetchall()
                    
                    # Write data rows
                    for date_str, time_str, energy, mood, notes in energy_results:
                        writer.writerow([date_str, time_str, energy, mood, notes or ""])
                        
                else:
                    # Generic export for other report types
                    # Write header based on report type
                    if report_type == "Weekly Summary":
                        writer.writerow(["Week", "Total Hours", "Top Category"])
                    elif report_type == "Productivity Patterns":
                        writer.writerow(["Date", "Avg Energy", "Avg Mood", "Hours"])
                    elif report_type == "Time Distribution":
                        writer.writerow(["Hour", "Total Hours", "Percentage"])
                    else:
                        writer.writerow(["Date", "Hours", "Description"])
                    
                    # Write some sample data
                    writer.writerow(["Data export for this report type is not fully implemented."])
            
            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Report exported to CSV successfully!\n\nFile: {filepath}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Export Failed", 
                f"Could not export to CSV: {e}"
            )

    def manage_categories(self):
        """Manage time tracking categories."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Categories")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Intro text
        intro_label = QLabel("Manage your time tracking categories below. You can add, edit, or remove categories.")
        intro_label.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(intro_label)
        
        # Categories table
        categories_table = QTableWidget()
        categories_table.setColumnCount(3)
        categories_table.setHorizontalHeaderLabels(["Category Name", "Color", "Actions"])
        categories_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        categories_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        categories_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        categories_table.setColumnWidth(1, 100)
        categories_table.setColumnWidth(2, 120)
        layout.addWidget(categories_table)
        
        # Populate table
        if self.cursor:
            try:
                self.cursor.execute("SELECT name, color FROM time_categories ORDER BY name")
                db_categories = self.cursor.fetchall()
                
                categories_table.setRowCount(len(db_categories))
                
                for i, (name, color) in enumerate(db_categories):
                    # Name
                    name_item = QTableWidgetItem(name)
                    categories_table.setItem(i, 0, name_item)
                    
                    # Color
                    color_widget = QWidget()
                    color_layout = QHBoxLayout(color_widget)
                    color_layout.setContentsMargins(4, 4, 4, 4)
                    
                    color_preview = QFrame()
                    color_preview.setFixedSize(20, 20)
                    color_preview.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
                    color_layout.addWidget(color_preview)
                    
                    color_label = QLabel(color)
                    color_layout.addWidget(color_label)
                    
                    categories_table.setCellWidget(i, 1, color_widget)
                    
                    # Actions
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(0, 0, 0, 0)
                    
                    edit_btn = QPushButton("Edit")
                    edit_btn.setFixedWidth(50)
                    edit_btn.clicked.connect(lambda checked, n=name, c=color: self.edit_category(categories_table, n, c))
                    actions_layout.addWidget(edit_btn)
                    
                    delete_btn = QPushButton("Delete")
                    delete_btn.setFixedWidth(50)
                    delete_btn.clicked.connect(lambda checked, n=name: self.delete_category(categories_table, n))
                    actions_layout.addWidget(delete_btn)
                    
                    categories_table.setCellWidget(i, 2, actions_widget)
                    
            except Exception as e:
                print(f"Error loading categories: {e}")
        
        # Add category button
        add_category_layout = QHBoxLayout()
        
        new_category_input = QLineEdit()
        new_category_input.setPlaceholderText("New category name")
        add_category_layout.addWidget(new_category_input)
        
        color_btn = QPushButton("Select Color")
        color_btn.setFixedWidth(100)
        current_color = "#4F46E5"  # Default color
        
        def select_color():
            nonlocal current_color
            color = QColorDialog.getColor(QColor(current_color), dialog, "Select Category Color")
            if color.isValid():
                current_color = color.name()
                color_btn.setStyleSheet(f"background-color: {current_color}; color: white;")
                
        color_btn.clicked.connect(select_color)
        color_btn.setStyleSheet(f"background-color: {current_color}; color: white;")
        add_category_layout.addWidget(color_btn)
        
        add_btn = QPushButton("Add Category")
        add_btn.setFixedWidth(120)
        
        def add_new_category():
            name = new_category_input.text().strip()
            if not name:
                QMessageBox.warning(dialog, "Invalid Input", "Please enter a category name.")
                return
                
            # Check if category already exists
            if self.cursor:
                self.cursor.execute("SELECT COUNT(*) FROM time_categories WHERE name = ?", (name,))
                if self.cursor.fetchone()[0] > 0:
                    QMessageBox.warning(dialog, "Duplicate Category", f"The category '{name}' already exists.")
                    return
                    
                # Add to database
                try:
                    self.cursor.execute(
                        "INSERT INTO time_categories (name, color) VALUES (?, ?)",
                        (name, current_color)
                    )
                    self.conn.commit()
                    
                    # Refresh table
                    self.manage_categories()
                    dialog.close()
                    
                    # Update categories list
                    self.cursor.execute("SELECT name FROM time_categories ORDER BY name")
                    categories = self.cursor.fetchall()
                    self.categories = [cat[0] for cat in categories]
                    
                except Exception as e:
                    print(f"Error adding category: {e}")
                    QMessageBox.critical(dialog, "Error", f"Could not add category: {e}")
        
        add_btn.clicked.connect(add_new_category)
        add_category_layout.addWidget(add_btn)
        
        layout.addLayout(add_category_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def edit_category(self, table, category_name, current_color):
        """Edit an existing category."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Category: {category_name}")
        
        layout = QVBoxLayout(dialog)
        
        # Name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        
        name_input = QLineEdit(category_name)
        name_layout.addWidget(name_input)
        
        layout.addLayout(name_layout)
        
        # Color selection
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        
        color_preview = QPushButton()
        color_preview.setFixedSize(30, 30)
        color_preview.setStyleSheet(f"background-color: {current_color};")
        
        def change_color():
            color = QColorDialog.getColor(QColor(color_preview.property("color")), dialog, "Select Category Color")
            if color.isValid():
                new_color = color.name()
                color_preview.setStyleSheet(f"background-color: {new_color};")
                color_preview.setProperty("color", new_color)
        
        color_preview.clicked.connect(change_color)
        color_preview.setProperty("color", current_color)
        
        color_layout.addWidget(color_preview)
        color_layout.addStretch()
        
        layout.addLayout(color_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = name_input.text().strip()
            new_color = color_preview.property("color")
            
            if not new_name:
                QMessageBox.warning(self, "Invalid Input", "Category name cannot be empty.")
                return
                
            # Update in database
            if self.cursor:
                try:
                    self.cursor.execute(
                        "UPDATE time_categories SET name = ?, color = ? WHERE name = ?",
                        (new_name, new_color, category_name)
                    )
                    
                    # Also update any existing time entries with this category
                    if new_name != category_name:
                        self.cursor.execute(
                            "UPDATE time_entries SET category = ? WHERE category = ?",
                            (new_name, category_name)
                        )
                        
                    self.conn.commit()
                    
                    # Refresh categories list
                    self.cursor.execute("SELECT name FROM time_categories ORDER BY name")
                    categories = self.cursor.fetchall()
                    self.categories = [cat[0] for cat in categories]
                    
                    # Refresh table
                    self.manage_categories()
                    
                    # Refresh entries table if we're on the current date
                    self.load_entries(self.current_date)
                    
                except Exception as e:
                    print(f"Error updating category: {e}")
                    QMessageBox.critical(self, "Error", f"Could not update category: {e}")
    
    def update_trend_analysis_chart(self, start_date, end_date):
        """Update the trend analysis chart."""
        if not HAS_MATPLOTLIB or not self.cursor:
            return
            
        try:
            # Clear previous chart
            self.trend_figure.clear()
            
            # Create a new axis
            ax = self.trend_figure.add_subplot(111)
            
            # Get trend metric
            metric = self.trend_metric.currentText()
            show_trend_line = self.trend_show_line.isChecked()
            
            if metric == "Daily Time":
                # Query total time per day
                self.cursor.execute("""
                    SELECT 
                        date,
                        SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as duration
                    FROM time_entries
                    WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
                    GROUP BY date
                    ORDER BY date
                """, (
                    start_date.toString("yyyy-MM-dd"),
                    end_date.toString("yyyy-MM-dd")
                ))
                
                results = self.cursor.fetchall()
                
                if not results:
                    ax.text(0.5, 0.5, "No data available for selected period",
                            horizontalalignment='center', verticalalignment='center',
                            transform=ax.transAxes, fontsize=12, color='gray')
                    self.trend_canvas.draw()
                    return
                
                # Process data
                dates = [datetime.strptime(row[0], "%Y-%m-%d").date() for row in results]
                values = [row[1] / 60 for row in results]  # Convert to hours
                
                # Plot data points
                ax.plot(dates, values, 'o-', color='#4F46E5', label='Daily Hours')
                
                if show_trend_line and len(values) > 1:
                    # Calculate and plot trend line
                    z = np.polyfit(range(len(dates)), values, 1)
                    p = np.poly1d(z)
                    trend_values = p(range(len(dates)))
                    ax.plot(dates, trend_values, 'r--', label='Trend')
                    
                    # Add trend information to plot
                    trend_direction = "increasing" if z[0] > 0 else "decreasing"
                    ax.text(0.05, 0.95, f"Trend: {trend_direction} by {abs(z[0]):.2f} hours/day",
                            transform=ax.transAxes, fontsize=9,
                            verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.7))
                
                ax.set_ylabel('Hours')
                ax.set_title('Daily Time Trend')
                
            elif metric == "Energy Level" or metric == "Mood Level":
                # Query daily average energy or mood
                field = "energy_level" if metric == "Energy Level" else "mood_level"
                
                self.cursor.execute(f"""
                    SELECT 
                        date,
                        AVG({field}) as avg_level
                    FROM time_entries
                    WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
                    GROUP BY date
                    ORDER BY date
                """, (
                    start_date.toString("yyyy-MM-dd"),
                    end_date.toString("yyyy-MM-dd")
                ))
                
                results = self.cursor.fetchall()
                
                if not results:
                    ax.text(0.5, 0.5, "No data available for selected period",
                            horizontalalignment='center', verticalalignment='center',
                            transform=ax.transAxes, fontsize=12, color='gray')
                    self.trend_canvas.draw()
                    return
                
                # Process data
                dates = [datetime.strptime(row[0], "%Y-%m-%d").date() for row in results]
                values = [row[1] for row in results]
                
                # Plot data points
                color = '#F97316' if metric == "Energy Level" else '#8B5CF6'
                ax.plot(dates, values, 'o-', color=color, label=f'Daily {metric}')
                
                if show_trend_line and len(values) > 1:
                    # Calculate and plot trend line
                    z = np.polyfit(range(len(dates)), values, 1)
                    p = np.poly1d(z)
                    trend_values = p(range(len(dates)))
                    ax.plot(dates, trend_values, 'r--', label='Trend')
                    
                    # Add trend information to plot
                    trend_direction = "increasing" if z[0] > 0 else "decreasing"
                    ax.text(0.05, 0.95, f"Trend: {trend_direction} by {abs(z[0]):.2f} points/day",
                            transform=ax.transAxes, fontsize=9,
                            verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.7))
                
                ax.set_ylabel('Level (1-10)')
                ax.set_title(f'{metric} Trend')
                
            else:  # Category Balance
                # Query time by category by day
                self.cursor.execute("""
                    SELECT 
                        date,
                        category,
                        SUM((strftime('%s', end_time) - strftime('%s', start_time)) / 60) as duration
                    FROM time_entries
                    WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
                    GROUP BY date, category
                    ORDER BY date, category
                """, (
                    start_date.toString("yyyy-MM-dd"),
                    end_date.toString("yyyy-MM-dd")
                ))
                
                results = self.cursor.fetchall()
                
                if not results:
                    ax.text(0.5, 0.5, "No data available for selected period",
                            horizontalalignment='center', verticalalignment='center',
                            transform=ax.transAxes, fontsize=12, color='gray')
                    self.trend_canvas.draw()
                    return
                
                # Process data - calculate category diversity for each day
                all_dates = sorted(list(set(row[0] for row in results)))
                date_to_diversity = {}
                
                for date in all_dates:
                    # Get categories for this date
                    categories_for_date = [row for row in results if row[0] == date]
                    
                    # Calculate total time for this date
                    total_time = sum(row[2] for row in categories_for_date)
                    
                    if total_time > 0:
                        # Calculate Shannon diversity index
                        proportions = [row[2] / total_time for row in categories_for_date]
                        diversity = -sum(p * np.log(p) for p in proportions if p > 0)
                        
                        # Normalize to 0-10 scale for easier interpretation
                        # Higher diversity = more balanced categories
                        max_possible_diversity = np.log(len(categories_for_date))
                        normalized_diversity = (diversity / max_possible_diversity) * 10 if max_possible_diversity > 0 else 0
                        
                        date_to_diversity[date] = normalized_diversity
                
                # Convert to lists for plotting
                dates = [datetime.strptime(date, "%Y-%m-%d").date() for date in date_to_diversity.keys()]
                diversity_values = list(date_to_diversity.values())
                
                # Plot data points
                ax.plot(dates, diversity_values, 'o-', color='#10B981', label='Category Balance')
                
                if show_trend_line and len(diversity_values) > 1:
                    # Calculate and plot trend line
                    z = np.polyfit(range(len(dates)), diversity_values, 1)
                    p = np.poly1d(z)
                    trend_values = p(range(len(dates)))
                    ax.plot(dates, trend_values, 'r--', label='Trend')
                    
                    # Add trend information to plot
                    trend_direction = "increasing" if z[0] > 0 else "decreasing"
                    ax.text(0.05, 0.95, f"Trend: {trend_direction} by {abs(z[0]):.2f} points/day",
                            transform=ax.transAxes, fontsize=9,
                            verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.7))
                
                ax.set_ylabel('Category Balance (0-10)')
                ax.set_title('Category Balance Trend')
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            
            # Rotate date labels
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
            # Add legend if trend line is shown
            if show_trend_line:
                ax.legend()
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Adjust layout
            self.trend_figure.tight_layout()
            
            # Draw the chart
            self.trend_canvas.draw()
            
        except Exception as e:
            print(f"Error updating trend analysis chart: {e}")
    
    def manage_attachment_categories(self):
        """Open a dialog to manage attachment categories."""
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Attachment Categories")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(400)
        
        # Main layout
        layout = QVBoxLayout(dialog)
        
        # Header
        header_label = QLabel("Manage Categories")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Instructions
        instructions = QLabel("Organize how your attachments are categorized in folders.")
        instructions.setStyleSheet("font-size: 13px; color: #6B7280; margin-bottom: 15px;")
        layout.addWidget(instructions)
        
        # Category list
        category_list = QListWidget()
        category_list.setStyleSheet("font-size: 14px; padding: 5px; border-radius: 6px; border: 1px solid #E5E7EB;")
        layout.addWidget(category_list)
        
        # Button row
        button_row = QHBoxLayout()
        
        add_btn = QPushButton("Add Category")
        add_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 6px 12px;
                border-radius: 6px;
                background: #EFF6FF;
                border: 1px solid #DBEAFE;
                color: #3B82F6;
            }
            QPushButton:hover {
                background: #DBEAFE;
            }
        """)
        
        rename_btn = QPushButton("Rename")
        rename_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 6px 12px;
                border-radius: 6px;
                background: #F3F4F6;
                border: 1px solid #E5E7EB;
            }
            QPushButton:hover {
                background: #E5E7EB;
            }
            QPushButton:disabled {
                color: #9CA3AF;
            }
        """)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("""
                QPushButton {
                font-size: 14px;
                padding: 6px 12px;
                    border-radius: 6px;
                background: #FEE2E2;
                border: 1px solid #FECACA;
                color: #DC2626;
                }
                QPushButton:hover {
                background: #FECACA;
            }
            QPushButton:disabled {
                background: #F3F4F6;
                color: #9CA3AF;
                border-color: #E5E7EB;
                }
            """)
    
        button_row.addWidget(add_btn)
        button_row.addWidget(rename_btn)
        button_row.addWidget(delete_btn)
        layout.addLayout(button_row)
        
        # Bottom button row
        bottom_row = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("font-size: 14px; padding: 8px 16px; border-radius: 6px;")
        close_btn.clicked.connect(dialog.accept)
        bottom_row.addStretch()
        bottom_row.addWidget(close_btn)
        layout.addLayout(bottom_row)
        
        # Load existing categories
        from app.utils.db_utils import list_attachment_categories
        categories = list_attachment_categories()
        
        # Add default categories if empty
        if not categories:
            categories = ["Journal", "Images", "Documents", "Notes", "Reference"]
        
        # Sort and add to list
        categories.sort()
        category_list.addItems(categories)
        
        # Enable/disable buttons based on selection
        def update_buttons():
            has_selection = category_list.currentItem() is not None
            rename_btn.setEnabled(has_selection)
            delete_btn.setEnabled(has_selection)
        
        # Add category function
        def add_category():
            category_name, ok = QInputDialog.getText(
                dialog, "Add Category", "Enter new category name:"
            )
            if ok and category_name:
                # Check if category already exists
                for i in range(category_list.count()):
                    if category_list.item(i).text() == category_name:
                        QMessageBox.warning(dialog, "Duplicate", f"Category '{category_name}' already exists")
                        return
                
                # Add to list
                category_list.addItem(category_name)
                categories.append(category_name)
                categories.sort()
                
                # Refresh the list to show in sorted order
                category_list.clear()
                category_list.addItems(categories)
        
        # Rename category function
        def rename_category():
            current_item = category_list.currentItem()
            if current_item:
                old_name = current_item.text()
                new_name, ok = QInputDialog.getText(
                    dialog, "Rename Category", "Enter new name:", text=old_name
                )
                if ok and new_name and new_name != old_name:
                    # Update in our list
                    categories.remove(old_name)
                    categories.append(new_name)
                    categories.sort()
                    
                    # Refresh the list
                    category_list.clear()
                    category_list.addItems(categories)
        
        # Delete category function
        def delete_category():
            current_item = category_list.currentItem()
            if current_item:
                name = current_item.text()
                confirm = QMessageBox.question(
                    dialog, 
                    "Confirm Delete",
                    f"Are you sure you want to delete category '{name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if confirm == QMessageBox.StandardButton.Yes:
                    # Remove from our list
                    categories.remove(name)
                    
                    # Refresh the list
                    category_list.clear()
                    category_list.addItems(categories)
        
        # Connect buttons
        add_btn.clicked.connect(add_category)
        rename_btn.clicked.connect(rename_category)
        delete_btn.clicked.connect(delete_category)
        
        # Connect selection changed
        category_list.itemSelectionChanged.connect(update_buttons)
        update_buttons()  # Initial state
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save the updated categories list (this would need actual DB interactions)
            pass

    def show_attachment_context_menu(self, position):
        """Show a context menu for attachment items in the list."""
        # Get the item at the position
        item = self.attachments_list.itemAt(position)
        
        # Only show context menu if there's an item
        if item:
            # Create context menu
            context_menu = QMenu()
            
            # Add actions
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.open_attached_file(item))
            
            open_folder_action = QAction("Show in Folder", self)
            open_folder_action.triggered.connect(lambda: self.show_attachment_in_folder(item))
            
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self.rename_attachment(item))
            
            change_category_action = QAction("Change Category", self)
            change_category_action.triggered.connect(lambda: self.change_attachment_category(item))
            
            remove_action = QAction("Remove", self)
            remove_action.triggered.connect(lambda: self.remove_selected_attachment())
            
            # Add actions to menu
            context_menu.addAction(open_action)
            context_menu.addAction(open_folder_action)
            context_menu.addSeparator()
            context_menu.addAction(rename_action)
            context_menu.addAction(change_category_action)
            context_menu.addSeparator()
            context_menu.addAction(remove_action)
            
            # Show the menu at the cursor position
            context_menu.exec(self.attachments_list.mapToGlobal(position))

    def show_attachment_in_folder(self, item):
        """Show the attachment file in its parent folder."""
        try:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            
            if not os.path.exists(file_path):
                # Try using the shortcut path instead
                file_path = item.data(Qt.ItemDataRole.UserRole + 3)
                
                if not os.path.exists(file_path):
                    QMessageBox.warning(self, "File Not Found", f"The file could not be found.")
                    return
            
            # Get the parent directory
            parent_dir = os.path.dirname(file_path)
            
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                # On Windows, use explorer to open and select the file
                subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(['open', parent_dir])
            else:  # Linux
                subprocess.run(['xdg-open', parent_dir])
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder: {e}")

    def rename_attachment(self, item):
        """Rename the selected attachment."""
        try:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            file_id = item.data(Qt.ItemDataRole.UserRole + 1)
            
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "File Not Found", f"The original file could not be found: {file_path}")
                return
            
            # Get the current filename
            current_name = os.path.basename(file_path)
            
            # Get new name from user
            new_name, ok = QInputDialog.getText(
                self, "Rename Attachment", "Enter new filename:", text=current_name
            )
            
            if ok and new_name and new_name != current_name:
                # Create new path with the new name
                new_path = os.path.join(os.path.dirname(file_path), new_name)
                
                # Check if file already exists
                if os.path.exists(new_path):
                    QMessageBox.warning(self, "File Exists", f"A file with that name already exists.")
                    return
                
                # Rename the file
                os.rename(file_path, new_path)
                
                # Update the database
                if self.cursor:
                    self.cursor.execute(
                        "UPDATE journal_attachments SET file_path = ? WHERE id = ?",
                        (new_path, file_id)
                    )
                    self.connection.commit()
                
                # Update the item in the list
                item.setText(new_name)
                item.setData(Qt.ItemDataRole.UserRole, new_path)
                
                # Also update the tooltip
                category = item.data(Qt.ItemDataRole.UserRole + 2)
                date_str = self.current_date.toString("yyyy-MM-dd")
                
                tooltip = f"File: {new_path}"
                if category:
                    tooltip += f"\nCategory: {category}"
                tooltip += f"\nDate: {date_str}"
                item.setToolTip(tooltip)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not rename file: {e}")

    def change_attachment_category(self, item):
        """Change the category of the selected attachment."""
        try:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            file_id = item.data(Qt.ItemDataRole.UserRole + 1)
            current_category = item.data(Qt.ItemDataRole.UserRole + 2)
            shortcut_path = item.data(Qt.ItemDataRole.UserRole + 3)
            
            # Get all available categories
            from app.utils.db_utils import list_attachment_categories
            categories = list_attachment_categories()
            
            if not categories:
                categories = ["Journal", "Images", "Documents", "Notes", "Reference"]
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Change Category")
            dialog.setMinimumWidth(300)
            
            layout = QVBoxLayout(dialog)
            
            # Add combobox with categories
            layout.addWidget(QLabel("Select Category:"))
            
            category_combo = QComboBox()
            category_combo.addItems(categories)
            category_combo.setEditable(True)
            
            # Set current category if it exists
            if current_category:
                index = category_combo.findText(current_category)
                if index >= 0:
                    category_combo.setCurrentIndex(index)
            
            layout.addWidget(category_combo)
            
            # Add buttons
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_category = category_combo.currentText()
                
                if new_category != current_category:
                    # Move the file to the new category using db_utils
                    from app.utils.db_utils import update_attachment_category
                    
                    # First, try to update in the database
                    if self.cursor:
                        # Remove old shortcut if it exists
                        if shortcut_path and os.path.exists(shortcut_path):
                            try:
                                os.remove(shortcut_path)
                            except Exception as e:
                                print(f"Failed to remove old shortcut: {e}")
                        
                        # Create new shortcut with the new category
                        new_shortcut_path = None
                        if new_category:
                            try:
                                from app.utils.db_utils import create_category_shortcut
                                new_shortcut_path = create_category_shortcut(file_path, new_category)
                            except Exception as e:
                                print(f"Failed to create new shortcut: {e}")
                        
                        # Update the database
                        self.cursor.execute(
                            "UPDATE journal_attachments SET category = ?, shortcut_path = ? WHERE id = ?",
                            (new_category, new_shortcut_path, file_id)
                        )
                        self.connection.commit()
                    
                    # Update display
                    self.load_journal_attachments(self.current_date)
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not change category: {e}")

    def update_attachment_buttons(self):
        """Update the attachment buttons based on the current selection."""
        has_selection = len(self.attachments_list.selectedItems()) > 0
        self.remove_attachment_btn.setEnabled(has_selection)

    def open_attachments_folder(self):
        """Open the attachments folder for the current date."""
        try:
            # Get attachments directory for the current date
            from app.utils.db_utils import get_attachments_dir
            date_str = self.current_date.toString("yyyy-MM-dd")
            attachments_dir = get_attachments_dir(date_str)
            
            # Check if directory exists and create it if not
            if not os.path.exists(attachments_dir):
                os.makedirs(attachments_dir)
            
            # Open the directory
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                os.startfile(attachments_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", attachments_dir])
            else:  # Linux
                subprocess.call(["xdg-open", attachments_dir])
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open attachments folder: {e}")

    def remove_selected_attachment(self):
        """Remove the selected attachment from the database and optionally delete the file."""
        selected_items = self.attachments_list.selectedItems()
        
        if not selected_items:
            return
        
        item = selected_items[0]  # We only allow single selection
        file_path = item.data(Qt.ItemDataRole.UserRole)
        file_id = item.data(Qt.ItemDataRole.UserRole + 1)
        shortcut_path = item.data(Qt.ItemDataRole.UserRole + 3)
        
        # Confirm deletion
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Confirm Deletion")
        msg_box.setText(f"Are you sure you want to remove this attachment?")
        msg_box.setInformativeText("Do you also want to delete the file from disk?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        response = msg_box.exec()
        
        if response == QMessageBox.StandardButton.Cancel:
            return
        
        delete_file = (response == QMessageBox.StandardButton.Yes)
        
        try:
            # Remove from database
            if self.cursor:
                self.cursor.execute("DELETE FROM journal_attachments WHERE id = ?", (file_id,))
                self.connection.commit()
            
            # Delete file from disk if requested
            if delete_file and os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete shortcut if it exists
            if shortcut_path and os.path.exists(shortcut_path):
                os.remove(shortcut_path)
            
            # Remove from list
            row = self.attachments_list.row(item)
            self.attachments_list.takeItem(row)
            
            # Update buttons
            self.update_attachment_buttons()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not remove attachment: {e}")
            print(f"Error removing attachment: {e}")

    def load_activities(self):
        """Load time tracking activities for the current date."""
        if not self.cursor:
            return
        
        try:
            # Create time_entries table if it doesn't exist
            self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS time_entries (
                        id TEXT PRIMARY KEY,
                        date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        category TEXT,
                        description TEXT,
                        energy_level INTEGER,
                        mood_level INTEGER
                    )
            """)
            
            # Create time_categories table if it doesn't exist
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS time_categories (
                    name TEXT PRIMARY KEY,
                    color TEXT
                )
            """)
            
            # Add default categories if none exist
            self.cursor.execute("SELECT COUNT(*) FROM time_categories")
            if self.cursor.fetchone()[0] == 0:
                default_categories = [
                    ("Work", "#4F46E5"),
                    ("Meeting", "#0891B2"),
                    ("Break", "#059669"),
                    ("Learning", "#7C3AED"),
                    ("Exercise", "#EF4444"),
                    ("Planning", "#F59E0B")
                ]
                self.cursor.executemany(
                    "INSERT OR IGNORE INTO time_categories (name, color) VALUES (?, ?)",
                    default_categories
                )
                self.connection.commit()
            
            # Load categories into memory
            self.cursor.execute("SELECT name FROM time_categories ORDER BY name")
            categories = self.cursor.fetchall()
            self.categories = [cat[0] for cat in categories]
            
            # Load time entries for current date
            self.load_entries(self.current_date)
        
        except Exception as e:
            print(f"Error loading activities: {e}")

    def update_word_count(self):
        """Update the word count for the free writing text area."""
        text = self.free_writing_edit.toPlainText()
        word_count = len(text.split()) if text.strip() else 0
        self.word_count_label.setText(f"{word_count} words")

    def journal_entry_selected(self, index):
        """Handle selection of a journal entry from the dropdown."""
        if index == 0:  # New Entry
            # Clear all fields and set a new timestamp
            self.clear_journal_entry_fields()
            self.current_entry_id = None
            self.current_entry_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.entry_timestamp.setText(f"Created: {self.current_entry_timestamp}")
            return
        
        # Get the selected entry ID
        entry_id = self.entry_selector.itemData(index, Qt.ItemDataRole.UserRole)
        
        if not entry_id or not self.cursor:
            return
        
        try:
            # Query database for the selected entry
            self.cursor.execute("""
                SELECT id, date, wins, challenges, learnings, tomorrow, gratitude, 
                       free_writing, timestamp, name
                FROM journal_entries
                WHERE id = ?
            """, (entry_id,))
            
            entry = self.cursor.fetchone()
            
            if entry:
                # Fill the form with entry data
                self.current_entry_id = entry[0]
                self.wins_edit.setPlainText(entry[2] or "")
                self.challenges_edit.setPlainText(entry[3] or "")
                self.learnings_edit.setPlainText(entry[4] or "")
                self.tomorrow_edit.setPlainText(entry[5] or "")
                self.gratitude_edit.setPlainText(entry[6] or "")
                
                # Set free writing text if it exists
                if entry[7]:
                    self.free_writing_edit.setPlainText(entry[7])
                    self.update_word_count()
                else:
                    self.free_writing_edit.clear()
                
                # Update timestamp
                self.current_entry_timestamp = entry[8] or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.entry_timestamp.setText(f"Created: {self.current_entry_timestamp}")
                
                # Set entry name if it exists
                if hasattr(self, 'name_edit'):
                    if len(entry) > 9 and entry[9]:
                        self.name_edit.setText(entry[9])
                    else:
                        self.name_edit.clear()
                
        except Exception as e:
            print(f"Error loading journal entry: {e}")
            
    def clear_journal_entry_fields(self):
        """Clear all journal entry fields."""
        self.wins_edit.clear()
        self.challenges_edit.clear()
        self.learnings_edit.clear()
        self.tomorrow_edit.clear()
        self.gratitude_edit.clear()
        if hasattr(self, 'tags_edit'):
            self.tags_edit.clear()
        if hasattr(self, 'name_edit'):
            self.name_edit.clear()
        self.free_writing_edit.clear()
        self.update_word_count()
        
        # Reset mood and rating to defaults
        if hasattr(self, 'mood_combo'):
            self.mood_combo.setCurrentIndex(0)
        if hasattr(self, 'rating_slider'):
            self.rating_slider.setValue(5)

    def has_unsaved_changes(self):
        """Check if there are unsaved changes in the current entry."""
        # If the form is empty, there are no changes
        if (not self.wins_edit.toPlainText().strip() and
            not self.challenges_edit.toPlainText().strip() and
            not self.learnings_edit.toPlainText().strip() and
            not self.tomorrow_edit.toPlainText().strip() and
            not self.gratitude_edit.toPlainText().strip() and
            not self.free_writing_edit.toPlainText().strip()):
            return False
        
        return True

    def load_journal_entries_for_date(self, date):
        """Load all journal entries for the specified date into the dropdown."""
        if not self.cursor:
            return
            
        try:
            # Clear the dropdown except for "New Entry"
            while self.entry_selector.count() > 1:
                self.entry_selector.removeItem(1)
            
            # Query database for all entries on this date
            date_str = date.toString("yyyy-MM-dd")
            
            # Check if the name column exists
            try:
                self.cursor.execute("""
                    SELECT id, timestamp, name
                    FROM journal_entries 
                    WHERE date = ?
                    ORDER BY timestamp DESC
                """, (date_str,))
                
                entries = self.cursor.fetchall()
                has_name_column = True
            except sqlite3.OperationalError:
                # Name column doesn't exist, fall back to original query
                self.cursor.execute("""
                    SELECT id, timestamp 
                    FROM journal_entries 
                    WHERE date = ?
                    ORDER BY timestamp DESC
                """, (date_str,))
                
                entries = self.cursor.fetchall()
                has_name_column = False
            
            # Add entries to dropdown
            for entry in entries:
                entry_id = entry[0]
                timestamp = entry[1]
                
                if has_name_column and len(entry) > 2 and entry[2]:
                    # Use the name if available
                    display_name = entry[2]
                    self.entry_selector.addItem(display_name, entry_id)
                elif timestamp:
                    # Format the timestamp for display
                    try:
                        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                        display_time = dt.strftime("%I:%M %p")  # Format as "1:30 PM"
                        self.entry_selector.addItem(f"Entry at {display_time}", entry_id)
                    except Exception:
                        # If timestamp parsing fails, just use the raw timestamp
                        self.entry_selector.addItem(f"Entry {timestamp}", entry_id)
                else:
                    self.entry_selector.addItem(f"Entry {entry_id[:8]}", entry_id)
            
        except Exception as e:
            print(f"Error loading journal entries: {e}")

    def add_new_journal_entry(self):
        """Create a new journal entry."""
        # Check if there are unsaved changes in the current entry
        if self.has_unsaved_changes():
            confirm = QMessageBox.question(
                self, 
                "Unsaved Changes", 
                "You have unsaved changes in the current entry. Save before creating a new one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )
            
            if confirm == QMessageBox.StandardButton.Cancel:
                return
            elif confirm == QMessageBox.StandardButton.Yes:
                self.save_journal_entry()
        
        # Clear the fields and select "New Entry" in the dropdown
        self.clear_journal_entry_fields()
        self.current_entry_id = None
        self.entry_selector.setCurrentIndex(0)
        self.current_entry_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.entry_timestamp.setText(f"Created: {self.current_entry_timestamp}")

    def delete_journal_entry(self):
        """Delete the current journal entry."""
        index = self.entry_selector.currentIndex()
        
        # Can't delete "New Entry"
        if index == 0 or not self.current_entry_id:
            QMessageBox.information(self, "Cannot Delete", "There is no saved entry to delete.")
            return
        
        if not self.cursor:
            return
        
        confirm = QMessageBox.question(
            self, 
            "Confirm Delete", 
            "Are you sure you want to delete this journal entry? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # Delete entry from database
                self.cursor.execute("DELETE FROM journal_entries WHERE id = ?", (self.current_entry_id,))
                self.connection.commit()
                
                # Refresh entries dropdown
                self.load_journal_entries_for_date(self.current_date)
                
                # Select "New Entry"
                self.entry_selector.setCurrentIndex(0)
                
                QMessageBox.information(self, "Success", "Journal entry deleted successfully.")
                
            except Exception as e:
                print(f"Error deleting journal entry: {e}")
                QMessageBox.warning(self, "Error", f"Could not delete journal entry: {e}")