"""
Habit tracking widget for TaskTitan.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QFrame, QListWidget, 
                            QListWidgetItem, QDialog, QLineEdit, QTimeEdit, 
                            QComboBox, QDialogButtonBox, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor
from datetime import datetime, timedelta
import random

from app.resources import get_icon

class HabitWidget(QWidget):
    """Widget for tracking habits."""
    
    # Signals for habit changes
    habitAdded = pyqtSignal(dict)
    habitCompleted = pyqtSignal(int, bool, str)  # id, completed, date
    habitDeleted = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store parent to access database
        
        # Habits data
        self.habits = []
        self.completions = {}  # Dictionary to track completions by date
        
        # Current date for displaying habits
        self.current_date = QDate.currentDate()
        
        # Setup UI
        self.setupUI()
        
        # Load initial data
        self.loadHabits()
    
    def setupUI(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("habitHeader")
        header.setMinimumHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Title
        title = QLabel("My Habits")
        title.setObjectName("habitTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        header_layout.addWidget(title)
        
        # Date navigation
        date_layout = QHBoxLayout()
        
        prev_day_btn = QPushButton()
        prev_day_btn.setIcon(QIcon.fromTheme("go-previous"))
        prev_day_btn.setFixedSize(32, 32)
        prev_day_btn.clicked.connect(self.previousDay)
        date_layout.addWidget(prev_day_btn)
        
        self.date_label = QLabel(self.current_date.toString("dddd, MMMM d, yyyy"))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_layout.addWidget(self.date_label)
        
        next_day_btn = QPushButton()
        next_day_btn.setIcon(QIcon.fromTheme("go-next"))
        next_day_btn.setFixedSize(32, 32)
        next_day_btn.clicked.connect(self.nextDay)
        date_layout.addWidget(next_day_btn)
        
        header_layout.addLayout(date_layout)
        
        # Add habit button
        self.add_btn = QPushButton("Add Habit")
        self.add_btn.setObjectName("addHabitButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setMinimumWidth(100)
        self.add_btn.clicked.connect(self.showAddHabitDialog)
        
        # Add icon to button
        add_icon = get_icon("add")
        if not add_icon.isNull():
            self.add_btn.setIcon(add_icon)
        
        header_layout.addWidget(self.add_btn)
        
        main_layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("habitSeparator")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Habits list
        self.habits_list = QListWidget()
        self.habits_list.setObjectName("habitsList")
        self.habits_list.setFrameShape(QFrame.Shape.NoFrame)
        self.habits_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.habits_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.habits_list.customContextMenuRequested.connect(self.showContextMenu)
        
        main_layout.addWidget(self.habits_list)
        
        # Apply styles
        self.setStyleSheet("""
            #habitHeader {
                background-color: #FFFFFF;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            #habitTitle {
                color: #111827;
            }
            #addHabitButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            #addHabitButton:hover {
                background-color: #4338CA;
            }
            #addHabitButton:pressed {
                background-color: #3730A3;
            }
            #habitSeparator {
                background-color: #E5E7EB;
            }
            #habitsList {
                background-color: #F9FAFB;
            }
            QListWidget::item {
                border-bottom: 1px solid #E5E7EB;
                padding: 4px;
            }
        """)
    
    def showAddHabitDialog(self):
        """Show the dialog to add a new habit."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Habit")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Habit Name:")
        name_layout.addWidget(name_label)
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Time
        time_layout = QHBoxLayout()
        time_label = QLabel("Time:")
        time_layout.addWidget(time_label)
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime(8, 0))  # Default to 8:00 AM
        time_layout.addWidget(self.time_input)
        layout.addLayout(time_layout)
        
        # Days of the week
        days_layout = QVBoxLayout()
        days_label = QLabel("Days of Week:")
        days_layout.addWidget(days_label)
        
        self.day_checkboxes = {}
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days_of_week:
            checkbox = QCheckBox(day)
            checkbox.setChecked(True)  # Default to all days selected
            days_layout.addWidget(checkbox)
            self.day_checkboxes[day] = checkbox
        
        layout.addLayout(days_layout)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.addHabit(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def addHabit(self, dialog):
        """Add a new habit from dialog data."""
        name = self.name_input.text().strip()
        time = self.time_input.time().toString("HH:mm")
        
        # Get selected days
        days_of_week = []
        for day, checkbox in self.day_checkboxes.items():
            if checkbox.isChecked():
                days_of_week.append(day)
        
        if not name:
            QMessageBox.warning(dialog, "Error", "Habit name cannot be empty")
            return
        
        if not days_of_week:
            QMessageBox.warning(dialog, "Error", "Please select at least one day of the week")
            return
        
        # In a real app, we'd save to database
        # For now we use a random ID
        habit_id = random.randint(1000, 9999)
        
        # Create habit dictionary
        habit = {
            'id': habit_id,
            'name': name,
            'time': time,
            'days_of_week': ",".join(days_of_week),
            'created_at': datetime.now().strftime("%Y-%m-%d")
        }
        
        # Add to our list
        self.habits.append(habit)
        
        # Refresh the habits list
        self.refreshHabitsList()
        
        # Emit the signal
        self.habitAdded.emit(habit)
        
        # Close the dialog
        dialog.accept()
    
    def refreshHabitsList(self):
        """Refresh the list of habits for the current day."""
        self.habits_list.clear()
        
        # Get the day of week for the current date
        current_day = self.current_date.toString("dddd")
        today_str = self.current_date.toString("yyyy-MM-dd")
        
        # Add habits for this day of week
        for habit in self.habits:
            if current_day in habit['days_of_week'].split(","):
                # Create a custom widget for this habit
                item = QListWidgetItem()
                item.setSizeHint(QSize(0, 60))  # Set height to 60px
                
                # Create widget for the item
                widget = HabitItemWidget(
                    habit['id'], 
                    habit['name'], 
                    habit['time'],
                    today_str in self.completions.get(habit['id'], []),
                    self
                )
                
                # Connect signals
                widget.toggled.connect(self.onHabitToggled)
                
                self.habits_list.addItem(item)
                self.habits_list.setItemWidget(item, widget)
    
    def onHabitToggled(self, habit_id, completed):
        """Handle when a habit is toggled."""
        today_str = self.current_date.toString("yyyy-MM-dd")
        
        # Update completions
        if completed:
            if habit_id not in self.completions:
                self.completions[habit_id] = []
            
            if today_str not in self.completions[habit_id]:
                self.completions[habit_id].append(today_str)
        else:
            if habit_id in self.completions and today_str in self.completions[habit_id]:
                self.completions[habit_id].remove(today_str)
        
        # Emit the signal
        self.habitCompleted.emit(habit_id, completed, today_str)
    
    def showContextMenu(self, position):
        """Show context menu for a habit."""
        # Get the item at the position
        item = self.habits_list.itemAt(position)
        if not item:
            return
        
        # Get the widget and habit ID
        habit_widget = self.habits_list.itemWidget(item)
        if not habit_widget:
            return
        
        habit_id = habit_widget.habit_id
        
        # Create the menu
        menu = QDialog.createPopupMenu()
        
        # Add actions
        edit_action = menu.addAction("Edit Habit")
        delete_action = menu.addAction("Delete Habit")
        
        # Handle selection
        action = menu.exec(self.habits_list.viewport().mapToGlobal(position))
        
        if action == edit_action:
            self.editHabit(habit_id)
        elif action == delete_action:
            self.deleteHabit(habit_id)
    
    def editHabit(self, habit_id):
        """Edit an existing habit."""
        # Find the habit
        habit = None
        for h in self.habits:
            if h['id'] == habit_id:
                habit = h
                break
        
        if not habit:
            return
        
        # Create and show edit dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Habit")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Habit Name:")
        name_layout.addWidget(name_label)
        self.edit_name_input = QLineEdit(habit['name'])
        name_layout.addWidget(self.edit_name_input)
        layout.addLayout(name_layout)
        
        # Time
        time_layout = QHBoxLayout()
        time_label = QLabel("Time:")
        time_layout.addWidget(time_label)
        self.edit_time_input = QTimeEdit()
        self.edit_time_input.setTime(QTime.fromString(habit['time'], "HH:mm"))
        time_layout.addWidget(self.edit_time_input)
        layout.addLayout(time_layout)
        
        # Days of the week
        days_layout = QVBoxLayout()
        days_label = QLabel("Days of Week:")
        days_layout.addWidget(days_label)
        
        self.edit_day_checkboxes = {}
        selected_days = habit['days_of_week'].split(",")
        
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days_of_week:
            checkbox = QCheckBox(day)
            checkbox.setChecked(day in selected_days)
            days_layout.addWidget(checkbox)
            self.edit_day_checkboxes[day] = checkbox
        
        layout.addLayout(days_layout)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.updateHabit(dialog, habit_id))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def updateHabit(self, dialog, habit_id):
        """Update a habit with the data from the edit dialog."""
        name = self.edit_name_input.text().strip()
        time = self.edit_time_input.time().toString("HH:mm")
        
        # Get selected days
        days_of_week = []
        for day, checkbox in self.edit_day_checkboxes.items():
            if checkbox.isChecked():
                days_of_week.append(day)
        
        if not name:
            QMessageBox.warning(dialog, "Error", "Habit name cannot be empty")
            return
        
        if not days_of_week:
            QMessageBox.warning(dialog, "Error", "Please select at least one day of the week")
            return
        
        # Update the habit
        for habit in self.habits:
            if habit['id'] == habit_id:
                habit['name'] = name
                habit['time'] = time
                habit['days_of_week'] = ",".join(days_of_week)
                break
        
        # Refresh the habits list
        self.refreshHabitsList()
        
        # Close the dialog
        dialog.accept()
    
    def deleteHabit(self, habit_id):
        """Delete a habit."""
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Delete Habit",
            "Are you sure you want to delete this habit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Remove from habits list
        self.habits = [h for h in self.habits if h['id'] != habit_id]
        
        # Remove completions
        if habit_id in self.completions:
            del self.completions[habit_id]
        
        # Refresh the list
        self.refreshHabitsList()
        
        # Emit signal
        self.habitDeleted.emit(habit_id)
    
    def previousDay(self):
        """Go to the previous day."""
        self.current_date = self.current_date.addDays(-1)
        self.date_label.setText(self.current_date.toString("dddd, MMMM d, yyyy"))
        self.refreshHabitsList()
    
    def nextDay(self):
        """Go to the next day."""
        self.current_date = self.current_date.addDays(1)
        self.date_label.setText(self.current_date.toString("dddd, MMMM d, yyyy"))
        self.refreshHabitsList()
    
    def getStreakInfo(self, habit_id):
        """Get streak information for a habit."""
        if habit_id not in self.completions:
            return 0, 0  # Current streak, max streak
        
        # Sort dates in ascending order
        dates = sorted(self.completions[habit_id])
        
        # Calculate streaks
        max_streak = 0
        current_streak = 0
        streak_start = None
        
        for i, date_str in enumerate(dates):
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            
            if streak_start is None:
                streak_start = date
                current_streak = 1
            elif i > 0:
                prev_date = QDate.fromString(dates[i-1], "yyyy-MM-dd")
                days_diff = prev_date.daysTo(date)
                
                if days_diff == 1:
                    # Consecutive day
                    current_streak += 1
                elif days_diff > 1:
                    # Streak broken
                    max_streak = max(max_streak, current_streak)
                    streak_start = date
                    current_streak = 1
        
        # Update max streak one last time
        max_streak = max(max_streak, current_streak)
        
        return current_streak, max_streak
    
    def loadHabits(self):
        """Load habits from the database."""
        if hasattr(self.parent, 'cursor') and self.parent.cursor:
            try:
                # Execute SQL to get habits
                self.parent.cursor.execute("""
                    SELECT id, name, time, days_of_week, created_at
                    FROM habits
                """)
                
                # Process results
                results = self.parent.cursor.fetchall()
                
                # Clear existing habits
                self.habits = []
                
                # Add results to habits list
                for row in results:
                    habit = {
                        'id': row[0],
                        'name': row[1],
                        'time': row[2],
                        'days_of_week': row[3],
                        'created_at': row[4]
                    }
                    self.habits.append(habit)
                
                # Load completions
                self.parent.cursor.execute("""
                    SELECT habit_id, completion_date
                    FROM habit_completions
                """)
                
                # Process results
                completion_results = self.parent.cursor.fetchall()
                
                # Clear existing completions
                self.completions = {}
                
                # Add to completions dictionary
                for row in completion_results:
                    habit_id, date_str = row
                    
                    if habit_id not in self.completions:
                        self.completions[habit_id] = []
                    
                    self.completions[habit_id].append(date_str)
                
                # Refresh the habits list
                self.refreshHabitsList()
                
            except Exception as e:
                print(f"Error loading habits: {e}")
                # Add sample data for testing
                self.addSampleHabits()
        else:
            # Add sample data for testing
            self.addSampleHabits()
    
    def addSampleHabits(self):
        """Add sample habits for testing."""
        # Clear existing habits
        self.habits = []
        self.completions = {}
        
        # Sample habits
        sample_habits = [
            {
                'id': 1001,
                'name': "Morning Exercise",
                'time': "06:00",
                'days_of_week': "Monday,Tuesday,Wednesday,Thursday,Friday",
                'created_at': "2023-01-01"
            },
            {
                'id': 1002,
                'name': "Read for 30 minutes",
                'time': "21:00",
                'days_of_week': "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday",
                'created_at': "2023-01-15"
            },
            {
                'id': 1003,
                'name': "Meditate",
                'time': "07:30",
                'days_of_week': "Monday,Wednesday,Friday,Sunday",
                'created_at': "2023-02-01"
            }
        ]
        
        # Add to the habits list
        self.habits.extend(sample_habits)
        
        # Add sample completions for the past week
        today = QDate.currentDate()
        
        for habit in sample_habits:
            self.completions[habit['id']] = []
            
            # Add random completions for the last 10 days
            for i in range(10):
                date = today.addDays(-i)
                day_name = date.toString("dddd")
                
                # Check if this habit is scheduled for this day
                if day_name in habit['days_of_week'].split(','):
                    # 80% chance of completing the habit
                    if random.random() < 0.8:
                        self.completions[habit['id']].append(date.toString("yyyy-MM-dd"))
        
        # Refresh the list
        self.refreshHabitsList()
    
    def refresh(self):
        """Refresh the widget's data."""
        self.loadHabits()


