import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QPushButton, QToolBar, QTabWidget, QScrollArea, QStackedWidget,
    QGridLayout, QSizePolicy, QSpacerItem, QMenu, QCalendarWidget, QProgressBar, QMessageBox, QFormLayout, QComboBox, QCheckBox, QFileDialog, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QSize, QDate, QTime, QTimer, pyqtSignal, QPropertyAnimation, QRect, QRectF
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor, QFont, QPainter, QBrush, QPen, QGuiApplication, QCursor, QShortcut, QKeySequence
import darkdetect
import pyqtgraph as pg
import sqlite3
import getpass
import pathlib
import threading
import time
import tempfile
import uuid

# Set up correct imports based on how the module is being used
if __name__ == "__main__" or not __package__:
    # Add the parent directory to the path for direct execution
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, parent_dir)
    
    # Direct imports
    from app.models.database import initialize_db
    from app.models.database_manager import get_manager, close_connection
    from app.views.calendar_widget import ModernCalendarWidget, CalendarWithEventList
    from app.views.task_widget import TaskWidget, BaseTaskDialog, TaskDialog
    from app.views.goal_widget import GoalWidget
    from app.views.productivity_view import ProductivityView
    from app.views.pomodoro_widget import PomodoroWidget
    from app.views.weekly_view import WeeklyView
    from app.views.daily_view import DailyView
    from app.views.settings_dialog import SettingsDialog
    from app.views.unified_activities_view import UnifiedActivitiesView
    from app.resources import get_icon, get_pixmap, VIEW_NAMES, DASHBOARD_VIEW, ACTIVITIES_VIEW, GOALS_VIEW, PRODUCTIVITY_VIEW, POMODORO_VIEW, WEEKLY_VIEW, DAILY_VIEW, SETTINGS_VIEW
else:
    # Normal imports when imported as a module
    from app.models.database import initialize_db
    from app.models.database_manager import get_manager, close_connection
    from app.views.calendar_widget import ModernCalendarWidget, CalendarWithEventList
    from app.views.task_widget import TaskWidget, BaseTaskDialog, TaskDialog
    from app.views.goal_widget import GoalWidget
    from app.views.productivity_view import ProductivityView
    from app.views.pomodoro_widget import PomodoroWidget
    from app.views.weekly_view import WeeklyView
    from app.views.daily_view import DailyView
    from app.views.settings_dialog import SettingsDialog
    from app.views.unified_activities_view import UnifiedActivitiesView
    from app.resources import get_icon, get_pixmap, VIEW_NAMES, DASHBOARD_VIEW, ACTIVITIES_VIEW, GOALS_VIEW, PRODUCTIVITY_VIEW, POMODORO_VIEW, WEEKLY_VIEW, DAILY_VIEW, SETTINGS_VIEW

# Import custom progress chart to avoid QRectF issues
from app.views.custom_progress import CircularProgressChart

# Import model classes
from app.models.task import Task, TaskStatus
from app.models.event import Event
from app.models.habit import Habit
from app.models.category import Category

# Import view and dialog classes
from app.views.event_widget import EventWidget, EventDialog
from app.views.habit_widget import HabitWidget, HabitDialog
from app.views.category_widget import CategoryWidget, CategoryDialog

# Import database utilities
from app.utils.db_utils import (
    create_tables, get_db_path, backup_database, restore_database
)

