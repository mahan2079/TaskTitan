import os
import json
import asyncio
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QPushButton, QToolBar, QTabWidget, QScrollArea, QStackedWidget,
    QGridLayout, QSizePolicy, QSpacerItem, QMenu, QCalendarWidget, QProgressBar, QLineEdit, QStatusBar, QDialog
)
from PyQt6.QtCore import Qt, QSize, QDate, QTime, QTimer, pyqtSignal, QPropertyAnimation, QRect, QRectF, QEasingCurve, QPoint
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor, QFont, QPainter, QBrush, QPen, QShortcut, QKeySequence
import darkdetect
import pyqtgraph as pg
import sqlite3

from app.models.database import initialize_db
from app.models.database_manager import get_manager, close_connection
from app.controllers.search_manager import SearchManager, SearchResult
from app.views.calendar_widget import ModernCalendarWidget, CalendarWithEventList
from app.views.unified_activities_widget import UnifiedActivitiesWidget
from app.views.goal_widget import GoalWidget
from app.views.productivity_view import DailyTrackerView
from app.views.pomodoro_widget import PomodoroWidget
from app.views.settings_dialog import SettingsDialog
from app.views.weekly_plan_view import WeeklyPlanView
from app.views.search_results_widget import SearchResultsWidget
from app.views.toast_notification import ToastManager, ToastType, show_toast
from app.views.custom_progress import CircularProgressChart
from app.resources import get_icon, get_pixmap, VIEW_NAMES, DASHBOARD_VIEW, ACTIVITIES_VIEW, GOALS_VIEW, PRODUCTIVITY_VIEW, POMODORO_VIEW, WEEKLY_PLAN_VIEW, SETTINGS_VIEW
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SearchLineEdit(QLineEdit):
    """Custom search line edit with focus handling."""
    
    def __init__(self, parent=None):
        """Initialize the search line edit."""
        super().__init__(parent)
        self.parent_window = parent
    
    def focusOutEvent(self, event):
        """Handle focus out event."""
        super().focusOutEvent(event)
        if self.parent_window and hasattr(self.parent_window, 'hideSearchResults'):
            # Delay hiding to allow clicking on results
            QTimer.singleShot(200, self.parent_window.hideSearchResults)


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
        # Ensure unified activities tables exist
        try:
            self.activities_manager.create_tables()
        except Exception as e:
            logger.error(f"Error ensuring activities tables: {e}", exc_info=True)
        
        # Initialize search manager
        self.search_manager = SearchManager(
            db_manager=self.db_manager,
            activities_manager=self.activities_manager
        )
        
        # Set up window properties
        self.setWindowTitle("TaskTitan")
        self.setMinimumSize(1200, 800)
        
        self.setupUI()
        self.loadData()
        
        # Start periodic data refresh timer (every 60 seconds)
        self.refreshTimer = QTimer(self)
        self.refreshTimer.timeout.connect(self.refreshData)
        self.refreshTimer.start(60000)
        
        # Search debounce timer
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.performSearch)

    def setupUI(self):
        """Set up the modern UI with dashboard layout."""
        self.setWindowTitle("TaskTitan")
        self.setMinimumSize(1200, 800)
        
        # Main central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Build a header bar and a content row (sidebar + stack)
        root_layout = QVBoxLayout(self.central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("headerBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        self.sidebar_toggle_btn = QPushButton("☰")
        self.sidebar_toggle_btn.setFixedWidth(36)
        self.sidebar_toggle_btn.clicked.connect(self.toggleSidebar)
        self.sidebar_toggle_btn.setToolTip("Toggle sidebar (Ctrl+B)")
        header_layout.addWidget(self.sidebar_toggle_btn)

        title = QLabel("TaskTitan")
        title.setObjectName("headerTitle")
        header_layout.addWidget(title)
        
        # Navigation controls container (for daily/weekly plan views)
        self.nav_controls_container = QWidget()
        self.nav_controls_container.setObjectName("navControlsContainer")
        nav_layout = QHBoxLayout(self.nav_controls_container)
        nav_layout.setContentsMargins(20, 0, 20, 0)
        nav_layout.setSpacing(12)
        
        # Daily view navigation
        self.daily_nav_container = QWidget()
        self.daily_nav_container.setObjectName("dailyNavContainer")
        daily_nav_layout = QHBoxLayout(self.daily_nav_container)
        daily_nav_layout.setContentsMargins(0, 0, 0, 0)
        daily_nav_layout.setSpacing(8)
        
        self.prev_day_btn = QPushButton("◀ Previous Day")
        self.prev_day_btn.setObjectName("navButton")
        self.prev_day_btn.clicked.connect(self.onPreviousDay)
        daily_nav_layout.addWidget(self.prev_day_btn)
        
        self.day_label = QLabel()
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day_label.setObjectName("dailyDayLabel")
        self.day_label.setMinimumWidth(250)
        daily_nav_layout.addWidget(self.day_label)
        
        self.next_day_btn = QPushButton("Next Day ▶")
        self.next_day_btn.setObjectName("navButton")
        self.next_day_btn.clicked.connect(self.onNextDay)
        daily_nav_layout.addWidget(self.next_day_btn)
        
        self.today_btn = QPushButton("Today")
        today_icon = get_icon("calendar-today")
        if not today_icon.isNull():
            self.today_btn.setIcon(today_icon)
        self.today_btn.setObjectName("navButton")
        self.today_btn.clicked.connect(self.onGoToToday)
        daily_nav_layout.addWidget(self.today_btn)
        
        # View toggle button (also in daily view to switch back to weekly)
        self.daily_view_toggle_btn = QPushButton("Weekly View")
        self.daily_view_toggle_btn.setCheckable(True)
        self.daily_view_toggle_btn.setChecked(True)  # Checked when in daily view
        self.daily_view_toggle_btn.setObjectName("navButton")
        self.daily_view_toggle_btn.clicked.connect(self.onToggleView)
        daily_nav_layout.addWidget(self.daily_view_toggle_btn)
        
        # Weekly view navigation
        self.weekly_nav_container = QWidget()
        self.weekly_nav_container.setObjectName("weeklyNavContainer")
        weekly_nav_layout = QHBoxLayout(self.weekly_nav_container)
        weekly_nav_layout.setContentsMargins(0, 0, 0, 0)
        weekly_nav_layout.setSpacing(8)
        
        self.prev_week_btn = QPushButton("◀ Previous Week")
        self.prev_week_btn.setObjectName("navButton")
        self.prev_week_btn.clicked.connect(self.onPreviousWeek)
        weekly_nav_layout.addWidget(self.prev_week_btn)
        
        self.week_label = QLabel()
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.week_label.setObjectName("weeklyWeekLabel")
        self.week_label.setMinimumWidth(250)
        weekly_nav_layout.addWidget(self.week_label)
        
        self.next_week_btn = QPushButton("Next Week ▶")
        self.next_week_btn.setObjectName("navButton")
        self.next_week_btn.clicked.connect(self.onNextWeek)
        weekly_nav_layout.addWidget(self.next_week_btn)
        
        self.today_week_btn = QPushButton("Today")
        today_week_icon = get_icon("calendar-today")
        if not today_week_icon.isNull():
            self.today_week_btn.setIcon(today_week_icon)
        self.today_week_btn.setObjectName("navButton")
        self.today_week_btn.clicked.connect(self.onGoToCurrentWeek)
        weekly_nav_layout.addWidget(self.today_week_btn)
        
        # View toggle button (for weekly plan view)
        self.view_toggle_btn = QPushButton("Daily View")
        self.view_toggle_btn.setCheckable(True)
        self.view_toggle_btn.setObjectName("navButton")
        self.view_toggle_btn.clicked.connect(self.onToggleView)
        weekly_nav_layout.addWidget(self.view_toggle_btn)
        
        # Add both nav containers to main nav layout
        nav_layout.addWidget(self.daily_nav_container)
        nav_layout.addWidget(self.weekly_nav_container)
        
        # Initially hide navigation controls
        self.nav_controls_container.hide()
        self.daily_nav_container.hide()
        self.weekly_nav_container.hide()
        
        header_layout.addWidget(self.nav_controls_container)
        header_layout.addStretch()

        self.search_field = SearchLineEdit(self)
        self.search_field.setObjectName("headerSearch")
        self.search_field.setPlaceholderText("Search (Ctrl+K)…")
        self.search_field.setFixedWidth(280)
        self.search_field.setToolTip("Search across tasks, events, habits, goals, and categories (Ctrl+K)")
        self.search_field.textChanged.connect(self.onSearchTextChanged)
        self.search_field.returnPressed.connect(self.onSearchEnterPressed)
        header_layout.addWidget(self.search_field)
        
        # Search results widget
        self.search_results_widget = SearchResultsWidget(self)
        self.search_results_widget.resultSelected.connect(self.onSearchResultSelected)
        self.search_results_widget.hide()

        root_layout.addWidget(header)

        content_row = QWidget()
        row_layout = QHBoxLayout(content_row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        # Sidebar
        self.setupSidebar()
        row_layout.addWidget(self.sidebar)

        # Stack
        self.content_stack = QStackedWidget()
        row_layout.addWidget(self.content_stack, 1)

        root_layout.addWidget(content_row, 1)
        
        # Create the dashboard page
        self.setupDashboard()
        
        # Create activities page (unified view for tasks, events, habits)
        self.activities_view = UnifiedActivitiesWidget(self)
        self.content_stack.addWidget(self.activities_view)
        
        # Create goals page
        self.goals_view = GoalWidget(self)
        self.content_stack.addWidget(self.goals_view)
        
        # Create productivity page
        self.productivity_view = DailyTrackerView(self)
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
        
        # Set up status bar
        self.setupStatusBar()
        
        # Initialize toast notification manager
        self._toast_manager = ToastManager(self)
        self._toast_manager.setGeometry(self.geometry())
        
        # Default start with dashboard page
        self.content_stack.setCurrentIndex(0)
        self.current_page = 0
        self.sidebarButtons[0].setProperty("data-selected", True)
        self.sidebarButtons[0].style().unpolish(self.sidebarButtons[0])
        self.sidebarButtons[0].style().polish(self.sidebarButtons[0])
        
        # Initialize navigation visibility
        self.updateNavigationVisibility(0)

        # Keyboard shortcuts
        self._installShortcuts()

    def setupSidebar(self):
        """Create a modern sidebar for navigation."""
        # Sidebar container
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self._sidebar_full_width = 240
        self.sidebar.setMinimumWidth(0)
        self.sidebar.setMaximumWidth(self._sidebar_full_width)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(4)

        logo_label = QLabel("TaskTitan")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sidebar_layout.addWidget(logo_label)

        self.sidebarButtons = []
        menu_items = [
            (VIEW_NAMES[DASHBOARD_VIEW], "dashboard", DASHBOARD_VIEW),
            (VIEW_NAMES[ACTIVITIES_VIEW], "calendar", ACTIVITIES_VIEW),
            (VIEW_NAMES[GOALS_VIEW], "goals", GOALS_VIEW),
            (VIEW_NAMES[PRODUCTIVITY_VIEW], "productivity", PRODUCTIVITY_VIEW),
            (VIEW_NAMES[POMODORO_VIEW], "pomodoro", POMODORO_VIEW),
            (VIEW_NAMES[WEEKLY_PLAN_VIEW], "weekly_plan", WEEKLY_PLAN_VIEW),
            (VIEW_NAMES[SETTINGS_VIEW], "settings", SETTINGS_VIEW),
        ]
        for label, icon_name, idx in menu_items:
            btn = QPushButton(label)
            icon = get_icon(icon_name)
            if not icon.isNull():
                btn.setIcon(icon)
                btn.setIconSize(QSize(18, 18))
            btn.setProperty("data-selected", False)
            btn.clicked.connect(lambda _=False, target=idx: self.changePage(target))
            
            # Add tooltips with keyboard shortcuts
            shortcut_map = {
                DASHBOARD_VIEW: "Ctrl+1",
                ACTIVITIES_VIEW: "Ctrl+2",
                GOALS_VIEW: "Ctrl+3",
                PRODUCTIVITY_VIEW: "Ctrl+4",
                POMODORO_VIEW: "Ctrl+5",
                WEEKLY_PLAN_VIEW: "Ctrl+6",
                SETTINGS_VIEW: "Ctrl+7"
            }
            shortcut = shortcut_map.get(idx, "")
            if shortcut:
                btn.setToolTip(f"{VIEW_NAMES[idx]} ({shortcut})")
            else:
                btn.setToolTip(VIEW_NAMES[idx])
            
            sidebar_layout.addWidget(btn)
            self.sidebarButtons.append(btn)

        sidebar_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

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
        dashboard_container.setProperty("data-card", "true")
        # Theme system will handle styling via data-card property
        dashboard_layout = QVBoxLayout(dashboard_container)
        dashboard_layout.setContentsMargins(20, 20, 20, 20)
        dashboard_layout.setSpacing(20)
        
        # Dashboard header card
        header_frame = QFrame()
        header_frame.setProperty("data-card", "true")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        welcome_label = QLabel(f"Welcome back! Today is {datetime.now().strftime('%A, %B %d')}")
        header_layout.addWidget(welcome_label)
        
        # Add spacer to push welcome label to the left
        header_layout.addStretch()
        
        # Add user menu button
        user_menu_btn = QPushButton("User Menu")
        # Theme system will handle button styling
        user_menu_btn.clicked.connect(self.showUserMenu)
        header_layout.addWidget(user_menu_btn)
        
        dashboard_layout.addWidget(header_frame)
        
        # Calendar widget card with enhanced styling
        calendar_card = QFrame()
        calendar_card.setObjectName("calendar-card")
        calendar_card.setProperty("data-card", "true")
        # Theme system will handle styling via data-card property
        calendar_layout = QVBoxLayout(calendar_card)
        calendar_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create simple header for calendar (theme handles styling)
        calendar_header_frame = QFrame()
        calendar_header_layout = QHBoxLayout(calendar_header_frame)
        calendar_header_layout.setContentsMargins(10, 8, 10, 8)
        
        calendar_icon = QLabel()
        calendar_pixmap = get_pixmap("calendar")
        if not calendar_pixmap.isNull():
            calendar_icon.setPixmap(calendar_pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio))
        calendar_header_layout.addWidget(calendar_icon)
        
        calendar_header = QLabel("Monthly Calendar")
        calendar_header_layout.addWidget(calendar_header)
        
        # Add today's date to the header
        today_label = QLabel(datetime.now().strftime("%B %Y"))
        calendar_header_layout.addStretch()
        calendar_header_layout.addWidget(today_label)
        
        calendar_layout.addWidget(calendar_header_frame)
        
        # Calendar widget with enhanced height
        self.dashboard_calendar = CalendarWithEventList()
        calendar_layout.addWidget(self.dashboard_calendar)
        
        # Add legend for calendar events
        legend_frame = QFrame()
        legend_layout = QHBoxLayout(legend_frame)
        
        # Current day legend
        current_day_icon = QFrame()
        current_day_icon.setFixedSize(16, 16)
        from app.themes import ThemeManager
        primary_color = ThemeManager.get_color("primary")
        current_day_icon.setStyleSheet(f"""
            background-color: {primary_color};
            border-radius: 4px;
        """)
        current_day_label = QLabel("Today")
        # Theme system will handle label styling
        current_day_label.setStyleSheet("font-size: 12px;")
        legend_layout.addWidget(current_day_icon)
        legend_layout.addWidget(current_day_label)
        legend_layout.addSpacing(10)
        
        # Event legend
        event_icon = QFrame()
        event_icon.setFixedSize(16, 16)
        event_icon.setStyleSheet("border: 1px solid rgba(0,0,0,0.1); border-radius: 8px;")
        
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
        # Theme system will handle label styling
        event_label.setStyleSheet("font-size: 12px;")
        legend_layout.addWidget(event_icon)
        legend_layout.addWidget(event_label)
        
        legend_layout.addStretch()
        
        # Quick navigation button to go to today
        today_btn = QPushButton("Go to Today")
        today_btn.clicked.connect(lambda: self.dashboard_calendar.calendar.setSelectedDate(QDate.currentDate()))
        legend_layout.addWidget(today_btn)
        
        calendar_layout.addWidget(legend_frame)
        
        # Add full-width calendar to layout
        dashboard_layout.addWidget(calendar_card)
        
        # Goal Progress Wheels Section with enhanced styling
        goals_card = QFrame()
        goals_card.setProperty("data-card", "true")
        # Theme system will handle styling via data-card property
        goals_layout = QVBoxLayout(goals_card)
        
        goals_header_layout = QHBoxLayout()
        goals_icon = QLabel()
        goals_pixmap = get_pixmap("goals")
        if not goals_pixmap.isNull():
            goals_icon.setPixmap(goals_pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio))
        goals_header_layout.addWidget(goals_icon)
        
        goals_header = QLabel("Goal Progress")
        # Theme system will handle label styling
        goals_header.setStyleSheet("font-size: 18px; font-weight: bold;")
        goals_header_layout.addWidget(goals_header)
        goals_header_layout.addStretch()
        
        view_all_goals = QPushButton("View All")
        # Theme system will handle button styling
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
        search_action.setToolTip("Focus search field (Ctrl+K)")
        search_action.triggered.connect(self.focusSearch)
        toolbar.addAction(search_action)
        
        toolbar.addSeparator()
        
        # Settings action (opens dialog with theme selection)
        settings_action = QAction("Settings", self)
        settings_icon = get_icon("settings")
        if not settings_icon.isNull():
            settings_action.setIcon(settings_icon)
        settings_action.setToolTip("Open settings dialog")
        settings_action.triggered.connect(self.openSettingsDialog)
        toolbar.addAction(settings_action)
        
        # Add spacer to push next items to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)
        
        # Sync action
        sync_action = QAction("Sync", self)
        sync_action.setToolTip("Refresh and sync all data")
        sync_action.triggered.connect(self.refreshData)
        toolbar.addAction(sync_action)
        
        # User menu action
        user_action = QAction("User", self)
        user_icon = get_icon("user")
        if not user_icon.isNull():
            user_action.setIcon(user_icon)
        user_action.setToolTip("User menu and settings")
        user_action.triggered.connect(self.showUserMenu)
        toolbar.addAction(user_action)
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_icon = get_icon("settings")
        if not settings_icon.isNull():
            settings_action.setIcon(settings_icon)
        settings_action.setToolTip("Open settings dialog")
        settings_action.triggered.connect(self.openSettingsDialog)
        toolbar.addAction(settings_action)
        
        self.addToolBar(toolbar)

    def setupStatusBar(self):
        """Set up the status bar for feedback messages."""
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        
        # Set initial status message
        self.status_bar.showMessage("Ready")
        
        # Style the status bar
        from app.themes import ThemeManager
        theme_colors = ThemeManager.get_current_palette()
        bg_color = theme_colors.get("surface", "#FFFFFF")
        text_color = theme_colors.get("text", "#000000")
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {bg_color};
                color: {text_color};
                border-top: 1px solid {theme_colors.get("border", "#E2E8F0")};
                padding: 4px;
            }}
        """)
    
    def show_status_message(self, message, timeout=3000):
        """Show a temporary status message.
        
        Args:
            message: Message to display
            timeout: Duration in milliseconds (0 = permanent)
        """
        self.status_bar.showMessage(message, timeout)
    
    def show_success_toast(self, message):
        """Show a success toast notification."""
        show_toast(self, message, ToastType.SUCCESS)
    
    def show_error_toast(self, message):
        """Show an error toast notification."""
        show_toast(self, message, ToastType.ERROR)
    
    def show_warning_toast(self, message):
        """Show a warning toast notification."""
        show_toast(self, message, ToastType.WARNING)
    
    def show_info_toast(self, message):
        """Show an info toast notification."""
        show_toast(self, message, ToastType.INFO)

    def changePage(self, index):
        """Change the current page and update selection styling."""
        self.content_stack.setCurrentIndex(index)
        self.current_page = index

        if index == ACTIVITIES_VIEW and hasattr(self, 'activities_view'):
            if hasattr(self.activities_view, 'refresh'):
                self.activities_view.refresh()
        if index == WEEKLY_PLAN_VIEW and hasattr(self, 'weekly_plan_view'):
            if hasattr(self.weekly_plan_view, 'refresh'):
                self.weekly_plan_view.refresh()

        for i, button in enumerate(self.sidebarButtons):
            button.setProperty("data-selected", i == index)
            button.style().unpolish(button)
            button.style().polish(button)
        
        # Show/hide navigation controls based on current view
        self.updateNavigationVisibility(index)

        return None
    
    def updateNavigationVisibility(self, page_index):
        """Update navigation controls visibility based on current page."""
        from app.resources.constants import WEEKLY_PLAN_VIEW
        
        if page_index == WEEKLY_PLAN_VIEW:
            # Show navigation controls for weekly plan view
            self.nav_controls_container.show()
            # Check if we're in daily or weekly view within weekly plan
            if hasattr(self, 'weekly_plan_view') and hasattr(self.weekly_plan_view, 'stacked_widget'):
                if self.weekly_plan_view.stacked_widget.currentWidget() == self.weekly_plan_view.daily_view:
                    # Show daily navigation
                    self.daily_nav_container.show()
                    self.weekly_nav_container.hide()
                    # Sync day label
                    if hasattr(self.weekly_plan_view.daily_view, 'current_date'):
                        self.day_label.setText(self.weekly_plan_view.daily_view.current_date.toString("dddd, MMMM d, yyyy"))
                    # Update toggle button state
                    if hasattr(self, 'daily_view_toggle_btn'):
                        self.daily_view_toggle_btn.setChecked(True)
                        self.daily_view_toggle_btn.setText("Weekly View")
                    if hasattr(self, 'view_toggle_btn'):
                        self.view_toggle_btn.setChecked(True)
                        self.view_toggle_btn.setText("Weekly View")
                else:
                    # Show weekly navigation
                    self.daily_nav_container.hide()
                    self.weekly_nav_container.show()
                    # Sync week label - update it first if needed
                    if hasattr(self.weekly_plan_view, 'updateWeekLabel'):
                        self.weekly_plan_view.updateWeekLabel()
                    elif hasattr(self.weekly_plan_view, 'week_label'):
                        self.week_label.setText(self.weekly_plan_view.week_label.text())
                    # Update toggle button state
                    if hasattr(self, 'daily_view_toggle_btn'):
                        self.daily_view_toggle_btn.setChecked(False)
                        self.daily_view_toggle_btn.setText("Daily View")
                    if hasattr(self, 'view_toggle_btn'):
                        self.view_toggle_btn.setChecked(False)
                        self.view_toggle_btn.setText("Daily View")
        else:
            # Hide navigation controls for other views
            self.nav_controls_container.hide()
    
    def onPreviousDay(self):
        """Handle previous day button click."""
        if hasattr(self, 'weekly_plan_view') and hasattr(self.weekly_plan_view, 'daily_view'):
            self.weekly_plan_view.daily_view.previousDay()
            # Update label
            if hasattr(self.weekly_plan_view.daily_view, 'current_date'):
                self.day_label.setText(self.weekly_plan_view.daily_view.current_date.toString("dddd, MMMM d, yyyy"))
    
    def onNextDay(self):
        """Handle next day button click."""
        if hasattr(self, 'weekly_plan_view') and hasattr(self.weekly_plan_view, 'daily_view'):
            self.weekly_plan_view.daily_view.nextDay()
            # Update label
            if hasattr(self.weekly_plan_view.daily_view, 'current_date'):
                self.day_label.setText(self.weekly_plan_view.daily_view.current_date.toString("dddd, MMMM d, yyyy"))
    
    def onGoToToday(self):
        """Handle today button click for daily view."""
        if hasattr(self, 'weekly_plan_view') and hasattr(self.weekly_plan_view, 'daily_view'):
            self.weekly_plan_view.daily_view.goToToday()
            # Update label
            if hasattr(self.weekly_plan_view.daily_view, 'current_date'):
                self.day_label.setText(self.weekly_plan_view.daily_view.current_date.toString("dddd, MMMM d, yyyy"))
    
    def onPreviousWeek(self):
        """Handle previous week button click."""
        if hasattr(self, 'weekly_plan_view'):
            self.weekly_plan_view.previousWeek()
            # Update label
            if hasattr(self.weekly_plan_view, 'week_label'):
                self.week_label.setText(self.weekly_plan_view.week_label.text())
    
    def onNextWeek(self):
        """Handle next week button click."""
        if hasattr(self, 'weekly_plan_view'):
            self.weekly_plan_view.nextWeek()
            # Update label
            if hasattr(self.weekly_plan_view, 'week_label'):
                self.week_label.setText(self.weekly_plan_view.week_label.text())
    
    def onGoToCurrentWeek(self):
        """Handle today button click for weekly view."""
        if hasattr(self, 'weekly_plan_view'):
            self.weekly_plan_view.goToCurrentWeek()
            # Update label
            if hasattr(self.weekly_plan_view, 'week_label'):
                self.week_label.setText(self.weekly_plan_view.week_label.text())
    
    def onToggleView(self):
        """Handle view toggle button click."""
        if hasattr(self, 'weekly_plan_view'):
            self.weekly_plan_view.toggleView()
            # Update navigation visibility
            from app.resources.constants import WEEKLY_PLAN_VIEW
            self.updateNavigationVisibility(WEEKLY_PLAN_VIEW)

    def loadData(self):
        """Load activities and tasks from database and update UI."""
        logger.debug("Loading data...")
        if hasattr(self, 'activities_view') and self.activities_view:
            if hasattr(self.activities_view, 'loadActivitiesFromDatabase'):
                self.activities_view.loadActivitiesFromDatabase()
            elif hasattr(self.activities_view, 'refresh'):
                self.activities_view.refresh()
        
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
            if hasattr(self, 'activities_view') and hasattr(self.activities_view, 'activities'):
                if isinstance(self.activities_view.activities, dict):
                    for activity_type, activities in self.activities_view.activities.items():
                        total_activities += len(activities)
                        completed_activities += sum(1 for a in activities if a.get('completed', False))
                else:
                    # Handle the case where activities is a list
                    total_activities = len(self.activities_view.activities)
                    completed_activities = sum(1 for a in self.activities_view.activities if a.get('completed', False))
            
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
            logger.error(f"Error refreshing data: {e}", exc_info=True)

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
                if hasattr(self, 'activities_view'):
                    self.activities_view.refresh()
        except Exception as e:
            logger.error(f"Error loading activities: {e}", exc_info=True)

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
                # Theme system will handle label styling - white text on colored background
                section_label.setStyleSheet("font-size: 16px; font-weight: bold;")
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
                    
                    # Theme system will handle label styling
                    due_label.setStyleSheet("font-size: 12px;")
                    header_layout.addWidget(due_label)
                
                header_layout.addStretch()
                
                # Add the header to the grid
                self.goals_wheels_container.addWidget(header_frame, current_row, 0, 1, 3)
                current_row += 1
                
                # Create a frame for the wheels section with theme-aware background
                wheels_frame = QFrame()
                wheels_frame.setProperty("data-card", "true")
                # Theme system will handle styling via data-card property
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
            logger.error(f"Error loading dashboard goals: {e}", exc_info=True)
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
            logger.error(f"Error calculating goal progress: {e}", exc_info=True)
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
        # Focus the header search; future: open command palette
        if hasattr(self, 'search_field'):
            self.search_field.setFocus()

    def showUserMenu(self):
        """Show the user menu."""
        from app.auth.authentication import get_auth_manager
        auth_manager = get_auth_manager()
        
        menu = QMenu(self)
        
        # Show current user info
        user = auth_manager.get_current_user()
        if user:
            user_info = QAction(f"User: {user['username']}", self)
            user_info.setEnabled(False)
            menu.addAction(user_info)
            menu.addSeparator()
        
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
        
        # Database manager action
        db_manager_action = QAction("Manage Databases...", self)
        db_manager_action.triggered.connect(self.openDatabaseManager)
        menu.addAction(db_manager_action)
        
        menu.addSeparator()
        
        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self.logout)
        menu.addAction(logout_action)
        
        # Position the menu
        toolbar = self.findChild(QToolBar)
        menu.exec(toolbar.mapToGlobal(toolbar.rect().bottomRight()))

    def openSettingsDialog(self):
        """Open the settings dialog (theme selection, etc.)."""
        try:
            dlg = SettingsDialog(self)
            dlg.exec()
        except Exception as e:
            logger.error(f"Failed to open Settings dialog: {e}", exc_info=True)

    def openDatabaseManager(self):
        """Open the database manager dialog."""
        from app.views.database_manager_dialog import DatabaseManagerDialog
        from app.models.database import set_current_database
        from PyQt6.QtWidgets import QMessageBox
        
        dialog = DatabaseManagerDialog(self)
        dialog.database_changed.connect(self.handleDatabaseChange)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Database change will be handled by the signal
            pass
    
    def handleDatabaseChange(self, new_db_path: str):
        """Handle database change event."""
        from app.models.database import set_current_database
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Database Changed",
            "Database has been changed. The application needs to restart to load the new database.\n\n"
            "Restart now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            set_current_database(new_db_path)
            # Restart application
            QMessageBox.information(
                self,
                "Restart Required",
                "Please restart the application to load the new database."
            )
            self.close()
        else:
            # User chose not to restart, but database path is already saved
            set_current_database(new_db_path)

    def showUserProfile(self):
        """Show the user profile dialog."""
        pass

    def syncData(self):
        """Sync application data."""
        self.refreshData()

    def toggleTheme(self):
        """Toggle between dark and light themes via ThemeManager."""
        try:
            from PyQt6.QtWidgets import QApplication
            from app.themes import ThemeManager
            app = QApplication.instance()
            if app:
                ThemeManager.toggle_dark_light(app)
        except Exception:
            pass

    def logout(self):
        """Logout the current user."""
        from app.auth.authentication import get_auth_manager
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            auth_manager = get_auth_manager()
            auth_manager.logout()
            logger.info("User logged out")
            
            # Close the application (or show login dialog again)
            QMessageBox.information(self, "Logged Out", "You have been logged out. Please restart the application to login again.")
            self.close() 

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
            logger.info("Added sample goals successfully!")
            
        except sqlite3.Error as e:
            logger.error(f"Error adding sample goals: {e}", exc_info=True)
            # Roll back any changes if something went wrong
            self.conn.rollback() 

    def addSampleActivities(self):
        """Add sample activities for demo purposes."""
        # Check if activities view is initialized
        if not hasattr(self, 'activities_view'):
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
        self.activities_view.addActivity(task_data)
        
        # Sample event
        event_data = {
            'type': 'event',
            'title': 'Team meeting',
            'date': QDate.currentDate(),
            'start_time': QTime(14, 0),
            'end_time': QTime(15, 30),
            'category': 'Work'
        }
        self.activities_view.addActivity(event_data)
        
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
        self.activities_view.addActivity(habit_data)
        
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
        self.activities_view.addActivity(future_task_data) 

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
            if hasattr(self, 'activities_view') and hasattr(self.activities_view, 'saveChanges'):
                logger.debug("Saving activities before exit...")
                self.activities_view.saveChanges()
            
            # Save any unsaved data in the current view
            current_widget = self.content_stack.currentWidget()
            if hasattr(current_widget, 'saveChanges'):
                logger.debug(f"Saving changes for {current_widget.__class__.__name__}")
                current_widget.saveChanges()
            
            # Loop through all views to save any pending changes
            for i in range(self.content_stack.count()):
                widget = self.content_stack.widget(i)
                if widget != current_widget and hasattr(widget, 'saveChanges'):
                    logger.debug(f"Saving changes for {widget.__class__.__name__}")
                    widget.saveChanges()
                    
            # Ensure database commits all changes
            if hasattr(self, 'conn'):
                self.conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving pending changes: {e}", exc_info=True) 

    # Sidebar interactions and shortcuts
    def toggleSidebar(self):
        try:
            current = self.sidebar.width()
            target = 0 if current > 60 else getattr(self, '_sidebar_full_width', 240)
            anim = QPropertyAnimation(self.sidebar, b"maximumWidth", self)
            anim.setDuration(180)
            anim.setStartValue(current)
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim.start()
            self._sidebar_anim = anim
        except Exception:
            # Fallback without animation
            self.sidebar.setFixedWidth(0 if self.sidebar.width() > 60 else getattr(self, '_sidebar_full_width', 240))

    def _installShortcuts(self):
        try:
            QShortcut(QKeySequence("Ctrl+K"), self, activated=self.focusSearch)
            # Navigation shortcuts Ctrl+1..7
            keys = ["Ctrl+1","Ctrl+2","Ctrl+3","Ctrl+4","Ctrl+5","Ctrl+6","Ctrl+7"]
            for idx, key in enumerate(keys):
                QShortcut(QKeySequence(key), self, activated=lambda i=idx: self.changePage(i))
            # Toggle sidebar
            QShortcut(QKeySequence("Ctrl+B"), self, activated=self.toggleSidebar)
            # Search navigation
            QShortcut(QKeySequence("Escape"), self, activated=self.hideSearchResults)
        except Exception:
            pass
    
    def focusSearch(self):
        """Focus the search field and show results if there's text."""
        self.search_field.setFocus()
        if self.search_field.text():
            self.performSearch()
    
    def onSearchTextChanged(self, text):
        """Handle search text changes with debounce."""
        if len(text.strip()) < 2:
            self.search_results_widget.hide()
            return
        
        # Debounce search (wait 300ms after user stops typing)
        self.search_timer.stop()
        self.search_timer.start(300)
    
    def performSearch(self):
        """Perform the actual search."""
        query = self.search_field.text().strip()
        
        if len(query) < 2:
            self.search_results_widget.hide()
            return
        
        # Perform search
        results = self.search_manager.search(query)
        
        # Update results widget
        self.search_results_widget.setResults(results)
        
        # Position and show results widget
        if results:
            self.positionSearchResults()
            self.search_results_widget.show()
        else:
            self.search_results_widget.hide()
    
    def positionSearchResults(self):
        """Position the search results widget below the search field."""
        search_field_rect = self.search_field.geometry()
        search_field_pos = self.search_field.mapToGlobal(QPoint(0, 0))
        
        # Position below search field
        results_x = search_field_pos.x()
        results_y = search_field_pos.y() + search_field_rect.height() + 5
        
        self.search_results_widget.move(results_x, results_y)
        self.search_results_widget.setMinimumWidth(search_field_rect.width())
    
    def onSearchEnterPressed(self):
        """Handle Enter key press in search field."""
        selected_result = self.search_results_widget.getSelectedResult()
        if selected_result:
            self.onSearchResultSelected(selected_result)
        elif self.search_results_widget.results_list.count() > 0:
            # Select first result if none selected
            self.search_results_widget.results_list.setCurrentRow(0)
            first_result = self.search_results_widget.getSelectedResult()
            if first_result:
                self.onSearchResultSelected(first_result)
    
    def onSearchFocusOut(self, event):
        """Handle search field focus out."""
        # Hide results after a short delay to allow clicking on results
        QTimer.singleShot(200, self.hideSearchResults)
    
    def hideSearchResults(self):
        """Hide the search results widget."""
        self.search_results_widget.hide()
    
    def onSearchResultSelected(self, result: SearchResult):
        """Handle search result selection."""
        self.hideSearchResults()
        self.search_field.clear()
        
        # Navigate to the appropriate view based on result type
        if result.item_type in ['task', 'event', 'habit']:
            # Switch to activities view
            self.changePage(ACTIVITIES_VIEW)
            # Scroll to or select the activity
            if hasattr(self, 'activities_view'):
                if hasattr(self.activities_view, 'selectActivityById'):
                    self.activities_view.selectActivityById(result.item_id)
                elif hasattr(self.activities_view, 'refresh'):
                    self.activities_view.refresh()
            self.show_info_toast(f"Selected {result.item_type}: {result.title}")
        
        elif result.item_type == 'goal':
            # Switch to goals view
            self.changePage(GOALS_VIEW)
            if hasattr(self, 'goals_view'):
                if hasattr(self.goals_view, 'selectGoalById'):
                    self.goals_view.selectGoalById(result.item_id)
            self.show_info_toast(f"Selected goal: {result.title}")
        
        elif result.item_type == 'category':
            # Switch to activities view and filter by category
            self.changePage(ACTIVITIES_VIEW)
            if hasattr(self, 'activities_view'):
                if hasattr(self.activities_view, 'filterByCategory'):
                    self.activities_view.filterByCategory(result.title)
            self.show_info_toast(f"Filtered by category: {result.title}")
    
    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)
        # Update toast manager geometry when window resizes
        if hasattr(self, '_toast_manager'):
            self._toast_manager.setGeometry(self.geometry())
            self._toast_manager.update_positions()
    
    def moveEvent(self, event):
        """Handle window move events."""
        super().moveEvent(event)
        # Update toast manager geometry when window moves
        if hasattr(self, '_toast_manager'):
            self._toast_manager.setGeometry(self.geometry())
            self._toast_manager.update_positions()

