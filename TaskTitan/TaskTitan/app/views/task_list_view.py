"""
Task list view for TaskTitan.
"""
import os
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QDialog, QLineEdit, QDateEdit, QTimeEdit, QDialogButtonBox,
    QFormLayout, QMessageBox, QMenu, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QIcon
from datetime import datetime
import random

from app.models.database_manager import get_manager
from app.resources import get_icon

class TaskListView(QWidget):
    """Widget for viewing and managing tasks."""
    
    # Signals
    taskAdded = pyqtSignal(dict)
    taskUpdated = pyqtSignal(int, bool)
    taskDeleted = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Get the database manager
        self.db_manager = get_manager()
        
        # Track additions for debugging
        self.last_added_task_id = None
        
        # Set up the UI
        self.setupUI()
        
        # Load initial task data
        self.loadTasks()
    
    def setupUI(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with title and add button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 20, 20, 10)
        
        # Title
        title = QLabel("Tasks")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Add task button
        self.add_btn = QPushButton("Add Task")
        self.add_btn.setIcon(get_icon("add"))
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4338CA;
            }
        """)
        self.add_btn.clicked.connect(self.showAddTaskDialog)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Task count label
        self.task_count_label = QLabel("Loading tasks...")
        self.task_count_label.setStyleSheet("color: #6B7280; margin-left: 20px;")
        layout.addWidget(self.task_count_label)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(20, 0, 20, 10)
        
        # Filter by status
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Tasks")
        self.status_filter.addItem("Pending Tasks")
        self.status_filter.addItem("Completed Tasks")
        self.status_filter.currentIndexChanged.connect(self.applyFilters)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Task list
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("""
            QListWidget {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #E5E7EB;
            }
            QListWidget::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
        """)
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.showContextMenu)
        layout.addWidget(self.task_list)
        
        # Debug/Info section
        self.debug_label = QLabel("")
        self.debug_label.setStyleSheet("color: #9CA3AF; font-size: 10px; margin: 5px;")
        layout.addWidget(self.debug_label)
    
    def loadTasks(self):
        """Load tasks from the database."""
        self.task_list.clear()
        
        # Verify database path exists
        db_path = self.db_manager.db_path
        if not os.path.exists(db_path):
            self.debug_label.setText(f"Database not found at: {db_path}")
            self.task_count_label.setText("No tasks found (database missing)")
            return
            
        try:
            # Determine filters
            status_filter = self.status_filter.currentIndex() if hasattr(self, 'status_filter') else 0
            completed = None
            if status_filter == 1:  # Pending Tasks
                completed = False
            elif status_filter == 2:  # Completed Tasks
                completed = True
            
            # Get tasks from database manager
            tasks = self.db_manager.get_tasks(completed=completed)
            
            # Update task count
            count_txt = f"{len(tasks)} task{'s' if len(tasks) != 1 else ''}"
            if status_filter == 1:
                count_txt += " (pending)"
            elif status_filter == 2:
                count_txt += " (completed)"
            self.task_count_label.setText(count_txt)
            
            # Add tasks to the list
            for task in tasks:
                self.addTaskToList(task)
                
            # Show debug info about the database
            self.debug_label.setText(f"Database: {db_path}")
            
        except Exception as e:
            self.debug_label.setText(f"Error loading tasks: {str(e)}")
            print(f"Error loading tasks: {e}")
    
    def addTaskToList(self, task):
        """Add a task to the list widget."""
        item = QListWidgetItem()
        
        # Create a widget for the item
        widget = QWidget()
        widget.setProperty("item_id", task['id'])  # Store ID for reference
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Task description
        desc_label = QLabel(task['description'])
        desc_label.setObjectName(f"task_label_{task['id']}")
        layout.addWidget(desc_label)
        
        # Due date and time if available
        if task.get('due_date'):
            date_str = f"{task['due_date']}"
            if task.get('due_time'):
                date_str += f" {task['due_time']}"
            date_label = QLabel(date_str)
            date_label.setStyleSheet("color: #6B7280; margin-left: 10px;")
            layout.addWidget(date_label)
        
        layout.addStretch()
        
        # Completion checkbox
        completed_check = QCheckBox()
        completed_check.setChecked(bool(task['completed']))
        completed_check.stateChanged.connect(lambda state, id=task['id']: self.toggleTaskCompletion(id, state))
        layout.addWidget(completed_check)
        
        # Set up the item
        item.setSizeHint(widget.sizeHint())
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, widget)
        
        # Store the task ID
        item.setData(Qt.ItemDataRole.UserRole, task['id'])
        
        # Style based on completion status
        if task['completed']:
            desc_label.setStyleSheet("text-decoration: line-through; color: #9CA3AF;")
    
    def showAddTaskDialog(self):
        """Show dialog to add a new task."""
        # Verify database is initialized
        if not hasattr(self, 'db_manager') or not self.db_manager:
            print("Reinitializing database manager...")
            from app.models.database_manager import get_manager
            self.db_manager = get_manager()
        
        # Check if database directory exists
        db_path = self.db_manager.db_path
        if not os.path.exists(os.path.dirname(db_path)):
            print(f"Creating database directory: {os.path.dirname(db_path)}")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Task")
        dialog.setMinimumWidth(400)
        
        # Create layout
        layout = QFormLayout(dialog)
        
        # Task description
        self.task_desc_input = QLineEdit()
        self.task_desc_input.setPlaceholderText("Enter task description")
        layout.addRow("Description:", self.task_desc_input)
        
        # Due date
        self.task_date_input = QDateEdit()
        self.task_date_input.setCalendarPopup(True)
        self.task_date_input.setDate(QDate.currentDate())
        layout.addRow("Due Date:", self.task_date_input)
        
        # Due time
        self.task_time_input = QTimeEdit()
        self.task_time_input.setTime(QTime(12, 0))
        layout.addRow("Due Time:", self.task_time_input)
        
        # Priority
        self.task_priority_input = QComboBox()
        self.task_priority_input.addItems(["Low", "Medium", "High"])
        self.task_priority_input.setCurrentIndex(1)  # Default to Medium
        layout.addRow("Priority:", self.task_priority_input)
        
        # Goal selection (if available)
        self.task_goal_input = QComboBox()
        self.task_goal_input.addItem("No Goal", None)
        
        # Add goals from database
        try:
            goals = self.db_manager.get_goals()
            for goal in goals:
                self.task_goal_input.addItem(goal['title'], goal['id'])
        except Exception as e:
            print(f"Error loading goals: {e}")
        
        layout.addRow("Related Goal:", self.task_goal_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.addTask(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        # Show the dialog
        dialog.exec()
    
    def addTask(self, dialog):
        """Add a new task to the database and list."""
        description = self.task_desc_input.text().strip()
        if not description:
            QMessageBox.warning(dialog, "Error", "Task description cannot be empty")
            return
        
        due_date = self.task_date_input.date().toString("yyyy-MM-dd")
        due_time = self.task_time_input.time().toString("HH:mm")
        priority = self.task_priority_input.currentIndex()
        goal_id = self.task_goal_input.currentData()
        
        # Display feedback that we're adding the task
        self.debug_label.setText(f"Adding task: {description}...")
        
        # Create task data dictionary
        task_data = {
            'description': description,
            'due_date': due_date,
            'due_time': due_time,
            'priority': priority,
            'goal_id': goal_id,
            'completed': False
        }
        
        # Print the task data for debugging
        print(f"Adding task: {task_data}")
        
        # Save to database via direct connection as a fallback
        try:
            # First check if database directory exists
            db_path = self.db_manager.db_path
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Try to get a connection directly
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            
            # Ensure tasks table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id INTEGER,
                    description TEXT NOT NULL,
                    duration_minutes INTEGER,
                    completed INTEGER DEFAULT 0,
                    due_date DATE,
                    due_time TIME,
                    priority INTEGER DEFAULT 1
                )
            """)
            conn.commit()
            
            # Insert the task
            cursor.execute("""
                INSERT INTO tasks (
                    goal_id, description, completed, due_date, due_time, priority
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                goal_id, 
                description, 
                0,  # Not completed
                due_date,
                due_time,
                priority
            ))
            conn.commit()
            
            # Get the ID of the inserted task
            task_id = cursor.lastrowid
            task_data['id'] = task_id
            
            # Close our direct connection
            cursor.close()
            conn.close()
            
            print(f"Successfully added task with ID {task_id}")
            self.debug_label.setText(f"Successfully added task: {description} (ID: {task_id})")
            
            # Add to the list
            self.addTaskToList(task_data)
            
            # Emit signal
            self.taskAdded.emit(task_data)
            
            # Update task count
            count = self.task_list.count()
            self.task_count_label.setText(f"{count} task{'s' if count != 1 else ''}")
            
            # Close dialog
            dialog.accept()
            
            # Refresh the view to show the new task
            self.loadTasks()
            
        except Exception as e:
            error_msg = f"Failed to save task: {str(e)}"
            self.debug_label.setText(error_msg)
            QMessageBox.critical(dialog, "Error", error_msg)
            print(error_msg)
            import traceback
            traceback.print_exc()
    
    def showEditTaskDialog(self, task_id):
        """Show dialog to edit an existing task."""
        # Get the task data
        task = self.db_manager.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "Error", "Task not found")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Task")
        dialog.setMinimumWidth(400)
        
        # Create layout
        layout = QFormLayout(dialog)
        
        # Task description
        self.edit_desc_input = QLineEdit(task['description'])
        layout.addRow("Description:", self.edit_desc_input)
        
        # Due date
        self.edit_date_input = QDateEdit()
        self.edit_date_input.setCalendarPopup(True)
        if task.get('due_date'):
            self.edit_date_input.setDate(QDate.fromString(task['due_date'], "yyyy-MM-dd"))
        else:
            self.edit_date_input.setDate(QDate.currentDate())
        layout.addRow("Due Date:", self.edit_date_input)
        
        # Due time
        self.edit_time_input = QTimeEdit()
        if task.get('due_time'):
            self.edit_time_input.setTime(QTime.fromString(task['due_time'], "HH:mm"))
        else:
            self.edit_time_input.setTime(QTime(12, 0))
        layout.addRow("Due Time:", self.edit_time_input)
        
        # Priority
        self.edit_priority_input = QComboBox()
        self.edit_priority_input.addItems(["Low", "Medium", "High"])
        self.edit_priority_input.setCurrentIndex(task.get('priority', 0))
        layout.addRow("Priority:", self.edit_priority_input)
        
        # Goal selection
        self.edit_goal_input = QComboBox()
        self.edit_goal_input.addItem("No Goal", None)
        
        # Add goals from database
        try:
            goals = self.db_manager.get_goals()
            for goal in goals:
                self.edit_goal_input.addItem(goal['title'], goal['id'])
            
            # Set current goal
            if task.get('goal_id'):
                index = self.edit_goal_input.findData(task['goal_id'])
                if index >= 0:
                    self.edit_goal_input.setCurrentIndex(index)
        except Exception as e:
            print(f"Error loading goals: {e}")
        
        layout.addRow("Related Goal:", self.edit_goal_input)
        
        # Completion status
        self.edit_completed_input = QCheckBox("Mark as completed")
        self.edit_completed_input.setChecked(bool(task['completed']))
        layout.addRow("", self.edit_completed_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.updateTask(dialog, task_id))
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        dialog.exec()
    
    def updateTask(self, dialog, task_id):
        """Update an existing task."""
        description = self.edit_desc_input.text().strip()
        if not description:
            QMessageBox.warning(dialog, "Error", "Task description cannot be empty")
            return
        
        due_date = self.edit_date_input.date().toString("yyyy-MM-dd")
        due_time = self.edit_time_input.time().toString("HH:mm")
        priority = self.edit_priority_input.currentIndex()
        goal_id = self.edit_goal_input.currentData()
        completed = self.edit_completed_input.isChecked()
        
        # Create task data dictionary
        task_data = {
            'id': task_id,
            'description': description,
            'due_date': due_date,
            'due_time': due_time,
            'priority': priority,
            'goal_id': goal_id,
            'completed': completed
        }
        
        # Save to database
        try:
            self.db_manager.save_task(task_data)
            
            # Reload tasks to update the list
            self.loadTasks()
            
            # Emit signal
            self.taskUpdated.emit(task_id, completed)
            
            # Update debug info
            self.debug_label.setText(f"Updated task ID {task_id} in database")
            
            # Close dialog
            dialog.accept()
        except Exception as e:
            error_msg = f"Failed to update task: {str(e)}"
            self.debug_label.setText(error_msg)
            QMessageBox.critical(dialog, "Error", error_msg)
            print(error_msg)
    
    def toggleTaskCompletion(self, task_id, state):
        """Toggle a task's completion status."""
        completed = state == Qt.CheckState.Checked.value
        
        # Update in database
        try:
            result = self.db_manager.update_task_status(task_id, completed)
            
            # Update UI to reflect the new status
            for i in range(self.task_list.count()):
                item = self.task_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == task_id:
                    widget = self.task_list.itemWidget(item)
                    desc_label = widget.findChild(QLabel, f"task_label_{task_id}")
                    if desc_label:
                        if completed:
                            desc_label.setStyleSheet("text-decoration: line-through; color: #9CA3AF;")
                        else:
                            desc_label.setStyleSheet("")
                    break
            
            # Emit signal
            self.taskUpdated.emit(task_id, completed)
            
            # Update debug info
            self.debug_label.setText(f"Updated task ID {task_id} status to {'completed' if completed else 'pending'}")
            
            # Reload tasks if filter is active
            if self.status_filter.currentIndex() > 0:
                self.loadTasks()
                
        except Exception as e:
            error_msg = f"Error updating task status: {e}"
            self.debug_label.setText(error_msg)
            print(error_msg)
    
    def deleteTask(self, task_id):
        """Delete a task."""
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            "Are you sure you want to delete this task?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Delete from database
        try:
            result = self.db_manager.delete_task(task_id)
            
            # Reload tasks
            self.loadTasks()
            
            # Emit signal
            self.taskDeleted.emit(task_id)
            
            # Update debug info
            self.debug_label.setText(f"Deleted task ID {task_id} from database")
            
        except Exception as e:
            error_msg = f"Failed to delete task: {str(e)}"
            self.debug_label.setText(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            print(error_msg)
    
    def showContextMenu(self, position):
        """Show context menu for a task item."""
        item = self.task_list.itemAt(position)
        if not item:
            return
        
        task_id = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        edit_action = menu.addAction("Edit Task")
        edit_action.triggered.connect(lambda: self.showEditTaskDialog(task_id))
        
        delete_action = menu.addAction("Delete Task")
        delete_action.triggered.connect(lambda: self.deleteTask(task_id))
        
        menu.exec(self.task_list.viewport().mapToGlobal(position))
    
    def applyFilters(self):
        """Apply current filters and reload tasks."""
        self.loadTasks()
    
    def refresh(self):
        """Refresh the task list view."""
        self.loadTasks()
        
    def saveChanges(self):
        """Save any pending changes before closing."""
        # No special action needed, all changes are saved immediately
        print("TaskListView: All changes already saved")
        
    def debugPrintDatabase(self):
        """Print database information for debugging."""
        try:
            db_path = self.db_manager.db_path
            if os.path.exists(db_path):
                file_size = os.path.getsize(db_path)
                print(f"Database exists at: {db_path} (Size: {file_size} bytes)")
                
                # Check if we can open it
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check task count
                cursor.execute("SELECT COUNT(*) FROM tasks")
                task_count = cursor.fetchone()[0]
                print(f"Task count in database: {task_count}")
                
                # List some tasks
                cursor.execute("SELECT id, description FROM tasks LIMIT 5")
                tasks = cursor.fetchall()
                for task in tasks:
                    print(f"  Task ID {task[0]}: {task[1]}")
                    
                conn.close()
            else:
                print(f"Database does NOT exist at: {db_path}")
        except Exception as e:
            print(f"Error debugging database: {e}") 