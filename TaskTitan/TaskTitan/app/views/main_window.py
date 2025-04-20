import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QPushButton, QToolBar, QTabWidget, QScrollArea, QStackedWidget,
    QGridLayout, QSizePolicy, QSpacerItem, QMenu, QCalendarWidget, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QDate, QTime, QTimer, pyqtSignal, QPropertyAnimation, QRect
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor, QFont
import darkdetect
import pyqtgraph as pg
import sqlite3

# Set up correct imports based on how the module is being used
if __name__ == "__main__" or not __package__:
    # Add the parent directory to the path for direct execution
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, parent_dir)
    
    # Direct imports
    from app.models.database import initialize_db
    from app.models.database_manager import get_manager, close_connection
    from app.views.calendar_widget import ModernCalendarWidget
    from app.views.task_widget import TaskWidget
    from app.views.goal_widget import GoalWidget
    from app.views.habit_widget import HabitWidget
    from app.views.productivity_view import ProductivityView
    from app.views.pomodoro_widget import PomodoroWidget
    from app.views.weekly_view import WeeklyView
    from app.views.daily_view import DailyView
    from app.views.settings_dialog import SettingsDialog
    from app.views.task_list_view import TaskListView
    from app.resources import get_icon, get_pixmap, VIEW_NAMES, DASHBOARD_VIEW, TASKS_VIEW, GOALS_VIEW, HABITS_VIEW, PRODUCTIVITY_VIEW, POMODORO_VIEW, WEEKLY_VIEW, DAILY_VIEW, SETTINGS_VIEW
