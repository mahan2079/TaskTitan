import os
import json
import asyncio
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QPushButton, QToolBar, QTabWidget, QScrollArea, QStackedWidget,
    QGridLayout, QSizePolicy, QSpacerItem, QMenu, QCalendarWidget, QProgressBar
)
from PyQt6.QtCore import Qt, QSize, QDate, QTime, QTimer, pyqtSignal, QPropertyAnimation, QRect, QRectF
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor, QFont, QPainter, QBrush, QPen
import darkdetect
import pyqtgraph as pg
import sqlite3
import logging

from app.models.database import initialize_db
from app.models.database_manager import get_manager, close_connection
from app.views.calendar_widget import ModernCalendarWidget, CalendarWithEventList
from app.views.unified_activities_widget import UnifiedActivitiesWidget
from app.views.goal_widget import GoalWidget
from app.views.productivity_view import ProductivityView
from app.views.pomodoro_widget import PomodoroWidget
from app.views.settings_dialog import SettingsDialog
from app.views.weekly_plan_view import WeeklyPlanView
from app.resources import get_icon, get_pixmap, VIEW_NAMES, DASHBOARD_VIEW, ACTIVITIES_VIEW, GOALS_VIEW, PRODUCTIVITY_VIEW, POMODORO_VIEW, WEEKLY_PLAN_VIEW, SETTINGS_VIEW

# Import custom progress chart to avoid QRectF issues
from app.views.custom_progress import CircularProgressChart

