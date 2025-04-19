from PyQt6.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, 
                              QCheckBox, QPushButton, QSizePolicy, QFrame,
                              QGraphicsDropShadowEffect, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QIcon, QCursor, QPainter, QBrush, QPen, QPalette, QFont

from app.resources import get_icon

class TaskWidget(QWidget):
    """A modern task widget for displaying a task with actions."""
    
    # Signals
    taskCompleted = pyqtSignal(int, bool)  # task_id, is_completed
    taskDeleted = pyqtSignal(int)  # task_id
    taskEdited = pyqtSignal(int)  # task_id
    
    def __init__(self, task_id, title, due_date=None, priority=0, category=None, completed=False, parent=None):
        super().__init__(parent)
        
        # Store task data
        self.task_id = task_id
        self.title = title
        self.due_date = due_date
        self.priority = priority  # 0=Low, 1=Medium, 2=High
        self.category = category
        self.completed = completed
        
        # Configure widget
        self.setObjectName("taskWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Set up the UI
        self.setupUI()
        
        # Apply shadow effect
        self.applyShadowEffect()
        
        # Set up animations
        self.setupAnimations()
    
    def setupUI(self):
        """Set up the UI components of the task widget."""
        
        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 8, 10, 8)
        self.main_layout.setSpacing(8)
        
        # Checkbox for completion status
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.completed)
        self.checkbox.setObjectName("taskCheckbox")
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.toggled.connect(self.onCompletionToggled)
        self.main_layout.addWidget(self.checkbox)
        
        # Container for all text information
        self.text_container = QVBoxLayout()
        self.text_container.setSpacing(2)
        
        # Task title
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("taskTitle")
        font = QFont()
        font.setPointSize(10)
        if self.completed:
            self.title_label.setStyleSheet("text-decoration: line-through; color: #6B7280;")
        else:
            font.setBold(True)
            self.title_label.setFont(font)
        self.text_container.addWidget(self.title_label)
        
        # Task details (date, category)
        if self.due_date or self.category:
            self.details_label = QLabel()
            self.details_label.setObjectName("taskDetails")
            
            details_text = ""
            if self.due_date:
                details_text += f"Due: {self.due_date} "
            if self.category:
                if details_text:
                    details_text += "• "
                details_text += f"{self.category}"
                
            self.details_label.setText(details_text)
            self.details_label.setStyleSheet("color: #6B7280; font-size: 9pt;")
            self.text_container.addWidget(self.details_label)
        
        self.main_layout.addLayout(self.text_container)
        
        # Priority indicator
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
        self.actions_btn.setObjectName("taskActionsButton")
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
                #taskWidget {
                    background-color: #F9FAFB;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                }
                #taskTitle {
                    text-decoration: line-through;
                    color: #6B7280;
                }
            """)
        else:
            self.setStyleSheet("""
                #taskWidget {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                }
                #taskTitle {
                    color: #1F2937;
                }
                #taskWidget:hover {
                    border: 1px solid #D1D5DB;
                    background-color: #F9FAFB;
                }
            """)
    
    def applyShadowEffect(self):
        """Apply shadow effect to the widget."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def setupAnimations(self):
        """Set up animations for the widget."""
        # Animation for hover effect
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def onCompletionToggled(self, checked):
        """Handle task completion toggling."""
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
        self.taskCompleted.emit(self.task_id, checked)
    
    def showActionsMenu(self):
        """Show the actions menu for the task."""
        menu = QMenu(self)
        
        edit_action = menu.addAction("Edit Task")
        delete_action = menu.addAction("Delete Task")
        
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
            self.taskEdited.emit(self.task_id)
        elif action == delete_action:
            self.taskDeleted.emit(self.task_id)
    
    def enterEvent(self, event):
        """Handle mouse enter event."""
        super().enterEvent(event)
        
        # Create a raised effect
        current_geo = self.geometry()
        target_geo = current_geo.adjusted(0, -2, 0, 0)
        
        self.hover_animation.setStartValue(current_geo)
        self.hover_animation.setEndValue(target_geo)
        self.hover_animation.start()
    
    def leaveEvent(self, event):
        """Handle mouse leave event."""
        super().leaveEvent(event)
        
        # Restore original position
        current_geo = self.geometry()
        target_geo = current_geo.adjusted(0, 2, 0, 0)
        
        self.hover_animation.setStartValue(current_geo)
        self.hover_animation.setEndValue(target_geo)
        self.hover_animation.start()
    
    def sizeHint(self):
        """Suggested size for the widget."""
        return QSize(300, 70) 