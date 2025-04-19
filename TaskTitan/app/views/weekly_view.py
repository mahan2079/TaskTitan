"""
Weekly planning view for TaskTitan.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QGridLayout, QFrame, QScrollArea,
                           QSizePolicy, QMenu, QDialog, QLineEdit, QTimeEdit,
                           QDateEdit, QComboBox, QCheckBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, QDate, QTime, QSize, pyqtSignal
from PyQt6.QtGui import QIcon
from datetime import datetime, timedelta
import sqlite3
from app.resources import get_icon

class TaskBlock(QFrame):
    """A block representing a task in the weekly view."""
    
    def __init__(self, task_id, title, category, start_time, end_time, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.title = title
        self.category = category
        self.start_time = start_time
        self.end_time = end_time
        
        self.setStyleSheet("""
            QFrame {
                background-color: #818CF8;
                border-radius: 6px;
                color: white;
                padding: 8px;
            }
        """)
        
        if category == "Work":
            self.setStyleSheet("""
                QFrame {
                    background-color: #60A5FA;
                    border-radius: 6px;
                    color: white;
                    padding: 8px;
                }
            """)
        elif category == "Personal":
            self.setStyleSheet("""
                QFrame {
                    background-color: #F472B6;
                    border-radius: 6px;
                    color: white;
                    padding: 8px;
                }
            """)
        elif category == "Health":
            self.setStyleSheet("""
                QFrame {
                    background-color: #34D399;
                    border-radius: 6px;
                    color: white;
                    padding: 8px;
                }
            """)
        
        self.setMinimumHeight(50)
        self.setMaximumHeight(100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        layout.addWidget(title_label)
        
        time_label = QLabel(f"{start_time} - {end_time}")
        time_label.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.9);")
        layout.addWidget(time_label)
        
        category_label = QLabel(category)
        category_label.setStyleSheet("font-size: 11px; color: rgba(255, 255, 255, 0.8);")
        layout.addWidget(category_label)
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
    
    def showContextMenu(self, position):
        menu = QMenu(self)
        
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(self.editTask)
        
        complete_action = menu.addAction("Mark Complete")
        complete_action.triggered.connect(self.completeTask)
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.deleteTask)
        
        menu.exec(self.mapToGlobal(position))
    
    def editTask(self):
        self.parent().parent().parent().editWeeklyTask(self.task_id)
    
    def completeTask(self):
        self.parent().parent().parent().completeWeeklyTask(self.task_id)
    
    def deleteTask(self):
        self.parent().parent().parent().deleteWeeklyTask(self.task_id)

class WeeklyView(QWidget):
    """Widget for weekly planning."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            # First try to use the parent's database connection if available
            if parent and hasattr(parent, 'conn') and parent.conn:
                self.conn = parent.conn
                self.cursor = parent.cursor
            else:
                # Otherwise create our own connection
                self.conn = sqlite3.connect('tasktitan.db')
                self.cursor = self.conn.cursor()
            
            # Ensure the required table exists
            self.ensure_weekly_tasks_table()
            
            self.week_start_date = self.getStartOfWeek()
            self.setupUI()
        except Exception as e:
            print(f"Error initializing WeeklyView: {e}")
            # Create a minimal UI to avoid crashing
            layout = QVBoxLayout(self)
            error_label = QLabel(f"Error loading weekly view: {e}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)
            
            # Set empty week_start_date to avoid further errors
            self.week_start_date = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
    
    def ensure_weekly_tasks_table(self):
        """Ensure the weekly_tasks table exists."""
        try:
            # Create table with all required columns
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS weekly_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT DEFAULT '',
                    date DATE DEFAULT CURRENT_DATE,
                    start_time TIME DEFAULT '09:00',
                    end_time TIME DEFAULT '10:00',
                    category TEXT DEFAULT 'Other',
                    completed INTEGER DEFAULT 0,
                    parent_id INTEGER,
                    description TEXT,
                    due_date DATE,
                    due_time TIME,
                    week_start_date DATE DEFAULT CURRENT_DATE
                )
            """)
            self.conn.commit()
            
            # Verify if week_start_date column exists, add it if not
            try:
                self.cursor.execute("SELECT week_start_date FROM weekly_tasks LIMIT 1")
            except sqlite3.OperationalError:
                print("Adding week_start_date column to weekly_tasks table")
                self.cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN week_start_date DATE DEFAULT CURRENT_DATE")
                self.conn.commit()
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            # Create a fallback in-memory representation
            self.weekly_tasks = []
        
    def setupUI(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header with week navigation
        header_layout = QHBoxLayout()
        
        # Previous week button
        prev_week_btn = QPushButton()
        prev_week_btn.setIcon(get_icon("arrow-left"))
        prev_week_btn.setIconSize(QSize(20, 20))
        prev_week_btn.setFixedSize(40, 40)
        prev_week_btn.clicked.connect(self.previousWeek)
        header_layout.addWidget(prev_week_btn)
        
        # Week label
        self.week_label = QLabel()
        self.week_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.updateWeekLabel()
        header_layout.addWidget(self.week_label, 1)
        
        # Next week button
        next_week_btn = QPushButton()
        next_week_btn.setIcon(get_icon("arrow-right"))
        next_week_btn.setIconSize(QSize(20, 20))
        next_week_btn.setFixedSize(40, 40)
        next_week_btn.clicked.connect(self.nextWeek)
        header_layout.addWidget(next_week_btn)
        
        # Add task button
        add_task_btn = QPushButton("Add Task")
        add_task_btn.setIcon(get_icon("add"))
        add_task_btn.setIconSize(QSize(16, 16))
        add_task_btn.clicked.connect(self.showAddTaskDialog)
        header_layout.addWidget(add_task_btn)
        
        layout.addLayout(header_layout)
        
        # Weekly calendar
        self.weekly_grid = QGridLayout()
        self.weekly_grid.setSpacing(10)
        
        # Time labels column
        for hour in range(7, 23):  # 7 AM to 10 PM
            time_label = QLabel(f"{hour:02d}:00")
            time_label.setStyleSheet("font-size: 12px; color: #64748B;")
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.weekly_grid.addWidget(time_label, hour - 6, 0)
        
        # Day headers
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day in enumerate(days):
            day_label = QLabel(day)
            day_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
            day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.weekly_grid.addWidget(day_label, 0, i + 1)
            
            # Add date below day name
            date = self.week_start_date + timedelta(days=i)
            date_label = QLabel(date.strftime("%b %d"))
            date_label.setStyleSheet("font-size: 12px; color: #64748B;")
            date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.weekly_grid.addWidget(date_label, 1, i + 1)
            
            # Create day columns (cells for each hour)
            for hour in range(7, 23):  # 7 AM to 10 PM
                cell = QFrame()
                cell.setStyleSheet("""
                    QFrame {
                        background-color: #F1F5F9;
                        border-radius: 4px;
                    }
                """)
                self.weekly_grid.addWidget(cell, hour - 6, i + 1)
        
        # Set column stretch
        self.weekly_grid.setColumnStretch(0, 1)  # Time column is smaller
        for i in range(1, 8):
            self.weekly_grid.setColumnStretch(i, 4)  # Day columns are wider
        
        # Create a scroll area for the weekly grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setLayout(self.weekly_grid)
        scroll_area.setWidget(scroll_content)
        
        layout.addWidget(scroll_area)
        
        # Load tasks
        self.loadWeeklyTasks()
    
    def getStartOfWeek(self):
        """Get the Monday of the current week."""
        today = datetime.now().date()
        return today - timedelta(days=today.weekday())
    
    def updateWeekLabel(self):
        """Update the week label based on the current week start date."""
        week_end = self.week_start_date + timedelta(days=6)
        self.week_label.setText(f"Week of {self.week_start_date.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    def previousWeek(self):
        """Go to the previous week."""
        self.week_start_date -= timedelta(days=7)
        self.updateWeekLabel()
        self.loadWeeklyTasks()
    
    def nextWeek(self):
        """Go to the next week."""
        self.week_start_date += timedelta(days=7)
        self.updateWeekLabel()
        self.loadWeeklyTasks()
    
    def loadWeeklyTasks(self):
        """Load tasks for the current week."""
        # Clear existing task blocks
        for i in range(2, self.weekly_grid.rowCount()):
            for j in range(1, 8):  # Day columns
                item = self.weekly_grid.itemAtPosition(i, j)
                if item and item.widget():
                    if isinstance(item.widget(), QFrame) and not hasattr(item.widget(), 'task_id'):
                        continue  # Skip the background cells
                    item.widget().setParent(None)
        
        # Get week end date
        week_end_date = self.week_start_date + timedelta(days=6)
        
        try:
            # Use a query that doesn't depend on the week_start_date column
            self.cursor.execute("""
                SELECT id, title, category, date, start_time, end_time
                FROM weekly_tasks
                WHERE date BETWEEN ? AND ?
                ORDER BY date, start_time
            """, (self.week_start_date.isoformat(), week_end_date.isoformat()))
            
            tasks = self.cursor.fetchall()
            
            for task in tasks:
                task_id, title, category, date_str, start_time, end_time = task
                
                # Calculate day column (1-based)
                task_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                day_col = (task_date - self.week_start_date).days + 1
                
                # Calculate hour row (in 24-hour format)
                start_hour = int(start_time.split(':')[0])
                
                # Create task block
                task_block = TaskBlock(task_id, title, category, start_time, end_time)
                
                # Add to grid
                self.weekly_grid.addWidget(task_block, start_hour - 6, day_col)
        except sqlite3.Error as e:
            print(f"Error loading weekly tasks: {e}")
            # Create the table if it doesn't exist
            self.ensure_weekly_tasks_table()
    
    def showAddTaskDialog(self):
        """Show dialog to add a weekly task."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Weekly Task")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Title field
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_layout.addWidget(title_label)
        
        title_input = QLineEdit()
        title_layout.addWidget(title_input)
        layout.addLayout(title_layout)
        
        # Date field
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_layout.addWidget(date_label)
        
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.fromString(self.week_start_date.isoformat(), Qt.DateFormat.ISODate))
        date_layout.addWidget(date_input)
        layout.addLayout(date_layout)
        
        # Time fields
        time_layout = QHBoxLayout()
        start_label = QLabel("Start Time:")
        time_layout.addWidget(start_label)
        
        start_time = QTimeEdit()
        start_time.setTime(QTime(9, 0))  # Default to 9 AM
        time_layout.addWidget(start_time)
        
        end_label = QLabel("End Time:")
        time_layout.addWidget(end_label)
        
        end_time = QTimeEdit()
        end_time.setTime(QTime(10, 0))  # Default to 10 AM
        time_layout.addWidget(end_time)
        
        layout.addLayout(time_layout)
        
        # Category field
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_layout.addWidget(category_label)
        
        category_combo = QComboBox()
        category_combo.addItems(["Work", "Personal", "Health", "Other"])
        category_layout.addWidget(category_combo)
        layout.addLayout(category_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = title_input.text()
            date = date_input.date().toString(Qt.DateFormat.ISODate)
            start = start_time.time().toString("HH:mm")
            end = end_time.time().toString("HH:mm")
            category = category_combo.currentText()
            
            self.addWeeklyTask(title, date, start, end, category)
    
    def addWeeklyTask(self, title, date, start_time, end_time, category):
        """Add a new task to the weekly calendar."""
        if not title:
            return
        
        # Insert into database
        self.cursor.execute("""
            INSERT INTO weekly_tasks (title, date, start_time, end_time, category, completed)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (title, date, start_time, end_time, category))
        self.conn.commit()
        
        # Refresh the view
        self.loadWeeklyTasks()
    
    def editWeeklyTask(self, task_id):
        """Edit an existing weekly task."""
        # Retrieve the task data
        self.cursor.execute("""
            SELECT title, date, start_time, end_time, category
            FROM weekly_tasks
            WHERE id = ?
        """, (task_id,))
        
        task = self.cursor.fetchone()
        if not task:
            return
        
        title, date_str, start_time, end_time, category = task
        
        # Create edit dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Task")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Title field
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_layout.addWidget(title_label)
        
        title_input = QLineEdit(title)
        title_layout.addWidget(title_input)
        layout.addLayout(title_layout)
        
        # Date field
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_layout.addWidget(date_label)
        
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.fromString(date_str, Qt.DateFormat.ISODate))
        date_layout.addWidget(date_input)
        layout.addLayout(date_layout)
        
        # Time fields
        time_layout = QHBoxLayout()
        start_label = QLabel("Start Time:")
        time_layout.addWidget(start_label)
        
        start_time_edit = QTimeEdit()
        start_time_edit.setTime(QTime.fromString(start_time, "HH:mm"))
        time_layout.addWidget(start_time_edit)
        
        end_label = QLabel("End Time:")
        time_layout.addWidget(end_label)
        
        end_time_edit = QTimeEdit()
        end_time_edit.setTime(QTime.fromString(end_time, "HH:mm"))
        time_layout.addWidget(end_time_edit)
        
        layout.addLayout(time_layout)
        
        # Category field
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_layout.addWidget(category_label)
        
        category_combo = QComboBox()
        category_combo.addItems(["Work", "Personal", "Health", "Other"])
        category_combo.setCurrentText(category)
        category_layout.addWidget(category_combo)
        layout.addLayout(category_layout)
        
        # Completed checkbox
        completed_layout = QHBoxLayout()
        completed_label = QLabel("Completed:")
        completed_layout.addWidget(completed_label)
        
        completed_checkbox = QCheckBox()
        self.cursor.execute("SELECT completed FROM weekly_tasks WHERE id = ?", (task_id,))
        completed = self.cursor.fetchone()[0]
        completed_checkbox.setChecked(completed == 1)
        completed_layout.addWidget(completed_checkbox)
        layout.addLayout(completed_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = title_input.text()
            date = date_input.date().toString(Qt.DateFormat.ISODate)
            start = start_time_edit.time().toString("HH:mm")
            end = end_time_edit.time().toString("HH:mm")
            category = category_combo.currentText()
            completed = 1 if completed_checkbox.isChecked() else 0
            
            # Update the database
            self.cursor.execute("""
                UPDATE weekly_tasks
                SET title = ?, date = ?, start_time = ?, end_time = ?, category = ?, completed = ?
                WHERE id = ?
            """, (title, date, start, end, category, completed, task_id))
            self.conn.commit()
            
            # Refresh the view
            self.loadWeeklyTasks()
    
    def completeWeeklyTask(self, task_id):
        """Mark a weekly task as completed."""
        self.cursor.execute("""
            UPDATE weekly_tasks
            SET completed = 1
            WHERE id = ?
        """, (task_id,))
        self.conn.commit()
        
        # Refresh the view
        self.loadWeeklyTasks()
    
    def deleteWeeklyTask(self, task_id):
        """Delete a weekly task."""
        self.cursor.execute("""
            DELETE FROM weekly_tasks
            WHERE id = ?
        """, (task_id,))
        self.conn.commit()
        
        # Refresh the view
        self.loadWeeklyTasks()
    
    def refresh(self):
        """Refresh the weekly view data."""
        self.loadWeeklyTasks() 