else:
    # Normal imports when imported as a module
    from app.models.database import initialize_db
    from app.models.database_manager import get_manager, close_connection
    from app.views.calendar_widget import ModernCalendarWidget
    from app.views.task_widget import TaskWidget
    from app.views.goal_widget import GoalWidget
    from app.views.habit_widget import HabitWidget
    from app.views.productivity_view import ProductivityView
    from app.views.pomodoro_widget import PomodoroWidget
    from app.views.weekly_view import WeeklyView
    from app.views.daily_view import DailyView
    from app.views.settings_dialog import SettingsDialog
    from app.views.task_list_view import TaskListView
    from app.resources import get_icon, get_pixmap, VIEW_NAMES, DASHBOARD_VIEW, TASKS_VIEW, GOALS_VIEW, HABITS_VIEW, PRODUCTIVITY_VIEW, POMODORO_VIEW, WEEKLY_VIEW, DAILY_VIEW, SETTINGS_VIEW

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
        self.setMinimumSize(1000, 700)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Setup the UI components
        self.setupSidebar()
        self.setupUI()
        
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
            # Save any unsaved data in the current view
            current_widget = self.stacked_widget.currentWidget()
            if hasattr(current_widget, 'saveChanges'):
                print(f"Saving changes for {current_widget.__class__.__name__}")
                current_widget.saveChanges()
            
            # Loop through all views to save any pending changes
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if widget != current_widget and hasattr(widget, 'saveChanges'):
                    print(f"Saving changes for {widget.__class__.__name__}")
                    widget.saveChanges()
        except Exception as e:
            print(f"Error saving pending changes: {e}")

    def setupUI(self):
        """Set up the main UI components."""
        # Create the content widget that will contain the stacked views
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)
        
        # Add content widget to main layout
        self.main_layout.addWidget(self.content_widget)
        
        # Create a toolbar for common actions
        self.setupToolbar()
        
        # Create a stacked widget to hold different views
        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget)
        
        # Create and add views to the stacked widget
        self.dashboard_view = QWidget()  # Placeholder for dashboard
        self.setupDashboard()
        self.stacked_widget.addWidget(self.dashboard_view)
        
        self.tasks_view = TaskListView(self)
        self.stacked_widget.addWidget(self.tasks_view)
        
        self.goals_view = GoalWidget(self)
        self.stacked_widget.addWidget(self.goals_view)
        
        self.habits_view = HabitWidget(self)
        self.stacked_widget.addWidget(self.habits_view)
        
        self.productivity_view = ProductivityView(self)
        self.stacked_widget.addWidget(self.productivity_view)
        
        self.pomodoro_view = PomodoroWidget(self)
        self.stacked_widget.addWidget(self.pomodoro_view)
        
        self.weekly_view = WeeklyView(self)
        self.stacked_widget.addWidget(self.weekly_view)
        
        self.daily_view = DailyView(self)
        self.stacked_widget.addWidget(self.daily_view)
        
        # Set initial view
        self.stacked_widget.setCurrentIndex(DASHBOARD_VIEW)

    # Add stubs for other required methods
    def setupSidebar(self):
        """Create sidebar for navigation."""
        # Create sidebar container
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet("""
            #sidebar {
                background-color: #1E293B;
                min-width: 200px;
                max-width: 200px;
            }
            
            QPushButton {
                background-color: transparent;
                color: #CBD5E1;
                text-align: left;
                padding: 12px 15px;
                border: none;
                font-size: 14px;
                border-radius: 0px;
            }
            
            QPushButton:hover {
                background-color: #334155;
            }
            
            QPushButton:checked {
                background-color: #334155;
                border-left: 4px solid #6366F1;
                color: white;
                font-weight: bold;
            }
        """)
        
        # Create sidebar layout
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 20, 0, 20)
        self.sidebar_layout.setSpacing(0)
        
        # App title
        self.app_title = QLabel("TaskTitan")
        self.app_title.setStyleSheet("""
            color: white; 
            font-size: 18px; 
            font-weight: bold;
            padding: 10px 15px;
            margin-bottom: 20px;
        """)
        self.sidebar_layout.addWidget(self.app_title)
        
        # Navigation buttons
        self.sidebarButtons = []
        
        # Dashboard button
        self.dashboard_btn = QPushButton("Dashboard")
        self.dashboard_btn.setIcon(get_icon("dashboard"))
        self.dashboard_btn.setIconSize(QSize(20, 20))
        self.dashboard_btn.setCheckable(True)
        self.dashboard_btn.setChecked(True)
        self.dashboard_btn.clicked.connect(lambda: self.changePage(DASHBOARD_VIEW))
        self.sidebar_layout.addWidget(self.dashboard_btn)
        self.sidebarButtons.append(self.dashboard_btn)
        
        # Tasks button
        self.tasks_btn = QPushButton("Tasks")
        self.tasks_btn.setIcon(get_icon("task"))
        self.tasks_btn.setIconSize(QSize(20, 20))
        self.tasks_btn.setCheckable(True)
        self.tasks_btn.clicked.connect(lambda: self.changePage(TASKS_VIEW))
        self.sidebar_layout.addWidget(self.tasks_btn)
        self.sidebarButtons.append(self.tasks_btn)
        
        # Goals button
        self.goals_btn = QPushButton("Goals")
        self.goals_btn.setIcon(get_icon("goal"))
        self.goals_btn.setIconSize(QSize(20, 20))
        self.goals_btn.setCheckable(True)
        self.goals_btn.clicked.connect(lambda: self.changePage(GOALS_VIEW))
        self.sidebar_layout.addWidget(self.goals_btn)
        self.sidebarButtons.append(self.goals_btn)
        
        # Habits button
        self.habits_btn = QPushButton("Habits")
        self.habits_btn.setIcon(get_icon("habit"))
        self.habits_btn.setIconSize(QSize(20, 20))
        self.habits_btn.setCheckable(True)
        self.habits_btn.clicked.connect(lambda: self.changePage(HABITS_VIEW))
        self.sidebar_layout.addWidget(self.habits_btn)
        self.sidebarButtons.append(self.habits_btn)
        
        # Productivity button
        self.productivity_btn = QPushButton("Productivity")
        self.productivity_btn.setIcon(get_icon("productivity"))
        self.productivity_btn.setIconSize(QSize(20, 20))
        self.productivity_btn.setCheckable(True)
        self.productivity_btn.clicked.connect(lambda: self.changePage(PRODUCTIVITY_VIEW))
        self.sidebar_layout.addWidget(self.productivity_btn)
        self.sidebarButtons.append(self.productivity_btn)
        
        # Pomodoro button
        self.pomodoro_btn = QPushButton("Pomodoro")
        self.pomodoro_btn.setIcon(get_icon("pomodoro"))
        self.pomodoro_btn.setIconSize(QSize(20, 20))
        self.pomodoro_btn.setCheckable(True)
        self.pomodoro_btn.clicked.connect(lambda: self.changePage(POMODORO_VIEW))
        self.sidebar_layout.addWidget(self.pomodoro_btn)
        self.sidebarButtons.append(self.pomodoro_btn)
        
        # Weekly View button
        self.weekly_btn = QPushButton("Weekly View")
        self.weekly_btn.setIcon(get_icon("calendar"))
        self.weekly_btn.setIconSize(QSize(20, 20))
        self.weekly_btn.setCheckable(True)
        self.weekly_btn.clicked.connect(lambda: self.changePage(WEEKLY_VIEW))
        self.sidebar_layout.addWidget(self.weekly_btn)
        self.sidebarButtons.append(self.weekly_btn)
        
        # Daily View button
        self.daily_btn = QPushButton("Daily View")
        self.daily_btn.setIcon(get_icon("calendar-day"))
        self.daily_btn.setIconSize(QSize(20, 20))
        self.daily_btn.setCheckable(True)
        self.daily_btn.clicked.connect(lambda: self.changePage(DAILY_VIEW))
        self.sidebar_layout.addWidget(self.daily_btn)
        self.sidebarButtons.append(self.daily_btn)
        
        # Add spacer to push the settings button to the bottom
        self.sidebar_layout.addStretch()
        
        # Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setIcon(get_icon("settings"))
        self.settings_btn.setIconSize(QSize(20, 20))
        self.settings_btn.clicked.connect(self.openSettings)
        self.sidebar_layout.addWidget(self.settings_btn)
        
        # Add sidebar to main layout
        self.main_layout.addWidget(self.sidebar)
    
    def setupDashboard(self):
        """Set up the dashboard view."""
        dashboard_layout = QVBoxLayout(self.dashboard_view)
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
        
        # Tasks stats
        tasks_label = QLabel("Tasks")
        tasks_label.setStyleSheet("font-weight: bold;")
        stats_grid.addWidget(tasks_label, 0, 0)
        
        self.tasks_counter = QLabel("0/0")
        stats_grid.addWidget(self.tasks_counter, 0, 1)
        
        # Goals stats
        goals_label = QLabel("Goals")
        goals_label.setStyleSheet("font-weight: bold;")
        stats_grid.addWidget(goals_label, 1, 0)
        
        self.goals_counter = QLabel("0/0")
        stats_grid.addWidget(self.goals_counter, 1, 1)
        
        # Habits stats
        habits_label = QLabel("Habits")
        habits_label.setStyleSheet("font-weight: bold;")
        stats_grid.addWidget(habits_label, 2, 0)
        
        self.habits_counter = QLabel("0/0")
        stats_grid.addWidget(self.habits_counter, 2, 1)
        
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
        
        daily_btn = QPushButton("Daily View")
        daily_btn.setIcon(get_icon("calendar-day"))
        daily_btn.clicked.connect(lambda: self.changePage(DAILY_VIEW))
        buttons_layout.addWidget(daily_btn)
        
        weekly_btn = QPushButton("Weekly View")
        weekly_btn.setIcon(get_icon("calendar"))
        weekly_btn.clicked.connect(lambda: self.changePage(WEEKLY_VIEW))
        buttons_layout.addWidget(weekly_btn)
        
        pomodoro_btn = QPushButton("Pomodoro")
        pomodoro_btn.setIcon(get_icon("pomodoro"))
        pomodoro_btn.clicked.connect(lambda: self.changePage(POMODORO_VIEW))
        buttons_layout.addWidget(pomodoro_btn)
        
        quick_access_layout.addLayout(buttons_layout)
        dashboard_layout.addWidget(quick_access_frame)
        
        # Add stretch to push everything to the top
        dashboard_layout.addStretch()
        
    def setupToolbar(self):
        """Set up the application toolbar."""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #F8FAFC;
                border-bottom: 1px solid #E2E8F0;
                spacing: 10px;
                padding: 5px 10px;
            }
            
            QToolButton {
                border-radius: 6px;
                padding: 5px;
            }
            
            QToolButton:hover {
                background-color: #E2E8F0;
            }
        """)
        
        # Add actions
        add_task_action = QAction(get_icon("add"), "Add Task", self)
        add_task_action.triggered.connect(self.addTask)
        self.toolbar.addAction(add_task_action)
        
        add_event_action = QAction(get_icon("event"), "Add Event", self)
        add_event_action.triggered.connect(self.addEvent)
        self.toolbar.addAction(add_event_action)
        
        self.toolbar.addSeparator()
        
        refresh_action = QAction(get_icon("refresh"), "Refresh", self)
        refresh_action.triggered.connect(self.refreshData)
        self.toolbar.addAction(refresh_action)
        
        # Add a diagnostics button (will be hidden in production)
        self.toolbar.addSeparator()
        diagnose_action = QAction(get_icon("settings"), "Database Diagnostics", self)
        diagnose_action.triggered.connect(self.runDatabaseDiagnostics)
        self.toolbar.addAction(diagnose_action)
        
        # Add the toolbar to the content layout
        self.content_layout.insertWidget(0, self.toolbar)
        
    def changePage(self, index):
        """Change the current page in the stacked widget.
        
        Args:
            index (int): The index of the page to show
        """
        # Update the checked state of sidebar buttons
        for i, button in enumerate(self.sidebarButtons):
            button.setChecked(i == index)
        
        # Change the page
        self.stacked_widget.setCurrentIndex(index)
        
    def loadData(self):
        """Load initial data for the application."""
        # This would load data from the database for all views
        # For now, just update the dashboard counters
        self.refreshData()
        
    def refreshData(self):
        """Refresh data periodically."""
        try:
            # Use the database manager to get counts
            total_tasks = self.db_manager.count_items('tasks')
            completed_tasks = self.db_manager.count_items('tasks', completed=True)
            self.tasks_counter.setText(f"{completed_tasks}/{total_tasks}")
            
            total_goals = self.db_manager.count_items('goals')
            completed_goals = self.db_manager.count_items('goals', completed=True)
            self.goals_counter.setText(f"{completed_goals}/{total_goals}")
            
            # Count habits for today
            today = datetime.now().strftime("%Y-%m-%d")
            completed_habits, total_habits = self.db_manager.count_habits_completion(today)
            self.habits_counter.setText(f"{completed_habits}/{total_habits}")
            
            # Refresh all views
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if hasattr(widget, 'refresh'):
                    widget.refresh()
                    
        except Exception as e:
            print(f"Error refreshing data: {e}")
    
    def addTask(self):
        """Open dialog to add a new task."""
        try:
            # Check if we are already on the tasks view
            if self.stacked_widget.currentIndex() != TASKS_VIEW:
                # Change to the tasks view first
                self.changePage(TASKS_VIEW)
            
            # Call the show add task dialog method on the task view
            if hasattr(self.tasks_view, 'showAddTaskDialog'):
                self.tasks_view.showAddTaskDialog()
            else:
                print("Error: tasks_view does not have showAddTaskDialog method")
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