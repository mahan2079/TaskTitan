from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont

from app.models.task import Task
from app.models.event import Event
from app.models.habit import Habit
from app.widgets.task_widget import TaskWidget
from app.widgets.event_widget import EventWidget
from app.widgets.habit_widget import HabitWidget
from app.dialogs.task_dialog import TaskDialog
from app.dialogs.event_dialog import EventDialog
from app.dialogs.habit_dialog import HabitDialog

class ActivitiesView(QWidget):
    """A unified view for tasks, events, and habits."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setupUI()
        self.loadActivities()
        
    def setupUI(self):
        """Setup the activities view UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header with title and buttons
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        header_frame.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        # Title
        title_label = QLabel("Activities")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E293B;")
        
        # Add activity buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.add_task_btn = QPushButton("Add Task")
        self.add_task_btn.setIcon(QIcon("icons/add_task.svg"))
        self.add_task_btn.setCursor(Qt.PointingHandCursor)
        self.add_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        self.add_task_btn.clicked.connect(self.showAddTaskDialog)
        
        self.add_event_btn = QPushButton("Add Event")
        self.add_event_btn.setIcon(QIcon("icons/add_event.svg"))
        self.add_event_btn.setCursor(Qt.PointingHandCursor)
        self.add_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.add_event_btn.clicked.connect(self.showAddEventDialog)
        
        self.add_habit_btn = QPushButton("Add Habit")
        self.add_habit_btn.setIcon(QIcon("icons/add_habit.svg"))
        self.add_habit_btn.setCursor(Qt.PointingHandCursor)
        self.add_habit_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
        """)
        self.add_habit_btn.clicked.connect(self.showAddHabitDialog)
        
        buttons_layout.addWidget(self.add_task_btn)
        buttons_layout.addWidget(self.add_event_btn)
        buttons_layout.addWidget(self.add_habit_btn)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(header_frame)
        
        # Tab widget for different activity types
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #F8FAFC;
            }
            QTabBar::tab {
                background-color: #F1F5F9;
                color: #64748B;
                padding: 10px 16px;
                margin-right: 4px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #1E293B;
                font-weight: bold;
                border-top: 3px solid #3B82F6;
            }
        """)
        
        # Tasks tab
        self.tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(self.tasks_tab)
        tasks_layout.setContentsMargins(30, 20, 30, 20)
        
        # Scroll area for tasks
        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_scroll.setFrameShape(QFrame.NoFrame)
        self.tasks_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.tasks_container = QWidget()
        self.tasks_container_layout = QVBoxLayout(self.tasks_container)
        self.tasks_container_layout.setAlignment(Qt.AlignTop)
        self.tasks_container_layout.setSpacing(10)
        
        self.tasks_scroll.setWidget(self.tasks_container)
        tasks_layout.addWidget(self.tasks_scroll)
        
        # Events tab
        self.events_tab = QWidget()
        events_layout = QVBoxLayout(self.events_tab)
        events_layout.setContentsMargins(30, 20, 30, 20)
        
        # Scroll area for events
        self.events_scroll = QScrollArea()
        self.events_scroll.setWidgetResizable(True)
        self.events_scroll.setFrameShape(QFrame.NoFrame)
        self.events_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.events_container = QWidget()
        self.events_container_layout = QVBoxLayout(self.events_container)
        self.events_container_layout.setAlignment(Qt.AlignTop)
        self.events_container_layout.setSpacing(10)
        
        self.events_scroll.setWidget(self.events_container)
        events_layout.addWidget(self.events_scroll)
        
        # Habits tab
        self.habits_tab = QWidget()
        habits_layout = QVBoxLayout(self.habits_tab)
        habits_layout.setContentsMargins(30, 20, 30, 20)
        
        # Scroll area for habits
        self.habits_scroll = QScrollArea()
        self.habits_scroll.setWidgetResizable(True)
        self.habits_scroll.setFrameShape(QFrame.NoFrame)
        self.habits_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.habits_container = QWidget()
        self.habits_container_layout = QVBoxLayout(self.habits_container)
        self.habits_container_layout.setAlignment(Qt.AlignTop)
        self.habits_container_layout.setSpacing(10)
        
        self.habits_scroll.setWidget(self.habits_container)
        habits_layout.addWidget(self.habits_scroll)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.tasks_tab, "Tasks")
        self.tab_widget.addTab(self.events_tab, "Events")
        self.tab_widget.addTab(self.habits_tab, "Habits")
        
        main_layout.addWidget(self.tab_widget, 1)
    
    def loadActivities(self):
        """Load all activities from the database."""
        self.loadTasks()
        self.loadEvents()
        self.loadHabits()
    
    def loadTasks(self):
        """Load tasks from the database."""
        # Clear existing tasks
        self.clearLayout(self.tasks_container_layout)
        
        # Load tasks from database (placeholder - replace with actual DB call)
        tasks = Task.get_all_tasks()
        
        if not tasks:
            empty_label = QLabel("No tasks yet. Click 'Add Task' to create one.")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #94A3B8; font-size: 16px; padding: 40px;")
            self.tasks_container_layout.addWidget(empty_label)
            return
        
        # Add task widgets
        for task in tasks:
            task_widget = TaskWidget(task, self)
            task_widget.task_updated.connect(self.loadTasks)
            task_widget.task_deleted.connect(self.loadTasks)
            self.tasks_container_layout.addWidget(task_widget)
        
        # Add stretch to push tasks to the top
        self.tasks_container_layout.addStretch()
    
    def loadEvents(self):
        """Load events from the database."""
        # Clear existing events
        self.clearLayout(self.events_container_layout)
        
        # Load events from database (placeholder - replace with actual DB call)
        events = Event.get_all_events()
        
        if not events:
            empty_label = QLabel("No events yet. Click 'Add Event' to create one.")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #94A3B8; font-size: 16px; padding: 40px;")
            self.events_container_layout.addWidget(empty_label)
            return
        
        # Add event widgets
        for event in events:
            event_widget = EventWidget(event, self)
            event_widget.event_updated.connect(self.loadEvents)
            event_widget.event_deleted.connect(self.loadEvents)
            self.events_container_layout.addWidget(event_widget)
        
        # Add stretch to push events to the top
        self.events_container_layout.addStretch()
    
    def loadHabits(self):
        """Load habits from the database."""
        # Clear existing habits
        self.clearLayout(self.habits_container_layout)
        
        # Load habits from database (placeholder - replace with actual DB call)
        habits = Habit.get_all_habits()
        
        if not habits:
            empty_label = QLabel("No habits yet. Click 'Add Habit' to create one.")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #94A3B8; font-size: 16px; padding: 40px;")
            self.habits_container_layout.addWidget(empty_label)
            return
        
        # Add habit widgets
        for habit in habits:
            habit_widget = HabitWidget(habit, self)
            habit_widget.habit_updated.connect(self.loadHabits)
            habit_widget.habit_deleted.connect(self.loadHabits)
            self.habits_container_layout.addWidget(habit_widget)
        
        # Add stretch to push habits to the top
        self.habits_container_layout.addStretch()
    
    def clearLayout(self, layout):
        """Clear all widgets from a layout."""
        if layout is None:
            return
        
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.clearLayout(item.layout())
    
    def showAddTaskDialog(self):
        """Show dialog to add a new task."""
        dialog = TaskDialog(parent=self)
        if dialog.exec_():
            # Reload tasks after adding
            self.loadTasks()
    
    def showAddEventDialog(self):
        """Show dialog to add a new event."""
        dialog = EventDialog(parent=self)
        if dialog.exec_():
            # Reload events after adding
            self.loadEvents()
    
    def showAddHabitDialog(self):
        """Show dialog to add a new habit."""
        dialog = HabitDialog(parent=self)
        if dialog.exec_():
            # Reload habits after adding
            self.loadHabits() 