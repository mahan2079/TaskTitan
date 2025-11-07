"""
Unified Activities View for TaskTitan.

This module provides a combined view for events, tasks, and habits with shared functionality.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QFrame, QListWidget, 
                            QListWidgetItem, QDialog, QLineEdit, QTimeEdit, 
                            QComboBox, QDialogButtonBox, QMessageBox, QCheckBox,
                            QDateEdit, QTabWidget, QSplitter, QSizePolicy, QMenu,
                            QGraphicsDropShadowEffect, QColorDialog, QCalendarWidget,
                            QListWidget, QAbstractItemView, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime, QSize, QPoint, QPointF, QEvent, QDateTime, QRect
from PyQt6.QtGui import QIcon, QFont, QColor, QAction, QCursor, QPainter, QPen, QMouseEvent
from datetime import datetime
import random

from app.resources import get_icon
from app.models.activities_manager import ActivitiesManager
from app.models.template_manager import TemplateManager
from app.views.todo_item_dialog import TodoItemDialog

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
        
        # Set up the UI components
        self.setupUI()
        
        # Apply shadow effect
        self.applyShadowEffect()
        
    def mousePressEvent(self, event):
        """Handle mouse press events - emit signal when the widget is clicked."""
        # Check if we have a checkbox and if the click is on it
        if hasattr(self, 'checkbox'):
            # Check if click is within checkbox bounds
            checkbox_rect = self.checkbox.geometry()
            if checkbox_rect.contains(event.pos()):
                # Map the event position to checkbox coordinates and forward to checkbox
                checkbox_pos = self.checkbox.mapFromParent(event.pos())
                # Create a new event with the mapped position (convert QPoint to QPointF)
                checkbox_event = QMouseEvent(
                    event.type(),
                    QPointF(checkbox_pos),
                    event.button(),
                    event.buttons(),
                    event.modifiers()
                )
                # Let the checkbox handle the event
                self.checkbox.mousePressEvent(checkbox_event)
                event.accept()
                return
        
        # Get the widget at the click position using global coordinates
        global_pos = self.mapToGlobal(event.pos())
        widget_at_pos = QApplication.widgetAt(global_pos)
        
        # Check if the click is on a checkbox, button, or their children
        if widget_at_pos:
            # Walk up the parent chain to see if we hit a checkbox or button
            check_widget = widget_at_pos
            while check_widget:
                # Check for standard QCheckBox, QPushButton, or our custom checkbox
                if isinstance(check_widget, (QCheckBox, QPushButton)) or check_widget == getattr(self, 'checkbox', None):
                    # This is a checkbox or button - let it handle the event normally
                    super().mousePressEvent(event)
                    return
                if check_widget == self:
                    # We've reached our widget, stop searching
                    break
                check_widget = check_widget.parent()
        
        # Also check using childAt as a fallback
        child_widget = self.childAt(event.pos())
        if child_widget:
            # Check if it's the checkbox or a standard widget type
            if isinstance(child_widget, (QCheckBox, QPushButton)) or child_widget == getattr(self, 'checkbox', None):
                # Let the child widget handle it
                super().mousePressEvent(event)
                return
            # Check parent chain
            parent = child_widget.parent()
            while parent and parent != self:
                if isinstance(parent, (QCheckBox, QPushButton)) or parent == getattr(self, 'checkbox', None):
                    # Let the parent widget handle it
                    super().mousePressEvent(event)
                    return
                parent = parent.parent()
        
        # Not clicking on a checkbox or button, handle the click ourselves
        if event.button() == Qt.MouseButton.LeftButton:
            self.activityClicked.emit(self.activity_data)
        else:
            # For other buttons, use default handling
            super().mousePressEvent(event)
        
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
        
        # Theme-driven color: expose type as property; allow custom color inline only for user color
        if self.custom_color:
            self.color_bar.setStyleSheet(f"background-color: {self.custom_color}; border-radius: 2px;")
        else:
            self.color_bar.setProperty("data-activity-type", self.activity_type)
            self.color_bar.setStyleSheet("")
        
        self.main_layout.addWidget(self.color_bar)
        
        # Custom checkbox widget that paints checkmark when checked
        class CheckboxWithCheckmark(QWidget):
            toggled = pyqtSignal(bool)  # Define signal at class level
            
            def __init__(self, checked=False, parent=None):
                super().__init__(parent)
                self._checked = checked
                self.setFixedSize(24, 24)
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
                # Ensure the widget can receive mouse events
                self.setAttribute(Qt.WidgetAttribute.WA_MouseTracking, False)
                self.setMouseTracking(False)
            
            def setChecked(self, checked):
                # Always update the state, even if it's the same, to ensure consistency
                old_checked = self._checked
                self._checked = bool(checked)  # Ensure it's a boolean
                # Force immediate repaint to show visual change
                self.update()
                self.repaint()
                # Only emit signal if state actually changed
                if old_checked != self._checked:
                    self.toggled.emit(self._checked)
            
            def isChecked(self):
                return self._checked
            
            def mousePressEvent(self, event):
                if event.button() == Qt.MouseButton.LeftButton:
                    # Toggle the state
                    new_state = not self._checked
                    self.setChecked(new_state)
                    event.accept()
                else:
                    super().mousePressEvent(event)
            
            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                # Draw checkbox box
                rect = QRect(2, 2, 20, 20)
                if self._checked:
                    # Checked state: blue background
                    painter.setBrush(QColor("#6366F1"))
                    painter.setPen(QPen(QColor("#6366F1"), 2))
                else:
                    # Unchecked state: white background with gray border
                    painter.setBrush(QColor("white"))
                    painter.setPen(QPen(QColor("#CBD5E1"), 2))
                
                painter.drawRoundedRect(rect, 4, 4)
                
                # Draw checkmark if checked - make it more visible
                if self._checked:
                    painter.setPen(QPen(QColor("white"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                    # Draw checkmark using lines (✓ shape) - centered and more prominent
                    check_x = 2 + 5
                    check_y = 2 + 10
                    # First line: bottom-left to middle
                    painter.drawLine(check_x, check_y, check_x + 5, check_y + 7)
                    # Second line: middle to top-right
                    painter.drawLine(check_x + 5, check_y + 7, check_x + 11, check_y - 3)
        
        # Create custom checkbox
        self.checkbox = CheckboxWithCheckmark(self.completed, self)
        self.checkbox.toggled.connect(self.onCompletionToggled)
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
            # Theme system will handle completed task styling
            self.title_label.setStyleSheet("text-decoration: line-through; font-size: 12pt;")
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
        # Theme system will handle muted text styling
        self.details_label.setStyleSheet("font-size: 10pt;")  # Smaller font
        self.details_label.setMaximumHeight(20)  # Fixed smaller height
        self.text_container.addWidget(self.details_label)
        
        # Add description label (additional info) - with much shorter text
        description_label = QLabel("This is a larger activity item with additional details.")
        description_label.setWordWrap(True)
        # Theme system will handle muted text styling
        description_label.setStyleSheet("font-size: 10pt;")  # Smaller font
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
        # Let the global theme style this button
        self.actions_btn.setStyleSheet("")
        
        self.actions_btn.clicked.connect(self.showActionsMenu)
        self.main_layout.addWidget(self.actions_btn)
        
        # Set the widget styling
        self.updateStyle()
    
    def updateStyle(self):
        """Update theming via properties (no inline styles)."""
        # Mark as a theme card so global QSS applies
        try:
            self.setProperty("data-card", "true")
            self.setProperty("data-activity", "true")
            self.setProperty("data-completed", "true" if self.completed else "false")
            # Re-polish to apply theme changes
            self.style().unpolish(self)
            self.style().polish(self)
        except Exception:
            pass
    
    def onCompletionToggled(self, checked):
        """Handle activity completion toggling."""
        self.completed = checked
        
        # Update title appearance without inline styles
        font = self.title_label.font()
        font.setBold(not checked)
        font.setStrikeOut(checked)
        self.title_label.setFont(font)
        # Clear any previous inline stylesheet if present
        self.title_label.setStyleSheet("")
        
        # Update widget style
        self.updateStyle()
        
        # Force repaint to show strikethrough line
        self.update()
        self.repaint()
        
        # Emit signal with the activity ID, current status, and type
        self.activityCompleted.emit(self.activity_id, checked, self.activity_type)
    
    def paintEvent(self, event):
        """Override paintEvent to draw strikethrough line when completed."""
        super().paintEvent(event)
        
        # Draw a strikethrough line across the entire widget if completed
        if self.completed:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw a diagonal line from top-left to bottom-right
            # Use a semi-transparent color that stands out
            pen = QPen(QColor(100, 100, 100, 200), 2)  # Gray with some transparency
            painter.setPen(pen)
            
            # Draw line across the widget
            margin = 10
            painter.drawLine(
                margin, 
                self.height() // 2,
                self.width() - margin,
                self.height() // 2
            )
    
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
        
        # Edit for today only action (for habits)
        edit_today_action = None
        # Delete for today only action (for habits)
        delete_today_action = None
        if self.activity_type == 'habit':
            edit_today_action = menu.addAction(f"Edit for Today Only")
            edit_today_icon = get_icon("edit")
            if not edit_today_icon.isNull():
                edit_today_action.setIcon(edit_today_icon)
            else:
                edit_today_action.setIcon(QIcon.fromTheme("document-edit"))
                
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
        elif action == edit_today_action:
            # Signal to edit this habit for today only
            self.activityEdited.emit(self.activity_id, "edit_today_habit")
        elif action == delete_today_action:
            # Signal to delete this habit for today only
            self.activityEdited.emit(self.activity_id, "delete_today_habit")


class ActivityAddEditDialog(QDialog):
    """Dialog for adding or editing activities."""
    
    def __init__(self, parent=None, activity_data=None, edit_mode=False):
        super().__init__(parent)
        
        self.edit_mode = edit_mode
        self.activity_data = activity_data or {}
        self.activity_id = activity_data.get('id') if activity_data else None
        
        # Get activities_manager from parent
        self.activities_manager = None
        if parent and hasattr(parent, 'activities_manager'):
            self.activities_manager = parent.activities_manager
        elif parent and hasattr(parent, 'parent') and hasattr(parent.parent, 'activities_manager'):
            self.activities_manager = parent.parent.activities_manager
        
        # Store todo items temporarily (will be saved when activity is saved)
        self.todo_items = []  # List of (item_id, text, completed) tuples
        
        # Set dialog title
        self.setWindowTitle("Add Activity" if not edit_mode else "Edit Activity")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        
        # Default color
        self.current_color = QColor(self.activity_data.get('color', "#6366F1"))
        
        # Set up the UI
        self.setupUI()
        
        # If in edit mode, populate fields and load todo items
        if edit_mode and activity_data:
            self.populateFields()
            self.loadTodoItems()
    
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
        
        # Todo List Section
        self.todo_section = QFrame()
        self.todo_section.setFrameShape(QFrame.Shape.StyledPanel)
        todo_layout = QVBoxLayout(self.todo_section)
        todo_layout.setContentsMargins(10, 10, 10, 10)
        todo_layout.setSpacing(10)
        
        # Todo section header
        todo_header = QHBoxLayout()
        todo_title = QLabel("Todo Items:")
        todo_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        todo_header.addWidget(todo_title)
        todo_header.addStretch()
        
        # Add todo button
        self.add_todo_btn = QPushButton("+ Add Todo")
        self.add_todo_btn.setMaximumWidth(100)
        self.add_todo_btn.clicked.connect(self.addTodoItem)
        todo_header.addWidget(self.add_todo_btn)
        todo_layout.addLayout(todo_header)
        
        # Todo list widget
        self.todo_list = QListWidget()
        self.todo_list.setMaximumHeight(200)
        self.todo_list.setAlternatingRowColors(True)
        self.todo_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        todo_layout.addWidget(self.todo_list)
        
        layout.addWidget(self.todo_section)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.onAccept)
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
        
        # Todo section is always visible (works for all activity types)
        # It's already added in setupUI, no need to recreate it here
    
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
    
    def loadTodoItems(self):
        """Load existing todo items for the activity being edited."""
        if not self.activities_manager or not self.activity_id:
            return
        
        try:
            todo_items = self.activities_manager.get_todo_items(self.activity_id)
            self.todo_items = list(todo_items)  # Store as list of tuples
            self.refreshTodoList()
        except Exception as e:
            print(f"Error loading todo items: {e}")
    
    def refreshTodoList(self):
        """Refresh the todo list display."""
        self.todo_list.clear()
        for idx, (item_id, text, completed) in enumerate(self.todo_items):
            item = QListWidgetItem()
            # Create a widget for the todo item
            todo_widget = QWidget()
            todo_layout = QHBoxLayout(todo_widget)
            todo_layout.setContentsMargins(5, 5, 5, 5)
            
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(bool(completed))
            # Use a lambda that captures item_id and index properly
            def make_toggle_handler(tid, index):
                return lambda state: self.toggleTodoItem(tid, state, index)
            checkbox.stateChanged.connect(make_toggle_handler(item_id, idx))
            todo_layout.addWidget(checkbox)
            
            # Text label
            label = QLabel(text)
            if completed:
                label.setStyleSheet("text-decoration: line-through; color: #9CA3AF;")
            todo_layout.addWidget(label, 1)
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.setMaximumWidth(50)
            # Use a closure function to properly capture item_id and index
            def make_edit_handler(tid, index):
                return lambda checked=False: self.editTodoItem(tid, index)
            edit_btn.clicked.connect(make_edit_handler(item_id, idx))
            todo_layout.addWidget(edit_btn)
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setMaximumWidth(60)
            # Use a closure function to properly capture item_id and index
            def make_delete_handler(tid, index):
                return lambda checked=False: self.deleteTodoItem(tid, index)
            delete_btn.clicked.connect(make_delete_handler(item_id, idx))
            todo_layout.addWidget(delete_btn)
            
            item.setSizeHint(todo_widget.sizeHint())
            self.todo_list.addItem(item)
            self.todo_list.setItemWidget(item, todo_widget)
    
    def addTodoItem(self):
        """Add a new todo item."""
        dialog = TodoItemDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            text = dialog.get_text()
            if text:
                # Add to temporary list (will be saved when activity is saved)
                # Use None as item_id for new items
                self.todo_items.append((None, text, False))
                self.refreshTodoList()
    
    def editTodoItem(self, item_id, index=None):
        """Edit an existing todo item."""
        # Use index if provided (for new items with None id), otherwise find by item_id
        if index is not None and index < len(self.todo_items):
            idx = index
        else:
            # Find the todo item by id
            idx = None
            for i, (tid, text, completed) in enumerate(self.todo_items):
                if tid == item_id:
                    idx = i
                    break
        
        if idx is not None and idx < len(self.todo_items):
            tid, text, completed = self.todo_items[idx]
            dialog = TodoItemDialog(self, text)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_text = dialog.get_text()
                if new_text:
                    self.todo_items[idx] = (tid, new_text, completed)
                    self.refreshTodoList()
    
    def deleteTodoItem(self, item_id, index=None):
        """Delete a todo item."""
        # Use index if provided (for new items with None id), otherwise find by item_id
        if index is not None and index < len(self.todo_items):
            # Remove by index
            self.todo_items.pop(index)
        else:
            # Remove by item_id
            self.todo_items = [(tid, text, completed) for tid, text, completed in self.todo_items if tid != item_id]
        self.refreshTodoList()
    
    def toggleTodoItem(self, item_id, state, index=None):
        """Toggle the completion status of a todo item."""
        # Use index if provided (for new items with None id), otherwise find by item_id
        if index is not None and index < len(self.todo_items):
            idx = index
        else:
            # Find the todo item by id
            idx = None
            for i, (tid, text, completed) in enumerate(self.todo_items):
                if tid == item_id:
                    idx = i
                    break
        
        if idx is not None and idx < len(self.todo_items):
            tid, text, completed = self.todo_items[idx]
            # CheckState.Checked is 2, CheckState.Unchecked is 0
            is_checked = state == Qt.CheckState.Checked.value
            self.todo_items[idx] = (tid, text, is_checked)
            self.refreshTodoList()
    
    def onAccept(self):
        """Handle accept button - save todo items before accepting."""
        # Accept the dialog first
        self.accept()
        
        # Note: Todo items will be saved by the caller after the activity is created/updated
        # We return the todo items data so the caller can save them
        return True
    
    def getTodoItems(self):
        """Get the todo items data to be saved."""
        return self.todo_items


class OverlapConflictDialog(QDialog):
    """Dialog for handling activity overlap conflicts."""
    
    def __init__(self, conflicts, date, start_time, end_time, parent=None):
        super().__init__(parent)
        self.conflicts = conflicts
        self.selected_action = None
        self.new_time = None
        self.activity_to_reschedule = None
        
        self.setWindowTitle("Scheduling Conflict Detected")
        self.setMinimumWidth(500)
        self.setupUI(date, start_time, end_time)
    
    def setupUI(self, date, start_time, end_time):
        """Set up the UI for the conflict dialog."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Warning header
        header = QLabel("⚠️ Scheduling Conflict")
        # Theme system will handle label styling
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Message
        message = QLabel(
            f"The scheduled time ({start_time.toString('HH:mm')} - {end_time.toString('HH:mm')}) "
            f"overlaps with {len(self.conflicts)} existing activity(ies)."
        )
        message.setWordWrap(True)
        # Theme system will handle label styling
        message.setStyleSheet("margin-bottom: 15px;")
        layout.addWidget(message)
        
        # Conflicting activities list
        conflicts_label = QLabel("Conflicting Activities:")
        # Theme system will handle label styling
        conflicts_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(conflicts_label)
        
        # Create scroll area for conflicts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(150)
        # Theme system will handle scroll area styling
        
        conflicts_widget = QWidget()
        conflicts_layout = QVBoxLayout(conflicts_widget)
        
        for conflict in self.conflicts:
            conflict_frame = QFrame()
            from app.themes import ThemeManager
            error_bg = ThemeManager.get_color("error_bg")
            error = ThemeManager.get_color("error")
            conflict_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {error_bg};
                    border: 1px solid {error};
                    border-radius: 6px;
                    padding: 8px;
                    margin: 2px;
                }}
            """)
            
            conflict_layout = QHBoxLayout(conflict_frame)
            
            # Icon based on type
            icon = "📅" if conflict['type'] == 'event' else "✓" if conflict['type'] == 'task' else "🔄"
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 16px;")
            conflict_layout.addWidget(icon_label)
            
            # Activity info
            info_label = QLabel(
                f"<b>{conflict['title']}</b><br>"
                f"{conflict['start_time']} - {conflict['end_time']}<br>"
                f"Type: {conflict['type']}"
            )
            # Theme system will handle label styling
            conflict_layout.addWidget(info_label)
            
            conflict_layout.addStretch()
            conflicts_layout.addWidget(conflict_frame)
        
        conflicts_layout.addStretch()
        scroll.setWidget(conflicts_widget)
        layout.addWidget(scroll)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Reschedule new activity button
        reschedule_btn = QPushButton("Reschedule New Activity")
        reschedule_btn.setObjectName("primaryBtn")
        # Theme system will handle button styling
        reschedule_btn.clicked.connect(lambda: self.handleAction('reschedule'))
        button_layout.addWidget(reschedule_btn)
        
        # Save anyway button
        save_anyway_btn = QPushButton("Save Anyway")
        # Theme system will handle button styling
        save_anyway_btn.clicked.connect(lambda: self.handleAction('force_save'))
        button_layout.addWidget(save_anyway_btn)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        # Theme system will handle button styling
        cancel_btn.clicked.connect(lambda: self.handleAction('cancel'))
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def handleAction(self, action):
        """Handle the action button click."""
        self.selected_action = action
        if action == 'reschedule':
            self.accept()  # Will need to handle rescheduling in parent
        elif action == 'force_save':
            # Confirm before force saving
            reply = QMessageBox.question(
                self, 'Confirm Save',
                'Are you sure you want to save this activity with overlapping times?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.accept()
        else:
            self.reject()
    
    def getAction(self):
        """Get the selected action."""
        return self.selected_action


class EmptySlotsDialog(QDialog):
    """Dialog for displaying empty time slots (free time)."""
    
    def __init__(self, empty_slots, date, parent=None):
        super().__init__(parent)
        self.empty_slots = empty_slots
        self.date = date
        self.selected_slot = None
        
        self.setWindowTitle(f"Free Time - {date.toString('MMMM d, yyyy')}")
        self.setMinimumWidth(450)
        self.setupUI()
    
    def setupUI(self):
        """Set up the UI for the empty slots dialog."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel(f"Free Time on {self.date.toString('dddd, MMMM d, yyyy')}")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F2937; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Summary
        total_free_minutes = sum(slot['duration_minutes'] for slot in self.empty_slots)
        total_free_hours = total_free_minutes // 60
        total_free_mins = total_free_minutes % 60
        summary = QLabel(f"Total free time: {total_free_hours}h {total_free_mins}m ({len(self.empty_slots)} slots)")
        # Theme system will handle muted text styling
        summary.setStyleSheet("margin-bottom: 15px;")
        layout.addWidget(summary)
        
        if not self.empty_slots:
            # No free time
            no_free_label = QLabel("No significant free time slots found.")
            # Theme system will handle muted text styling
            no_free_label.setStyleSheet("font-size: 14px; padding: 20px;")
            no_free_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_free_label)
            
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.accepted.connect(self.accept)
            button_box.rejected.connect(self.reject)
            layout.addWidget(button_box)
            return
        
        # Scroll area for slots
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(300)
        # Theme system will handle scroll area styling
        
        slots_widget = QWidget()
        slots_layout = QVBoxLayout(slots_widget)
        
        for i, slot in enumerate(self.empty_slots):
            slot_frame = QFrame()
            slot_frame.setProperty("data-card", "true")
            # Theme system will handle card styling
            slot_layout = QHBoxLayout(slot_frame)
            
            # Time info
            duration_hours = slot['duration_minutes'] // 60
            duration_mins = slot['duration_minutes'] % 60
            duration_str = f"{duration_hours}h {duration_mins}m" if duration_hours > 0 else f"{duration_mins}m"
            
            time_info = QLabel(
                f"<b>{slot['start_time'].toString('HH:mm')} - {slot['end_time'].toString('HH:mm')}</b><br>"
                f"Duration: {duration_str}"
            )
            # Theme system will handle label styling
            slot_layout.addWidget(time_info)
            
            slot_layout.addStretch()
            
            # Schedule activity button
            schedule_btn = QPushButton("Schedule Activity")
            schedule_btn.setObjectName("primaryBtn")
            # Theme system will handle button styling
            schedule_btn.clicked.connect(lambda checked, idx=i: self.scheduleActivity(idx))
            slot_layout.addWidget(schedule_btn)
            
            slots_layout.addWidget(slot_frame)
        
        slots_layout.addStretch()
        scroll.setWidget(slots_widget)
        layout.addWidget(scroll)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def scheduleActivity(self, slot_index):
        """Handle scheduling an activity in the selected slot."""
        self.selected_slot = self.empty_slots[slot_index]
        self.accept()


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
        
        # Remove hardcoded stylesheet - let theme system handle styling
        # The theme system already provides QDialog styling
        
        # Activity header with type indicator
        header_layout = QHBoxLayout()
        
        # Activity type indicator
        type_indicator = QFrame()
        type_indicator.setFixedSize(32, 32)
        
        activity_type = self.activity.get('type', '')
        type_indicator.setProperty("data-activity-type", activity_type)
        # Theme system will style this via QFrame[data-activity-type="..."]
        type_indicator.setStyleSheet("border-radius: 16px;")
            
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
        separator.setFixedHeight(2)
        # Theme system will handle separator styling
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
        self.parent = parent
        self.activities = {'task': [], 'event': [], 'habit': []}
        # Attempt to connect to DB via parent's ActivitiesManager
        try:
            if hasattr(parent, 'activities_manager'):
                self.activities_manager = parent.activities_manager
            else:
                self.activities_manager = ActivitiesManager()
                if hasattr(parent, 'conn') and hasattr(parent, 'cursor'):
                    self.activities_manager.set_connection(parent.conn, parent.cursor)
            # Ensure tables exist
            self.activities_manager.create_tables()
        except Exception as e:
            print(f"UnifiedActivitiesWidget init error: {e}")
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
        # Theme system will handle button styling
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
        # Theme system will handle button styling
        self.next_day_btn.clicked.connect(self.nextDay)
        date_layout.addWidget(self.next_day_btn)
        
        header_layout.addLayout(date_layout)

        # Template controls
        try:
            self.template_manager = TemplateManager(self.parent.conn, self.parent.cursor)
            self.template_manager.create_tables()
        except Exception:
            self.template_manager = None

        if self.template_manager:
            template_bar = QHBoxLayout()
            template_bar.setSpacing(8)
            self.template_combo = QComboBox()
            self.template_combo.setObjectName("templateCombo")
            self.template_combo.setMinimumWidth(160)
            self._reload_templates_into_combo()
            self.template_combo.currentIndexChanged.connect(self._on_template_selected)
            template_bar.addWidget(self.template_combo)

            apply_btn = QPushButton("Apply")
            apply_btn.setObjectName("templateApplyBtn")
            apply_btn.clicked.connect(self._apply_selected_template)
            template_bar.addWidget(apply_btn)

            save_btn = QPushButton("Save Habits as Template")
            save_btn.setObjectName("templateSaveBtn")
            save_btn.clicked.connect(self._save_current_habits_as_template)
            template_bar.addWidget(save_btn)

            header_layout.addLayout(template_bar)
        
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
        self.empty_state.setObjectName("emptyState")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        # Theme system will handle empty state styling via object name
        self.activities_layout.addWidget(self.empty_state)
        
        self.main_layout.addWidget(self.scroll_area)
        
        # Remove hardcoded styles - theme system handles styling via object names
        # Object names are already set: activitiesHeader, activitiesTitle, filterButton, 
        # addActivityButton, activitiesSeparator, activitiesScrollArea, activitiesContainer
    
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
        
        # Theme system will handle calendar styling
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
        """Load activities from the database for the current date."""
        if not hasattr(self, 'activities_manager'):
            return
            
        try:
            # Get activities for the current date - this includes date-specific completion status
            # We need to get all activities first, then filter by date with proper completion status
            # For now, get all activities but we'll use get_activities_for_date in refreshActivitiesList
            # to ensure completion status is correct
            all_activities = self.activities_manager.get_all_activities()
            
            # Store all activities for filtering, but we'll get date-specific completion in refreshActivitiesList
            self.activities = all_activities
            
            # Update the current date label
            if self.current_date == QDate.currentDate():
                self.date_label.setText(f"Today: {self.current_date.toString('dddd, MMMM d, yyyy')}")
            else:
                self.date_label.setText(self.current_date.toString("dddd, MMMM d, yyyy"))
            
            # Refresh the activities list - this will use get_activities_for_date for proper completion status
            self.refreshActivitiesList()
        except Exception as e:
            print(f"Error loading activities: {e}")

    # ---------- Template integration ----------
    def _reload_templates_into_combo(self):
        if not getattr(self, 'template_manager', None):
            return
        try:
            self.template_combo.blockSignals(True)
            self.template_combo.clear()
            items = self.template_manager.list_templates()
            for tid, name in items:
                self.template_combo.addItem(name, tid)
            active_id = self.template_manager.get_active_template_id()
            if active_id is not None:
                idx = self.template_combo.findData(active_id)
                if idx >= 0:
                    self.template_combo.setCurrentIndex(idx)
        finally:
            self.template_combo.blockSignals(False)

    def _on_template_selected(self, _index: int):
        # Selection alone does not apply; keep UX simple
        pass

    def _apply_selected_template(self):
        if not getattr(self, 'template_manager', None):
            return
        tid = self.template_combo.currentData()
        if tid is None:
            return
        try:
            # Apply to DB, replacing current habits
            self.template_manager.set_active_template(int(tid), replace_existing=True)
            # Refresh activities everywhere
            self.refresh()
            # Also inform parent weekly view if present
            if hasattr(self.parent, 'weekly_plan_view') and getattr(self.parent, 'weekly_plan_view'):
                try:
                    self.parent.weekly_plan_view.loadActivities()
                except Exception:
                    pass
        except Exception as e:
            print(f"Failed to apply template: {e}")

    def _save_current_habits_as_template(self):
        if not getattr(self, 'template_manager', None):
            return
        try:
            from PyQt6.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(self, "Save Habit Template", "Template name:")
            if not ok or not name.strip():
                return
            tid = self.template_manager.save_template_from_current_habits(name.strip(), overwrite=True)
            self._reload_templates_into_combo()
            # Select the saved one
            idx = self.template_combo.findData(tid)
            if idx >= 0:
                self.template_combo.setCurrentIndex(idx)
        except Exception as e:
            print(f"Failed to save template: {e}")
    
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
            activity_id = self.addActivity(activity_data)
            
            # Save todo items if any were added
            if activity_id and hasattr(dialog, 'getTodoItems'):
                todo_items = dialog.getTodoItems()
                if todo_items and self.activities_manager:
                    for item_id, text, completed in todo_items:
                        # item_id will be None for new items
                        new_todo_id = self.activities_manager.add_todo_item(activity_id, text)
                        # If it was marked as completed, update it
                        if completed and new_todo_id:
                            self.activities_manager.update_todo_item(new_todo_id, text, True)
    
    def showEditActivityDialog(self, activity_id, activity_type):
        """Show the dialog to edit an activity."""
        # Handle special action types
        if activity_type.startswith("duplicate_"):
            original_type = activity_type.split("_")[1]
            self.duplicateActivity(activity_id, original_type)
            return
        elif activity_type.startswith("reschedule_"):
            original_type = activity_type.split("_")[1]
            self.rescheduleActivity(activity_id, original_type)
            return
        elif activity_type == "delete_today_habit":
            self.deleteHabitForToday(activity_id)
            return
        elif activity_type == "edit_today_habit":
            self.editHabitForToday(activity_id)
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
                
                # Save todo items
                if hasattr(dialog, 'getTodoItems') and self.activities_manager:
                    todo_items = dialog.getTodoItems()
                    
                    # Get existing todo items from database
                    existing_todos = {item[0]: item for item in self.activities_manager.get_todo_items(activity_id)}
                    
                    # Process todo items
                    current_todo_ids = set()
                    for item_id, text, completed in todo_items:
                        if item_id is None:
                            # New item - add it
                            new_id = self.activities_manager.add_todo_item(activity_id, text)
                            if completed and new_id:
                                self.activities_manager.update_todo_item(new_id, text, True)
                        else:
                            # Existing item - update it
                            current_todo_ids.add(item_id)
                            existing_item = existing_todos.get(item_id)
                            if existing_item:
                                # Update if text or completion status changed
                                if existing_item[1] != text or bool(existing_item[2]) != completed:
                                    self.activities_manager.update_todo_item(item_id, text, completed)
                    
                    # Delete items that were removed
                    for existing_id in existing_todos.keys():
                        if existing_id not in current_todo_ids:
                            self.activities_manager.delete_todo_item(existing_id)
                
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
        
        # Load original todo items to include in the dialog
        original_todos = []
        if self.activities_manager:
            original_todos = self.activities_manager.get_todo_items(activity_id)
            # Convert to format expected by dialog (item_id will be None for new items when duplicating)
            new_activity['_todo_items'] = [(None, text, completed) for item_id, text, completed in original_todos]
        
        # Open the edit dialog with the duplicated data
        dialog = ActivityAddEditDialog(self, new_activity, edit_mode=False)
        
        # Pre-populate todo items in dialog if we have them
        if original_todos and hasattr(dialog, 'todo_items'):
            dialog.todo_items = [(None, text, completed) for item_id, text, completed in original_todos]
            dialog.refreshTodoList()
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            activity_data = dialog.getActivityData()
            activity_id = self.addActivity(activity_data)
            
            # Save todo items from dialog
            if activity_id and hasattr(dialog, 'getTodoItems'):
                todo_items = dialog.getTodoItems()
                if todo_items and self.activities_manager:
                    for item_id, text, completed in todo_items:
                        # item_id will be None for new items
                        new_todo_id = self.activities_manager.add_todo_item(activity_id, text)
                        if completed and new_todo_id:
                            self.activities_manager.update_todo_item(new_todo_id, text, True)
            
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
                
                # Ensure database changes are committed immediately
                if success and hasattr(self.activities_manager, 'conn'):
                    try:
                        self.activities_manager.conn.commit()
                    except Exception as e:
                        print(f"Error committing completion change: {e}")
                
                if success:
                    # Update our local data
                    activity['completed'] = new_status
                    
                    # Update the widget directly instead of refreshing the whole list
                    widget_key = f"{activity_type}_{activity_id}"
                    if widget_key in self.activity_widgets:
                        widget = self.activity_widgets[widget_key]
                        # Update widget's completed state first
                        widget.completed = new_status
                        
                        if hasattr(widget, 'checkbox'):
                            # Block signals to prevent recursive updates
                            if hasattr(widget.checkbox, 'blockSignals'):
                                widget.checkbox.blockSignals(True)
                            # Update checkbox state - ensure it's set as boolean
                            if hasattr(widget.checkbox, 'setChecked'):
                                widget.checkbox.setChecked(bool(new_status))
                            # Unblock signals
                            if hasattr(widget.checkbox, 'blockSignals'):
                                widget.checkbox.blockSignals(False)
                        
                        # Update widget style and trigger repaint
                        if hasattr(widget, 'updateStyle'):
                            widget.updateStyle()
                        # Force widget and checkbox repaint to show changes
                        widget.update()
                        widget.repaint()
                        if hasattr(widget, 'checkbox'):
                            widget.checkbox.update()
                            widget.checkbox.repaint()
                    else:
                        # Widget doesn't exist, refresh the list
                        self.refreshActivitiesList()
                    
                    # If this is an event, make sure the calendar is updated
                    if activity_type == 'event':
                        self.syncWithCalendar()
                    
                    # Also refresh the weekly plan view if it exists
                    # BUT don't let it refresh us back, as we've already updated the widget
                    if hasattr(self.parent, 'weekly_plan_view') and self.parent.weekly_plan_view:
                        # Temporarily disable refresh to prevent circular refresh
                        self._prevent_refresh = True
                        try:
                            self.parent.weekly_plan_view.refresh()
                        finally:
                            self._prevent_refresh = False
                    
                    # Emit a signal that activity was completed (if applicable)
                    if hasattr(self, 'activityCompleted'):
                        # Make sure to pass the correct types (int, bool, str)
                        self.activityCompleted.emit(int(activity_id), bool(new_status), str(activity_type))
                        
                break
    
    def refresh(self):
        """Refresh the activities view - but preserve widget states if possible."""
        # If we're in the middle of updating a widget, don't refresh
        if hasattr(self, '_prevent_refresh') and self._prevent_refresh:
            return
        # Otherwise, reload from database
        self.loadActivitiesFromDatabase()
    
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
        
        # Get activities for the current date with proper completion status
        # This uses get_activities_for_date which joins with activity_completions
        try:
            date_activities = self.activities_manager.get_activities_for_date(self.current_date)
        except Exception as e:
            print(f"Error getting activities for date: {e}")
            date_activities = []
        
        # Filter activities by type (get_activities_for_date already filtered by date)
        filtered_activities = []
        
        for activity in date_activities:
            # Check if the activity type is enabled in filters
            if not self.filter_settings.get(activity['type'], True):
                continue
            
            # All activities from get_activities_for_date are already for the current date
            # so we can add them directly
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
            # Remove existing empty state if present
            if hasattr(self, 'empty_state') and self.empty_state:
                self.empty_state.setParent(None)
            
            # Create enhanced empty state
            self.empty_state = self.createEmptyState()
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
    
    def createEmptyState(self):
        """Create an enhanced empty state widget."""
        empty_widget = QWidget()
        empty_widget.setObjectName("emptyState")
        
        layout = QVBoxLayout(empty_widget)
        layout.setContentsMargins(40, 60, 40, 60)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calendar_icon = get_icon("calendar")
        if not calendar_icon.isNull():
            icon_label.setPixmap(calendar_icon.pixmap(QSize(64, 64)))
        else:
            icon_label.setText("📅")
            icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(f"No activities for {self.current_date.toString('MMMM d, yyyy')}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("color: #374151; margin-top: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Get started by adding a task, event, or habit")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #6B7280; font-size: 14px; margin-top: 5px;")
        layout.addWidget(desc_label)
        
        # Action button
        action_btn = QPushButton("Add Activity")
        action_btn.setObjectName("addActivityButton")
        action_btn.setFixedWidth(200)
        action_btn.clicked.connect(self.showAddActivityDialog)
        action_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
        """)
        layout.addWidget(action_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return empty_widget
    
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
            
            # Store a reference to the widget by type and ID (matching lookup format)
            widget_key = f"{activity_type}_{activity_id}"
            self.activity_widgets[widget_key] = widget
            
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
        menu.setObjectName("filterMenu")
        # Theme system will handle menu styling via object name
        
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
        from app.themes import ThemeManager
        
        # Check if any filters are active (not all types are shown)
        all_showing = all(self.filter_settings.values())
        any_showing = any(self.filter_settings.values())
        
        surface2 = ThemeManager.get_color("surface2")
        border = ThemeManager.get_color("border")
        error = ThemeManager.get_color("error")
        error_bg = ThemeManager.get_color("error_bg")
        primary = ThemeManager.get_color("primary")
        selection = ThemeManager.get_color("selection")
        
        if all_showing:
            # All types are showing - regular state
            self.filter_btn.setStyleSheet(f"""
                background-color: {surface2};
                border: 1px solid {border};
                border-radius: 8px;
            """)
        elif not any_showing:
            # No types are showing - error state
            self.filter_btn.setStyleSheet(f"""
                background-color: {error_bg};
                border: 1px solid {error};
                border-radius: 8px;
            """)
        else:
            # Some types are showing - active filter state
            self.filter_btn.setStyleSheet(f"""
                background-color: {selection};
                border: 1px solid {primary};
                border-radius: 8px;
            """)

    def editHabitForToday(self, habit_id):
        """Edit a habit for the current day only without affecting the routine."""
        # Find the habit in our list
        habit = None
        for activity in self.activities:
            if activity.get('id') == habit_id and activity.get('type') == 'habit':
                habit = activity
                break
                
        if not habit:
            return
            
        # Get the current day name and date
        current_day_name = self.current_date.toString("dddd")  # e.g., "Monday"
        current_date = self.current_date
        
        # Create a copy of the habit data for a single-day instance
        one_time_habit = dict(habit)
        one_time_habit.pop('id', None)  # Remove the ID to create a new entry
        
        # Set the one-time habit to only appear on the current date
        one_time_habit['date'] = current_date
        one_time_habit['days_of_week'] = ''  # Clear recurring days
        
        # Get the current days of the week for the original habit
        days_of_week = habit.get('days_of_week', '')
        days_list = days_of_week.split(',') if days_of_week else []
        
        # Check if current day exists in the list for the original habit
        if current_day_name in days_list:
            # Remove this day from the original habit's schedule
            days_list.remove(current_day_name)
            
            # Update the original habit to skip the current day
            updated_data = {
                'days_of_week': ','.join(days_list)
            }
            
            # Update the original habit in the database
            self.activities_manager.update_activity(habit_id, updated_data)
            
            # Update in our list
            habit['days_of_week'] = ','.join(days_list)
            
        # Check if the habit already has a specific date entry for today
        specific_date_habit = None
        current_date_str = current_date.toString("yyyy-MM-dd")
        
        for activity in self.activities:
            if activity.get('type') == 'habit':
                habit_date = activity.get('date')
                if hasattr(habit_date, 'toString'):
                    habit_date_str = habit_date.toString("yyyy-MM-dd")
                else:
                    habit_date_str = habit_date
                    
                if (habit_date_str == current_date_str and 
                    activity.get('title') == habit.get('title')):
                    specific_date_habit = activity
                    break
        
        # Create a custom edit dialog for single day editing
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Habit for Today Only")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_layout.addWidget(title_label)
        
        title_input = QLineEdit()
        title_input.setPlaceholderText("Enter habit title")
        title_input.setText(habit.get('title', ''))
        title_layout.addWidget(title_input)
        layout.addLayout(title_layout)
        
        # Notice that this is for today only
        today_label = QLabel(f"This will modify the habit for {current_date.toString('dddd, MMMM d')} only.")
        today_label.setStyleSheet("color: #4F46E5; font-weight: bold;")
        layout.addWidget(today_label)
        
        # Time range
        time_layout = QHBoxLayout()
        
        start_time_label = QLabel("Start Time:")
        time_layout.addWidget(start_time_label)
        
        start_time_input = QTimeEdit()
        start_time = habit.get('start_time')
        if hasattr(start_time, 'toString'):
            start_time_input.setTime(start_time)
        elif isinstance(start_time, str) and ':' in start_time:
            start_time_input.setTime(QTime.fromString(start_time, "HH:mm"))
        else:
            start_time_input.setTime(QTime.currentTime())
        time_layout.addWidget(start_time_input)
        
        end_time_label = QLabel("End Time:")
        time_layout.addWidget(end_time_label)
        
        end_time_input = QTimeEdit()
        end_time = habit.get('end_time')
        if hasattr(end_time, 'toString'):
            end_time_input.setTime(end_time)
        elif isinstance(end_time, str) and ':' in end_time:
            end_time_input.setTime(QTime.fromString(end_time, "HH:mm"))
        else:
            end_time_input.setTime(QTime.currentTime().addSecs(3600))
        time_layout.addWidget(end_time_input)
        
        layout.addLayout(time_layout)
        
        # Category
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_layout.addWidget(category_label)
        
        category_combo = QComboBox()
        category_combo.addItems(["Work", "Personal", "Health", "Learning", "Other"])
        current_category = habit.get('category', 'Work')
        index = category_combo.findText(current_category)
        if index >= 0:
            category_combo.setCurrentIndex(index)
        category_layout.addWidget(category_combo)
        
        layout.addLayout(category_layout)
        
        # Color selector
        color_layout = QHBoxLayout()
        color_label = QLabel("Color:")
        color_layout.addWidget(color_label)
        
        # Color display
        color_preview = QFrame()
        color_preview.setFixedSize(30, 30)
        current_color = QColor(habit.get('color', "#34D399"))
        color_preview.setStyleSheet(f"""
            background-color: {current_color.name()};
            border-radius: 4px;
            border: 1px solid #CBD5E1;
        """)
        color_layout.addWidget(color_preview)
        
        # Color button
        color_button = QPushButton("Choose Color")
        color_layout.addWidget(color_button)
        
        # Capture the current color in the dialog scope for the color selector
        dialog.current_color = current_color
        
        # Define color selector within the dialog scope
        def select_color():
            color = QColorDialog.getColor(dialog.current_color, self, "Select Habit Color")
            if color.isValid():
                dialog.current_color = color
                color_preview.setStyleSheet(f"""
                    background-color: {color.name()};
                    border-radius: 4px;
                    border: 1px solid #CBD5E1;
                """)
        
        color_button.clicked.connect(select_color)
        
        layout.addLayout(color_layout)
        
        # Completion status
        completed_check = QCheckBox("Mark as completed")
        completed_check.setChecked(habit.get('completed', False))
        layout.addWidget(completed_check)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # If a specific date entry already exists, load its values
        if specific_date_habit:
            title_input.setText(specific_date_habit.get('title', ''))
            
            # Set start time
            start_time = specific_date_habit.get('start_time')
            if hasattr(start_time, 'toString'):
                start_time_input.setTime(start_time)
            elif isinstance(start_time, str) and ':' in start_time:
                start_time_input.setTime(QTime.fromString(start_time, "HH:mm"))
                
            # Set end time
            end_time = specific_date_habit.get('end_time')
            if hasattr(end_time, 'toString'):
                end_time_input.setTime(end_time)
            elif isinstance(end_time, str) and ':' in end_time:
                end_time_input.setTime(QTime.fromString(end_time, "HH:mm"))
                
            # Set category
            current_category = specific_date_habit.get('category', 'Work')
            index = category_combo.findText(current_category)
            if index >= 0:
                category_combo.setCurrentIndex(index)
                
            # Set color
            if 'color' in specific_date_habit:
                if isinstance(specific_date_habit['color'], QColor):
                    current_color = specific_date_habit['color']
                elif isinstance(specific_date_habit['color'], str):
                    current_color = QColor(specific_date_habit['color'])
                color_preview.setStyleSheet(f"""
                    background-color: {current_color.name()};
                    border-radius: 4px;
                    border: 1px solid #CBD5E1;
                """)
            
            # Set completion status
            completed_check.setChecked(specific_date_habit.get('completed', False))
        
        # Show the dialog and process result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Create a new one-time habit or update existing one
            habit_data = {
                'type': 'habit',
                'title': title_input.text(),
                'date': current_date,
                'start_time': start_time_input.time(),
                'end_time': end_time_input.time(),
                'category': category_combo.currentText(),
                'color': dialog.current_color.name(),
                'completed': completed_check.isChecked(),
                'days_of_week': ''  # Important: ensure this is empty for single-day habits
            }
            
            if specific_date_habit:
                # Update existing single-day habit
                self.updateActivity(specific_date_habit.get('id'), 'habit', habit_data)
            else:
                # Create a new one-time habit
                self.addActivity(habit_data)
            
            # Refresh the UI
            self.refreshActivitiesList()
            
            # Show confirmation message
            QMessageBox.information(
                self,
                "Habit Modified for Today",
                f"This habit has been modified for {current_date.toString('dddd, MMMM d')} only. The regular schedule remains unchanged for other days."
            )