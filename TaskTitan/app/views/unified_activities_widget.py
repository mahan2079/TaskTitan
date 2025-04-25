"""
Unified Activities View for TaskTitan.

This module provides a combined view for events, tasks, and habits with shared functionality.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QFrame, QListWidget, 
                            QListWidgetItem, QDialog, QLineEdit, QTimeEdit, 
                            QComboBox, QDialogButtonBox, QMessageBox, QCheckBox,
                            QDateEdit, QTabWidget, QSplitter, QSizePolicy, QMenu,
                            QGraphicsDropShadowEffect, QColorDialog, QCalendarWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime, QSize, QPoint, QEvent, QDateTime
from PyQt6.QtGui import QIcon, QFont, QColor, QAction, QCursor
from datetime import datetime
import random

from app.resources import get_icon
from app.models.activities_manager import ActivitiesManager

class ActivityItemWidget(QWidget):
    """A unified widget for displaying activities (events, tasks, habits)."""
    
    # Signals
    activityCompleted = pyqtSignal(int, bool, str)  # id, completed status, type
    activityDeleted = pyqtSignal(int, str)  # id, type
    activityEdited = pyqtSignal(int, str)  # id, type
    activityClicked = pyqtSignal(dict)  # Full activity data
    
    def __init__(self, activity_id, title, start_time, end_time, activity_type, 
                 priority=0, category=None, completed=False, color=None, parent=None):
        """Initialize the activity widget with the given parameters."""
        super().__init__(parent)
        
        # Store the activity data
        self.activity_id = activity_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.activity_type = activity_type
        self.priority = priority
        self.category = category
        self.completed = completed
        self.custom_color = color  # Custom color for the activity
        
        # Store full activity data for details dialog
        self.activity_data = {
            'id': activity_id,
            'title': title,
            'description': title,
            'start_time': start_time,
            'end_time': end_time,
            'type': activity_type,
            'priority': priority,
            'category': category,
            'completed': completed,
            'color': color
        }
        
        # Set object name for styling
        self.setObjectName("activityWidget")
        
        # Set up mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Set up context menu policy
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenuRequested)
        
        # Configure widget
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(120)  # Much smaller height
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Install event filter for mouse press
        self.installEventFilter(self)
        
        # Set up the UI components
        self.setupUI()
        
        # Apply shadow effect
        self.applyShadowEffect()
        
    def eventFilter(self, obj, event):
        """Filter events for this widget."""
        if obj is self and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.onMousePress(event)
            elif event.button() == Qt.MouseButton.RightButton:
                # Handle right click (already handled by custom context menu)
                pass
            return True
        return super().eventFilter(obj, event)
        
    def onMousePress(self, event):
        """Handle mouse press events - emit signal when the widget is clicked."""
        self.activityClicked.emit(self.activity_data)
        
    def onContextMenuRequested(self, pos):
        """Handle right-click context menu requests."""
        self.showActionsMenu()
    
    def setupUI(self):
        """Set up the UI components of the activity widget."""
        
        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 12, 10, 12)  # Smaller margins
        self.main_layout.setSpacing(8)  # Reduced spacing
        
        # Left color bar based on activity type
        self.color_bar = QFrame()
        self.color_bar.setFixedWidth(4)  # Thin color bar
        
        # Set color based on activity type or custom color
        if self.custom_color:
            self.color_bar.setStyleSheet(f"background-color: {self.custom_color}; border-radius: 2px;")
        elif self.activity_type == 'task':
            self.color_bar.setStyleSheet("background-color: #F87171; border-radius: 2px;")
        elif self.activity_type == 'event':
            self.color_bar.setStyleSheet("background-color: #818CF8; border-radius: 2px;")
        elif self.activity_type == 'habit':
            self.color_bar.setStyleSheet("background-color: #34D399; border-radius: 2px;")
        
        self.main_layout.addWidget(self.color_bar)
        
        # Checkbox for completion status
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.completed)
        self.checkbox.setObjectName("activityCheckbox")
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.toggled.connect(self.onCompletionToggled)
        self.checkbox.setFixedSize(24, 24)  # Smaller checkbox
        self.main_layout.addWidget(self.checkbox)
        
        # Activity type icon
        self.type_icon_label = QLabel()
        self.type_icon_label.setFixedSize(24, 24)  # Smaller icon
        
        # Set icon based on activity type
        if self.activity_type == 'task':
            task_icon = get_icon("task")
            if not task_icon.isNull():
                self.type_icon_label.setPixmap(task_icon.pixmap(QSize(24, 24)))
            else:
                # Fallback to emoji
                self.type_icon_label.setText("✓")
                self.type_icon_label.setStyleSheet("color: #F87171; font-weight: bold; font-size: 16px;")
        elif self.activity_type == 'event':
            event_icon = get_icon("event")
            if not event_icon.isNull():
                self.type_icon_label.setPixmap(event_icon.pixmap(QSize(24, 24)))
            else:
                # Fallback to emoji
                self.type_icon_label.setText("📅")
                self.type_icon_label.setStyleSheet("color: #818CF8; font-size: 16px;")
        elif self.activity_type == 'habit':
            habit_icon = get_icon("habit")
            if not habit_icon.isNull():
                self.type_icon_label.setPixmap(habit_icon.pixmap(QSize(24, 24)))
            else:
                # Fallback to emoji
                self.type_icon_label.setText("↻")
                self.type_icon_label.setStyleSheet("color: #34D399; font-weight: bold; font-size: 16px;")
                
        self.main_layout.addWidget(self.type_icon_label)
        
        # Container for all text information
        self.text_container = QVBoxLayout()
        self.text_container.setSpacing(4)  # Minimal spacing between text elements
        self.text_container.setContentsMargins(8, 0, 0, 0)  # Add left padding
        
        # Activity title
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("activityTitle")
        font = QFont()
        font.setPointSize(12)  # Smaller font
        if self.completed:
            self.title_label.setStyleSheet("text-decoration: line-through; color: #6B7280; font-size: 12pt;")
        else:
            font.setBold(True)
            self.title_label.setFont(font)
        self.title_label.setMaximumHeight(30)  # Fixed smaller height
        self.text_container.addWidget(self.title_label)
        
        # Activity details (time, category, type)
        self.details_label = QLabel()
        self.details_label.setObjectName("activityDetails")
        
        details_text = ""
        if self.start_time:
            details_text += f"{self.start_time}-{self.end_time} "
        if self.category:
            if details_text:
                details_text += "• "
            details_text += f"{self.category} "
        
        # Add activity type tag
        details_text += f"• {self.activity_type.capitalize()}"
            
        self.details_label.setText(details_text)
        self.details_label.setStyleSheet("color: #6B7280; font-size: 10pt;")  # Smaller font
        self.details_label.setMaximumHeight(20)  # Fixed smaller height
        self.text_container.addWidget(self.details_label)
        
        # Add description label (additional info) - with much shorter text
        description_label = QLabel("This is a larger activity item with additional details.")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #4B5563; font-size: 10pt;")  # Smaller font
        description_label.setMaximumHeight(30)  # Fixed smaller height
        self.text_container.addWidget(description_label)
        
        self.main_layout.addLayout(self.text_container, 1)  # Give text container stretch factor
        
        # Priority indicator (for tasks)
        if self.activity_type == 'task':
            self.priority_indicator = QFrame()
            self.priority_indicator.setFixedSize(14, 14)  # Much smaller indicator
            self.priority_indicator.setObjectName("priorityIndicator")
            
            if self.priority == 0:  # Low
                self.priority_indicator.setStyleSheet("""
                    background-color: #10B981;
                    border-radius: 7px;
                """)
            elif self.priority == 1:  # Medium
                self.priority_indicator.setStyleSheet("""
                    background-color: #F59E0B;
                    border-radius: 7px;
                """)
            elif self.priority == 2:  # High
                self.priority_indicator.setStyleSheet("""
                    background-color: #EF4444;
                    border-radius: 7px;
                """)
                
            self.main_layout.addWidget(self.priority_indicator)
        
        # Actions button
        self.actions_btn = QPushButton()
        self.actions_btn.setObjectName("activityActionsButton")
        more_icon = get_icon("more")
        if not more_icon.isNull():
            self.actions_btn.setIcon(more_icon)
        else:
            self.actions_btn.setText("...")
        self.actions_btn.setFixedSize(24, 24)  # Smaller button
        self.actions_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.actions_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F3F4F6;
                border-radius: 12px;
            }
            QPushButton:pressed {
                background-color: #E5E7EB;
            }
        """)
        
        self.actions_btn.clicked.connect(self.showActionsMenu)
        self.main_layout.addWidget(self.actions_btn)
        
        # Set the widget styling
        self.updateStyle()
    
    def updateStyle(self):
        """Update the styling of the widget based on completion state."""
        if self.completed:
            self.setStyleSheet("""
                #activityWidget {
                    background-color: #F9FAFB;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                }
                #activityTitle {
                    text-decoration: line-through;
                    color: #6B7280;
                    font-size: 12pt;
                    padding: 2px 0;
                }
            """)
        else:
            self.setStyleSheet("""
                #activityWidget {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                }
                #activityTitle {
                    color: #1F2937;
                    font-size: 12pt;
                    padding: 2px 0;
                    font-weight: bold;
                }
                #activityWidget:hover {
                    border: 1px solid #D1D5DB;
                    background-color: #F9FAFB;
                }
            """)
    
    def onCompletionToggled(self, checked):
        """Handle activity completion toggling."""
        self.completed = checked
        
        # Update title appearance
        if checked:
            self.title_label.setStyleSheet("text-decoration: line-through; color: #6B7280; font-size: 12pt;")
            font = self.title_label.font()
            font.setBold(False)
            self.title_label.setFont(font)
        else:
            self.title_label.setStyleSheet("color: #1F2937; font-size: 12pt; font-weight: bold;")
            font = self.title_label.font()
            font.setBold(True)
            self.title_label.setFont(font)
        
        # Update widget style
        self.updateStyle()
        
        # Emit signal with the activity ID, current status, and type
        self.activityCompleted.emit(self.activity_id, checked, self.activity_type)
    
    def applyShadowEffect(self):
        """Apply shadow effect to the widget."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(6)  # Smaller blur radius
        shadow.setColor(QColor(0, 0, 0, 20))  # More subtle shadow
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def showActionsMenu(self):
        """Show the actions menu for the activity."""
        menu = QMenu(self)
        
        # Completion action
        if not self.completed:
            complete_action = menu.addAction(f"Mark as Complete")
            complete_icon = get_icon("complete")
            if not complete_icon.isNull():
                complete_action.setIcon(complete_icon)
            else:
                # Use Unicode checkbox character as fallback
                complete_action.setIcon(QIcon.fromTheme("dialog-ok"))
        else:
            complete_action = menu.addAction(f"Mark as Incomplete")
            incomplete_icon = get_icon("incomplete")
            if not incomplete_icon.isNull():
                complete_action.setIcon(incomplete_icon)
            else:
                # Use Unicode checkbox character as fallback
                complete_action.setIcon(QIcon.fromTheme("dialog-cancel"))
        
        # View details action
        view_action = menu.addAction(f"View Details")
        view_icon = get_icon("view")
        if not view_icon.isNull():
            view_action.setIcon(view_icon)
        else:
            view_action.setIcon(QIcon.fromTheme("document-open"))
        
        menu.addSeparator()
        
        # Edit action
        edit_action = menu.addAction(f"Edit {self.activity_type.capitalize()}")
        edit_icon = get_icon("edit")
        if not edit_icon.isNull():
            edit_action.setIcon(edit_icon)
        else:
            edit_action.setIcon(QIcon.fromTheme("document-edit"))
        
        # Duplicate action
        duplicate_action = menu.addAction(f"Duplicate")
        duplicate_icon = get_icon("duplicate")
        if not duplicate_icon.isNull():
            duplicate_action.setIcon(duplicate_icon)
        else:
            duplicate_action.setIcon(QIcon.fromTheme("edit-copy"))
        
        # Reschedule action
        reschedule_action = menu.addAction(f"Reschedule")
        reschedule_icon = get_icon("calendar")
        if not reschedule_icon.isNull():
            reschedule_action.setIcon(reschedule_icon)
        else:
            reschedule_action.setIcon(QIcon.fromTheme("appointment-new"))
        
        menu.addSeparator()
        
        # Delete for today only action (for habits)
        delete_today_action = None
        if self.activity_type == 'habit':
            delete_today_action = menu.addAction(f"Delete for Today Only")
            delete_today_icon = get_icon("delete-today")
            if not delete_today_icon.isNull():
                delete_today_action.setIcon(delete_today_icon)
            else:
                delete_today_action.setIcon(QIcon.fromTheme("edit-cut"))
                
        # Delete action
        delete_action = menu.addAction(f"Delete {self.activity_type.capitalize()}")
        delete_icon = get_icon("delete")
        if not delete_icon.isNull():
            delete_action.setIcon(delete_icon)
        else:
            delete_action.setIcon(QIcon.fromTheme("edit-delete"))
        
        # Add styling to the menu
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 25px 6px 25px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E5E7EB;
                margin: 4px 10px;
            }
        """)
        
        # Show menu at button position
        action = menu.exec(self.actions_btn.mapToGlobal(QPoint(0, self.actions_btn.height())))
        
        if action == edit_action:
            self.activityEdited.emit(self.activity_id, self.activity_type)
        elif action == delete_action:
            self.activityDeleted.emit(self.activity_id, self.activity_type)
        elif action == complete_action:
            self.onCompletionToggled(not self.completed)
        elif action == view_action:
            # Create a dict with the activity data
            activity_data = {
                'id': self.activity_id,
                'title': self.title,
                'type': self.activity_type,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'completed': self.completed,
                'priority': self.priority,
                'category': self.category,
                'color': self.custom_color
            }
            self.activityClicked.emit(activity_data)
        elif action == duplicate_action:
            # Signal to duplicate - use the activityEdited signal for now
            # The parent will need to handle this specially
            self.activityEdited.emit(self.activity_id, f"duplicate_{self.activity_type}")
        elif action == reschedule_action:
            # Signal to reschedule - use the activityEdited signal for now
            # The parent will need to handle this specially
            self.activityEdited.emit(self.activity_id, f"reschedule_{self.activity_type}")
        elif action == delete_today_action:
            # Signal to delete this habit for today only
            self.activityEdited.emit(self.activity_id, "delete_today_habit")


