from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QLabel, QHBoxLayout, QPushButton, 
                              QFrame, QDialog, QLineEdit, QDateEdit, QComboBox, QDialogButtonBox, QTimeEdit,
                              QListWidget, QListWidgetItem, QSizePolicy, QCheckBox, QButtonGroup, QMenu,
                              QGraphicsDropShadowEffect, QColorDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime, QSize, QPoint
from PyQt6.QtGui import QIcon, QFont, QColor, QAction
from datetime import datetime

from app.resources import get_icon
from app.models.activities_manager import ActivitiesManager

class ActivityItemWidget(QWidget):
    """A unified widget for displaying activities (events, tasks, habits)."""
    
    # Signals
    activityCompleted = pyqtSignal(int, bool, str)  # id, completed, type
    activityDeleted = pyqtSignal(int, str)  # id, type
    activityEdited = pyqtSignal(int, str)  # id, type
    
    def __init__(self, activity_id, title, start_time, end_time, activity_type, 
                 priority=0, category=None, completed=False, color=None, parent=None):
        super().__init__(parent)
        
        # Store activity data
        self.activity_id = activity_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.activity_type = activity_type  # 'task', 'event', or 'habit'
        self.priority = priority
        self.category = category
        self.completed = completed
        self.custom_color = color  # Store custom color
        
        # Configure widget
        self.setObjectName("activityWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Set up the UI
        self.setupUI()
        
        # Apply shadow effect
        self.applyShadowEffect()
    
    def setupUI(self):
        """Set up the UI components of the activity widget."""
        
        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 8, 10, 8)
        self.main_layout.setSpacing(8)
        
        # Checkbox for completion status
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.completed)
        self.checkbox.setObjectName("activityCheckbox")
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.toggled.connect(self.onCompletionToggled)
        self.main_layout.addWidget(self.checkbox)
        
        # Activity type icon
        self.type_icon_label = QLabel()
        self.type_icon_label.setFixedSize(16, 16)
        
        # Set icon based on activity type
        if self.activity_type == 'task':
            task_icon = get_icon("task")
            if not task_icon.isNull():
                self.type_icon_label.setPixmap(task_icon.pixmap(QSize(16, 16)))
            else:
                # Fallback to emoji
                self.type_icon_label.setText("✓")
                self.type_icon_label.setStyleSheet("color: #F87171; font-weight: bold;")
        elif self.activity_type == 'event':
            event_icon = get_icon("event")
            if not event_icon.isNull():
                self.type_icon_label.setPixmap(event_icon.pixmap(QSize(16, 16)))
            else:
                # Fallback to emoji
                self.type_icon_label.setText("📅")
                self.type_icon_label.setStyleSheet("color: #818CF8;")
        elif self.activity_type == 'habit':
            habit_icon = get_icon("habit")
            if not habit_icon.isNull():
                self.type_icon_label.setPixmap(habit_icon.pixmap(QSize(16, 16)))
            else:
                # Fallback to emoji
                self.type_icon_label.setText("↻")
                self.type_icon_label.setStyleSheet("color: #34D399; font-weight: bold;")
                
        self.main_layout.addWidget(self.type_icon_label)
        
        # Container for all text information
        self.text_container = QVBoxLayout()
        self.text_container.setSpacing(2)
        
        # Activity title
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("activityTitle")
        font = QFont()
        font.setPointSize(10)
        if self.completed:
            self.title_label.setStyleSheet("text-decoration: line-through; color: #6B7280;")
        else:
            font.setBold(True)
            self.title_label.setFont(font)
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
        self.details_label.setStyleSheet("color: #6B7280; font-size: 9pt;")
        self.text_container.addWidget(self.details_label)
        
        self.main_layout.addLayout(self.text_container)
        
        # Priority indicator (for tasks)
        if self.activity_type == 'task':
            self.priority_indicator = QWidget()
            self.priority_indicator.setFixedSize(12, 12)
            self.priority_indicator.setObjectName("priorityIndicator")
            
            if self.priority == 0:  # Low
                self.priority_indicator.setStyleSheet("""
                    background-color: #10B981;
                    border-radius: 6px;
                """)
            elif self.priority == 1:  # Medium
                self.priority_indicator.setStyleSheet("""
                    background-color: #F59E0B;
                    border-radius: 6px;
                """)
            elif self.priority == 2:  # High
                self.priority_indicator.setStyleSheet("""
                    background-color: #EF4444;
                    border-radius: 6px;
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
        self.actions_btn.setFixedSize(24, 24)
        self.actions_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.actions_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
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
                }
                #activityWidget:hover {
                    border: 1px solid #D1D5DB;
                    background-color: #F9FAFB;
                }
            """)
            
            # Add type-specific styling or use custom color if available
            if self.custom_color:
                self.setStyleSheet(self.styleSheet() + f"""
                    #activityWidget {{
                        border-left: 4px solid {self.custom_color};
                    }}
                """)
            else:
                # Fallback to default colors if no custom color is provided
                if self.activity_type == 'event':
                    self.setStyleSheet(self.styleSheet() + """
                        #activityWidget {
                            border-left: 4px solid #818CF8;
                        }
                    """)
                elif self.activity_type == 'habit':
                    self.setStyleSheet(self.styleSheet() + """
                        #activityWidget {
                            border-left: 4px solid #34D399;
                        }
                    """)
                elif self.activity_type == 'task':
                    self.setStyleSheet(self.styleSheet() + """
                        #activityWidget {
                            border-left: 4px solid #F87171;
                        }
                    """)
    
    def onCompletionToggled(self, checked):
        """Handle activity completion toggling."""
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
        
        # Update widget style
        self.updateStyle()
        
        # Emit signal
        self.activityCompleted.emit(self.activity_id, checked, self.activity_type)
    
    def showActionsMenu(self):
        """Show the actions menu for the activity."""
        menu = QMenu(self)
        
        # Add icons to the menu actions
        edit_action = menu.addAction(f"Edit {self.activity_type.capitalize()}")
        edit_icon = get_icon("edit")
        if not edit_icon.isNull():
            edit_action.setIcon(edit_icon)
            
        delete_action = menu.addAction(f"Delete {self.activity_type.capitalize()}")
        delete_icon = get_icon("delete")
        if not delete_icon.isNull():
            delete_action.setIcon(delete_icon)
        
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
        """)
        
        # Show menu at button position
        action = menu.exec(self.actions_btn.mapToGlobal(QPoint(0, self.actions_btn.height())))
        
        if action == edit_action:
            self.activityEdited.emit(self.activity_id, self.activity_type)
        elif action == delete_action:
            self.activityDeleted.emit(self.activity_id, self.activity_type)
    
    def applyShadowEffect(self):
        """Apply shadow effect to the widget."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


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
                for day in days:
                    if day.startswith(day_abbr):
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
                    selected_days.append(day_abbr)
            data['days_of_week'] = ','.join(selected_days)
        
        return data


