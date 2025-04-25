"""
Unified Activities View for TaskTitan.

This module provides a combined view for events, tasks, and habits with shared functionality.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QFrame, QListWidget, 
                            QListWidgetItem, QDialog, QLineEdit, QTimeEdit, 
                            QComboBox, QDialogButtonBox, QMessageBox, QCheckBox,
                            QDateEdit, QTabWidget, QSplitter, QSizePolicy)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QSize, QDateTime
from PyQt6.QtGui import QIcon, QFont, QColor
from datetime import datetime, timedelta
import random

from app.resources import get_icon
from app.views.task_widget import TaskWidget

class UnifiedActivitiesView(QWidget):
    """Widget that combines events, tasks, and habits into a single unified view."""
    
    # Signals for changes
    activityAdded = pyqtSignal(dict)
    activityCompleted = pyqtSignal(int, bool, str, str)  # id, completed, date, type
    activityDeleted = pyqtSignal(int, str)  # id, type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store parent to access database
        
        # Activities data
        self.activities = {
            'task': [],
            'event': [],
            'habit': []
        }
        self.completions = {}  # Dictionary to track completions by date
        
        # Current date for displaying activities
        self.current_date = QDate.currentDate()
        
        # Setup UI
        self.setupUI()
        
        # Load initial data
        self.loadActivities()
    
    def setupUI(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("activitiesHeader")
        header.setMinimumHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Title
        title = QLabel("My Activities")
        title.setObjectName("activitiesTitle")
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
        
        # Add activity buttons
        self.add_buttons_layout = QHBoxLayout()
        
        # Add task button
        self.add_task_btn = QPushButton("Add Task")
        self.add_task_btn.setObjectName("addButton")
        self.add_task_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_task_btn.clicked.connect(lambda: self.showAddActivityDialog('task'))
        add_icon = get_icon("add")
        if not add_icon.isNull():
            self.add_task_btn.setIcon(add_icon)
        self.add_buttons_layout.addWidget(self.add_task_btn)
        
        # Add event button
        self.add_event_btn = QPushButton("Add Event")
        self.add_event_btn.setObjectName("addButton")
        self.add_event_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_event_btn.clicked.connect(lambda: self.showAddActivityDialog('event'))
        event_icon = get_icon("event")
        if not event_icon.isNull():
            self.add_event_btn.setIcon(event_icon)
        self.add_buttons_layout.addWidget(self.add_event_btn)
        
        # Add habit button
        self.add_habit_btn = QPushButton("Add Habit")
        self.add_habit_btn.setObjectName("addButton")
        self.add_habit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_habit_btn.clicked.connect(lambda: self.showAddActivityDialog('habit'))
        habit_icon = get_icon("habits")
        if not habit_icon.isNull():
            self.add_habit_btn.setIcon(habit_icon)
        self.add_buttons_layout.addWidget(self.add_habit_btn)
        
        header_layout.addLayout(self.add_buttons_layout)
        
        main_layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("activitiesSeparator")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Activities container
        self.activities_container = QWidget()
        self.activities_layout = QVBoxLayout(self.activities_container)
        self.activities_layout.setContentsMargins(20, 15, 20, 15)
        
        # Activities list
        self.activities_list = QListWidget()
        self.activities_list.setObjectName("activitiesList")
        self.activities_list.setFrameShape(QFrame.Shape.NoFrame)
        self.activities_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.activities_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.activities_list.customContextMenuRequested.connect(self.showContextMenu)
        
        self.activities_layout.addWidget(self.activities_list)
        
        # Scroll area for activities
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidget(self.activities_container)
        
        main_layout.addWidget(scroll_area, 1)  # Give it a stretch factor
        
        # Apply styles
        self.setStyleSheet("""
            #activitiesHeader {
                background-color: #FFFFFF;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            #activitiesTitle {
                color: #111827;
            }
            #addButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                margin-left: 5px;
            }
            #addButton:hover {
                background-color: #4338CA;
            }
            #addButton:pressed {
                background-color: #3730A3;
            }
            #activitiesSeparator {
                background-color: #E5E7EB;
            }
            #activitiesList {
                background-color: #F9FAFB;
            }
            QListWidget::item {
                border-bottom: 1px solid #E5E7EB;
                padding: 4px;
            }
        """)
    
    def showAddActivityDialog(self, activity_type):
        """Show the dialog to add a new activity."""
        dialog = QDialog(self)
        
        if activity_type == 'task':
            dialog.setWindowTitle("Add New Task")
        elif activity_type == 'event':
            dialog.setWindowTitle("Add New Event")
        else:  # habit
            dialog.setWindowTitle("Add New Habit")
            
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Name/Title/Description
        name_layout = QHBoxLayout()
        if activity_type == 'task':
            name_label = QLabel("Task Description:")
        elif activity_type == 'event':
            name_label = QLabel("Event Description:")
        else:  # habit
            name_label = QLabel("Habit Name:")
            
        name_layout.addWidget(name_label)
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Date
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_layout.addWidget(date_label)
        self.date_input = QDateEdit()
        self.date_input.setDate(self.current_date)
        self.date_input.setCalendarPopup(True)
        date_layout.addWidget(self.date_input)
        layout.addLayout(date_layout)
        
        # Start Time
        start_time_layout = QHBoxLayout()
        start_time_label = QLabel("Start Time:")
        start_time_layout.addWidget(start_time_label)
        self.start_time_input = QTimeEdit()
        current_time = QTime.currentTime()
        self.start_time_input.setTime(QTime(current_time.hour(), 0))  # Default to current hour, 0 minutes
        start_time_layout.addWidget(self.start_time_input)
        layout.addLayout(start_time_layout)
        
        # End Time
        end_time_layout = QHBoxLayout()
        end_time_label = QLabel("End Time:")
        end_time_layout.addWidget(end_time_label)
        self.end_time_input = QTimeEdit()
        self.end_time_input.setTime(QTime(current_time.hour() + 1, 0))  # Default to next hour
        end_time_layout.addWidget(self.end_time_input)
        layout.addLayout(end_time_layout)
        
        # Additional fields based on type
        if activity_type == 'task':
            # Priority for tasks
            priority_layout = QHBoxLayout()
            priority_label = QLabel("Priority:")
            priority_layout.addWidget(priority_label)
            self.priority_input = QComboBox()
            self.priority_input.addItems(["Low", "Medium", "High"])
            self.priority_input.setCurrentIndex(1)  # Default to Medium
            priority_layout.addWidget(self.priority_input)
            layout.addLayout(priority_layout)
            
            # Category for tasks
            category_layout = QHBoxLayout()
            category_label = QLabel("Category:")
            category_layout.addWidget(category_label)
            self.category_input = QComboBox()
            self.category_input.addItems(["Work", "Personal", "Health", "Learning", "Other"])
            category_layout.addWidget(self.category_input)
            layout.addLayout(category_layout)
            
        elif activity_type == 'habit':
            # Days of the week for habits
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
        button_box.accepted.connect(lambda: self.addActivity(dialog, activity_type))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def addActivity(self, dialog, activity_type):
        """Add a new activity from dialog data."""
        name = self.name_input.text().strip()
        date = self.date_input.date().toString("yyyy-MM-dd")
        start_time = self.start_time_input.time().toString("HH:mm")
        end_time = self.end_time_input.time().toString("HH:mm")
        
        if not name:
            QMessageBox.warning(dialog, "Error", "Description cannot be empty")
            return
            
        # Generate a unique ID (in a real app, this would come from the database)
        activity_id = random.randint(1000, 9999)
        
        # Create activity dictionary with common fields
        activity = {
            'id': activity_id,
            'description': name,
            'date': date,
            'start_time': start_time,
            'end_time': end_time,
            'completed': False,
            'type': activity_type
        }
        
        # Add type-specific fields
        if activity_type == 'task':
            priority_map = {"Low": 0, "Medium": 1, "High": 2}
            activity['priority'] = priority_map[self.priority_input.currentText()]
            activity['category'] = self.category_input.currentText()
        
        elif activity_type == 'habit':
            # Get selected days
            days_of_week = []
            for day, checkbox in self.day_checkboxes.items():
                if checkbox.isChecked():
                    days_of_week.append(day)
            
            if not days_of_week:
                QMessageBox.warning(dialog, "Error", "Please select at least one day of the week")
                return
                
            activity['days_of_week'] = ",".join(days_of_week)
            activity['created_at'] = datetime.now().strftime("%Y-%m-%d")
        
        # Add to our activities list
        self.activities[activity_type].append(activity)
        
        # Refresh the activities list
        self.refreshActivitiesList()
        
        # Emit the signal
        self.activityAdded.emit(activity)
        
        # Close the dialog
        dialog.accept()
    
    def refreshActivitiesList(self):
        """Refresh the list of activities for the current day."""
        self.activities_list.clear()
        
        current_date_str = self.current_date.toString("yyyy-MM-dd")
        
        # Helper function to check if activity should be shown today
        def should_show_activity(activity):
            # For events and tasks, check the date
            if activity['type'] in ['event', 'task']:
                return activity['date'] == current_date_str
            
            # For habits, check if today's day of week is in the selected days
            elif activity['type'] == 'habit':
                today_day = self.current_date.toString("dddd")  # e.g., "Monday"
                return today_day in activity['days_of_week'].split(",")
        
        # Combine and sort activities by start time
        all_activities = []
        for activity_type, activities in self.activities.items():
            for activity in activities:
                if should_show_activity(activity):
                    all_activities.append(activity)
        
        # Sort by start time
        all_activities.sort(key=lambda x: x['start_time'])
        
        # Add each activity to the list
        for activity in all_activities:
            item = QListWidgetItem()
            
            # Create an appropriate widget based on type
            if activity['type'] == 'task':
                widget = TaskWidget(
                    task_id=activity['id'],
                    title=activity['description'],
                    due_date=f"{activity['date']} {activity['start_time']}-{activity['end_time']}",
                    priority=activity.get('priority', 0),
                    category=activity.get('category', 'Other'),
                    completed=activity.get('completed', False)
                )
                widget.taskCompleted.connect(
                    lambda id, completed, activity_type='task': 
                    self.onActivityToggled(id, completed, activity_type)
                )
                widget.taskDeleted.connect(
                    lambda id, activity_type='task': 
                    self.deleteActivity(id, activity_type)
                )
            else:
                # Create an activity item widget similar to TaskWidget
                widget = ActivityItemWidget(
                    activity_id=activity['id'],
                    description=activity['description'],
                    start_time=activity['start_time'],
                    end_time=activity['end_time'],
                    activity_type=activity['type'],
                    completed=activity.get('completed', False)
                )
                widget.toggled.connect(
                    lambda id, completed, activity_type=activity['type']: 
                    self.onActivityToggled(id, completed, activity_type)
                )
                widget.deleted.connect(
                    lambda id, activity_type=activity['type']: 
                    self.deleteActivity(id, activity_type)
                )
            
            # Set up the item
            item.setSizeHint(widget.sizeHint())
            self.activities_list.addItem(item)
            self.activities_list.setItemWidget(item, widget)
    
    def onActivityToggled(self, activity_id, completed, activity_type):
        """Handle activity completion toggling."""
        # Update the activity's completion status
        for activity in self.activities[activity_type]:
            if activity['id'] == activity_id:
                activity['completed'] = completed
                break
        
        # Get the current date as string
        current_date_str = self.current_date.toString("yyyy-MM-dd")
        
        # Emit the signal
        self.activityCompleted.emit(activity_id, completed, current_date_str, activity_type)
    
    def showContextMenu(self, position):
        """Show context menu for an activity."""
        item = self.activities_list.itemAt(position)
        if not item:
            return
            
        # Get the widget and activity ID
        widget = self.activities_list.itemWidget(item)
        if not widget:
            return
            
        # Show menu
        menu = QMenu(self)
        
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        
        # Add "Delete for Today Only" option for habits
        delete_today_action = None
        if hasattr(widget, 'activity_type') and widget.activity_type == 'habit':
            delete_today_action = menu.addAction("Delete for Today Only")
        
        # Show the menu and get the selected action
        action = menu.exec(self.activities_list.mapToGlobal(position))
        
        # Handle the selected action
        if action == edit_action:
            if hasattr(widget, 'task_id'):
                self.editActivity(widget.task_id, 'task')
            elif hasattr(widget, 'activity_id'):
                self.editActivity(widget.activity_id, widget.activity_type)
        elif action == delete_action:
            if hasattr(widget, 'task_id'):
                self.deleteActivity(widget.task_id, 'task')
            elif hasattr(widget, 'activity_id'):
                self.deleteActivity(widget.activity_id, widget.activity_type)
        elif action == delete_today_action:
            if hasattr(widget, 'activity_id'):
                self.deleteHabitForToday(widget.activity_id)
    
    def editActivity(self, activity_id, activity_type):
        """Edit an existing activity."""
        # Find the activity
        activity = None
        for a in self.activities[activity_type]:
            if a['id'] == activity_id:
                activity = a
                break
                
        if not activity:
            return
            
        # Show edit dialog
        dialog = QDialog(self)
        
        if activity_type == 'task':
            dialog.setWindowTitle("Edit Task")
        elif activity_type == 'event':
            dialog.setWindowTitle("Edit Event")
        else:  # habit
            dialog.setWindowTitle("Edit Habit")
            
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Name/Description
        name_layout = QHBoxLayout()
        if activity_type == 'task':
            name_label = QLabel("Task Description:")
        elif activity_type == 'event':
            name_label = QLabel("Event Description:")
        else:  # habit
            name_label = QLabel("Habit Name:")
            
        name_layout.addWidget(name_label)
        self.edit_name_input = QLineEdit(activity['description'])
        name_layout.addWidget(self.edit_name_input)
        layout.addLayout(name_layout)
        
        # Date
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_layout.addWidget(date_label)
        self.edit_date_input = QDateEdit()
        self.edit_date_input.setDate(QDate.fromString(activity['date'], "yyyy-MM-dd"))
        self.edit_date_input.setCalendarPopup(True)
        date_layout.addWidget(self.edit_date_input)
        layout.addLayout(date_layout)
        
        # Start Time
        start_time_layout = QHBoxLayout()
        start_time_label = QLabel("Start Time:")
        start_time_layout.addWidget(start_time_label)
        self.edit_start_time_input = QTimeEdit()
        self.edit_start_time_input.setTime(QTime.fromString(activity['start_time'], "HH:mm"))
        start_time_layout.addWidget(self.edit_start_time_input)
        layout.addLayout(start_time_layout)
        
        # End Time
        end_time_layout = QHBoxLayout()
        end_time_label = QLabel("End Time:")
        end_time_layout.addWidget(end_time_label)
        self.edit_end_time_input = QTimeEdit()
        self.edit_end_time_input.setTime(QTime.fromString(activity['end_time'], "HH:mm"))
        end_time_layout.addWidget(self.edit_end_time_input)
        layout.addLayout(end_time_layout)
        
        # Type-specific fields
        if activity_type == 'task':
            # Priority for tasks
            priority_layout = QHBoxLayout()
            priority_label = QLabel("Priority:")
            priority_layout.addWidget(priority_label)
            self.edit_priority_input = QComboBox()
            self.edit_priority_input.addItems(["Low", "Medium", "High"])
            self.edit_priority_input.setCurrentIndex(activity.get('priority', 1))
            priority_layout.addWidget(self.edit_priority_input)
            layout.addLayout(priority_layout)
            
            # Category for tasks
            category_layout = QHBoxLayout()
            category_label = QLabel("Category:")
            category_layout.addWidget(category_label)
            self.edit_category_input = QComboBox()
            self.edit_category_input.addItems(["Work", "Personal", "Health", "Learning", "Other"])
            # Find the index of the current category
            category_index = self.edit_category_input.findText(activity.get('category', 'Other'))
            if category_index != -1:
                self.edit_category_input.setCurrentIndex(category_index)
            category_layout.addWidget(self.edit_category_input)
            layout.addLayout(category_layout)
            
        elif activity_type == 'habit':
            # Days of the week for habits
            days_layout = QVBoxLayout()
            days_label = QLabel("Days of Week:")
            days_layout.addWidget(days_label)
            
            self.edit_day_checkboxes = {}
            days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            selected_days = activity.get('days_of_week', '').split(',')
            
            for day in days_of_week:
                checkbox = QCheckBox(day)
                checkbox.setChecked(day in selected_days)
                days_layout.addWidget(checkbox)
                self.edit_day_checkboxes[day] = checkbox
            
            layout.addLayout(days_layout)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.updateActivity(dialog, activity_id, activity_type))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def updateActivity(self, dialog, activity_id, activity_type):
        """Update an activity with new values from the edit dialog."""
        # Get values from dialog
        description = self.edit_name_input.text().strip()
        date = self.edit_date_input.date().toString("yyyy-MM-dd")
        start_time = self.edit_start_time_input.time().toString("HH:mm")
        end_time = self.edit_end_time_input.time().toString("HH:mm")
        
        if not description:
            QMessageBox.warning(dialog, "Error", "Description cannot be empty")
            return
        
        # Find and update the activity
        for activity in self.activities[activity_type]:
            if activity['id'] == activity_id:
                # Update common fields
                activity['description'] = description
                activity['date'] = date
                activity['start_time'] = start_time
                activity['end_time'] = end_time
                
                # Update type-specific fields
                if activity_type == 'task':
                    priority_map = {"Low": 0, "Medium": 1, "High": 2}
                    activity['priority'] = priority_map[self.edit_priority_input.currentText()]
                    activity['category'] = self.edit_category_input.currentText()
                
                elif activity_type == 'habit':
                    # Get selected days
                    days_of_week = []
                    for day, checkbox in self.edit_day_checkboxes.items():
                        if checkbox.isChecked():
                            days_of_week.append(day)
                    
                    if not days_of_week:
                        QMessageBox.warning(dialog, "Error", "Please select at least one day of the week")
                        return
                        
                    activity['days_of_week'] = ",".join(days_of_week)
                
                break
        
        # Refresh the activities list
        self.refreshActivitiesList()
        
        # Close the dialog
        dialog.accept()
    
    def deleteActivity(self, activity_id, activity_type):
        """Delete an activity."""
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this {activity_type}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Remove from our list
            self.activities[activity_type] = [a for a in self.activities[activity_type] if a['id'] != activity_id]
            
            # Refresh the activities list
            self.refreshActivitiesList()
            
            # Emit the signal
            self.activityDeleted.emit(activity_id, activity_type)
    
    def previousDay(self):
        """Go to the previous day."""
        self.current_date = self.current_date.addDays(-1)
        self.date_label.setText(self.current_date.toString("dddd, MMMM d, yyyy"))
        self.refreshActivitiesList()
    
    def nextDay(self):
        """Go to the next day."""
        self.current_date = self.current_date.addDays(1)
        self.date_label.setText(self.current_date.toString("dddd, MMMM d, yyyy"))
        self.refreshActivitiesList()
    
    def loadActivities(self):
        """Load activities from the database."""
        # No longer adding sample data
        # Just refresh the list with existing data
        self.refreshActivitiesList()
    
    def refresh(self):
        """Refresh the view."""
        self.loadActivities()

    def deleteHabitForToday(self, activity_id):
        """Delete a habit for the current day only, without removing the habit completely."""
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion for Today",
            "Are you sure you want to delete this habit for today only?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Find the habit in our list
            habit = None
            for h in self.activities['habit']:
                if h['id'] == activity_id:
                    habit = h
                    break
            
            if habit:
                # Get the current day of the week
                current_day = self.current_date.toString("dddd")  # e.g., "Monday"
                
                # Get the current days of the week for this habit
                days_of_week = habit['days_of_week'].split(",")
                
                # Remove the current day if it exists in the list
                if current_day in days_of_week:
                    days_of_week.remove(current_day)
                    
                    # Update the habit with the new days of week
                    habit['days_of_week'] = ",".join(days_of_week)
                    
                    # Update in database if possible
                    if hasattr(self.parent, 'conn') and self.parent.conn:
                        try:
                            self.parent.cursor.execute(
                                "UPDATE activities SET days_of_week = ? WHERE id = ?",
                                (habit['days_of_week'], activity_id)
                            )
                            self.parent.conn.commit()
                        except Exception as e:
                            print(f"Error updating habit days of week: {e}")
                    
                    # Emit signal so parent widgets can update
                    self.activityDeleted.emit(activity_id, 'habit')
                    
                    # Refresh the activities list
                    self.refreshActivitiesList()
                    
                    QMessageBox.information(
                        self,
                        "Habit Removed for Today",
                        f"This habit will no longer appear on {current_day}s."
                    )
                else:
                    QMessageBox.information(
                        self,
                        "No Change Needed",
                        f"This habit is not scheduled for {current_day}s."
                    )

class ActivityItemWidget(QWidget):
    """Custom widget for displaying an activity in the list."""
    
    # Signals
    toggled = pyqtSignal(int, bool)  # activity_id, completed
    deleted = pyqtSignal(int)  # activity_id
    
    def __init__(self, activity_id, description, start_time, end_time, activity_type, completed=False, parent=None):
        super().__init__(parent)
        
        self.activity_id = activity_id
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.activity_type = activity_type
        self.completed = completed
        
        self.setupUI()
    
    def setupUI(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(8)
        
        # Checkbox for completion status
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.completed)
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.toggled.connect(self.onToggled)
        main_layout.addWidget(self.checkbox)
        
        # Icon based on activity type
        icon_label = QLabel()
        if self.activity_type == 'event':
            icon = get_icon("event")
        else:  # habit
            icon = get_icon("habits")
            
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(QSize(16, 16)))
        main_layout.addWidget(icon_label)
        
        # Container for text information
        text_container = QVBoxLayout()
        text_container.setSpacing(2)
        
        # Activity description
        self.title_label = QLabel(self.description)
        font = QFont()
        font.setPointSize(10)
        if self.completed:
            self.title_label.setStyleSheet("text-decoration: line-through; color: #6B7280;")
        else:
            font.setBold(True)
            self.title_label.setFont(font)
        text_container.addWidget(self.title_label)
        
        # Time details
        self.details_label = QLabel(f"{self.start_time} - {self.end_time}")
        self.details_label.setStyleSheet("color: #6B7280; font-size: 9pt;")
        text_container.addWidget(self.details_label)
        
        main_layout.addLayout(text_container, 1)  # Give it a stretch factor
        
        # Type indicator
        type_indicator = QLabel(self.activity_type.capitalize())
        type_indicator.setStyleSheet(f"""
            color: white;
            background-color: {self.getTypeColor()};
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 9pt;
        """)
        main_layout.addWidget(type_indicator)
        
        # Set widget styling
        self.setStyleSheet("""
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
        """)
    
    def getTypeColor(self):
        """Get the color associated with this activity type."""
        if self.activity_type == 'event':
            return "#3B82F6"  # Blue
        elif self.activity_type == 'habit':
            return "#10B981"  # Green
        else:
            return "#6366F1"  # Indigo
    
    def onToggled(self, checked):
        """Handle completion toggling."""
        self.completed = checked
        
        # Update title appearance
        if checked:
            self.title_label.setStyleSheet("text-decoration: line-through; color: #6B7280;")
            font = self.title_label.font()
            font.setBold(False)
            self.title_label.setFont(font)
        else:
            self.title_label.setStyleSheet("color: #1F2937;")
            font = self.title_label.font()
            font.setBold(True)
            self.title_label.setFont(font)
        
        # Emit signal
        self.toggled.emit(self.activity_id, checked) 