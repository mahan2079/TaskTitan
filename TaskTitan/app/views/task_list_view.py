from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, 
                              QLabel, QHBoxLayout, QPushButton, QFrame, QDialog, QLineEdit, QDateEdit, QComboBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont
from datetime import datetime

from app.views.task_widget import TaskWidget
from app.resources import get_icon

class TaskListView(QWidget):
    """A modern list view for displaying tasks with filtering and sorting."""
    
    # Signals
    taskAdded = pyqtSignal()
    taskCompleted = pyqtSignal(int, bool)
    taskDeleted = pyqtSignal(int)
    taskEdited = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure widget
        self.setObjectName("taskListView")
        
        # Tasks data
        self.tasks = []
        self.task_widgets = {}
        
        # Set up the UI
        self.setupUI()
    
    def setupUI(self):
        """Set up the UI components of the task list view."""
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header section
        self.setupHeader()
        
        # Tasks container
        self.setupTasksContainer()
        
        # Empty state
        self.setupEmptyState()
        
        # Show empty state if no tasks
        self.updateEmptyState()
    
    def setupHeader(self):
        """Set up the header section with title and actions."""
        
        # Header container
        self.header = QWidget()
        self.header.setObjectName("taskListHeader")
        self.header.setMinimumHeight(60)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Header title
        self.header_title = QLabel("My Tasks")
        self.header_title.setObjectName("taskListHeaderTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.header_title.setFont(font)
        header_layout.addWidget(self.header_title)
        
        # Add task button
        self.add_btn = QPushButton("Add Task")
        self.add_btn.setObjectName("addTaskButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setMinimumWidth(100)
        self.add_btn.clicked.connect(self.taskAdded.emit)
        
        # Add icon to button
        add_icon = get_icon("add")
        if not add_icon.isNull():
            self.add_btn.setIcon(add_icon)
        
        header_layout.addWidget(self.add_btn)
        
        # Add header to main layout
        self.main_layout.addWidget(self.header)
        
        # Add separator line
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.separator.setObjectName("headerSeparator")
        self.separator.setFixedHeight(1)
        self.main_layout.addWidget(self.separator)
        
        # Apply styles
        self.header.setStyleSheet("""
            #taskListHeader {
                background-color: #FFFFFF;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            #taskListHeaderTitle {
                color: #111827;
            }
            #addTaskButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            #addTaskButton:hover {
                background-color: #4338CA;
            }
            #addTaskButton:pressed {
                background-color: #3730A3;
            }
            #headerSeparator {
                background-color: #E5E7EB;
            }
        """)
    
    def setupTasksContainer(self):
        """Set up the scrollable container for task widgets."""
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("taskScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container widget
        self.tasks_container = QWidget()
        self.tasks_container.setObjectName("tasksContainer")
        
        # Layout for tasks
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(20, 15, 20, 15)
        self.tasks_layout.setSpacing(12)
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Set container as scroll area widget
        self.scroll_area.setWidget(self.tasks_container)
        
        # Add to main layout
        self.main_layout.addWidget(self.scroll_area)
        
        # Apply styles
        self.scroll_area.setStyleSheet("""
            #taskScrollArea {
                background-color: #F9FAFB;
            }
            #tasksContainer {
                background-color: #F9FAFB;
            }
            QScrollBar:vertical {
                border: none;
                background: #F9FAFB;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #D1D5DB;
                min-height: 30px;
                border-radius: 4px;
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
    
    def setupEmptyState(self):
        """Set up the empty state widget when no tasks are available."""
        
        # Empty state widget
        self.empty_state = QWidget()
        self.empty_state.setObjectName("emptyState")
        self.empty_state.setVisible(False)
        
        # Layout for empty state
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(0, 30, 0, 0)
        empty_layout.setSpacing(15)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        
        # Empty state message
        empty_message = QLabel("No tasks yet")
        empty_message.setObjectName("emptyStateMessage")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        empty_message.setFont(font)
        
        # Empty state description
        empty_description = QLabel("Click 'Add Task' to create your first task")
        empty_description.setObjectName("emptyStateDescription")
        
        empty_layout.addWidget(empty_message)
        empty_layout.addWidget(empty_description)
        
        # Add to tasks container layout
        self.tasks_layout.addWidget(self.empty_state)
        
        # Apply styles
        self.empty_state.setStyleSheet("""
            #emptyState {
                background-color: transparent;
            }
            #emptyStateMessage {
                color: #111827;
            }
            #emptyStateDescription {
                color: #6B7280;
                font-size: 12px;
            }
        """)
    
    def updateEmptyState(self):
        """Update the visibility of the empty state based on tasks count."""
        if not self.tasks:
            self.empty_state.setVisible(True)
        else:
            self.empty_state.setVisible(False)
    
    def addTask(self, task_id, title, due_date=None, priority=0, category=None, completed=False):
        """Add a task to the list view."""
        
        # Create the task widget
        task_widget = TaskWidget(
            task_id=task_id,
            title=title,
            due_date=due_date,
            priority=priority,
            category=category,
            completed=completed
        )
        
        # Connect signals
        task_widget.taskCompleted.connect(self.taskCompleted.emit)
        task_widget.taskDeleted.connect(self.taskDeleted.emit)
        task_widget.taskEdited.connect(self.taskEdited.emit)
        
        # Add to container and store in dict
        self.tasks_layout.insertWidget(0, task_widget)  # Add to the top
        self.task_widgets[task_id] = task_widget
        
        # Add to tasks list
        self.tasks.append({
            'id': task_id,
            'title': title,
            'due_date': due_date,
            'priority': priority,
            'category': category,
            'completed': completed
        })
        
        # Hide empty state
        self.updateEmptyState()
        
        # Animate the new task
        self.animateNewTask(task_widget)
    
    def removeTask(self, task_id):
        """Remove a task from the list view."""
        if task_id in self.task_widgets:
            # Remove widget
            task_widget = self.task_widgets[task_id]
            self.tasks_layout.removeWidget(task_widget)
            task_widget.deleteLater()
            
            # Remove from dict
            del self.task_widgets[task_id]
            
            # Remove from list
            self.tasks = [task for task in self.tasks if task['id'] != task_id]
            
            # Update empty state
            self.updateEmptyState()
    
    def updateTask(self, task_id, title=None, due_date=None, priority=None, category=None, completed=None):
        """Update a task in the list view."""
        if task_id in self.task_widgets:
            task_widget = self.task_widgets[task_id]
            
            # Update task data
            if title is not None:
                task_widget.title = title
                task_widget.title_label.setText(title)
            
            if completed is not None:
                task_widget.completed = completed
                task_widget.checkbox.setChecked(completed)
                task_widget.updateStyle()
            
            # Find the task in the list and update it
            for task in self.tasks:
                if task['id'] == task_id:
                    if title is not None:
                        task['title'] = title
                    if due_date is not None:
                        task['due_date'] = due_date
                    if priority is not None:
                        task['priority'] = priority
                    if category is not None:
                        task['category'] = category
                    if completed is not None:
                        task['completed'] = completed
                    break
    
    def clearTasks(self):
        """Clear all tasks from the list view."""
        for task_id in list(self.task_widgets.keys()):
            self.removeTask(task_id)
    
    def animateNewTask(self, task_widget):
        """Animate a new task being added."""
        # Save the original opacity
        task_widget.setMaximumHeight(0)
        
        # Create animation for height
        height_anim = QPropertyAnimation(task_widget, b"maximumHeight")
        height_anim.setDuration(300)
        height_anim.setStartValue(0)
        height_anim.setEndValue(task_widget.sizeHint().height())
        height_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        height_anim.start()
    
    def getTasks(self):
        """Get the list of all tasks."""
        return self.tasks.copy()
        
    def showAddTaskDialog(self):
        """Show dialog to add a new task."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Task")
        layout = QVBoxLayout(dialog)
        
        # Title field
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_layout.addWidget(title_label)
        title_input = QLineEdit()
        title_layout.addWidget(title_input)
        layout.addLayout(title_layout)
        
        # Due date field
        date_layout = QHBoxLayout()
        date_label = QLabel("Due Date:")
        date_layout.addWidget(date_label)
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(datetime.now())
        date_layout.addWidget(date_input)
        layout.addLayout(date_layout)
        
        # Priority field
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Priority:")
        priority_layout.addWidget(priority_label)
        priority_input = QComboBox()
        priority_input.addItems(["Low", "Medium", "High"])
        priority_layout.addWidget(priority_input)
        layout.addLayout(priority_layout)
        
        # Category field
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_layout.addWidget(category_label)
        category_input = QLineEdit()
        category_layout.addWidget(category_input)
        layout.addLayout(category_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.addTaskFromDialog(dialog, title_input.text(), date_input.date(), priority_input.currentIndex(), category_input.text()))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setMinimumWidth(300)
        dialog.exec()
        
    def addTaskFromDialog(self, dialog, title, due_date, priority, category):
        """Add a task from the dialog data."""
        if not title:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(dialog, "Error", "Title cannot be empty")
            return
        
        # In a real app, you'd save to database and get a real ID
        import random
        task_id = random.randint(1000, 9999)
        
        date_str = due_date.toString("yyyy-MM-dd")
        
        self.addTask(task_id, title, date_str, priority, category if category else None)
        dialog.accept()
    
    def refresh(self):
        """Refresh tasks from data source."""
        # In a real app, you'd reload from database
        pass 