class TaskTitanApp(QMainWindow):
    """Main application window for TaskTitan with modern UI."""
    
    def __init__(self):
        """Initialize the main application window."""
        super().__init__()
        
        # Initialize database connection
        self.conn, self.cursor = initialize_db()
        
        # Get the database manager for direct access
        self.db_manager = get_manager()
        
        # Initialize activities manager
        from app.models.activities_manager import ActivitiesManager
        self.activities_manager = ActivitiesManager()
        self.activities_manager.set_connection(self.conn, self.cursor)
        
        # Set up window properties
        self.setWindowTitle("TaskTitan")
        self.setMinimumSize(1200, 800)
        
        self.setupUI()
        self.loadData()
        
        # Start periodic data refresh timer (every 60 seconds)
        self.refreshTimer = QTimer(self)
        self.refreshTimer.timeout.connect(self.refreshData)
        self.refreshTimer.start(60000)

    def setupUI(self):
        """Set up the modern UI with dashboard layout."""
        self.setWindowTitle("TaskTitan")
        self.setMinimumSize(1200, 800)
        
        # Main central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout with sidebar and content area
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create sidebar for navigation
        self.setupSidebar()
        
        # Create stacked widget for main content
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack, 1)
        
        # Create the dashboard page
        self.setupDashboard()
        
        # Create activities page (unified view for tasks, events, habits)
        self.activities_view = UnifiedActivitiesWidget(self)
        self.content_stack.addWidget(self.activities_view)
        
        # Create goals page
        self.goals_view = GoalWidget(self)
        self.content_stack.addWidget(self.goals_view)
        
        # Create productivity page
        self.productivity_view = ProductivityView(self)
        self.content_stack.addWidget(self.productivity_view)
        
        # Create pomodoro page
        self.pomodoro_view = PomodoroWidget(self)
        self.content_stack.addWidget(self.pomodoro_view)
        
        # Create weekly plan page
        self.weekly_plan_view = WeeklyPlanView(self)
        self.content_stack.addWidget(self.weekly_plan_view)
        
        # Create settings page
        self.settings_widget = QWidget()
        self.content_stack.addWidget(self.settings_widget)
        
        # Set up toolbar with user options
        self.setupToolbar()
        
        # Default start with dashboard page
        self.content_stack.setCurrentIndex(0)
        self.current_page = 0
        self.sidebarButtons[0].setProperty("selected", True)
        self.sidebarButtons[0].style().unpolish(self.sidebarButtons[0])
        self.sidebarButtons[0].style().polish(self.sidebarButtons[0])

    def setupSidebar(self):
        """Create a modern sidebar for navigation."""
        # Sidebar container
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        
        # Set style for the sidebar
        self.sidebar.setStyleSheet("""
            #sidebar {
                background-color: #1E293B;
                color: white;
                border-right: 1px solid #334155;
            }
            
            QPushButton {
                border: none;
                text-align: left;
                padding: 12px 16px 12px 20px;
                margin: 4px 8px;
                border-radius: 8px;
                color: white;
                font-size: 15px;
                font-weight: 500;
                background-color: transparent;
            }
            
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
            
            QPushButton[selected="true"] {
                background-color: #6366F1;
                color: white;
                font-weight: bold;
            }
            
            QLabel {
                color: white;
                font-size: 22px;
                font-weight: bold;
                padding: 20px;
                margin-bottom: 10px;
            }
        """)
        
        # Vertical layout for sidebar content
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 20)
        sidebar_layout.setSpacing(2)
        
        # App logo and title
        logo_label = QLabel("TaskTitan")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(logo_label)
        
        # Navigation buttons
        self.sidebarButtons = []
        
        # The menu items with icons and labels
        menu_items = [
            (VIEW_NAMES[DASHBOARD_VIEW], "dashboard", DASHBOARD_VIEW),
            ("Activities", "calendar", ACTIVITIES_VIEW),
            (VIEW_NAMES[GOALS_VIEW], "goals", GOALS_VIEW),
            (VIEW_NAMES[PRODUCTIVITY_VIEW], "productivity", PRODUCTIVITY_VIEW),
            (VIEW_NAMES[POMODORO_VIEW], "pomodoro", POMODORO_VIEW),
            (VIEW_NAMES[WEEKLY_PLAN_VIEW], "weekly_plan", WEEKLY_PLAN_VIEW),
            (VIEW_NAMES[SETTINGS_VIEW], "settings", SETTINGS_VIEW),
        ]
        
        for index, (label, icon_name, view_index) in enumerate(menu_items):
            btn = QPushButton(label)
            
            # Set icon from resources
            icon = get_icon(icon_name)
            if not icon.isNull():
                btn.setIcon(icon)
                btn.setIconSize(QSize(20, 20))
            
            btn.setProperty("selected", False)
            btn.setProperty("index", view_index)
            btn.clicked.connect(lambda checked, idx=view_index: self.changePage(idx))
            sidebar_layout.addWidget(btn)
            self.sidebarButtons.append(btn)
        
        # Add vertical spacer at the bottom
        sidebar_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Add sidebar to main layout
        self.main_layout.addWidget(self.sidebar)

    def setupDashboard(self):
        """Create a modern dashboard view with widgets."""
        # Create a scrollable dashboard
        self.dashboard = QWidget()
        
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
        
        # Dashboard header with gradient background
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
            border-radius: 12px;
            padding: 10px;
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        welcome_label = QLabel(f"Welcome back! Today is {datetime.now().strftime('%A, %B %d')}")
        welcome_label.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header_layout.addWidget(welcome_label)
        
        # Add spacer to push welcome label to the left
        header_layout.addStretch()
        
        # Add user menu button
        user_menu_btn = QPushButton("User Menu")
        user_menu_btn.setStyleSheet("""
            QPushButton {
                background-color: #EEF2FF;
                color: #4F46E5;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
                border: 1px solid #C7D2FE;
            }
            QPushButton:hover {
                background-color: #E0E7FF;
            }
        """)
        user_menu_btn.clicked.connect(self.showUserMenu)
        header_layout.addWidget(user_menu_btn)
        
        dashboard_layout.addWidget(header_frame)
        
        # Calendar widget card with enhanced styling
        calendar_card = QFrame()
        calendar_card.setObjectName("calendar-card")
        calendar_card.setStyleSheet("""
            QFrame#calendar-card {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                             stop:0 #F8FAFC, 
                                             stop:1 #FFFFFF);
                border-radius: 16px;
                border: 1px solid #E2E8F0;
                padding: 15px;
            }
        """)
        calendar_layout = QVBoxLayout(calendar_card)
        calendar_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create fancy header for calendar
        calendar_header_frame = QFrame()
        calendar_header_frame.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                       stop:0 #6366F1, 
                                       stop:1 #818CF8);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        """)
        calendar_header_layout = QHBoxLayout(calendar_header_frame)
        calendar_header_layout.setContentsMargins(10, 8, 10, 8)
        
        calendar_icon = QLabel()
        calendar_pixmap = get_pixmap("calendar")
        if not calendar_pixmap.isNull():
            calendar_icon.setPixmap(calendar_pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio))
        calendar_header_layout.addWidget(calendar_icon)
        
        calendar_header = QLabel("Monthly Calendar")
        calendar_header.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        calendar_header_layout.addWidget(calendar_header)
        
        # Add today's date to the header
        today_label = QLabel(datetime.now().strftime("%B %Y"))
        today_label.setStyleSheet("color: white; font-size: 14px;")
        calendar_header_layout.addStretch()
        calendar_header_layout.addWidget(today_label)
        
        calendar_layout.addWidget(calendar_header_frame)
        
        # Calendar widget with enhanced height
        self.dashboard_calendar = CalendarWithEventList()
        calendar_layout.addWidget(self.dashboard_calendar)
        
        # Add legend for calendar events
        legend_frame = QFrame()
        legend_frame.setStyleSheet("""
            background-color: #F8FAFC;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
            padding: 8px;
            margin-top: 10px;
        """)
        legend_layout = QHBoxLayout(legend_frame)
        
        # Current day legend
        current_day_icon = QFrame()
        current_day_icon.setFixedSize(16, 16)
        current_day_icon.setStyleSheet("""
            background-color: #6366F1;
            border-radius: 4px;
        """)
        current_day_label = QLabel("Today")
        current_day_label.setStyleSheet("color: #4B5563; font-size: 12px;")
        legend_layout.addWidget(current_day_icon)
        legend_layout.addWidget(current_day_label)
        legend_layout.addSpacing(10)
        
        # Event legend
        event_icon = QFrame()
        event_icon.setFixedSize(16, 16)
        event_icon.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
        """)
        
        # Add colored dots to the event icon
        event_icon_layout = QHBoxLayout(event_icon)
        event_icon_layout.setContentsMargins(2, 10, 2, 2)
        event_icon_layout.setSpacing(2)
        
        for i in range(3):
            dot = QFrame()
            dot.setFixedSize(3, 3)
            dot.setStyleSheet(f"""
                background-color: {['#F87171', '#FBBF24', '#34D399'][i]};
                border-radius: 1px;
            """)
            event_icon_layout.addWidget(dot)
        
        event_label = QLabel("Events")
        event_label.setStyleSheet("color: #4B5563; font-size: 12px;")
        legend_layout.addWidget(event_icon)
        legend_layout.addWidget(event_label)
        
        legend_layout.addStretch()
        
        # Quick navigation button to go to today
        today_btn = QPushButton("Go to Today")
        today_btn.setStyleSheet("""
            QPushButton {
                background-color: #EEF2FF;
                color: #4F46E5;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
                border: 1px solid #C7D2FE;
            }
            QPushButton:hover {
                background-color: #E0E7FF;
            }
        """)
        today_btn.clicked.connect(lambda: self.dashboard_calendar.calendar.setSelectedDate(QDate.currentDate()))
        legend_layout.addWidget(today_btn)
        
        calendar_layout.addWidget(legend_frame)
        
        # Add full-width calendar to layout
        dashboard_layout.addWidget(calendar_card)
        
        # Goal Progress Wheels Section with enhanced styling
        goals_card = QFrame()
        goals_card.setStyleSheet("""
            background-color: white;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            padding: 10px;
        """)
        goals_layout = QVBoxLayout(goals_card)
        
        goals_header_layout = QHBoxLayout()
        goals_icon = QLabel()
        goals_pixmap = get_pixmap("goals")
        if not goals_pixmap.isNull():
            goals_icon.setPixmap(goals_pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio))
        goals_header_layout.addWidget(goals_icon)
        
        goals_header = QLabel("Goal Progress")
        goals_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        goals_header_layout.addWidget(goals_header)
        goals_header_layout.addStretch()
        
        view_all_goals = QPushButton("View All")
        view_all_goals.setStyleSheet("""
            QPushButton {
                background-color: #EEF2FF;
                color: #6366F1;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #DBEAFE;
            }
        """)
        view_all_goals.setFixedWidth(100)
        view_all_goals.clicked.connect(lambda: self.changePage(2))  # Go to Goals page
        goals_header_layout.addWidget(view_all_goals)
        
        goals_layout.addLayout(goals_header_layout)
        
        # Create a grid layout for the goal progress wheels
        goals_grid = QGridLayout()
        goals_grid.setSpacing(20)
        
        # We'll populate this grid with goal progress wheels in loadData()
        self.goals_wheels_container = goals_grid
        goals_layout.addLayout(goals_grid)
        
        # Add the goals card to the dashboard
        dashboard_layout.addWidget(goals_card)
        
        # Set the scroll area's widget to the container
        scroll_area.setWidget(dashboard_container)
        
        # Create a layout for the main dashboard widget
        main_dashboard_layout = QVBoxLayout(self.dashboard)
        main_dashboard_layout.setContentsMargins(0, 0, 0, 0)
        main_dashboard_layout.addWidget(scroll_area)
        
        # Add dashboard to stack
        self.content_stack.addWidget(self.dashboard)

    def setupToolbar(self):
        """Set up the application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(20, 20))
        
        # Search action
        search_action = QAction("Search", self)
        search_icon = get_icon("search")
        if not search_icon.isNull():
            search_action.setIcon(search_icon)
        search_action.triggered.connect(self.openSearchDialog)
        toolbar.addAction(search_action)
        
        toolbar.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_icon = get_icon("settings")
        if not settings_icon.isNull():
            settings_action.setIcon(settings_icon)
        settings_action.triggered.connect(lambda: self.changePage(SETTINGS_VIEW))  # Go to Settings page
        toolbar.addAction(settings_action)
        
        # Add spacer to push next items to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)
        
        # Sync action
        sync_action = QAction("Sync", self)
        sync_action.triggered.connect(self.refreshData)
        toolbar.addAction(sync_action)
        
        # User menu action
        user_action = QAction("User", self)
        user_icon = get_icon("user")
        if not user_icon.isNull():
            user_action.setIcon(user_icon)
        user_action.triggered.connect(self.showUserMenu)
        toolbar.addAction(user_action)
        
        self.addToolBar(toolbar)

    def changePage(self, index):
        """Change the current page in the stacked widget."""
        self.content_stack.setCurrentIndex(index)
        self.current_page = index
        
        # Refresh data when switching to activities or weekly plan views
        if index == 1:  # Activities view
            if hasattr(self, 'activities_view') and self.activities_view:
                self.activities_view.refresh()
        elif index == 5:  # Weekly plan view
            if hasattr(self, 'weekly_plan_view') and self.weekly_plan_view:
                self.weekly_plan_view.refresh()
        
        # Update sidebar button styling
        for button in self.sidebarButtons:
            button.setProperty("selected", False)
            button.style().unpolish(button)
            button.style().polish(button)
            
        if index < len(self.sidebarButtons):
            self.sidebarButtons[index].setProperty("selected", True)
            self.sidebarButtons[index].style().unpolish(self.sidebarButtons[index])
            self.sidebarButtons[index].style().polish(self.sidebarButtons[index])

    def loadData(self):
        """Load activities and tasks from database and update UI."""
        logging.debug("Loading data...")
        if hasattr(self, 'activitiesView') and self.activitiesView:
            if hasattr(self.activitiesView, 'loadActivitiesFromDatabase'):
                self.activitiesView.loadActivitiesFromDatabase()
            elif hasattr(self.activitiesView, 'refresh'):
                self.activitiesView.refresh()
        
        # Sync calendar with activities if both exist
        if hasattr(self, 'dashboard_calendar') and hasattr(self, 'activities_manager'):
            self.dashboard_calendar.sync_with_activities(self.activities_manager)
        
        self.refreshData()

    def refreshData(self):
        """Refresh data periodically."""
        try:
            # Count all activities
            total_activities = 0
            completed_activities = 0
            
            # In our sample implementation we'll get data from the activities view
            if hasattr(self, 'activitiesView') and hasattr(self.activitiesView, 'activities'):
                if isinstance(self.activitiesView.activities, dict):
                    for activity_type, activities in self.activitiesView.activities.items():
                        total_activities += len(activities)
                        completed_activities += sum(1 for a in activities if a.get('completed', False))
                else:
                    # Handle the case where activities is a list
                    total_activities = len(self.activitiesView.activities)
                    completed_activities = sum(1 for a in self.activitiesView.activities if a.get('completed', False))
            
            if hasattr(self, 'activities_counter'):
                self.activities_counter.setText(f"{completed_activities}/{total_activities}")
            
            # Count goals (unchanged)
            if hasattr(self, 'db_manager') and hasattr(self, 'goals_counter'):
                total_goals = self.db_manager.count_items('goals') 
                completed_goals = self.db_manager.count_items('goals', completed=True)
                self.goals_counter.setText(f"{completed_goals}/{total_goals}")
            
            # Refresh all views
            if hasattr(self, 'content_stack'):
                for i in range(self.content_stack.count()):
                    widget = self.content_stack.widget(i)
                    if hasattr(widget, 'refresh'):
                        widget.refresh()
                    
        except Exception as e:
            print(f"Error refreshing data: {e}")

    def loadActivities(self):
        """Load activities data for the unified activities view."""
        try:
            # First, check if there are existing activities in the database
            from app.models.activities_manager import ActivitiesManager
            activities_manager = ActivitiesManager(self.conn, self.cursor)
            
            # Get count of existing activities
            self.cursor.execute("SELECT COUNT(*) FROM activities")
            activity_count = self.cursor.fetchone()[0]
            
            # Only add sample activities if none exist
            if activity_count == 0:
                self.addSampleActivities()
            else:
                # Refresh the activities view
                self.activitiesView.refresh()
        except Exception as e:
            print(f"Error loading activities: {e}")

    def loadDashboardGoals(self):
        """Load goals and create progress wheel visualizations for them."""
        try:
            # Clear existing items in the goals container
            self.clearLayout(self.goals_wheels_container)
            
            # First, get all parent goals (top-level goals)
            self.cursor.execute("""
                SELECT id, title, due_date, created_date, parent_id, completed, priority
            FROM goals 
                WHERE parent_id IS NULL AND completed = 0
                ORDER BY priority DESC, due_date ASC
                LIMIT 10
            """)
            
            parent_goals = self.cursor.fetchall()
            
            if not parent_goals:
                # No goals found, add sample goals and reload
                self.addSampleGoals()
                
                # Try fetching goals again
                self.cursor.execute("""
                    SELECT id, title, due_date, created_date, parent_id, completed, priority
                    FROM goals
                    WHERE parent_id IS NULL AND completed = 0
                    ORDER BY priority DESC, due_date ASC
                    LIMIT 10
                """)
                
                parent_goals = self.cursor.fetchall()
                
                # If still no goals, show the message
                if not parent_goals:
                    empty_label = QLabel("No active goals found")
                    empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    empty_label.setStyleSheet("color: #64748B; padding: 20px;")
                    self.goals_wheels_container.addWidget(empty_label, 0, 0, 1, 3)
                    return
            
            # Row counter for the grid layout
            current_row = 0
            
            # Define colors for different priority levels
            priority_colors = {
                0: "#10B981",  # Low - Green
                1: "#6366F1",  # Medium - Purple
                2: "#F97316"   # High - Orange
            }
            
            # Process each parent goal
            for parent_goal in parent_goals:
                parent_id, parent_title, parent_due_date, parent_created_date, _, parent_completed, parent_priority = parent_goal
                
                # Get priority color
                priority_color = priority_colors.get(parent_priority, "#6366F1")
                
                # Create colorful section header for this parent goal
                header_frame = QFrame()
                header_frame.setStyleSheet(f"""
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                              stop:0 {priority_color}, 
                                              stop:1 {priority_color}88);
                    border-radius: 8px;
                    padding: 8px;
                    margin-top: 10px;
                """)
                header_layout = QHBoxLayout(header_frame)
                header_layout.setContentsMargins(10, 5, 10, 5)
                
                # Add priority indicator dot
                priority_indicator = QLabel()
                priority_indicator.setFixedSize(12, 12)
                priority_indicator.setStyleSheet(f"""
                    background-color: white;
                    border-radius: 6px;
                """)
                header_layout.addWidget(priority_indicator)
                
                # Add goal title
                section_label = QLabel(parent_title)
                section_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
                header_layout.addWidget(section_label)
                
                # Add due date if it exists
                if parent_due_date:
                    due_date = datetime.strptime(parent_due_date, "%Y-%m-%d").date()
                    today = datetime.now().date()
                    days_remaining = (due_date - today).days
                    
                    if days_remaining > 0:
                        due_label = QLabel(f"{days_remaining} days left")
                    elif days_remaining == 0:
                        due_label = QLabel("Due today!")
                    else:
                        due_label = QLabel(f"Overdue by {-days_remaining} days")
                    
                    due_label.setStyleSheet("color: white; font-size: 12px;")
                    header_layout.addWidget(due_label)
                
                header_layout.addStretch()
                
                # Add the header to the grid
                self.goals_wheels_container.addWidget(header_frame, current_row, 0, 1, 3)
                current_row += 1
                
                # Create a frame for the wheels section with light background
                wheels_frame = QFrame()
                wheels_frame.setStyleSheet(f"""
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #E2E8F0;
                    padding: 15px;
                    margin-bottom: 5px;
                """)
                wheels_layout = QGridLayout(wheels_frame)
                wheels_layout.setSpacing(20)
                
                # Parent goal as dictionary
                parent_goal_dict = {
                    'id': parent_id,
                    'title': parent_title,
                    'due_date': parent_due_date,
                    'created_date': parent_created_date,
                    'parent_id': None,
                    'completed': parent_completed == 1,
                    'priority': parent_priority
                }
                
                # Calculate parent goal progress
                parent_progress = self.calculateGoalProgress(parent_goal_dict)
                
                # Create parent goal chart - make it larger than subgoals
                parent_chart = CircularProgressChart("Overall Progress", parent_progress)
                parent_chart.setMinimumSize(160, 200)
                parent_chart.mousePressEvent = lambda e, g_id=parent_id: self.openGoalDetails(g_id)
                
                # Add parent goal chart to first column
                wheels_layout.addWidget(parent_chart, 0, 0)
                
                # Get subgoals for this parent
                self.cursor.execute("""
                    SELECT id, title, due_date, created_date, parent_id, completed
                    FROM goals
                    WHERE parent_id = ? AND completed = 0
                    ORDER BY due_date ASC
                    LIMIT 5
                """, (parent_id,))
                
                subgoals = self.cursor.fetchall()
                
                # Column counter for subgoals in current row
                col = 1
                sub_row = 0
                
                # Process each subgoal
                for subgoal in subgoals:
                    subgoal_id, subgoal_title, subgoal_due_date, subgoal_created_date, subgoal_parent_id, subgoal_completed = subgoal
                    
                    # Convert to dictionary
                    subgoal_dict = {
                        'id': subgoal_id,
                        'title': subgoal_title,
                        'due_date': subgoal_due_date,
                        'created_date': subgoal_created_date,
                        'parent_id': subgoal_parent_id,
                        'completed': subgoal_completed == 1
                    }
                    
                    # Calculate progress
                    subgoal_progress = self.calculateGoalProgress(subgoal_dict)
                    
                    # Create progress wheel
                    subgoal_chart = CircularProgressChart(subgoal_title, subgoal_progress)
                    subgoal_chart.mousePressEvent = lambda e, g_id=subgoal_id: self.openGoalDetails(g_id)
                    
                    # Add to grid - maximum 3 items per row (0, 1, 2)
                    if col <= 2:
                        wheels_layout.addWidget(subgoal_chart, sub_row, col)
                        col += 1
                else:
                        # Start a new row
                        sub_row += 1
                        col = 1
                        wheels_layout.addWidget(subgoal_chart, sub_row, col)
                        col += 1
                
                # Add the entire wheels frame to the main grid
                self.goals_wheels_container.addWidget(wheels_frame, current_row, 0, 1, 3)
                current_row += 1
                
                # Add some space between goal sections
                spacer = QWidget()
                spacer.setFixedHeight(15)
                self.goals_wheels_container.addWidget(spacer, current_row, 0, 1, 3)
                current_row += 1
                
        except (sqlite3.Error, ValueError) as e:
            print(f"Error loading dashboard goals: {e}")
            # Show error message
            error_label = QLabel("Error loading goals")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #EF4444; padding: 20px;")
            self.goals_wheels_container.addWidget(error_label, 0, 0, 1, 3)
            
    def calculateGoalProgress(self, goal):
        """Calculate the progress percentage for a goal based on time.
        
        Args:
            goal: The goal dictionary to calculate progress for
            
        Returns:
            int: Progress percentage (0-100)
        """
        # If goal is completed, return 100%
        if goal['completed']:
            return 100
        
        # Find all subgoals for this goal
        try:
            self.cursor.execute("""
                SELECT id, due_date, created_date, completed
                FROM goals
                WHERE parent_id = ?
            """, (goal['id'],))
            
            subgoals = self.cursor.fetchall()
            
            # If there are no subgoals, calculate progress based on time
            if not subgoals:
                return self.calculateTimeBasedProgress(goal)
            
            # If there are subgoals, calculate based on subgoal completion
            total_count = len(subgoals)
            completed_count = sum(1 for sg in subgoals if sg[3] == 1)
            
            if total_count > 0:
                return int((completed_count / total_count) * 100)
            else:
                return self.calculateTimeBasedProgress(goal)
                
        except sqlite3.Error as e:
            print(f"Error calculating goal progress: {e}")
            return 0
    
    def calculateTimeBasedProgress(self, goal):
        """Calculate progress based on time elapsed.
        
        Args:
            goal: The goal to calculate progress for
            
        Returns:
            int: Progress percentage (0-100)
        """
        try:
            # Get the start and due dates
            if goal['created_date']:
                start_date = datetime.strptime(goal['created_date'], "%Y-%m-%d").date()
            else:
                # Default to 2 weeks before due date
                due_date = datetime.strptime(goal['due_date'], "%Y-%m-%d").date()
                start_date = due_date - timedelta(days=14)
            
            due_date = datetime.strptime(goal['due_date'], "%Y-%m-%d").date()
            today = datetime.now().date()
            
            # Calculate total duration and elapsed duration
            total_days = (due_date - start_date).days
            if total_days <= 0:  # Guard against invalid dates
                return 0
                
            elapsed_days = (today - start_date).days
            
            # Calculate progress percentage
            if elapsed_days < 0:  # Goal hasn't started yet
                progress = 0
            elif elapsed_days >= total_days:  # Goal is overdue
                progress = 90  # Almost complete but not 100% until actually marked complete
            else:
                progress = (elapsed_days / total_days) * 100
                
            return int(progress)
        except (ValueError, TypeError):
            # Return 0 if there are date parsing errors
            return 0
            
    def openGoalDetails(self, goal_id):
        """Open goal details in the goals view."""
        # Switch to goals view
        self.changePage(2)
        
        # Locate and select the goal in the goals view
        if hasattr(self.goals_view, 'selectGoalById'):
            self.goals_view.selectGoalById(goal_id)

    def loadStatistics(self):
        """Load statistics for dashboard charts."""
        # We've moved this functionality to loadDashboardGoals
        pass

    def getStartOfWeek(self):
        """Get the start date of the current week (Monday)."""
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week.isoformat()

    def clearLayout(self, layout):
        """Clear all items from a layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    self.clearLayout(item.layout())

    def openSearchDialog(self):
        """Open the search dialog."""
        # Not implemented in this version
        pass

    def showUserMenu(self):
        """Show the user menu."""
        menu = QMenu(self)
        
        profile_action = QAction("Profile", self)
        profile_action.triggered.connect(self.showUserProfile)
        
        sync_action = QAction("Sync Data", self)
        sync_action.triggered.connect(self.syncData)
        
        theme_action = QAction("Toggle Theme", self)
        theme_action.triggered.connect(self.toggleTheme)
        
        menu.addAction(profile_action)
        menu.addAction(sync_action)
        menu.addAction(theme_action)
        menu.addSeparator()
        
        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self.logout)
        menu.addAction(logout_action)
        
        # Position the menu
        toolbar = self.findChild(QToolBar)
        menu.exec(toolbar.mapToGlobal(toolbar.rect().bottomRight()))

    def showUserProfile(self):
        """Show the user profile dialog."""
        pass

    def syncData(self):
        """Sync application data."""
        self.refreshData()

    def toggleTheme(self):
        """Toggle between light and dark theme."""
        # This would be implemented to switch stylesheets
        pass

    def logout(self):
        """Logout the current user."""
        # This would be implemented in a real application
        pass 

    def addSampleGoals(self):
        """Add sample goals to the database if none exist."""
        try:
            # Get current date
            today = datetime.now().date()
            
            # Check if we already have goals
            self.cursor.execute("SELECT COUNT(*) FROM goals")
            count = self.cursor.fetchone()[0]
            
            if count > 0:
                # We already have goals, don't add samples
                return
                
            # Add sample parent goals with subgoals
            sample_goals = [
                # Parent goal 1: Learn Programming
                {
                    'title': 'Learn Programming',
                    'created_date': (today - timedelta(days=30)).isoformat(),
                    'due_date': (today + timedelta(days=150)).isoformat(),
                    'due_time': '23:59',
                    'priority': 2,  # High
                    'completed': 0,
                    'parent_id': None
                },
                # Parent goal 2: Get Fit
                {
                    'title': 'Get Fit',
                    'created_date': (today - timedelta(days=15)).isoformat(),
                    'due_date': (today + timedelta(days=90)).isoformat(),
                    'due_time': '23:59',
                    'priority': 1,  # Medium
                    'completed': 0,
                    'parent_id': None
                },
                # Parent goal 3: Read More Books
                {
                    'title': 'Read More Books',
                    'created_date': (today - timedelta(days=10)).isoformat(),
                    'due_date': (today + timedelta(days=120)).isoformat(),
                    'due_time': '23:59',
                    'priority': 0,  # Low
                    'completed': 0,
                    'parent_id': None
                }
            ]
            
            # Add parent goals first to get their IDs
            parent_ids = {}
            
            for goal in sample_goals:
                self.cursor.execute("""
                    INSERT INTO goals (title, created_date, due_date, due_time, priority, completed, parent_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    goal['title'], 
                    goal['created_date'], 
                    goal['due_date'], 
                    goal['due_time'],
                    goal['priority'],
                    goal['completed'],
                    goal['parent_id']
                ))
                
                # Store the ID for this parent goal
                parent_ids[goal['title']] = self.cursor.lastrowid
            
            # Now add subgoals with references to parent goals
            subgoals = [
                # Subgoals for "Learn Programming"
                {
                    'title': 'Complete Python Course',
                    'created_date': (today - timedelta(days=30)).isoformat(),
                    'due_date': (today + timedelta(days=30)).isoformat(),
                    'due_time': '23:59',
                    'priority': 2,
                    'completed': 0,
                    'parent_id': parent_ids['Learn Programming']
                },
                {
                    'title': 'Build a Web Application',
                    'created_date': (today + timedelta(days=31)).isoformat(),
                    'due_date': (today + timedelta(days=90)).isoformat(),
                    'due_time': '23:59',
                    'priority': 1,
                    'completed': 0,
                    'parent_id': parent_ids['Learn Programming']
                },
                {
                    'title': 'Learn Machine Learning',
                    'created_date': (today + timedelta(days=91)).isoformat(),
                    'due_date': (today + timedelta(days=150)).isoformat(),
                    'due_time': '23:59',
                    'priority': 0,
                    'completed': 0,
                    'parent_id': parent_ids['Learn Programming']
                },
                
                # Subgoals for "Get Fit"
                {
                    'title': 'Cardio 3x per week',
                    'created_date': (today - timedelta(days=15)).isoformat(),
                    'due_date': (today + timedelta(days=90)).isoformat(),
                    'due_time': '23:59',
                    'priority': 1,
                    'completed': 0,
                    'parent_id': parent_ids['Get Fit']
                },
                {
                    'title': 'Strength Training 2x per week',
                    'created_date': (today - timedelta(days=15)).isoformat(),
                    'due_date': (today + timedelta(days=90)).isoformat(),
                    'due_time': '23:59',
                    'priority': 1,
                    'completed': 0,
                    'parent_id': parent_ids['Get Fit']
                },
                
                # Subgoals for "Read More Books"
                {
                    'title': 'Fiction: 6 books',
                    'created_date': (today - timedelta(days=10)).isoformat(),
                    'due_date': (today + timedelta(days=120)).isoformat(),
                    'due_time': '23:59',
                    'priority': 0,
                    'completed': 0,
                    'parent_id': parent_ids['Read More Books']
                },
                {
                    'title': 'Non-fiction: 6 books',
                    'created_date': (today - timedelta(days=10)).isoformat(),
                    'due_date': (today + timedelta(days=120)).isoformat(),
                    'due_time': '23:59',
                    'priority': 0,
                    'completed': 0,
                    'parent_id': parent_ids['Read More Books']
                }
            ]
            
            # Add all subgoals
            for subgoal in subgoals:
                self.cursor.execute("""
                    INSERT INTO goals (title, created_date, due_date, due_time, priority, completed, parent_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    subgoal['title'], 
                    subgoal['created_date'], 
                    subgoal['due_date'], 
                    subgoal['due_time'],
                    subgoal['priority'],
                    subgoal['completed'],
                    subgoal['parent_id']
                ))
            
            # Commit the transaction
            self.conn.commit()
            print("Added sample goals successfully!")
            
        except sqlite3.Error as e:
            print(f"Error adding sample goals: {e}")
            # Roll back any changes if something went wrong
            self.conn.rollback() 

    def addSampleActivities(self):
        """Add sample activities for demo purposes."""
        # Check if activities view is initialized
        if not hasattr(self, 'activitiesView'):
            return
            
        # Sample task
        task_data = {
            'type': 'task',
            'title': 'Complete project proposal',
            'date': QDate.currentDate(),
            'start_time': QTime(10, 0),
            'end_time': QTime(12, 0),
            'priority': 2,  # High
            'category': 'Work'
        }
        self.activitiesView.addActivity(task_data)
        
        # Sample event
        event_data = {
            'type': 'event',
            'title': 'Team meeting',
            'date': QDate.currentDate(),
            'start_time': QTime(14, 0),
            'end_time': QTime(15, 30),
            'category': 'Work'
        }
        self.activitiesView.addActivity(event_data)
        
        # Sample habit
        habit_data = {
            'type': 'habit',
            'title': 'Morning meditation',
            'date': QDate.currentDate(),
            'start_time': QTime(7, 0),
            'end_time': QTime(7, 30),
            'days_of_week': 'Mon,Wed,Fri',
            'category': 'Health'
        }
        self.activitiesView.addActivity(habit_data)
        
        # Sample future task
        tomorrow = QDate.currentDate().addDays(1)
        future_task_data = {
            'type': 'task',
            'title': 'Review documentation',
            'date': tomorrow,
            'start_time': QTime(11, 0),
            'end_time': QTime(12, 30),
            'priority': 1,  # Medium
            'category': 'Work'
        }
        self.activitiesView.addActivity(future_task_data) 

    def onActivityAdded(self, activity):
        """Handle when a new activity is added."""
        # Refresh the dashboard counters
        self.refreshData()
        
        # Refresh the dashboard calendar if it exists and this is an event
        if activity.get('type') == 'event' and hasattr(self, 'dashboard_calendar') and hasattr(self, 'activities_manager'):
            self.dashboard_calendar.sync_with_activities(self.activities_manager)
        
    def onActivityCompleted(self, activity_id, completed, activity_type):
        """Handle when an activity is marked as completed."""
        # Refresh the dashboard counters
        self.refreshData()
        
        # Refresh the dashboard calendar if it exists and this is an event
        if activity_type == 'event' and hasattr(self, 'dashboard_calendar') and hasattr(self, 'activities_manager'):
            self.dashboard_calendar.sync_with_activities(self.activities_manager)
        
    def onActivityDeleted(self, activity_id, activity_type):
        """Handle when an activity is deleted."""
        # Refresh the dashboard counters
        self.refreshData()
        
        # Refresh the dashboard calendar if it exists and this is an event
        if activity_type == 'event' and hasattr(self, 'dashboard_calendar') and hasattr(self, 'activities_manager'):
            self.dashboard_calendar.sync_with_activities(self.activities_manager) 

    def savePendingChanges(self):
        """Save any pending changes before closing."""
        try:
            # Make sure activities view explicitly saves its data
            if hasattr(self, 'activitiesView') and hasattr(self.activitiesView, 'saveChanges'):
                print("Saving activities before exit...")
                self.activitiesView.saveChanges()
            
            # Save any unsaved data in the current view
            current_widget = self.content_stack.currentWidget()
            if hasattr(current_widget, 'saveChanges'):
                print(f"Saving changes for {current_widget.__class__.__name__}")
                current_widget.saveChanges()
            
            # Loop through all views to save any pending changes
            for i in range(self.content_stack.count()):
                widget = self.content_stack.widget(i)
                if widget != current_widget and hasattr(widget, 'saveChanges'):
                    print(f"Saving changes for {widget.__class__.__name__}")
                    widget.saveChanges()
                    
            # Ensure database commits all changes
            if hasattr(self, 'conn'):
                self.conn.commit()
                
        except Exception as e:
            print(f"Error saving pending changes: {e}") 

