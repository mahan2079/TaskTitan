import os
import json
import asyncio
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QPushButton, QToolBar, QTabWidget, QScrollArea, QStackedWidget,
    QGridLayout, QSizePolicy, QSpacerItem, QMenu, QCalendarWidget, QProgressBar
)
from PyQt6.QtCore import Qt, QSize, QDate, QTime, QTimer, pyqtSignal, QPropertyAnimation, QRect
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor, QFont
import darkdetect
import pyqtgraph as pg

from app.models.database import initialize_db
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
        super().__init__()
        self.conn, self.cursor = initialize_db()
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
        
        # Create tasks page
        self.tasks_view = TaskListView(self)
        self.content_stack.addWidget(self.tasks_view)
        
        # Create goals page
        self.goals_view = GoalWidget(self)
        self.content_stack.addWidget(self.goals_view)
        
        # Create habits page
        self.habits_view = HabitWidget(self)
        self.content_stack.addWidget(self.habits_view)
        
        # Create productivity page
        self.productivity_view = ProductivityView(self)
        self.content_stack.addWidget(self.productivity_view)
        
        # Create pomodoro page
        self.pomodoro_view = PomodoroWidget(self)
        self.content_stack.addWidget(self.pomodoro_view)
        
        # Create weekly view
        self.weekly_view = WeeklyView(self)
        self.content_stack.addWidget(self.weekly_view)
        
        # Create daily view
        self.daily_view = DailyView(self)
        self.content_stack.addWidget(self.daily_view)
        
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
            (VIEW_NAMES[TASKS_VIEW], "tasks", TASKS_VIEW),
            (VIEW_NAMES[GOALS_VIEW], "goals", GOALS_VIEW),
            (VIEW_NAMES[HABITS_VIEW], "habits", HABITS_VIEW),
            (VIEW_NAMES[PRODUCTIVITY_VIEW], "productivity", PRODUCTIVITY_VIEW),
            (VIEW_NAMES[POMODORO_VIEW], "pomodoro", POMODORO_VIEW),
            (VIEW_NAMES[WEEKLY_VIEW], "weekly", WEEKLY_VIEW),
            (VIEW_NAMES[DAILY_VIEW], "daily", DAILY_VIEW),
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
        self.dashboard = QWidget()
        dashboard_layout = QVBoxLayout(self.dashboard)
        dashboard_layout.setContentsMargins(20, 20, 20, 20)
        dashboard_layout.setSpacing(20)
        
        # Dashboard header
        header_layout = QHBoxLayout()
        welcome_label = QLabel(f"Welcome back! Today is {datetime.now().strftime('%A, %B %d')}")
        welcome_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #1E293B;")
        header_layout.addWidget(welcome_label)
        
        # Add quick action buttons in header
        quick_task_btn = QPushButton("+ Quick Task")
        quick_task_btn.setProperty("class", "accent")
        quick_task_btn.setFixedWidth(150)
        
        # Add icon from resources
        add_icon = get_icon("add")
        if not add_icon.isNull():
            quick_task_btn.setIcon(add_icon)
            quick_task_btn.setIconSize(QSize(16, 16))
        
        quick_task_btn.clicked.connect(self.addQuickTask)
        
        header_layout.addWidget(quick_task_btn)
        header_layout.addStretch()
        dashboard_layout.addLayout(header_layout)
        
        # Main dashboard content - split into 2 columns
        dashboard_content = QHBoxLayout()
        
        # Left column - Calendar and upcoming tasks
        left_column = QVBoxLayout()
        
        # Calendar widget card
        calendar_card = QFrame()
        calendar_card.setObjectName("calendar-card")
        calendar_card.setProperty("class", "card")
        calendar_layout = QVBoxLayout(calendar_card)
        
        calendar_header = QLabel("Calendar")
        calendar_header.setProperty("class", "dashboard-widget-header")
        calendar_layout.addWidget(calendar_header)
        
        self.dashboard_calendar = ModernCalendarWidget()
        self.dashboard_calendar.clicked.connect(self.openDailyView)
        calendar_layout.addWidget(self.dashboard_calendar)
        
        left_column.addWidget(calendar_card)
        
        # Upcoming tasks
        tasks_card = QFrame()
        tasks_card.setProperty("class", "card")
        tasks_layout = QVBoxLayout(tasks_card)
        
        tasks_header_layout = QHBoxLayout()
        tasks_header = QLabel("Upcoming Tasks")
        tasks_header.setProperty("class", "dashboard-widget-header")
        tasks_header_layout.addWidget(tasks_header)
        
        view_all_tasks = QPushButton("View All")
        view_all_tasks.setProperty("class", "secondary")
        view_all_tasks.setFixedWidth(100)
        view_all_tasks.clicked.connect(lambda: self.changePage(1))  # Go to Tasks page
        tasks_header_layout.addWidget(view_all_tasks)
        
        tasks_layout.addLayout(tasks_header_layout)
        
        # Placeholder for task list - will be populated in loadData()
        self.tasks_container = QVBoxLayout()
        tasks_layout.addLayout(self.tasks_container)
        
        left_column.addWidget(tasks_card)
        dashboard_content.addLayout(left_column, 1)
        
        # Right column - stats, goals, habits
        right_column = QVBoxLayout()
        
        # Stats card
        stats_card = QFrame()
        stats_card.setProperty("class", "card")
        stats_layout = QVBoxLayout(stats_card)
        
        stats_header = QLabel("Your Progress")
        stats_header.setProperty("class", "dashboard-widget-header")
        stats_layout.addWidget(stats_header)
        
        # Stats grid
        stats_grid = QGridLayout()
        
        # Task completion rate
        self.task_completion_rate = QLabel("0%")
        self.task_completion_rate.setProperty("class", "stat-item")
        stats_grid.addWidget(self.task_completion_rate, 0, 0)
        
        task_completion_label = QLabel("Task Completion")
        task_completion_label.setProperty("class", "stat-label")
        stats_grid.addWidget(task_completion_label, 1, 0)
        
        # Habit streak
        self.habit_streak = QLabel("0")
        self.habit_streak.setProperty("class", "stat-item")
        stats_grid.addWidget(self.habit_streak, 0, 1)
        
        habit_streak_label = QLabel("Day Streak")
        habit_streak_label.setProperty("class", "stat-label")
        stats_grid.addWidget(habit_streak_label, 1, 1)
        
        # Focus time
        self.focus_time = QLabel("0h")
        self.focus_time.setProperty("class", "stat-item")
        stats_grid.addWidget(self.focus_time, 0, 2)
        
        focus_time_label = QLabel("Focus Time Today")
        focus_time_label.setProperty("class", "stat-label")
        stats_grid.addWidget(focus_time_label, 1, 2)
        
        stats_layout.addLayout(stats_grid)
        
        # Weekly progress
        weekly_header = QLabel("Weekly Goal Progress")
        weekly_header.setProperty("class", "dashboard-widget-header")
        stats_layout.addWidget(weekly_header)
        
        self.weekly_progress = QProgressBar()
        self.weekly_progress.setRange(0, 100)
        self.weekly_progress.setValue(0)
        self.weekly_progress.setFormat("%v%")
        self.weekly_progress.setTextVisible(True)
        stats_layout.addWidget(self.weekly_progress)
        
        right_column.addWidget(stats_card)
        
        # Current goals widget
        goals_card = QFrame()
        goals_card.setProperty("class", "card")
        goals_layout = QVBoxLayout(goals_card)
        
        goals_header_layout = QHBoxLayout()
        goals_header = QLabel("Current Goals")
        goals_header.setProperty("class", "dashboard-widget-header")
        goals_header_layout.addWidget(goals_header)
        
        view_all_goals = QPushButton("View All")
        view_all_goals.setProperty("class", "secondary")
        view_all_goals.setFixedWidth(100)
        view_all_goals.clicked.connect(lambda: self.changePage(2))  # Go to Goals page
        goals_header_layout.addWidget(view_all_goals)
        
        goals_layout.addLayout(goals_header_layout)
        
        # Placeholder for goals list - will be populated in loadData()
        self.goals_container = QVBoxLayout()
        goals_layout.addLayout(self.goals_container)
        
        right_column.addWidget(goals_card)
        
        # Today's habits
        habits_card = QFrame()
        habits_card.setProperty("class", "card")
        habits_layout = QVBoxLayout(habits_card)
        
        habits_header_layout = QHBoxLayout()
        habits_header = QLabel("Today's Habits")
        habits_header.setProperty("class", "dashboard-widget-header")
        habits_header_layout.addWidget(habits_header)
        
        view_all_habits = QPushButton("View All")
        view_all_habits.setProperty("class", "secondary")
        view_all_habits.setFixedWidth(100)
        view_all_habits.clicked.connect(lambda: self.changePage(3))  # Go to Habits page
        habits_header_layout.addWidget(view_all_habits)
        
        habits_layout.addLayout(habits_header_layout)
        
        # Placeholder for habits list - will be populated in loadData()
        self.habits_container = QVBoxLayout()
        habits_layout.addLayout(self.habits_container)
        
        right_column.addWidget(habits_card)
        
        dashboard_content.addLayout(right_column, 1)
        dashboard_layout.addLayout(dashboard_content)
        
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
        # Update sidebar button styles
        for button in self.sidebarButtons:
            button.setProperty("selected", False)
            button.style().unpolish(button)
            button.style().polish(button)
        
        self.sidebarButtons[index].setProperty("selected", True)
        self.sidebarButtons[index].style().unpolish(self.sidebarButtons[index])
        self.sidebarButtons[index].style().polish(self.sidebarButtons[index])
        
        # Animate the transition
        self.content_stack.setCurrentIndex(index)
        self.current_page = index

    def loadData(self):
        """Load initial data for the dashboard."""
        # Load upcoming tasks
        self.loadUpcomingTasks()
        
        # Load goals
        self.loadGoals()
        
        # Load habits
        self.loadHabits()
        
        # Load statistics
        self.loadStatistics()

    def refreshData(self):
        """Refresh all data in the app."""
        # Clear existing data containers
        self.clearLayout(self.tasks_container)
        self.clearLayout(self.goals_container)
        self.clearLayout(self.habits_container)
        
        # Reload data
        self.loadData()
        
        # Also refresh the current view if not on dashboard
        if self.current_page == 1:  # Tasks page
            self.tasks_view.refresh()
        elif self.current_page == 2:  # Goals page
            self.goals_view.refresh()
        elif self.current_page == 3:  # Habits page
            self.habits_view.refresh()
        elif self.current_page == 4:  # Productivity page
            self.productivity_view.refresh()
        elif self.current_page == 6:  # Weekly view
            self.weekly_view.refresh()
        elif self.current_page == 7:  # Daily view
            self.daily_view.refresh()

    def loadUpcomingTasks(self):
        """Load upcoming tasks for the dashboard."""
        # Get today's date and upcoming week
        today = datetime.now().date()
        end_date = today + timedelta(days=7)
        
        self.cursor.execute("""
            SELECT id, title, due_date, due_time, completed 
            FROM goals 
            WHERE due_date BETWEEN ? AND ? 
            ORDER BY due_date, due_time
            LIMIT 5
        """, (today.isoformat(), end_date.isoformat()))
        
        upcoming_tasks = self.cursor.fetchall()
        
        if upcoming_tasks:
            for task in upcoming_tasks:
                task_id, title, due_date, due_time, completed = task
                
                # Create a task card
                task_frame = QFrame()
                task_frame.setProperty("class", "task-card")
                
                # Calculate days until due
                task_date = datetime.strptime(due_date, "%Y-%m-%d").date()
                days_until = (task_date - today).days
                
                if days_until < 0:
                    task_frame.setProperty("priority", "high")  # Overdue
                elif days_until == 0:
                    task_frame.setProperty("priority", "medium")  # Due today
                elif days_until <= 2:
                    task_frame.setProperty("priority", "medium")  # Soon
                else:
                    task_frame.setProperty("priority", "low")  # Future
                
                # Setup task layout
                task_layout = QVBoxLayout(task_frame)
                task_layout.setContentsMargins(10, 10, 10, 10)
                
                # Task title
                task_title = QLabel(title)
                task_title.setStyleSheet("font-weight: bold; font-size: 15px;")
                task_layout.addWidget(task_title)
                
                # Due date/time
                due_label = QLabel(f"Due: {due_date} at {due_time}")
                due_label.setStyleSheet("color: #64748B; font-size: 13px;")
                task_layout.addWidget(due_label)
                
                # Add to container
                self.tasks_container.addWidget(task_frame)
        else:
            empty_label = QLabel("No upcoming tasks!")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #64748B; padding: 20px;")
            self.tasks_container.addWidget(empty_label)
        
        # Add stretch at the end
        self.tasks_container.addStretch()

    def loadGoals(self):
        """Load current goals for the dashboard."""
        self.cursor.execute("""
            SELECT id, title, due_date, completed
            FROM goals
            WHERE completed = 0
            ORDER BY due_date
            LIMIT 3
        """)
        
        goals = self.cursor.fetchall()
        
        if goals:
            for goal in goals:
                goal_id, title, due_date, completed = goal
                
                # Create a goal card
                goal_frame = QFrame()
                goal_frame.setProperty("class", "goal-card")
                
                # Setup goal layout
                goal_layout = QVBoxLayout(goal_frame)
                goal_layout.setContentsMargins(10, 10, 10, 10)
                
                # Goal title
                goal_title = QLabel(title)
                goal_title.setStyleSheet("font-weight: bold; font-size: 15px;")
                goal_layout.addWidget(goal_title)
                
                # Due date
                due_label = QLabel(f"Target Date: {due_date}")
                due_label.setStyleSheet("color: #64748B; font-size: 13px;")
                goal_layout.addWidget(due_label)
                
                # Add to container
                self.goals_container.addWidget(goal_frame)
        else:
            empty_label = QLabel("No active goals!")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #64748B; padding: 20px;")
            self.goals_container.addWidget(empty_label)
        
        # Add stretch at the end
        self.goals_container.addStretch()

    def loadHabits(self):
        """Load today's habits for the dashboard."""
        today_weekday = datetime.now().strftime("%A")
        
        self.cursor.execute("""
            SELECT id, name, time
            FROM habits
            WHERE days_of_week LIKE ?
            ORDER BY time
        """, (f"%{today_weekday}%",))
        
        habits = self.cursor.fetchall()
        
        if habits:
            for habit in habits:
                habit_id, name, time = habit
                
                # Create a habit card
                habit_frame = QFrame()
                habit_frame.setProperty("class", "habit-card")
                
                # Setup habit layout
                habit_layout = QHBoxLayout(habit_frame)
                habit_layout.setContentsMargins(10, 10, 10, 10)
                
                # Habit info
                habit_info = QLabel(f"{name} - {time}")
                habit_info.setStyleSheet("font-weight: bold; font-size: 15px;")
                habit_layout.addWidget(habit_info)
                
                # Add to container
                self.habits_container.addWidget(habit_frame)
        else:
            empty_label = QLabel("No habits scheduled for today!")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #64748B; padding: 20px;")
            self.habits_container.addWidget(empty_label)
        
        # Add stretch at the end
        self.habits_container.addStretch()

    def loadStatistics(self):
        """Load statistics for the dashboard."""
        today = datetime.now().date().isoformat()
        
        # Task completion rate
        self.cursor.execute("""
            SELECT COUNT(*), SUM(completed)
            FROM goals
            WHERE due_date <= ?
        """, (today,))
        
        result = self.cursor.fetchone()
        if result and result[0] > 0:
            task_count = result[0]
            completed_count = result[1] or 0
            completion_rate = int((completed_count / task_count) * 100)
            self.task_completion_rate.setText(f"{completion_rate}%")
        else:
            self.task_completion_rate.setText("0%")
        
        # Habit streak
        # This is a simplified calculation - in a real app you'd have a more sophisticated streak calculation
        streak_days = 0
        current_date = datetime.now().date()
        
        while streak_days < 30:  # Limit to checking the last 30 days
            check_date = current_date - timedelta(days=streak_days)
            weekday = check_date.strftime("%A")
            
            # Get habits for this weekday
            self.cursor.execute("""
                SELECT COUNT(*)
                FROM habits
                WHERE days_of_week LIKE ?
            """, (f"%{weekday}%",))
            
            habit_count = self.cursor.fetchone()[0]
            
            if habit_count == 0:
                # No habits scheduled for this day, so continue the streak
                streak_days += 1
                continue
            
            # Check if all habits for this day were completed
            self.cursor.execute("""
                SELECT COUNT(*)
                FROM events
                WHERE date = ? AND type = 'habit' AND completed = 1
            """, (check_date.isoformat(),))
            
            completed_habit_count = self.cursor.fetchone()[0]
            
            if completed_habit_count >= habit_count:
                # All habits completed for this day
                streak_days += 1
            else:
                # Streak broken
                break
        
        self.habit_streak.setText(str(streak_days))
        
        # Focus time today
        self.cursor.execute("""
            SELECT SUM(duration_minutes)
            FROM productivity_sessions
            WHERE date = ?
        """, (today,))
        
        result = self.cursor.fetchone()
        if result and result[0]:
            focus_minutes = result[0]
            focus_hours = focus_minutes / 60.0
            self.focus_time.setText(f"{focus_hours:.1f}h")
        else:
            self.focus_time.setText("0h")
        
        # Weekly goal progress
        self.cursor.execute("""
            SELECT COUNT(*), SUM(completed)
            FROM weekly_tasks
            WHERE week_start_date = ?
        """, (self.getStartOfWeek(),))
        
        result = self.cursor.fetchone()
        if result and result[0] > 0:
            weekly_task_count = result[0]
            weekly_completed_count = result[1] or 0
            weekly_progress = int((weekly_completed_count / weekly_task_count) * 100)
            self.weekly_progress.setValue(weekly_progress)
        else:
            self.weekly_progress.setValue(0)

    def getStartOfWeek(self):
        """Get the start date of the current week (Monday)."""
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week.isoformat()

    def clearLayout(self, layout):
        """Clear all widgets from a layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    def addQuickTask(self):
        """Show dialog to add a quick task."""
        self.tasks_view.showAddTaskDialog()
        # Switch to tasks view after adding
        self.changePage(1)

    def openDailyView(self, date):
        """Open the daily view for the selected date."""
        self.daily_view.setDate(date.toPyDate())
        self.changePage(7)  # Switch to daily view

    def openSearchDialog(self):
        """Open the global search dialog."""
        # This would be implemented to search across all data
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