class ActivityAddEditDialog(QDialog):
    """Dialog for adding or editing activities."""
    
    def __init__(self, parent=None, activity_data=None, edit_mode=False):
        super().__init__(parent)
        
        self.edit_mode = edit_mode
        self.activity_data = activity_data or {}
        
        # Set dialog title
        self.setWindowTitle("Add Activity" if not edit_mode else "Edit Activity")
        self.setMinimumWidth(400)
        
        # Default color
        self.current_color = QColor(self.activity_data.get('color', "#6366F1"))
        
        # Set up the UI
        self.setupUI()
        
        # If in edit mode, populate fields
        if edit_mode and activity_data:
            self.populateFields()
    
    def setupUI(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Activity type
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        type_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Task", "Event", "Habit"])
        
        # Set default or current type
        if 'type' in self.activity_data:
            activity_type = self.activity_data['type'].capitalize()
            index = self.type_combo.findText(activity_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
        
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter activity title")
        title_layout.addWidget(self.title_input)
        layout.addLayout(title_layout)
        
        # Date
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_layout.addWidget(date_label)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_input)
        layout.addLayout(date_layout)
        
        # Time range
        time_layout = QHBoxLayout()
        
        start_time_label = QLabel("Start Time:")
        time_layout.addWidget(start_time_label)
        
        self.start_time_input = QTimeEdit()
        self.start_time_input.setTime(QTime.currentTime())
        time_layout.addWidget(self.start_time_input)
        
        end_time_label = QLabel("End Time:")
        time_layout.addWidget(end_time_label)
        
        self.end_time_input = QTimeEdit()
        # Set default end time to 1 hour after start time
        end_time = QTime.currentTime().addSecs(3600)
        self.end_time_input.setTime(end_time)
        time_layout.addWidget(self.end_time_input)
        
        layout.addLayout(time_layout)
        
        # Task-specific: Priority (wrapped in a container widget)
        self.priority_container = QWidget()
        self.priority_layout = QHBoxLayout(self.priority_container)
        self.priority_layout.setContentsMargins(0, 0, 0, 0)
        
        priority_label = QLabel("Priority:")
        self.priority_layout.addWidget(priority_label)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        self.priority_combo.setCurrentIndex(0)  # Default to Low
        self.priority_layout.addWidget(self.priority_combo)
        
        layout.addWidget(self.priority_container)
        
        # Category
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Work", "Personal", "Health", "Learning", "Other"])
        self.category_combo.setCurrentIndex(0)  # Default to Work
        category_layout.addWidget(self.category_combo)
        
        layout.addLayout(category_layout)
        
        # Color selector (for events primarily)
        self.color_container = QWidget()
        self.color_layout = QHBoxLayout(self.color_container)
        self.color_layout.setContentsMargins(0, 0, 0, 0)
        
        color_label = QLabel("Color:")
        self.color_layout.addWidget(color_label)
        
        # Color display
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet(f"""
            background-color: {self.current_color.name()};
            border-radius: 4px;
            border: 1px solid #CBD5E1;
        """)
        self.color_layout.addWidget(self.color_preview)
        
        # Color button
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.select_color)
        self.color_layout.addWidget(self.color_button)
        
        layout.addWidget(self.color_container)
        
        # Habit-specific: Days of week (wrapped in a container widget)
        self.habit_days_container = QWidget()
        self.habit_days_layout = QVBoxLayout(self.habit_days_container)
        self.habit_days_layout.setContentsMargins(0, 0, 0, 0)
        
        days_label = QLabel("Repeat on:")
        self.habit_days_layout.addWidget(days_label)
        
        self.day_checkboxes = {}
        days_of_week_layout = QHBoxLayout()
        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for day in days_of_week:
            checkbox = QCheckBox(day)
            checkbox.setChecked(True)  # Default to all days selected
            days_of_week_layout.addWidget(checkbox)
            self.day_checkboxes[day] = checkbox
        
        self.habit_days_layout.addLayout(days_of_week_layout)
        
        layout.addWidget(self.habit_days_container)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect signals
        self.type_combo.currentTextChanged.connect(self.onTypeChanged)
        
        # Set initial visibility based on type
        self.onTypeChanged(self.type_combo.currentText())
    
    def select_color(self):
        """Open color dialog to select event color."""
        color = QColorDialog.getColor(self.current_color, self, "Select Event Color")
        if color.isValid():
            self.current_color = color
            self.color_preview.setStyleSheet(f"""
                background-color: {self.current_color.name()};
                border-radius: 4px;
                border: 1px solid #CBD5E1;
            """)
    
    def onTypeChanged(self, activity_type):
        """Handle type change to show/hide relevant fields."""
        activity_type = activity_type.lower()
        
        # Show/hide priority (for tasks)
        self.priority_container.setVisible(activity_type == 'task')
        
        # Show/hide days of week (for habits)
        self.habit_days_container.setVisible(activity_type == 'habit')
        
        # If switching to habit, make sure days aren't all selected by default
        # Only check current day if this is a new activity (not edit mode)
        if activity_type == 'habit' and not self.edit_mode:
            # Uncheck all days first
            for checkbox in self.day_checkboxes.values():
                checkbox.setChecked(False)
                
            # Only check the current day if it's a new habit
            current_day = QDate.currentDate().toString("ddd")  # Short day name (e.g., "Mon")
            if current_day in self.day_checkboxes:
                self.day_checkboxes[current_day].setChecked(True)
        
        # Show color selector for all activity types
        self.color_container.setVisible(True)
    
    def populateFields(self):
        """Populate fields with existing data for editing."""
        if 'title' in self.activity_data:
            self.title_input.setText(self.activity_data['title'])
        
        if 'date' in self.activity_data:
            self.date_input.setDate(self.activity_data['date'])
        
        if 'start_time' in self.activity_data:
            self.start_time_input.setTime(self.activity_data['start_time'])
        
        if 'end_time' in self.activity_data:
            self.end_time_input.setTime(self.activity_data['end_time'])
        
        if 'priority' in self.activity_data:
            self.priority_combo.setCurrentIndex(self.activity_data['priority'])
        
        if 'category' in self.activity_data:
            category = self.activity_data['category']
            index = self.category_combo.findText(category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        
        if 'color' in self.activity_data:
            if isinstance(self.activity_data['color'], QColor):
                self.current_color = self.activity_data['color']
            elif isinstance(self.activity_data['color'], str):
                self.current_color = QColor(self.activity_data['color'])
            self.color_preview.setStyleSheet(f"""
                background-color: {self.current_color.name()};
                border-radius: 4px;
                border: 1px solid #CBD5E1;
            """)
        
        if 'days_of_week' in self.activity_data and self.activity_data['days_of_week']:
            days = self.activity_data['days_of_week'].split(',')
            # Reset all checkboxes first
            for checkbox in self.day_checkboxes.values():
                checkbox.setChecked(False)
            # Set the ones that are in the data
            for day_abbr, checkbox in self.day_checkboxes.items():
                if any(day.startswith(day_abbr) or day == day_abbr for day in days):
                    checkbox.setChecked(True)
    
    def getActivityData(self):
        """Get the activity data from the dialog."""
        activity_type = self.type_combo.currentText().lower()
        
        data = {
            'type': activity_type,
            'title': self.title_input.text(),
            'date': self.date_input.date(),
            'start_time': self.start_time_input.time(),
            'end_time': self.end_time_input.time(),
            'category': self.category_combo.currentText(),
            'color': self.current_color.name()  # Add color for all activity types
        }
        
        # Add type-specific data
        if activity_type == 'task':
            data['priority'] = self.priority_combo.currentIndex()
        
        if activity_type == 'habit':
            selected_days = []
            for day_abbr, checkbox in self.day_checkboxes.items():
                if checkbox.isChecked():
                    # Map abbreviated day names to full day names
                    day_mapping = {
                        'Mon': 'Monday',
                        'Tue': 'Tuesday',
                        'Wed': 'Wednesday',
                        'Thu': 'Thursday',
                        'Fri': 'Friday',
                        'Sat': 'Saturday',
                        'Sun': 'Sunday'
                    }
                    selected_days.append(day_mapping.get(day_abbr, day_abbr))
            
            # Make sure at least one day is selected
            if not selected_days:
                # Default to current day if no days selected
                current_day = QDate.currentDate().toString("dddd")  # Full day name
                selected_days.append(current_day)
                
            data['days_of_week'] = ','.join(selected_days)
        
        return data


class ActivityDetailsDialog(QDialog):
    """Dialog for displaying activity details when clicked in the activities list."""
    
    def __init__(self, activity, parent=None):
        super().__init__(parent)
        self.activity = activity
        self.setWindowTitle("Activity Details")
        
        # Use minimum size instead of fixed size for better adaptability
        self.setMinimumSize(400, 350)
        
        # Store the parent properly to ensure button connections work
        self.parent_widget = parent
        
        self.setupUI()
        
    def setupUI(self):
        """Set up the UI for the activity details dialog."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Set dialog styling with improved contrast
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #D1D5DB;
            }
            QLabel {
                color: #1F2937;
                font-size: 14px;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #111827;
            }
            QLabel#subtitle {
                font-size: 16px;  
                font-weight: bold;
                color: #4B5563;
            }
            QLabel#sectionHeader {
                font-size: 16px;
                font-weight: bold;
                color: #374151;
                margin-top: 10px;
            }
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 8px 12px;
                color: #374151;
                font-weight: bold;
                font-size: 13px;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
            QPushButton#primaryBtn {
                background-color: #4F46E5;
                color: white;
                border: none;
            }
            QPushButton#primaryBtn:hover {
                background-color: #4338CA;
            }
            QPushButton#deleteBtn {
                background-color: #FEE2E2;
                color: #B91C1C;
                border: 1px solid #FECACA;
            }
            QPushButton#deleteBtn:hover {
                background-color: #FEE2E2;
                color: #991B1B;
            }
            QFrame#detailsItem {
                background-color: #F9FAFB;
                border-radius: 6px;
                padding: 10px;
                border: 1px solid #E5E7EB;
            }
            QLabel#icon {
                font-size: 18px;
                min-width: 30px;
            }
        """)
        
        # Activity header with type indicator
        header_layout = QHBoxLayout()
        
        # Activity type indicator
        type_indicator = QFrame()
        type_indicator.setFixedSize(32, 32)
        
        activity_type = self.activity.get('type', '')
        if activity_type == 'task':
            type_indicator.setStyleSheet("background-color: #F87171; border-radius: 16px;")
        elif activity_type == 'event':
            type_indicator.setStyleSheet("background-color: #818CF8; border-radius: 16px;")
        elif activity_type == 'habit':
            type_indicator.setStyleSheet("background-color: #34D399; border-radius: 16px;")
        else:
            type_indicator.setStyleSheet("background-color: #9CA3AF; border-radius: 16px;")
            
        header_layout.addWidget(type_indicator)
        
        # Activity title layout
        title_layout = QVBoxLayout()
        title_label = QLabel(self.activity.get('title', self.activity.get('description', 'Untitled')))
        title_label.setObjectName("title")
        title_label.setWordWrap(True)
        title_layout.addWidget(title_label)
        
        # Activity type subtitle
        type_label = QLabel(f"{activity_type.capitalize()}")
        type_label.setObjectName("subtitle")
        title_layout.addWidget(type_label)
        
        header_layout.addLayout(title_layout, 1)
        layout.addLayout(header_layout)
        
        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #E5E7EB; border: none; height: 2px;")
        layout.addWidget(separator)
        
        # Details section
        details_section = QLabel("Details")
        details_section.setObjectName("sectionHeader")
        layout.addWidget(details_section)
        
        # Time information with better contrast
        if self.activity.get('start_time') and self.activity.get('end_time'):
            time_frame = QFrame()
            time_frame.setObjectName("detailsItem")
            time_layout = QHBoxLayout(time_frame)
            time_layout.setContentsMargins(10, 10, 10, 10)
            
            time_icon = QLabel("⏱")
            time_icon.setObjectName("icon")
            time_icon.setFixedWidth(30)
            time_layout.addWidget(time_icon)
            
            # Format the time appropriately based on data type
            start_time = self.activity.get('start_time')
            end_time = self.activity.get('end_time')
            
            if isinstance(start_time, str) and isinstance(end_time, str):
                time_str = f"Time: {start_time} - {end_time}"
            else:
                time_str = f"Time: {start_time.toString('HH:mm')} - {end_time.toString('HH:mm')}"
                
            time_label = QLabel(time_str)
            time_layout.addWidget(time_label)
            time_layout.addStretch()
            layout.addWidget(time_frame)
        
        # Category with better contrast
        if self.activity.get('category'):
            category_frame = QFrame()
            category_frame.setObjectName("detailsItem")
            category_layout = QHBoxLayout(category_frame)
            category_layout.setContentsMargins(10, 10, 10, 10)
            
            category_icon = QLabel("🏷️")
            category_icon.setObjectName("icon")
            category_icon.setFixedWidth(30)
            category_layout.addWidget(category_icon)
            
            category_label = QLabel(f"Category: {self.activity.get('category')}")
            category_layout.addWidget(category_label)
            category_layout.addStretch()
            layout.addWidget(category_frame)
        
        # Priority (for tasks) with better contrast
        if self.activity.get('type') == 'task' and 'priority' in self.activity:
            priority_map = {0: "Low", 1: "Medium", 2: "High"}
            priority_value = self.activity.get('priority')
            priority_name = priority_map.get(priority_value, "Unknown")
            
            priority_frame = QFrame()
            priority_frame.setObjectName("detailsItem")
            priority_layout = QHBoxLayout(priority_frame)
            priority_layout.setContentsMargins(10, 10, 10, 10)
            
            priority_icon = QLabel("⚠️")
            priority_icon.setObjectName("icon")
            priority_icon.setFixedWidth(30)
            priority_layout.addWidget(priority_icon)
            
            priority_label = QLabel(f"Priority: {priority_name}")
            priority_layout.addWidget(priority_label)
            priority_layout.addStretch()
            layout.addWidget(priority_frame)
        
        # Completed status with better contrast
        status_frame = QFrame()
        status_frame.setObjectName("detailsItem")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 10, 10, 10)
        
        status_icon = QLabel("✅" if self.activity.get('completed') else "⏳")
        status_icon.setObjectName("icon")
        status_icon.setFixedWidth(30)
        status_layout.addWidget(status_icon)
        
        status_label = QLabel(f"Status: {'Completed' if self.activity.get('completed') else 'Pending'}")
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        layout.addWidget(status_frame)
        
        layout.addStretch()
        
        # Add buttons for quick actions
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        if not self.activity.get('completed'):
            complete_btn = QPushButton("✓ Complete")
            complete_btn.setObjectName("primaryBtn")
            complete_btn.clicked.connect(self.markComplete)
            btn_layout.addWidget(complete_btn)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self.editActivity)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.clicked.connect(self.deleteActivity)
        btn_layout.addWidget(delete_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def markComplete(self):
        """Mark the activity as complete."""
        try:
            # First try direct parent
            if hasattr(self.parent_widget, 'onActivityCompleted'):
                self.parent_widget.onActivityCompleted(
                    self.activity.get('id'), 
                    True,  # Mark as completed
                    self.activity.get('type')
                )
                self.close()
                return
            
            # Then try unified activities widget
            if hasattr(self.parent_widget, 'activities_manager'):
                # Get activity date
                activity_date = self.activity.get('date')
                
                self.parent_widget.activities_manager.toggle_activity_completion(
                    self.activity.get('id'), 
                    True,
                    activity_date
                )
                self.parent_widget.refreshActivitiesList()
                self.close()
                return
                    
            # As a fallback, try to find the activities manager through any parent
            parent = self.parent_widget
            while parent:
                if hasattr(parent, 'onActivityCompleted'):
                    parent.onActivityCompleted(
                        self.activity.get('id'), 
                        True,  # Mark as completed
                        self.activity.get('type')
                    )
                    self.close()
                    break
                elif hasattr(parent, 'activities_manager'):
                    # Get activity date
                    activity_date = self.activity.get('date')
                    
                    parent.activities_manager.toggle_activity_completion(
                        self.activity.get('id'), 
                        True,
                        activity_date
                    )
                    if hasattr(parent, 'refreshActivitiesList'):
                        parent.refreshActivitiesList()
                    self.close()
                    break
                if hasattr(parent, 'parent'):
                    parent = parent.parent()
                else:
                    break
                    
        except Exception as e:
            print(f"Error marking activity complete: {e}")
            # At least close the dialog even if operation failed
            self.close()
    
    def editActivity(self):
        """Open the edit dialog for this activity."""
        try:
            # First try direct parent
            if hasattr(self.parent_widget, 'showEditActivityDialog'):
                self.parent_widget.showEditActivityDialog(self.activity.get('id'), self.activity.get('type'))
                self.close()
                return
                
            # As a fallback, try to find the edit method through any parent
            parent = self.parent_widget
            while parent:
                if hasattr(parent, 'showEditActivityDialog'):
                    parent.showEditActivityDialog(self.activity.get('id'), self.activity.get('type'))
                    self.close()
                    break
                if hasattr(parent, 'parent'):
                    parent = parent.parent()
                else:
                    break
                    
        except Exception as e:
            print(f"Error editing activity: {e}")
            # At least close the dialog even if operation failed
            self.close()
    
    def deleteActivity(self):
        """Delete this activity."""
        try:
            # First try direct parent
            if hasattr(self.parent_widget, 'deleteActivity'):
                self.parent_widget.deleteActivity(self.activity.get('id'), self.activity.get('type'))
                self.close()
                return
                
            # As a fallback, try to find the activities manager through any parent
            parent = self.parent_widget
            while parent:
                if hasattr(parent, 'deleteActivity'):
                    parent.deleteActivity(self.activity.get('id'), self.activity.get('type'))
                    self.close()
                    break
                elif hasattr(parent, 'activities_manager'):
                    parent.activities_manager.delete_activity(self.activity.get('id'))
                    if hasattr(parent, 'refreshActivitiesList'):
                        parent.refreshActivitiesList()
                    self.close()
                    break
                if hasattr(parent, 'parent'):
                    parent = parent.parent()
                else:
                    break
                    
        except Exception as e:
            print(f"Error deleting activity: {e}")
            # At least close the dialog even if operation failed
            self.close()


class UnifiedActivitiesWidget(QWidget):
    """A widget that unifies tasks, events, and habits into a single view."""
    
    # Signals
    activityAdded = pyqtSignal(dict)
    activityCompleted = pyqtSignal(int, bool, str)  # id, completed status, activity_type
    activityDeleted = pyqtSignal(int, str)  # id, type
    activityUpdated = pyqtSignal(int, str)  # id, type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store parent to access database
        
        # Initialize activities manager
        self.activities_manager = ActivitiesManager()
        if hasattr(parent, 'conn') and hasattr(parent, 'cursor'):
            self.activities_manager.set_connection(parent.conn, parent.cursor)
            # Create tables if they don't exist
            self.activities_manager.create_tables()
            # Migrate existing data if needed
            self.activities_manager.migrate_existing_data()
        
        # Activities data
        self.activities = []
        self.activity_widgets = {}
        
        # Current date
        self.current_date = QDate.currentDate()
        
        # Filter settings
        self.filter_settings = {
            'task': True,
            'event': True,
            'habit': True
        }
        
        # Setup UI
        self.setupUI()
        
        # Load initial data
        self.loadActivitiesFromDatabase()
    
    def setupUI(self):
        """Set up the UI components."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("activitiesHeader")
        header.setMinimumHeight(120)  # Reduced from 180
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(40, 20, 40, 20)  # Reduced from 60,30,60,30
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(16)  # Reduced from 24
        
        # Add activities icon
        activities_icon_label = QLabel()
        activities_icon = get_icon("calendar")
        if not activities_icon.isNull():
            activities_icon_label.setPixmap(activities_icon.pixmap(QSize(48, 48)))  # Reduced from 72x72
        else:
            # Fallback to emoji icon
            activities_icon_label.setText("📅")
            activities_icon_label.setFont(QFont("Arial", 28))  # Reduced from 36
        title_layout.addWidget(activities_icon_label)
        
        # Title layout - add vertical layout to include subtitle
        title_container = QVBoxLayout()
        
        # Title text
        title = QLabel("All Activities")
        title.setObjectName("activitiesTitle")
        font = QFont()
        font.setPointSize(24)  # Reduced from 32
        font.setBold(True)
        title.setFont(font)
        title_container.addWidget(title)
        
        # Add subtitle
        subtitle = QLabel("Activities are grouped by date")
        subtitle.setObjectName("activitiesSubtitle")
        subtitle.setStyleSheet("color: #6B7280; font-size: 14px;")
        title_container.addWidget(subtitle)
        
        title_layout.addLayout(title_container)
        
        header_layout.addLayout(title_layout)
        
        # Date display with navigation buttons and calendar shortcut
        date_layout = QHBoxLayout()
        
        # Previous day button
        self.prev_day_btn = QPushButton()
        prev_icon = get_icon("left-arrow")
        if not prev_icon.isNull():
            self.prev_day_btn.setIcon(prev_icon)
        else:
            self.prev_day_btn.setText("◀")
        self.prev_day_btn.setFixedSize(40, 40)
        self.prev_day_btn.setToolTip("Previous Day")
        self.prev_day_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_day_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        self.prev_day_btn.clicked.connect(self.previousDay)
        date_layout.addWidget(self.prev_day_btn)
        
        # Date label with calendar popup capability
        self.date_label = QLabel(QDate.currentDate().toString("Today: dddd, MMMM d, yyyy"))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setFont(QFont("Arial", 16))
        
        # Make the date label clickable to show calendar
        self.date_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.date_label.mousePressEvent = self.showDatePicker
        date_layout.addWidget(self.date_label)
        
        # Calendar icon button
        self.calendar_btn = QPushButton()
        calendar_icon = get_icon("calendar")
        if not calendar_icon.isNull():
            self.calendar_btn.setIcon(calendar_icon)
        else:
            self.calendar_btn.setText("📅")
        self.calendar_btn.setFixedSize(40, 40)
        self.calendar_btn.setToolTip("Select Date")
        self.calendar_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.calendar_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        self.calendar_btn.clicked.connect(self.showDatePicker)
        date_layout.addWidget(self.calendar_btn)
        
        # Next day button
        self.next_day_btn = QPushButton()
        next_icon = get_icon("right-arrow")
        if not next_icon.isNull():
            self.next_day_btn.setIcon(next_icon)
        else:
            self.next_day_btn.setText("▶")
        self.next_day_btn.setFixedSize(40, 40)
        self.next_day_btn.setToolTip("Next Day")
        self.next_day_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_day_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        self.next_day_btn.clicked.connect(self.nextDay)
        date_layout.addWidget(self.next_day_btn)
        
        header_layout.addLayout(date_layout)
        
        # Filter button
        self.filter_btn = QPushButton()
        self.filter_btn.setObjectName("filterButton")
        self.filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.filter_btn.setFixedSize(60, 60)  # Reduced from 100x100
        self.filter_btn.setToolTip("Filter Activities")
        
        # Add filter icon
        filter_icon = get_icon("filter")
        if not filter_icon.isNull():
            self.filter_btn.setIcon(filter_icon)
        else:
            # Use Unicode filter icon character as fallback
            self.filter_btn.setText("⚑")
            self.filter_btn.setFont(QFont("Arial", 24))  # Reduced from 32
            
        self.filter_btn.clicked.connect(self.showFilterMenu)
        header_layout.addWidget(self.filter_btn)
        
        # Add activity button
        self.add_btn = QPushButton("Add Activity")
        self.add_btn.setObjectName("addActivityButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setMinimumWidth(200)  # Reduced from 300
        self.add_btn.setMinimumHeight(60)  # Reduced from 90
        self.add_btn.setFont(QFont("Arial", 16))  # Reduced from 20
        self.add_btn.clicked.connect(self.showAddActivityDialog)
        
        # Add icon to button
        add_icon = get_icon("add")
        if not add_icon.isNull():
            self.add_btn.setIcon(add_icon)
        
        header_layout.addWidget(self.add_btn)
        
        self.main_layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("activitiesSeparator")
        separator.setFixedHeight(2)  # Reduced from 4
        self.main_layout.addWidget(separator)
        
        # Activities scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("activitiesScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container widget
        self.activities_container = QWidget()
        self.activities_container.setObjectName("activitiesContainer")
        
        # Layout for activities
        self.activities_layout = QVBoxLayout(self.activities_container)
        self.activities_layout.setContentsMargins(40, 30, 40, 30)  # Reduced from 60,45,60,45
        self.activities_layout.setSpacing(16)  # Further reduced spacing between activities
        self.activities_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Set container as scroll area widget
        self.scroll_area.setWidget(self.activities_container)
        
        # Empty state message
        self.empty_state = QLabel("No activities for this day")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.empty_state.setStyleSheet("color: #6B7280; margin-top: 60px; font-size: 18pt;")  # Reduced margin and font
        self.activities_layout.addWidget(self.empty_state)
        
        self.main_layout.addWidget(self.scroll_area)
        
        # Apply styles
        self.setStyleSheet("""
            #activitiesHeader {
                background-color: #FFFFFF;
                border-top-left-radius: 12px;  /* Increased from 8px */
                border-top-right-radius: 12px;  /* Increased from 8px */
            }
            #activitiesTitle {
                color: #111827;
            }
            #filterButton {
                background-color: #F3F4F6;
                border: 2px solid #E5E7EB;  /* Increased from 1px */
                border-radius: 12px;  /* Increased from 8px */
            }
            #filterButton:hover {
                background-color: #E5E7EB;
            }
            #addActivityButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 12px;  /* Increased from 6px */
                padding: 16px 32px;  /* Doubled from 8px 16px */
                font-weight: bold;
            }
            #addActivityButton:hover {
                background-color: #4338CA;
            }
            #addActivityButton:pressed {
                background-color: #3730A3;
            }
            #activitiesSeparator {
                background-color: #E5E7EB;
            }
            #activitiesScrollArea {
                background-color: #F9FAFB;
            }
            #activitiesContainer {
                background-color: #F9FAFB;
            }
            QScrollBar:vertical {
                border: none;
                background: #F9FAFB;
                width: 12px;  /* Increased from 8px */
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #D1D5DB;
                min-height: 45px;  /* Increased from 30px */
                border-radius: 6px;  /* Increased from 4px */
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
    
    def showDatePicker(self, event=None):
        """Show a date picker to select a specific date."""
        from PyQt6.QtWidgets import QDialog, QCalendarWidget, QVBoxLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Date")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        calendar = QCalendarWidget()
        calendar.setSelectedDate(self.current_date)
        calendar.setGridVisible(True)
        
        # Highlight current date
        calendar.setStyleSheet("""
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #F3F4F6;
            }
            QCalendarWidget QToolButton {
                color: #4F46E5;
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 5px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #E0E7FF;
                border: 1px solid #6366F1;
            }
            QCalendarWidget QMenu {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
            }
            QCalendarWidget QSpinBox {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                background-color: #FFFFFF;
                padding: 2px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: #FFFFFF;
                color: #1F2937;
                selection-background-color: #EEF2FF;
                selection-color: #4F46E5;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #D1D5DB;
            }
        """)
        
        layout.addWidget(calendar)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_date = calendar.selectedDate()
            self.changeDate(selected_date)
    
    def previousDay(self):
        """Navigate to the previous day."""
        new_date = self.current_date.addDays(-1)
        self.changeDate(new_date)
    
    def nextDay(self):
        """Navigate to the next day."""
        new_date = self.current_date.addDays(1)
        self.changeDate(new_date)
    
    def changeDate(self, new_date):
        """Change the current date and update the view."""
        # Update the current date
        self.current_date = new_date
        
        # Update the date label
        if self.current_date == QDate.currentDate():
            self.date_label.setText(f"Today: {self.current_date.toString('dddd, MMMM d, yyyy')}")
        else:
            self.date_label.setText(self.current_date.toString("dddd, MMMM d, yyyy"))
        
        # Refresh the activities list with the new date
        self.refreshActivitiesList()
        
        # Also refresh the weekly plan view if it exists
        if hasattr(self.parent, 'weekly_plan_view') and self.parent.weekly_plan_view:
            self.parent.weekly_plan_view.refresh()
    
    def scrollToDate(self, target_date):
        """Scroll the view to show activities for the target date."""
        # Convert date to string for comparison
        target_date_str = target_date.toString("yyyy-MM-dd")
        
        # Looking for a date header widget that matches our target date
        for i in range(self.activities_layout.count()):
            widget = self.activities_layout.itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text().strip():
                # Check if this is a date header
                if widget.styleSheet() and "background-color: #F3F4F6;" in widget.styleSheet():
                    # Parse the date from the header text (format: "dddd, MMMM d, yyyy")
                    header_text = widget.text()
                    try:
                        # Try to convert the date text to a QDate
                        header_date = QDate.fromString(header_text, "dddd, MMMM d, yyyy")
                        if header_date.isValid() and header_date.toString("yyyy-MM-dd") == target_date_str:
                            # Found the matching date header, scroll to it
                            self.scroll_area.ensureWidgetVisible(widget)
                            return
                    except:
                        continue
        
        # If we didn't find the date header, just scroll to top
        self.scroll_area.verticalScrollBar().setValue(0)
    
    def loadActivitiesFromDatabase(self):
        """Load all activities from the database."""
        if not hasattr(self, 'activities_manager'):
            return
            
        try:
            # Get all activities from the database
            self.activities = self.activities_manager.get_all_activities()
            
            # Update the current date label
            if self.current_date == QDate.currentDate():
                self.date_label.setText(f"Today: {self.current_date.toString('dddd, MMMM d, yyyy')}")
            else:
                self.date_label.setText(self.current_date.toString("dddd, MMMM d, yyyy"))
            
            # Refresh the activities list
            self.refreshActivitiesList()
        except Exception as e:
            print(f"Error loading activities: {e}")
    
    def refresh(self):
        """Refresh the activities list."""
        # Load all activities from the database
        self.loadActivitiesFromDatabase()
        
    def filterActivities(self, filter_type=None, filter_value=None):
        """Filter activities based on specified criteria.
        
        Args:
            filter_type: The type of filter to apply (e.g., 'date', 'type', 'category')
            filter_value: The value to filter by
            
        Returns:
            A filtered list of activities
        """
        if not self.activities:
            return []
            
        # Start with all activities
        filtered_activities = self.activities.copy()
        
        # Apply type filters from filter settings
        filtered_activities = [
            activity for activity in filtered_activities
            if self.filter_settings.get(activity.get('type', ''), True)
        ]
        
        # Apply additional filter if specified
        if filter_type and filter_value:
            if filter_type == 'date':
                # Filter by specific date
                date_str = filter_value
                if hasattr(filter_value, 'toString'):
                    date_str = filter_value.toString("yyyy-MM-dd")
                    
                filtered_activities = [
                    activity for activity in filtered_activities
                    if (hasattr(activity.get('date'), 'toString') and 
                        activity.get('date').toString("yyyy-MM-dd") == date_str) or
                       (isinstance(activity.get('date'), str) and 
                        activity.get('date') == date_str)
                ]
            elif filter_type == 'category':
                # Filter by category
                filtered_activities = [
                    activity for activity in filtered_activities
                    if activity.get('category') == filter_value
                ]
            elif filter_type == 'priority':
                # Filter by priority
                filtered_activities = [
                    activity for activity in filtered_activities
                    if activity.get('priority') == filter_value
                ]
                
        return filtered_activities
    
    def showAddActivityDialog(self):
        """Show the dialog to add a new activity."""
        dialog = ActivityAddEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            activity_data = dialog.getActivityData()
            self.addActivity(activity_data)
    
    def showEditActivityDialog(self, activity_id, activity_type):
        """Show the dialog to edit an existing activity."""
        # Check if this is a special action (duplicate or reschedule)
        if activity_type.startswith("duplicate_"):
            original_type = activity_type.replace("duplicate_", "")
            self.duplicateActivity(activity_id, original_type)
            return
        elif activity_type.startswith("reschedule_"):
            original_type = activity_type.replace("reschedule_", "")
            self.rescheduleActivity(activity_id, original_type)
            return
        elif activity_type == "delete_today_habit":
            self.deleteHabitForToday(activity_id)
            return
        
        # Find the activity in our list
        activity_data = None
        for activity in self.activities:
            if activity.get('id') == activity_id and activity.get('type') == activity_type:
                activity_data = activity
                break
        
        if activity_data:
            dialog = ActivityAddEditDialog(self, activity_data, edit_mode=True)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.getActivityData()
                self.updateActivity(activity_id, activity_type, updated_data)
                
                # If this is an event, make sure the calendar is updated
                if activity_type == 'event':
                    self.syncWithCalendar()
                    
    def duplicateActivity(self, activity_id, activity_type):
        """Duplicate an existing activity."""
        # Find the activity to duplicate
        original_activity = None
        for activity in self.activities:
            if activity.get('id') == activity_id and activity.get('type') == activity_type:
                original_activity = activity
                break
                
        if not original_activity:
            return
            
        # Create a copy of the activity data
        new_activity = original_activity.copy()
        
        # Remove the ID so a new one will be generated
        if 'id' in new_activity:
            del new_activity['id']
            
        # Set title to indicate it's a copy
        new_activity['title'] = f"{original_activity.get('title', '')} (Copy)"
        
        # Set completed to False for the new copy
        new_activity['completed'] = False
        
        # Open the edit dialog with the duplicated data
        dialog = ActivityAddEditDialog(self, new_activity, edit_mode=False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            activity_data = dialog.getActivityData()
            self.addActivity(activity_data)
            
    def rescheduleActivity(self, activity_id, activity_type):
        """Reschedule an existing activity to a different date."""
        # Find the activity to reschedule
        activity_data = None
        for activity in self.activities:
            if activity.get('id') == activity_id and activity.get('type') == activity_type:
                activity_data = activity
                break
                
        if not activity_data:
            return
            
        # Create a reschedule dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Reschedule {activity_type.capitalize()}")
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        
        # Add info about what's being rescheduled
        title_label = QLabel(f"Reschedule: {activity_data.get('title', '')}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Current date display
        current_date = activity_data.get('date')
        if hasattr(current_date, 'toString'):
            current_date_str = current_date.toString("yyyy-MM-dd")
        else:
            current_date_str = current_date
            
        current_date_label = QLabel(f"Current date: {current_date_str}")
        layout.addWidget(current_date_label)
        
        # New date selector
        date_layout = QHBoxLayout()
        date_label = QLabel("New date:")
        date_layout.addWidget(date_label)
        
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        
        # Set default to current date of the activity
        if hasattr(current_date, 'toString'):
            date_edit.setDate(current_date)
        else:
            try:
                date_edit.setDate(QDate.fromString(current_date, "yyyy-MM-dd"))
            except:
                date_edit.setDate(QDate.currentDate())
                
        date_layout.addWidget(date_edit)
        layout.addLayout(date_layout)
        
        # Update time checkboxes
        update_times_check = QCheckBox("Update times")
        update_times_check.setChecked(False)
        layout.addWidget(update_times_check)
        
        # Time container that will be shown/hidden
        time_container = QWidget()
        time_layout = QVBoxLayout(time_container)
        
        # Time fields
        start_time_layout = QHBoxLayout()
        start_time_label = QLabel("Start time:")
        start_time_layout.addWidget(start_time_label)
        
        start_time_edit = QTimeEdit()
        start_time = activity_data.get('start_time')
        if isinstance(start_time, QTime):
            start_time_edit.setTime(start_time)
        elif isinstance(start_time, str) and ':' in start_time:
            start_time_edit.setTime(QTime.fromString(start_time, "HH:mm"))
        else:
            start_time_edit.setTime(QTime.currentTime())
            
        start_time_layout.addWidget(start_time_edit)
        time_layout.addLayout(start_time_layout)
        
        # End time
        end_time_layout = QHBoxLayout()
        end_time_label = QLabel("End time:")
        end_time_layout.addWidget(end_time_label)
        
        end_time_edit = QTimeEdit()
        end_time = activity_data.get('end_time')
        if isinstance(end_time, QTime):
            end_time_edit.setTime(end_time)
        elif isinstance(end_time, str) and ':' in end_time:
            end_time_edit.setTime(QTime.fromString(end_time, "HH:mm"))
        else:
            end_time_edit.setTime(QTime.currentTime().addSecs(3600))  # Default to 1 hour later
            
        end_time_layout.addWidget(end_time_edit)
        time_layout.addLayout(end_time_layout)
        
        # Initially hide time container
        time_container.setVisible(False)
        update_times_check.toggled.connect(time_container.setVisible)
        
        layout.addWidget(time_container)
        
        # Option for recurring activities
        if activity_type == 'habit':
            recurring_check = QCheckBox("Update all occurrences")
            recurring_check.setChecked(False)
            layout.addWidget(recurring_check)
            
            # Warning about updating all occurrences
            warning_label = QLabel("Note: Updating all occurrences will change the schedule for this habit on all days.")
            warning_label.setStyleSheet("color: #EF4444; font-size: 12px;")
            warning_label.setWordWrap(True)
            layout.addWidget(warning_label)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show the dialog and process result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the new date
            new_date = date_edit.date()
            
            # Create updated data
            updated_data = {}
            updated_data['date'] = new_date
            
            # Update times if requested
            if update_times_check.isChecked():
                updated_data['start_time'] = start_time_edit.time()
                updated_data['end_time'] = end_time_edit.time()
            
            # Update the activity
            self.updateActivity(activity_id, activity_type, updated_data)
            
            # If this is an event, make sure the calendar is updated
            if activity_type == 'event':
                self.syncWithCalendar()
    
    def addActivity(self, activity_data):
        """Add a new activity to the database and list."""
        if not hasattr(self, 'activities_manager'):
            return
            
        try:
            # Add to database
            activity_id = self.activities_manager.add_activity(activity_data)
            
            if activity_id:
                # Add ID to the data and append to our list
                activity_data['id'] = activity_id
                self.activities.append(activity_data)
                
                # Refresh the UI
                self.refreshActivitiesList()
                
                # Sync with calendar if this is an event
                if activity_data['type'] == 'event':
                    self.syncWithCalendar()
                
                # Emit a signal that activity was added (if applicable)
                if hasattr(self, 'activityAdded'):
                    self.activityAdded.emit(activity_id, activity_data['type'])
                    
        except Exception as e:
            print(f"Error adding activity: {e}")
    
    def updateActivity(self, activity_id, activity_type, updated_data):
        """Update an existing activity in the database and list."""
        if not hasattr(self, 'activities_manager'):
            return
            
        try:
            # Update in database
            success = self.activities_manager.update_activity(activity_id, updated_data)
            
            if success:
                # Update in our list
                for i, activity in enumerate(self.activities):
                    if activity['id'] == activity_id and activity['type'] == activity_type:
                        # Create a new dictionary with updated values
                        updated_activity = activity.copy()
                        updated_activity.update(updated_data)
                        self.activities[i] = updated_activity
                        break
                
                # Refresh the UI
                self.refreshActivitiesList()
                
                # Sync with calendar if this is an event and main window has a dashboard calendar
                if activity_type == 'event':
                    self.syncWithCalendar()
                            
                # Emit a signal that activity was updated (if applicable)
                if hasattr(self, 'activityUpdated'):
                    self.activityUpdated.emit(activity_id, activity_type)
                            
        except Exception as e:
            print(f"Error updating activity: {e}")
    
    def deleteActivity(self, activity_id, activity_type):
        """Delete an activity from the database and list."""
        if not hasattr(self, 'activities_manager'):
            return
            
        try:
            # Delete from database
            success = self.activities_manager.delete_activity(activity_id)
            
            if success:
                # Remove from our list
                self.activities = [a for a in self.activities if not (a['id'] == activity_id)]
                
                # Remove widget if it exists
                widget_key = f"{activity_type}_{activity_id}"
                if widget_key in self.activity_widgets:
                    widget = self.activity_widgets[widget_key]
                    self.activities_layout.removeWidget(widget)
                    widget.deleteLater()
                    del self.activity_widgets[widget_key]
                
                # Refresh the UI
                self.refreshActivitiesList()
                
                # Sync with calendar if this is an event and main window has a dashboard calendar
                if activity_type == 'event':
                    parent = self.parent
                    if parent and hasattr(parent, 'dashboard_calendar') and hasattr(parent, 'activities_manager'):
                        try:
                            parent.dashboard_calendar.sync_with_activities(parent.activities_manager)
                        except Exception as e:
                            print(f"Error syncing calendar after event deletion: {e}")
                
                # Emit the signal
                self.activityDeleted.emit(activity_id, activity_type)
        except Exception as e:
            print(f"Error deleting activity: {e}")
            # At least close the dialog even if operation failed
            self.close()
    
    def onActivityCompleted(self, activity_id, completed, activity_type):
        """Mark an activity as completed or not completed."""
        if not hasattr(self, 'activities_manager'):
            return
            
        # Find the activity in our list
        for i, activity in enumerate(self.activities):
            if activity.get('id') == activity_id and activity.get('type') == activity_type:
                # Use the provided completion status
                new_status = completed
                
                # Get the current date for the completion
                current_date = self.current_date
                
                # Toggle completion in the database for this specific date
                success = self.activities_manager.toggle_activity_completion(
                    activity_id, 
                    new_status,
                    current_date
                )
                
                if success:
                    # Update our local data
                    activity['completed'] = new_status
                    
                    # Refresh the UI
                    self.refreshActivitiesList()
                    
                    # If this is an event, make sure the calendar is updated
                    if activity_type == 'event':
                        self.syncWithCalendar()
                    
                    # Also refresh the weekly plan view if it exists
                    if hasattr(self.parent, 'weekly_plan_view') and self.parent.weekly_plan_view:
                        self.parent.weekly_plan_view.refresh()
                    
                    # Emit a signal that activity was completed (if applicable)
                    if hasattr(self, 'activityCompleted'):
                        # Make sure to pass the correct types (int, bool, str)
                        self.activityCompleted.emit(int(activity_id), bool(new_status), str(activity_type))
                        
                break
    
    def refreshActivitiesList(self):
        """Refresh the list of activities for the current date."""
        # Save a reference to the empty state before clearing
        if hasattr(self, 'empty_state'):
            # Remove from layout without deleting
            self.activities_layout.removeWidget(self.empty_state)
            # Keep it alive by setting its parent to self
            self.empty_state.setParent(self)
            self.empty_state.hide()
            
        # Clear existing widgets
        for widget in self.activity_widgets.values():
            self.activities_layout.removeWidget(widget)
            widget.deleteLater()
        self.activity_widgets.clear()
        
        # Clear any other widgets from the layout
        while self.activities_layout.count():
            item = self.activities_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Filter activities by type and current date
        filtered_activities = []
        current_date_str = self.current_date.toString("yyyy-MM-dd")
        current_day_name = self.current_date.toString("dddd")  # e.g., "Monday"
        
        for activity in self.activities:
            # First check if the activity type is enabled in filters
            if not self.filter_settings.get(activity['type'], True):
                continue
            
            # Special handling for habits - check days of week
            if activity['type'] == 'habit' and 'days_of_week' in activity:
                days_of_week = activity.get('days_of_week', '')
                if days_of_week and current_day_name in days_of_week.split(','):
                    filtered_activities.append(activity)
                    continue
            
            # Regular date comparison for tasks and events
            activity_date = activity.get('date')
            if activity_date:
                # Handle QDate objects
                if hasattr(activity_date, 'toString'):
                    activity_date_str = activity_date.toString("yyyy-MM-dd")
                # Handle string dates
                elif isinstance(activity_date, str):
                    # Try to convert to QDate for proper comparison
                    try:
                        qdate = QDate.fromString(activity_date, "yyyy-MM-dd")
                        if qdate.isValid():
                            activity_date_str = activity_date
                        else:
                            # Skip invalid dates
                            continue
                    except:
                        activity_date_str = activity_date
                else:
                    # Skip if date format is unknown
                    continue
                    
                # Check if date matches current date
                if activity_date_str == current_date_str:
                    filtered_activities.append(activity)
        
        # Sort by time
        filtered_activities.sort(key=lambda x: (
            x.get('start_time').toString("HH:mm") if hasattr(x.get('start_time'), 'toString') else str(x.get('start_time'))
        ))
        
        # Make sure empty state exists
        if not hasattr(self, 'empty_state') or self.empty_state is None:
            self.empty_state = QLabel(f"No activities found for {self.current_date.toString('MMMM d, yyyy')}")
            self.empty_state.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.empty_state.setStyleSheet("color: #6B7280; margin-top: 60px; font-size: 18pt;")
        
        # Add empty state if needed
        if len(filtered_activities) == 0:
            self.empty_state.setText(f"No activities found for {self.current_date.toString('MMMM d, yyyy')}")
            self.empty_state.setParent(self.activities_container)
            self.activities_layout.addWidget(self.empty_state)
            self.empty_state.show()
        else:
            # Add a date header for the current date
            date_header_str = self.current_date.toString("dddd, MMMM d, yyyy")
            date_header = QLabel(date_header_str)
            date_header.setStyleSheet("""
                font-weight: bold;
                font-size: 16px;
                color: #4B5563;
                padding: 10px 5px;
                background-color: #F3F4F6;
                border-radius: 4px;
                margin-top: 10px;
            """)
            self.activities_layout.addWidget(date_header)
            
            # Add each activity widget
            for activity in filtered_activities:
                self.addActivityWidget(activity)
        
        # Force layout update
        self.activities_container.updateGeometry()
    
    def addActivityWidget(self, activity):
        """Add an activity widget to the list."""
        try:
            # Create a listwidget item
            activity_id = activity.get('id')
            activity_title = activity.get('title', activity.get('description', 'Untitled'))
            activity_type = activity.get('type', 'task')
            
            # Process start and end times
            start_time = activity.get('start_time', '')
            end_time = activity.get('end_time', '')
            
            if isinstance(start_time, str) and start_time:
                # Assume format is "HH:MM"
                start_time_display = start_time
            elif hasattr(start_time, 'toString'):
                start_time_display = start_time.toString('HH:mm')
            else:
                start_time_display = ''
                
            if isinstance(end_time, str) and end_time:
                end_time_display = end_time
            elif hasattr(end_time, 'toString'):
                end_time_display = end_time.toString('HH:mm')
            else:
                end_time_display = ''
            
            # Other activity properties
            priority = activity.get('priority', 0)  # Default to low priority
            category = activity.get('category', None)
            completed = activity.get('completed', False)
            color = activity.get('color', None)
            
            # Create the activity widget
            widget = ActivityItemWidget(
                activity_id=activity_id,
                title=activity_title,
                start_time=start_time_display,
                end_time=end_time_display,
                activity_type=activity_type,
                priority=priority,
                category=category,
                completed=completed,
                color=color,
                parent=self.activities_container
            )
            
            # Connect signals for activity actions
            widget.activityCompleted.connect(self.onActivityCompleted)
            widget.activityDeleted.connect(self.deleteActivity)
            widget.activityEdited.connect(lambda id, type: self.showEditActivityDialog(id, type))
            widget.activityClicked.connect(lambda data: self.showActivityDetails(data))
            
            # Add to layout
            self.activities_layout.addWidget(widget)
            
            # Store a reference to the widget by ID
            self.activity_widgets[activity_id] = widget
            
        except Exception as e:
            print(f"Error adding activity widget: {e}")

    def showActivityDetails(self, activity_data):
        """Show activity details dialog when an activity is clicked."""
        try:
            dialog = ActivityDetailsDialog(activity_data, self)
            dialog.show()
        except Exception as e:
            print(f"Error showing activity details: {e}")
    
    def saveChanges(self):
        """Save any pending changes to the database."""
        if hasattr(self, 'activities_manager') and hasattr(self.activities_manager, 'conn'):
            try:
                # Ensure all changes are committed
                self.activities_manager.conn.commit()
                print("Activities saved successfully")
            except Exception as e:
                print(f"Error saving activities: {e}")
                
    def closeEvent(self, event):
        """Handle the widget close event."""
        self.saveChanges()
        super().closeEvent(event)
    
    def syncWithCalendar(self):
        """Sync events with the dashboard calendar if it exists.
        This is called when an event is added, updated, or deleted."""
        parent = self.parent
        if parent and hasattr(parent, 'dashboard_calendar') and hasattr(parent, 'activities_manager'):
            try:
                parent.dashboard_calendar.sync_with_activities(parent.activities_manager)
            except Exception as e:
                print(f"Error syncing with calendar: {e}")
                
    def showAddActivityDialog(self, activity_type=None):
        """Show the dialog to add a new activity."""
        dialog = ActivityAddEditDialog(self)
        
        # If a type was specified, set it in the dialog
        if activity_type:
            type_index = dialog.type_combo.findText(activity_type.capitalize())
            if type_index >= 0:
                dialog.type_combo.setCurrentIndex(type_index)
                
        if dialog.exec() == QDialog.DialogCode.Accepted:
            activity_data = dialog.getActivityData()
            self.addActivity(activity_data)
            
    def showEditActivityDialog(self, activity_id, activity_type):
        """Show the dialog to edit an existing activity."""
        # Check if this is a special action (duplicate or reschedule)
        if activity_type.startswith("duplicate_"):
            original_type = activity_type.replace("duplicate_", "")
            self.duplicateActivity(activity_id, original_type)
            return
        elif activity_type.startswith("reschedule_"):
            original_type = activity_type.replace("reschedule_", "")
            self.rescheduleActivity(activity_id, original_type)
            return
        elif activity_type == "delete_today_habit":
            self.deleteHabitForToday(activity_id)
            return
        
        # Find the activity in our list
        activity_data = None
        for activity in self.activities:
            if activity.get('id') == activity_id and activity.get('type') == activity_type:
                activity_data = activity
                break
        
        if activity_data:
            dialog = ActivityAddEditDialog(self, activity_data, edit_mode=True)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.getActivityData()
                self.updateActivity(activity_id, activity_type, updated_data)
                
                # If this is an event, make sure the calendar is updated
                if activity_type == 'event':
                    self.syncWithCalendar()
                    
    def deleteHabitForToday(self, habit_id):
        """Remove a habit for the current day only by modifying its days_of_week property."""
        # Find the habit in our list
        habit = None
        for activity in self.activities:
            if activity.get('id') == habit_id and activity.get('type') == 'habit':
                habit = activity
                break
                
        if not habit:
            return
            
        # Get the current day name
        current_day_name = self.current_date.toString("dddd")  # e.g., "Monday"
        
        # Get the current days of the week for this habit
        days_of_week = habit.get('days_of_week', '')
        
        if not days_of_week:
            return
            
        # Convert to list, remove the current day, and convert back to string
        days_list = days_of_week.split(',')
        
        # Check if current day exists in the list
        if current_day_name in days_list:
            days_list.remove(current_day_name)
            
            # Create updated data with the new days_of_week
            updated_data = {
                'days_of_week': ','.join(days_list)
            }
            
            # Update the habit in the database
            success = self.activities_manager.update_activity(habit_id, updated_data)
            
            if success:
                # Update in our list
                habit['days_of_week'] = ','.join(days_list)
                
                # Refresh the UI
                self.refreshActivitiesList()
                
                # Show confirmation message
                QMessageBox.information(
                    self,
                    "Habit Removed for Today",
                    f"This habit will no longer appear on {current_day_name}s."
                )
        else:
            # If the habit is not set for the current day, it might be a one-time habit for this specific date
            # Check if the habit date matches the current date
            habit_date = habit.get('date')
            if hasattr(habit_date, 'toString'):
                habit_date_str = habit_date.toString("yyyy-MM-dd")
            else:
                habit_date_str = habit_date
                
            current_date_str = self.current_date.toString("yyyy-MM-dd")
            
            if habit_date_str == current_date_str:
                # Create a future date (e.g., 100 years in the future) to effectively hide it
                future_date = QDate.currentDate().addDays(36500)  # ~100 years
                
                # Update the habit date
                updated_data = {
                    'date': future_date
                }
                
                # Update the habit in the database
                success = self.activities_manager.update_activity(habit_id, updated_data)
                
                if success:
                    # Update in our list
                    habit['date'] = future_date
                    
                    # Refresh the UI
                    self.refreshActivitiesList()
                    
                    # Show confirmation message
                    QMessageBox.information(
                        self,
                        "Habit Removed for Today",
                        "This one-time habit has been removed from today."
                    )
            else:
                # The habit is not scheduled for today
                QMessageBox.information(
                    self,
                    "No Change Needed",
                    f"This habit is not scheduled for {current_day_name}s or today specifically."
                )
    
    def showAddTaskDialog(self):
        """Add a task (compatibility with the original interface)."""
        dialog = ActivityAddEditDialog(self)
        dialog.type_combo.setCurrentText("Task")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            activity_data = dialog.getActivityData()
            self.addActivity(activity_data)
    
    def showFilterMenu(self):
        """Show the filter menu for activities."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 25px 6px 6px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
            QMenu::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        
        # Get counts for each type for the menu
        task_count = sum(1 for a in self.activities if a['type'] == 'task')
        event_count = sum(1 for a in self.activities if a['type'] == 'event')
        habit_count = sum(1 for a in self.activities if a['type'] == 'habit')
        
        # Create checkable actions for each activity type with counts
        task_action = QAction(f"Tasks ({task_count})", self)
        task_action.setCheckable(True)
        task_action.setChecked(self.filter_settings['task'])
        
        event_action = QAction(f"Events ({event_count})", self)
        event_action.setCheckable(True)
        event_action.setChecked(self.filter_settings['event'])
        
        habit_action = QAction(f"Habits ({habit_count})", self)
        habit_action.setCheckable(True)
        habit_action.setChecked(self.filter_settings['habit'])
        
        # Add actions to menu
        menu.addAction(task_action)
        menu.addAction(event_action)
        menu.addAction(habit_action)
        
        # Add separator
        menu.addSeparator()
        
        # Add "Show All" and "Hide All" actions
        show_all_action = QAction("Show All", self)
        hide_all_action = QAction("Hide All", self)
        
        menu.addAction(show_all_action)
        menu.addAction(hide_all_action)
        
        # Connect actions to handlers
        task_action.triggered.connect(lambda checked: self.updateFilter('task', checked))
        event_action.triggered.connect(lambda checked: self.updateFilter('event', checked))
        habit_action.triggered.connect(lambda checked: self.updateFilter('habit', checked))
        show_all_action.triggered.connect(self.showAllTypes)
        hide_all_action.triggered.connect(self.hideAllTypes)
        
        # Show menu at button position
        menu.exec(self.filter_btn.mapToGlobal(QPoint(0, self.filter_btn.height())))
    
    def updateFilter(self, activity_type, show):
        """Update filter settings for a specific activity type."""
        self.filter_settings[activity_type] = show
        self.updateFilterButtonState()
        self.refreshActivitiesList()
    
    def showAllTypes(self):
        """Show all activity types."""
        for activity_type in self.filter_settings:
            self.filter_settings[activity_type] = True
        self.updateFilterButtonState()
        self.refreshActivitiesList()
    
    def hideAllTypes(self):
        """Hide all activity types."""
        for activity_type in self.filter_settings:
            self.filter_settings[activity_type] = False
        self.updateFilterButtonState()
        self.refreshActivitiesList()
    
    def updateFilterButtonState(self):
        """Update the filter button appearance based on current filter state."""
        # Check if any filters are active (not all types are shown)
        all_showing = all(self.filter_settings.values())
        any_showing = any(self.filter_settings.values())
        
        if all_showing:
            # All types are showing - regular state
            self.filter_btn.setStyleSheet("""
                background-color: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            """)
        elif not any_showing:
            # No types are showing - error state
            self.filter_btn.setStyleSheet("""
                background-color: #FEE2E2;
                border: 1px solid #EF4444;
                border-radius: 8px;
            """)
        else:
            # Some types are showing - active filter state
            self.filter_btn.setStyleSheet("""
                background-color: #E0E7FF;
                border: 1px solid #6366F1;
                border-radius: 8px;
            """)