class TaskTitanApp(QMainWindow):
    """Main application window for TaskTitan with modern UI.""" 
    
    def __init__(self):
        """Initialize the main application window."""
        super().__init__()
        
        # Initialize database connection
        self.conn, self.cursor = initialize_db()
        
        # Get the database manager for direct access
        self.db_manager = get_manager()
        
        # Set up window properties
        self.setWindowTitle("TaskTitan")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Current view tracking
        self.current_page = DASHBOARD_VIEW
        
        # Setup the UI components
        self.setupSidebar()
        self.setupContentStack()
        
        # Load initial data
        self.loadData()
        
        # Set up a timer to refresh data periodically
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refreshData)
        self.refresh_timer.start(60000)  # Refresh every minute
    
    def closeEvent(self, event):
        """Handle the window close event."""
        try:
            # Save any pending changes
            self.savePendingChanges()
            
            # Close the database connection through the manager
            close_connection()
            
            print("Database connection closed successfully")
            
            # Accept the event and close the window
            event.accept()
        except Exception as e:
            print(f"Error during application close: {e}")
            # We still want to exit the app even if there was an error
            event.accept()

    def savePendingChanges(self):
        """Save any pending changes before closing."""
        try:
            # Make sure activities view explicitly saves its data
            if hasattr(self, 'activitiesView') and hasattr(self.activitiesView, 'saveChanges'):
                print("Saving activities before exit...")
                self.activitiesView.saveChanges()
            
            # Save any unsaved data in the current view
            current_widget = self.contentStack.currentWidget()
            if hasattr(current_widget, 'saveChanges'):
                print(f"Saving changes for {current_widget.__class__.__name__}")
                current_widget.saveChanges()
            
            # Loop through all views to save any pending changes
            for i in range(self.contentStack.count()):
                widget = self.contentStack.widget(i)
                if widget != current_widget and hasattr(widget, 'saveChanges'):
                    print(f"Saving changes for {widget.__class__.__name__}")
                    widget.saveChanges()
                    
            # Ensure database commits all changes
            if hasattr(self, 'conn'):
                self.conn.commit()
                
        except Exception as e:
            print(f"Error saving pending changes: {e}")

    def setupContentStack(self):
        """Create the stacked content area."""
        # Create a stacked widget for content
        self.contentStack = QStackedWidget()
        self.contentStack.setObjectName("contentStack")
        self.contentStack.setStyleSheet("""
            #contentStack {
                background-color: #F8FAFC;
            }
        """)
        
        # Dashboard view
        self.dashboardView = QWidget()
        self.dashboardView.setObjectName("dashboardPage")
        dashboard_layout = QVBoxLayout(self.dashboardView)
        
        # Dashboard header
        dashboard_header = QWidget()
        dashboard_header_layout = QHBoxLayout(dashboard_header)
        dashboard_header_layout.setContentsMargins(30, 30, 30, 0)
        
        dashboard_title = QLabel("Dashboard")
        dashboard_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E293B;")
        dashboard_header_layout.addWidget(dashboard_title)
        dashboard_header_layout.addStretch()
        
        # Add greeting based on time of day
        current_hour = QTime.currentTime().hour()
        greeting = "Good morning" if 5 <= current_hour < 12 else "Good afternoon" if 12 <= current_hour < 18 else "Good evening"
        greeting_label = QLabel(f"{greeting}, {getpass.getuser()}!")
        greeting_label.setStyleSheet("font-size: 18px; color: #64748B;")
        dashboard_header_layout.addWidget(greeting_label)
        
        dashboard_layout.addWidget(dashboard_header)
        
        # Dashboard content
        dashboard_content = QWidget()
        dashboard_content_layout = QGridLayout(dashboard_content)
        dashboard_content_layout.setContentsMargins(20, 20, 20, 20)
        dashboard_content_layout.setSpacing(20)
        
        # Create dashboard widgets
        self.setupDashboardWidgets(dashboard_content_layout)
        
        dashboard_layout.addWidget(dashboard_content)
        self.contentStack.addWidget(self.dashboardView)
        
        # Activities view (unified view for tasks, events, and habits)
        self.activitiesView = UnifiedActivitiesView(self)
        self.contentStack.addWidget(self.activitiesView)
        
        # Connect the signals from the activities view
        self.activitiesView.activityAdded.connect(self.onActivityAdded)
        self.activitiesView.activityCompleted.connect(self.onActivityCompleted)
        self.activitiesView.activityDeleted.connect(self.onActivityDeleted)
        
        # Goals view
        self.goalsView = QWidget()
        self.goalsView.setObjectName("goalsPage")
        goals_layout = QVBoxLayout(self.goalsView)
        
        # Goals header
        goals_header = QWidget()
        goals_header_layout = QHBoxLayout(goals_header)
        goals_header_layout.setContentsMargins(30, 30, 30, 20)
        
        goals_title = QLabel("Goals & Objectives")
        goals_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E293B;")
        goals_header_layout.addWidget(goals_title)
        goals_header_layout.addStretch()
        
        add_goal_btn = QPushButton("+ New Goal")
        add_goal_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
        """)
        goals_header_layout.addWidget(add_goal_btn)
        
        goals_layout.addWidget(goals_header)
        
        # Goals content - placeholder for now
        goals_content = QLabel("Goals feature coming soon...")
        goals_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        goals_content.setStyleSheet("font-size: 16px; color: #64748B; padding: 40px;")
        goals_layout.addWidget(goals_content)
        
        self.contentStack.addWidget(self.goalsView)
        
        # Pomodoro view
        self.pomodoroView = PomodoroWidget(self)
        self.contentStack.addWidget(self.pomodoroView)
        
        # Settings view
        self.settingsView = QWidget()
        self.settingsView.setObjectName("settingsPage")
        settings_layout = QVBoxLayout(self.settingsView)
        
        # Settings header
        settings_header = QWidget()
        settings_header_layout = QHBoxLayout(settings_header)
        settings_header_layout.setContentsMargins(30, 30, 30, 20)
        
        settings_title = QLabel("Settings")
        settings_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E293B;")
        settings_header_layout.addWidget(settings_title)
        
        settings_layout.addWidget(settings_header)
        
        # Settings form
        settings_form = QWidget()
        form_layout = QFormLayout(settings_form)
        form_layout.setContentsMargins(30, 10, 30, 30)
        form_layout.setSpacing(20)
        
        # Theme selection
        theme_combo = QComboBox()
        theme_combo.addItems(["Light", "Dark", "System"])
        form_layout.addRow("Theme:", theme_combo)
        
        # Notification settings
        notification_check = QCheckBox("Enable notifications")
        notification_check.setChecked(True)
        form_layout.addRow("Notifications:", notification_check)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 8px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
        """)
        form_layout.addRow("", save_btn)
        
        settings_layout.addWidget(settings_form)
        settings_layout.addStretch()
        
        self.contentStack.addWidget(self.settingsView)
        
        # Add to main layout
        self.main_layout.addWidget(self.contentStack, 1)

    def setupSidebar(self):
        """Set up the sidebar navigation."""
        # Create sidebar container
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet("""
            #sidebar {
                background-color: #2E3440;
                border-right: 1px solid #3B4252;
                min-width: 220px;
                max-width: 220px;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo container
        logo_container = QWidget()
        logo_container.setFixedHeight(80)
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo label with text (replace with actual logo when available)
        logo_label = QLabel("TaskTitan")
        logo_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #88C0D0;
        """)
        logo_layout.addWidget(logo_label)
        sidebar_layout.addWidget(logo_container)
        
        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3B4252; margin: 0 10px;")
        separator.setFixedHeight(1)
        sidebar_layout.addWidget(separator)

        # Scrollable area for navigation categories
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Navigation container
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(10)
        
        # Button style
        button_style = """
            QPushButton {
                text-align: left;
                padding: 12px 15px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: medium;
                color: #ECEFF4;
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #3B4252;
            }
            QPushButton:checked {
                background-color: #5E81AC;
                color: #ECEFF4;
            }
            QPushButton:checked:hover {
                background-color: #5E81AC;
            }
        """
        
        # Navigation buttons
        self.nav_buttons = []
        
        # Dashboard button
        dashboard_btn = QPushButton("Dashboard")
        dashboard_btn.setIcon(QIcon("assets/icons/dashboard.png"))
        dashboard_btn.setIconSize(QSize(20, 20))
        dashboard_btn.setCheckable(True)
        dashboard_btn.setStyleSheet(button_style)
        dashboard_btn.clicked.connect(lambda: self.switchView(DASHBOARD_VIEW, dashboard_btn))
        nav_layout.addWidget(dashboard_btn)
        self.nav_buttons.append(dashboard_btn)
        
        # Activities button (unified)
        activities_btn = QPushButton("Activities")
        activities_btn.setIcon(QIcon("assets/icons/activities.png"))
        activities_btn.setIconSize(QSize(20, 20))
        activities_btn.setCheckable(True)
        activities_btn.setStyleSheet(button_style)
        activities_btn.clicked.connect(lambda: self.switchView(ACTIVITIES_VIEW, activities_btn))
        nav_layout.addWidget(activities_btn)
        self.nav_buttons.append(activities_btn)
        
        # Goals button
        goals_btn = QPushButton("Goals")
        goals_btn.setIcon(QIcon("assets/icons/goals.png"))
        goals_btn.setIconSize(QSize(20, 20))
        goals_btn.setCheckable(True)
        goals_btn.setStyleSheet(button_style)
        goals_btn.clicked.connect(lambda: self.switchView(GOALS_VIEW, goals_btn))
        nav_layout.addWidget(goals_btn)
        self.nav_buttons.append(goals_btn)
        
        # Pomodoro button
        pomodoro_btn = QPushButton("Pomodoro")
        pomodoro_btn.setIcon(QIcon("assets/icons/pomodoro.png"))
        pomodoro_btn.setIconSize(QSize(20, 20))
        pomodoro_btn.setCheckable(True)
        pomodoro_btn.setStyleSheet(button_style)
        pomodoro_btn.clicked.connect(lambda: self.switchView(POMODORO_VIEW, pomodoro_btn))
        nav_layout.addWidget(pomodoro_btn)
        self.nav_buttons.append(pomodoro_btn)
        
        # Add spacing
        nav_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Settings button
        settings_btn = QPushButton("Settings")
        settings_btn.setIcon(QIcon("assets/icons/settings.png"))
        settings_btn.setIconSize(QSize(20, 20))
        settings_btn.setCheckable(True)
        settings_btn.setStyleSheet(button_style)
        settings_btn.clicked.connect(lambda: self.switchView(SETTINGS_VIEW, settings_btn))
        nav_layout.addWidget(settings_btn)
        self.nav_buttons.append(settings_btn)
        
        scroll_area.setWidget(nav_container)
        sidebar_layout.addWidget(scroll_area)
        
        # Add sidebar to main layout
        self.main_layout.addWidget(sidebar)
        
        # Set default active button
        dashboard_btn.setChecked(True)

    def setupDashboard(self):
        """Create a modern dashboard view with widgets."""
        # Create a scrollable dashboard
        self.dashboard_view = QWidget()
        
        # Create a scroll area to make dashboard scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create the container widget for the scrollable content
        dashboard_container = QWidget()
        dashboard_container.setStyleSheet("""
            background-color: #F8FAFC;
            border-radius: 12px;
        """)
        dashboard_layout = QVBoxLayout(dashboard_container)
        dashboard_layout.setContentsMargins(20, 20, 20, 20)
        dashboard_layout.setSpacing(20)
        
        # Welcome header
        welcome_label = QLabel("Welcome to TaskTitan")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E293B;")
        dashboard_layout.addWidget(welcome_label)
        
        # Quick summary
        summary_frame = QFrame()
        summary_frame.setStyleSheet("background-color: white; border-radius: 10px;")
        summary_layout = QVBoxLayout(summary_frame)
        
        summary_title = QLabel("Today's Summary")
        summary_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #334155;")
        summary_layout.addWidget(summary_title)
        
        # Grid for stats
        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)
        
        # Activities stats
        activities_label = QLabel("Activities")
        activities_label.setStyleSheet("font-weight: bold;")
        stats_grid.addWidget(activities_label, 0, 0)
        
        self.activities_counter = QLabel("0/0")
        stats_grid.addWidget(self.activities_counter, 0, 1)
        
        # Goals stats
        goals_label = QLabel("Goals")
        goals_label.setStyleSheet("font-weight: bold;")
        stats_grid.addWidget(goals_label, 1, 0)
        
        self.goals_counter = QLabel("0/0")
        stats_grid.addWidget(self.goals_counter, 1, 1)
        
        summary_layout.addLayout(stats_grid)
        dashboard_layout.addWidget(summary_frame)
        
        # Quick access buttons
        quick_access_frame = QFrame()
        quick_access_frame.setStyleSheet("background-color: white; border-radius: 10px;")
        quick_access_layout = QVBoxLayout(quick_access_frame)
        
        quick_access_title = QLabel("Quick Access")
        quick_access_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #334155;")
        quick_access_layout.addWidget(quick_access_title)
        
        # Buttons for quick access
        buttons_layout = QHBoxLayout()
        
        activities_btn = QPushButton("Activities")
        activities_btn.setIcon(get_icon("tasks"))
        activities_btn.clicked.connect(lambda: self.changePage(ACTIVITIES_VIEW))
        buttons_layout.addWidget(activities_btn)
        
        daily_btn = QPushButton("Daily View")
        daily_btn.setIcon(get_icon("calendar-day"))
        daily_btn.clicked.connect(lambda: self.changePage(DAILY_VIEW))
        buttons_layout.addWidget(daily_btn)
        
        weekly_btn = QPushButton("Weekly View")
        weekly_btn.setIcon(get_icon("calendar"))
        weekly_btn.clicked.connect(lambda: self.changePage(WEEKLY_VIEW))
        buttons_layout.addWidget(weekly_btn)
        
        quick_access_layout.addLayout(buttons_layout)
        dashboard_layout.addWidget(quick_access_frame)
        
        # Add quick action buttons in header
        quick_add_btn = QPushButton("+ Add Activity")
        quick_add_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #6366F1;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
            }
        """)
        quick_add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Create a menu for the button
        quick_add_menu = QMenu(self)
        quick_add_menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
        """)
        
        # Add menu actions
        add_task_action = QAction("Add Task", self)
        add_task_action.triggered.connect(lambda: self.addActivity('task'))
        quick_add_menu.addAction(add_task_action)
        
        add_event_action = QAction("Add Event", self)
        add_event_action.triggered.connect(lambda: self.addActivity('event'))
        quick_add_menu.addAction(add_event_action)
        
        add_habit_action = QAction("Add Habit", self)
        add_habit_action.triggered.connect(lambda: self.addActivity('habit'))
        quick_add_menu.addAction(add_habit_action)
        
        # Set the menu for the button
        quick_add_btn.setMenu(quick_add_menu)
        dashboard_layout.addWidget(quick_add_btn)
        
        # Add stretch to push everything to the top
        dashboard_layout.addStretch()
        
        # Set up the dashboard
        scroll_area.setWidget(dashboard_container)
        
        # Add the scroll area to the dashboard view layout
        dashboard_view_layout = QVBoxLayout(self.dashboard_view)
        dashboard_view_layout.setContentsMargins(0, 0, 0, 0)
        dashboard_view_layout.addWidget(scroll_area)
        
        # Add the dashboard view to the content stack
        self.content_stack.addWidget(self.dashboard_view)

    def setupToolbar(self):
        """Set up the toolbar with user options and actions."""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(20, 20))
        self.toolbar.setStyleSheet("""
            QToolBar {
                spacing: 10px;
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #F3F4F6;
            }
            QToolButton:pressed {
                background-color: #E5E7EB;
            }
        """)
        
        # Activities button - go directly to activities view
        activities_action = QAction(get_icon("tasks"), "Activities", self)
        activities_action.triggered.connect(self.openActivitiesView)
        self.toolbar.addAction(activities_action)
        
        # Spacer to push actions to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.toolbar.addWidget(spacer)
        
        # Add activities dropdown
        add_menu = QMenu(self)
        add_menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
        """)
        
        add_task_action = QAction("Add Task", self)
        add_task_action.triggered.connect(lambda: self.addActivity('task'))
        add_menu.addAction(add_task_action)
        
        add_event_action = QAction("Add Event", self)
        add_event_action.triggered.connect(lambda: self.addActivity('event'))
        add_menu.addAction(add_event_action)
        
        add_habit_action = QAction("Add Habit", self)
        add_habit_action.triggered.connect(lambda: self.addActivity('habit'))
        add_menu.addAction(add_habit_action)
        
        add_button = QAction(get_icon("add"), "Add Activity", self)
        add_button.setMenu(add_menu)
        self.toolbar.addAction(add_button)
        
        # Search action
        search_action = QAction(get_icon("search"), "Search", self)
        search_action.triggered.connect(self.openSearchDialog)
        self.toolbar.addAction(search_action)
        
        # User menu action
        self.user_action = QAction(get_icon("user"), "User", self)
        self.user_action.triggered.connect(self.showUserMenu)
        self.toolbar.addAction(self.user_action)
        
        self.addToolBar(self.toolbar)

    def changePage(self, index):
        """Change to a different page in the application."""
        # Unselect the current page button
        self.nav_buttons[self.current_page].setChecked(False)
        self.nav_buttons[self.current_page].style().unpolish(self.nav_buttons[self.current_page])
        self.nav_buttons[self.current_page].style().polish(self.nav_buttons[self.current_page])
        
        # Select the new page button
        self.nav_buttons[index].setChecked(True)
        self.nav_buttons[index].style().unpolish(self.nav_buttons[index])
        self.nav_buttons[index].style().polish(self.nav_buttons[index])
        
        # Change the stack widget to show the selected page
        self.contentStack.setCurrentIndex(index)
        self.current_page = index

    def loadData(self):
        """Load initial data for the application."""
        # Initialize the activities view data
        self.activitiesView.loadActivities()
        
        # This would load data from the database for all views
        # For now, just update the dashboard counters
        self.refreshData()
        
    def refreshData(self):
        """Refresh data periodically."""
        try:
            # Use the database manager to get counts for activities
            # For a real implementation, this would query the unified activities table
            # with different type filters
            
            # Count all activities
            total_activities = 0
            completed_activities = 0
            
            # In our sample implementation we'll get data from the activities_view
            for activity_type, activities in self.activitiesView.activities.items():
                total_activities += len(activities)
                completed_activities += sum(1 for a in activities if a.get('completed', False))
            
            self.activities_counter.setText(f"{completed_activities}/{total_activities}")
            
            # Count goals (unchanged)
            total_goals = self.db_manager.count_items('goals')
            completed_goals = self.db_manager.count_items('goals', completed=True)
            self.goals_counter.setText(f"{completed_goals}/{total_goals}")
            
            # Refresh all views
            for i in range(self.contentStack.count()):
                widget = self.contentStack.widget(i)
                if hasattr(widget, 'refresh'):
                    widget.refresh()
                    
        except Exception as e:
            print(f"Error refreshing data: {e}")
    
    def addTask(self):
        """Open dialog to add a new task."""
        try:
            # Check if we are already on the tasks view
            if self.contentStack.currentIndex() != ACTIVITIES_VIEW:
                # Change to the activities view first
                self.changePage(ACTIVITIES_VIEW)
            
            # Call the show add task dialog method on the task view
            if hasattr(self.activitiesView, 'showAddActivityDialog'):
                self.activitiesView.showAddActivityDialog('task')
            else:
                print("Error: activitiesView does not have showAddActivityDialog method")
                QMessageBox.warning(self, "Error", "Could not open the add task dialog")
        except Exception as e:
            print(f"Error showing add task dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open add task dialog: {str(e)}")
    
    def addEvent(self):
        """Open dialog to add a new event."""
        # Placeholder for event addition functionality
        pass
    
    def openSettings(self):
        """Open the settings dialog."""
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()
    
    def openDailyView(self):
        """Show the daily view with the current date."""
        self.changePage(DAILY_VIEW)
        self.daily_view.setDate(QDate.currentDate())

    def runDatabaseDiagnostics(self):
        """Run diagnostics on the database and fix issues."""
        try:
            # Check the database file
            db_path = self.db_manager.db_path
            db_dir = os.path.dirname(db_path)
            
            msg = QMessageBox()
            msg.setWindowTitle("Database Diagnostics")
            
            # Build the diagnostic message
            diag_text = f"Database Path: {db_path}\n"
            
            # Check if directory exists
            if not os.path.exists(db_dir):
                diag_text += f"❌ Database directory does not exist\n"
                os.makedirs(db_dir, exist_ok=True)
                diag_text += f"✅ Created database directory\n"
            else:
                diag_text += f"✅ Database directory exists\n"
            
            # Check if database file exists
            if not os.path.exists(db_path):
                diag_text += f"❌ Database file does not exist\n"
            else:
                file_size = os.path.getsize(db_path)
                diag_text += f"✅ Database file exists (Size: {file_size} bytes)\n"
                
                # Check if we can open the database
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Check if tables exist
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    table_names = [table[0] for table in tables]
                    
                    if 'tasks' in table_names:
                        diag_text += f"✅ Tasks table exists\n"
                        
                        # Count tasks
                        cursor.execute("SELECT COUNT(*) FROM tasks")
                        task_count = cursor.fetchone()[0]
                        diag_text += f"ℹ️ Found {task_count} tasks in the database\n"
                    else:
                        diag_text += f"❌ Tasks table missing\n"
                    
                    conn.close()
                except Exception as e:
                    diag_text += f"❌ Database error: {str(e)}\n"
            
            # Check if we should fix the database
            fix_button = msg.addButton("Fix Database", QMessageBox.ButtonRole.ActionRole)
            msg.addButton("Close", QMessageBox.ButtonRole.RejectRole)
            msg.setText(diag_text)
            
            result = msg.exec()
            
            # If user clicked "Fix Database"
            if msg.clickedButton() == fix_button:
                self.fixDatabaseIssues()
        
        except Exception as e:
            QMessageBox.critical(self, "Diagnostics Error", f"Error running diagnostics: {str(e)}")

    def fixDatabaseIssues(self):
        """Fix database issues."""
        try:
            # Reinitialize the database
            db_path = self.db_manager.db_path
            
            # Create a backup if the file exists
            if os.path.exists(db_path):
                backup_path = f"{db_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                import shutil
                shutil.copy2(db_path, backup_path)
                
            # Force recreation of tables
            self.db_manager.initialize_db()
            
            # Refresh the data
            self.refreshData()
            
            QMessageBox.information(self, "Database Fixed", 
                f"Database has been fixed and tables recreated.\n"
                f"If a backup was needed, it was saved to:\n{os.path.dirname(db_path)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Fix Error", f"Error fixing database: {str(e)}")

    def addActivity(self, activity_type='task'):
        """Open dialog to add a new activity."""
        # Change to the activities view first
        self.changePage(ACTIVITIES_VIEW)
        
        # Then show the add dialog for the specified activity type
        self.activitiesView.showAddActivityDialog(activity_type)

    def openActivitiesView(self):
        """Show the unified activities view."""
        self.changePage(ACTIVITIES_VIEW)

    def switchView(self, index, button=None):
        """Switch between different views in the content stack."""
        # Update the content stack index
        self.contentStack.setCurrentIndex(index)
        
        # Update button states
        if button:
            # Uncheck all buttons first
            for btn in self.nav_buttons:
                if btn != button:
                    btn.setChecked(False)
            # Check the active button
            button.setChecked(True)
            
    def onActivityAdded(self, activity):
        """Handle when a new activity is added."""
        # Refresh the dashboard counters
        self.refreshData()
        
    def onActivityCompleted(self, activity_id, activity_type):
        """Handle when an activity is marked as completed."""
        # Refresh the dashboard counters
        self.refreshData()
        
    def onActivityDeleted(self, activity_id, activity_type):
        """Handle when an activity is deleted."""
        # Refresh the dashboard counters
        self.refreshData()