class UnifiedActivitiesWidget(QWidget):
    """A widget that unifies tasks, events, and habits into a single view."""
    
    # Signals
    activityAdded = pyqtSignal(dict)
    activityCompleted = pyqtSignal(int, bool, str)  # id, completed, type
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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("activitiesHeader")
        header.setMinimumHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        # Add activities icon
        activities_icon_label = QLabel()
        activities_icon = get_icon("calendar")  # or use any appropriate icon
        if not activities_icon.isNull():
            activities_icon_label.setPixmap(activities_icon.pixmap(QSize(24, 24)))
        else:
            # Fallback to emoji icon
            activities_icon_label.setText("📅")
            activities_icon_label.setFont(QFont("Arial", 14))
        title_layout.addWidget(activities_icon_label)
        
        # Title text
        title = QLabel("My Activities")
        title.setObjectName("activitiesTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        title_layout.addWidget(title)
        
        header_layout.addLayout(title_layout)
        
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
        
        # Filter button
        self.filter_btn = QPushButton()
        self.filter_btn.setObjectName("filterButton")
        self.filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.filter_btn.setFixedSize(40, 40)
        self.filter_btn.setToolTip("Filter Activities")
        
        # Add filter icon
        filter_icon = get_icon("filter")
        if not filter_icon.isNull():
            self.filter_btn.setIcon(filter_icon)
        else:
            # Use Unicode filter icon character as fallback
            self.filter_btn.setText("⚑")
            self.filter_btn.setFont(QFont("Arial", 14))
            
        self.filter_btn.clicked.connect(self.showFilterMenu)
        header_layout.addWidget(self.filter_btn)
        
        # Add activity button
        self.add_btn = QPushButton("Add Activity")
        self.add_btn.setObjectName("addActivityButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setMinimumWidth(120)
        self.add_btn.clicked.connect(self.showAddActivityDialog)
        
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
        separator.setObjectName("activitiesSeparator")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
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
        self.activities_layout.setContentsMargins(20, 15, 20, 15)
        self.activities_layout.setSpacing(12)
        self.activities_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Set container as scroll area widget
        self.scroll_area.setWidget(self.activities_container)
        
        # Empty state message
        self.empty_state = QLabel("No activities for this day")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.empty_state.setStyleSheet("color: #6B7280; margin-top: 20px;")
        self.activities_layout.addWidget(self.empty_state)
        
        main_layout.addWidget(self.scroll_area)
        
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
            #filterButton {
                background-color: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
            #filterButton:hover {
                background-color: #E5E7EB;
            }
            #addActivityButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
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
    
    def loadActivitiesFromDatabase(self):
        """Load activities from the database for the current date."""
        if not hasattr(self, 'activities_manager'):
            return
            
        try:
            # Get activities for current date
            self.activities = self.activities_manager.get_activities_for_date(self.current_date)
            self.refreshActivitiesList()
        except Exception as e:
            print(f"Error loading activities: {e}")
    
    def showAddActivityDialog(self):
        """Show the dialog to add a new activity."""
        dialog = ActivityAddEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            activity_data = dialog.getActivityData()
            self.addActivity(activity_data)
    
    def showEditActivityDialog(self, activity_id, activity_type):
        """Show the dialog to edit an existing activity."""
        # Find the activity in our list
        activity_data = None
        for activity in self.activities:
            if activity['id'] == activity_id and activity['type'] == activity_type:
                activity_data = activity
                break
        
        if activity_data:
            dialog = ActivityAddEditDialog(self, activity_data, edit_mode=True)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.getActivityData()
                self.updateActivity(activity_id, activity_type, updated_data)
    
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
    
    def onActivityCompleted(self, activity_id, activity_type):
        """Mark an activity as completed or not completed."""
        if not hasattr(self, 'activities_manager'):
            return
            
        # Find the activity in our list
        for i, activity in enumerate(self.activities):
            if activity.get('id') == activity_id and activity.get('type') == activity_type:
                # Toggle the completed status
                new_status = not activity.get('completed', False)
                
                # Update in database
                update_data = {'completed': new_status}
                if new_status:
                    update_data['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                else:
                    update_data['completed_at'] = None
                    
                success = self.activities_manager.update_activity(activity_id, update_data)
                
                if success:
                    # Update our local data
                    self.activities[i].update(update_data)
                    
                    # Refresh the UI
                    self.refreshActivitiesList()
                    
                    # If this is an event, make sure the calendar is updated
                    if activity_type == 'event':
                        self.syncWithCalendar()
                    
                    # Emit a signal that activity was completed (if applicable)
                    if hasattr(self, 'activityCompleted'):
                        self.activityCompleted.emit(activity_id, activity_type, new_status)
                        
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
        
        # Filter activities for the current date and based on filter settings
        filtered_activities = [
            activity for activity in self.activities
            if self.filter_settings.get(activity['type'], True)
        ]
        
        # Make sure empty state exists
        if not hasattr(self, 'empty_state') or self.empty_state is None:
            self.empty_state = QLabel("No activities for this day")
            self.empty_state.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.empty_state.setStyleSheet("color: #6B7280; margin-top: 20px;")
        
        # Add empty state if needed
        if len(filtered_activities) == 0:
            self.empty_state.setParent(self.activities_container)
            self.activities_layout.addWidget(self.empty_state)
            self.empty_state.show()
        
        # Add widgets for each activity
        for activity in filtered_activities:
            self.addActivityWidget(activity)
            
        # Force layout update
        self.activities_container.updateGeometry()
    
    def addActivityWidget(self, activity):
        """Add a widget for an activity to the UI."""
        # Create the widget
        widget = ActivityItemWidget(
            activity_id=activity['id'],
            title=activity['title'],
            start_time=activity['start_time'].toString("HH:mm"),
            end_time=activity['end_time'].toString("HH:mm") if 'end_time' in activity else None,
            activity_type=activity['type'],
            priority=activity.get('priority', 0),
            category=activity.get('category', None),
            completed=activity.get('completed', False),
            color=activity.get('color', None)  # Pass the custom color
        )
        
        # Connect signals
        widget.activityCompleted.connect(self.onActivityCompleted)
        widget.activityDeleted.connect(self.deleteActivity)
        widget.activityEdited.connect(self.showEditActivityDialog)
        
        # Add to layout
        self.activities_layout.addWidget(widget)
        
        # Store reference
        widget_key = f"{activity['type']}_{activity['id']}"
        self.activity_widgets[widget_key] = widget
    
    def previousDay(self):
        """Go to the previous day."""
        self.current_date = self.current_date.addDays(-1)
        self.date_label.setText(self.current_date.toString("dddd, MMMM d, yyyy"))
        self.loadActivitiesFromDatabase()
    
    def nextDay(self):
        """Go to the next day."""
        self.current_date = self.current_date.addDays(1)
        self.date_label.setText(self.current_date.toString("dddd, MMMM d, yyyy"))
        self.loadActivitiesFromDatabase()
    
    def refresh(self):
        """Refresh the activities list."""
        self.loadActivitiesFromDatabase()
        
    def showAddTaskDialog(self):
        """Add a task (compatibility with the original interface)."""
        dialog = ActivityAddEditDialog(self)
        dialog.type_combo.setCurrentText("Task")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            activity_data = dialog.getActivityData()
            self.addActivity(activity_data)
    
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