class HabitItemWidget(QWidget):
    """Custom widget for displaying a habit in the list."""
    
    # Signal for habit completion toggling
    toggled = pyqtSignal(int, bool)  # habit_id, completed
    
    def __init__(self, habit_id, name, time, completed, parent=None):
        super().__init__(parent)
        
        self.habit_id = habit_id
        self.name = name
        self.time = time
        self.completed = completed
        
        self.setupUI()
    
    def setupUI(self):
        """Set up the UI for the habit item."""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Checkbox for completion
        checkbox = QCheckBox()
        checkbox.setChecked(self.completed)
        checkbox.toggled.connect(self.onToggled)
        layout.addWidget(checkbox)
        
        # Habit information
        info_layout = QVBoxLayout()
        
        # Name label
        name_label = QLabel(self.name)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        name_label.setFont(font)
        
        if self.completed:
            name_label.setStyleSheet("text-decoration: line-through; color: #6B7280;")
        
        info_layout.addWidget(name_label)
        
        # Time label
        time_label = QLabel(f"Scheduled for {self.time}")
        time_label.setStyleSheet("color: #6B7280;")
        info_layout.addWidget(time_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
    
    def onToggled(self, checked):
        """Handle when the checkbox is toggled."""
        self.completed = checked
        
        # Update the name label style
        name_label = self.findChild(QLabel)
        if name_label:
            if checked:
                name_label.setStyleSheet("text-decoration: line-through; color: #6B7280;")
            else:
                name_label.setStyleSheet("")
        
        # Emit the signal
        self.toggled.emit(self.habit_id, checked) 