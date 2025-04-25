"""
Weekly Plan view for TaskTitan.

This module provides a weekly view of activities with an hourly breakdown.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QGraphicsView, QGraphicsScene, 
                           QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem,
                           QGraphicsEllipseItem, QSlider, QSizePolicy, QScrollArea, QMenu, QDialog, QMainWindow, QGraphicsProxyWidget,
                           QGraphicsPathItem)
from PyQt6.QtCore import Qt, QDate, QTime, QRectF, QTimer, QPointF, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QColor, QPen, QBrush, QPainterPath, QPainter
from datetime import datetime, timedelta
import random

from app.resources import get_icon
from app.models.activities_manager import ActivitiesManager


class ActivityDetailsDialog(QDialog):
    """Dialog for displaying activity details when clicked on the timeline."""
    
    def __init__(self, activity, parent=None):
        super().__init__(parent)
        self.activity = activity
        self.setWindowTitle("Activity Details")
        
        # Use minimum size instead of fixed size for better adaptability
        self.setMinimumSize(400, 350)
        
        # Store the parent properly to ensure button connections work
        self.parent_widget = parent
        
        # Update completion status from parent if possible
        self.updateCompletionStatusFromParent()
        
        self.setupUI()
        
    def updateCompletionStatusFromParent(self):
        """Try to update the completion status from the parent's activities manager."""
        try:
            activity_id = self.activity.get('id')
            # Try to find an activities manager to get the latest status
            manager = None
            
            # First check immediate parent
            if hasattr(self.parent_widget, 'activities_manager'):
                manager = self.parent_widget.activities_manager
            # Then try parent's parent
            elif hasattr(self.parent_widget, 'parent') and callable(self.parent_widget.parent):
                parent = self.parent_widget.parent()
                if hasattr(parent, 'activities_manager'):
                    manager = parent.activities_manager
            
            # If we found a manager, get the current status
            if manager and activity_id:
                db_activity = manager.get_activity_by_id(activity_id)
                if db_activity:
                    self.activity['completed'] = db_activity.get('completed', self.activity.get('completed', False))
        except Exception as e:
            print(f"Error updating completion status: {e}")
            # Continue anyway
            pass
    
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
        title_label = QLabel(self.activity.get('title', 'Untitled'))
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
        start_time = self.activity.get('start_time')
        end_time = self.activity.get('end_time')
        if start_time and end_time:
            time_frame = QFrame()
            time_frame.setObjectName("detailsItem")
            time_layout = QHBoxLayout(time_frame)
            time_layout.setContentsMargins(10, 10, 10, 10)
            
            time_icon = QLabel("⏱")
            time_icon.setObjectName("icon")
            time_icon.setFixedWidth(30)
            time_layout.addWidget(time_icon)
            
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
            if hasattr(self.parent_widget, 'markActivityComplete'):
                self.parent_widget.markActivityComplete(self.activity.get('id'), self.activity.get('type'))
                self.close()
                return
            
            # Then try parent's parent which is more likely the WeeklyPlanView
            if hasattr(self.parent_widget, 'parent') and callable(self.parent_widget.parent):
                parent = self.parent_widget.parent()
                if hasattr(parent, 'markActivityComplete'):
                    parent.markActivityComplete(self.activity.get('id'), self.activity.get('type'))
                    self.close()
                    return
                # Try to use the activities_manager directly
                elif hasattr(parent, 'activities_manager'):
                    # Get the activity date
                    activity_date = self.activity.get('date')
                    
                    # If date isn't available, try to calculate it from day_index
                    if not activity_date and 'day_index' in self.activity and hasattr(parent, 'current_week_start'):
                        day_index = self.activity.get('day_index', 0)
                        activity_date = parent.current_week_start.addDays(day_index)
                    
                    if activity_date:
                        parent.activities_manager.toggle_activity_completion(
                            self.activity.get('id'), 
                            True,
                            activity_date
                        )
                        # Refresh the view
                        if hasattr(parent, 'updateWeekView'):
                            parent.updateWeekView()
                        self.close()
                        return
            
            # If that fails, try to find the main window
            main_window = self.findMainWindow()
            if main_window and hasattr(main_window, 'activities_manager'):
                # Get the activity date
                activity_date = self.activity.get('date')
                
                # If date isn't available, try to calculate it
                if not activity_date and 'day_index' in self.activity:
                    # Try to find a WeeklyPlanView to get the week start date
                    weekly_view = None
                    if hasattr(main_window, 'weekly_plan_view'):
                        weekly_view = main_window.weekly_plan_view
                    elif hasattr(self.parent_widget, 'current_week_start'):
                        weekly_view = self.parent_widget
                        
                    if weekly_view and hasattr(weekly_view, 'current_week_start'):
                        day_index = self.activity.get('day_index', 0)
                        activity_date = weekly_view.current_week_start.addDays(day_index)
                
                if activity_date:
                    main_window.activities_manager.toggle_activity_completion(
                        self.activity.get('id'), 
                        True,
                        activity_date
                    )
                    # Reload views
                    if hasattr(main_window, 'weekly_plan_view'):
                        main_window.weekly_plan_view.refresh()
                    if hasattr(main_window, 'activities_view'):
                        main_window.activities_view.refresh()
                    # Also check for onActivityCompleted method (matches unified_activities_widget)
                    if hasattr(main_window, 'onActivityCompleted'):
                        main_window.onActivityCompleted(
                            self.activity.get('id'),
                            True,  # Mark as completed
                            self.activity.get('type')
                        )
                    self.close()
                    return
                
        except Exception as e:
            print(f"Error marking activity complete: {e}")
            # At least close the dialog even if operation failed
            self.close()
    
    def findMainWindow(self):
        """Find the main window from any child widget."""
        parent = self.parent_widget
        while parent:
            if isinstance(parent, QMainWindow) or hasattr(parent, 'activities_manager'):
                return parent
            if hasattr(parent, 'parent') and callable(parent.parent):
                parent = parent.parent()
            else:
                break
        return None
    
    def editActivity(self):
        """Open the edit dialog for this activity."""
        try:
            # First try direct parent
            if hasattr(self.parent_widget, 'editActivity'):
                self.parent_widget.editActivity(self.activity.get('id'), self.activity.get('type'))
                self.close()
                return
            
            # Then try parent's parent which is more likely the WeeklyPlanView
            if hasattr(self.parent_widget, 'parent') and callable(self.parent_widget.parent):
                parent = self.parent_widget.parent()
                if hasattr(parent, 'editActivity'):
                    parent.editActivity(self.activity.get('id'), self.activity.get('type'))
                    self.close()
                    return
                    
            # If that fails, try getting the main window through the scene
            if isinstance(self.parent_widget, QGraphicsView):
                view = self.parent_widget
                if hasattr(view, 'parent') and callable(view.parent):
                    view_parent = view.parent()
                    if hasattr(view_parent, 'showEditActivityDialog'):
                        view_parent.showEditActivityDialog(self.activity.get('id'), self.activity.get('type'))
                        self.close()
                        return
            
            # As a fallback, try to find the edit method through any parent
            parent = self.parent_widget
            while parent:
                if hasattr(parent, 'editActivity'):
                    parent.editActivity(self.activity.get('id'), self.activity.get('type'))
                    self.close()
                    break
                elif hasattr(parent, 'showEditActivityDialog'):
                    parent.showEditActivityDialog(self.activity.get('id'), self.activity.get('type'))
                    self.close()
                    break
                if hasattr(parent, 'parent') and callable(parent.parent):
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
            
            # Then try parent's parent which is more likely the WeeklyPlanView
            if hasattr(self.parent_widget, 'parent') and callable(self.parent_widget.parent):
                parent = self.parent_widget.parent()
                if hasattr(parent, 'deleteActivity'):
                    parent.deleteActivity(self.activity.get('id'), self.activity.get('type'))
                    self.close()
                    return
                    
            # If that fails, try getting the main window through the scene
            if isinstance(self.parent_widget, QGraphicsView):
                view = self.parent_widget
                if hasattr(view, 'parent') and callable(view.parent):
                    view_parent = view.parent()
                    if hasattr(view_parent, 'activities_manager'):
                        view_parent.activities_manager.delete_activity(self.activity.get('id'))
                        self.close()
                        return
            
            # As a fallback, try to find the activities manager through any parent
            parent = self.parent_widget
            while parent:
                if hasattr(parent, 'activities_manager'):
                    parent.activities_manager.delete_activity(self.activity.get('id'))
                    self.close()
                    break
                if hasattr(parent, 'parent') and callable(parent.parent):
                    parent = parent.parent()
                else:
                    break
                    
        except Exception as e:
            print(f"Error deleting activity: {e}")
            # At least close the dialog even if operation failed
            self.close()


class WeeklyPlanView(QWidget):
    """Widget for displaying a week view with hourly breakdown of activities."""
    
    # Signals
    activityClicked = pyqtSignal(dict)  # Emitted when an activity is clicked
    activityCompletionChanged = pyqtSignal(int, bool, str)  # id, completed status, type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Configure view settings
        self.zoom_factor = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 2.0
        
        # Track the current week
        self.current_week_start = self.getStartOfWeek(QDate.currentDate())
        
        # Map of activity IDs to their graphical items
        self.activity_items = {}
        
        # Store activities data
        self.activities = []
        
        # Get activities manager from parent or create new one
        if hasattr(parent, 'activities_manager'):
            print("Using parent's activities_manager")
            self.activities_manager = parent.activities_manager
        else:
            print("Creating new ActivitiesManager instance")
            # Create our own manager if needed
            self.activities_manager = ActivitiesManager()
            if hasattr(parent, 'conn') and hasattr(parent, 'cursor'):
                print("Setting connection from parent")
                self.activities_manager.set_connection(parent.conn, parent.cursor)
        
        # Set up the UI
        self.setupUI()
        
        # Load initial data
        self.loadActivities()
        
        # Set background color
        self.setStyleSheet("background-color: #F9FAFB;")
        
        # Connect to parent signals if available
        self.connectParentSignals()

    def setupUI(self):
        """Set up the user interface components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Set base styles
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
                color: #374151;
                font-weight: bold;
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
            QSlider::groove:horizontal {
                height: 4px;
                background: #D1D5DB;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #4F46E5;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #111827;
            }
        """)
        
        # Add a fancy header with gradient background
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
            border-radius: 10px;
            padding: 10px;
        """)
        header_frame.setFixedHeight(70)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 5, 15, 5)
        
        # Title and navigation
        nav_layout = QHBoxLayout()
        
        # Week navigation buttons
        prev_week_btn = QPushButton("◀ Previous Week")
        prev_week_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        prev_week_btn.clicked.connect(self.previousWeek)
        header_layout.addWidget(prev_week_btn)
        
        # Week display
        self.week_label = QLabel()
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.week_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: white;
        """)
        self.updateWeekLabel()
        header_layout.addWidget(self.week_label, 1)
        
        # Next week button
        next_week_btn = QPushButton("Next Week ▶")
        next_week_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        next_week_btn.clicked.connect(self.nextWeek)
        header_layout.addWidget(next_week_btn)
        
        # Today button with calendar icon
        today_btn = QPushButton("Today")
        today_icon = get_icon("calendar-today")
        if not today_icon.isNull():
            today_btn.setIcon(today_icon)
        else:
            today_btn.setText("📅 Today")
        today_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #4F46E5;
                font-weight: bold;
                border: none;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
            }
        """)
        today_btn.clicked.connect(self.goToCurrentWeek)
        header_layout.addWidget(today_btn)
        
        main_layout.addWidget(header_frame)
        
        # Controls panel
        controls_panel = QFrame()
        controls_panel.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            border: 1px solid #E5E7EB;
        """)
        controls_layout = QHBoxLayout(controls_panel)
        controls_layout.setContentsMargins(15, 10, 15, 10)
        
        # Zoom controls
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("font-weight: bold;")
        controls_layout.addWidget(zoom_label)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(int(self.min_zoom * 100), int(self.max_zoom * 100))
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.zoom_slider.valueChanged.connect(self.handleZoomSlider)
        self.zoom_slider.setMaximumWidth(150)
        controls_layout.addWidget(self.zoom_slider)
        
        zoom_out_btn = QPushButton()
        zoom_out_btn.setFixedSize(30, 30)
        zoom_out_icon = get_icon("zoom-out")
        if not zoom_out_icon.isNull():
            zoom_out_btn.setIcon(zoom_out_icon)
        else:
            zoom_out_btn.setText("🔍-")
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.clicked.connect(self.zoomOut)
        controls_layout.addWidget(zoom_out_btn)
        
        zoom_in_btn = QPushButton()
        zoom_in_btn.setFixedSize(30, 30)
        zoom_in_icon = get_icon("zoom-in")
        if not zoom_in_icon.isNull():
            zoom_in_btn.setIcon(zoom_in_icon)
        else:
            zoom_in_btn.setText("🔍+")
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.clicked.connect(self.zoomIn)
        controls_layout.addWidget(zoom_in_btn)
        
        reset_btn = QPushButton("Reset View")
        reset_icon = get_icon("reset")
        if not reset_icon.isNull():
            reset_btn.setIcon(reset_icon)
        reset_btn.clicked.connect(self.resetView)
        controls_layout.addWidget(reset_btn)
        
        # Add filter options
        controls_layout.addStretch(1)
        
        # Legend section
        legend_label = QLabel("Activity Types:")
        legend_label.setStyleSheet("font-weight: bold;")
        controls_layout.addWidget(legend_label)
        
        # Task color
        task_color = QFrame()
        task_color.setFixedSize(16, 16)
        task_color.setStyleSheet("background-color: #F87171; border-radius: 8px;")
        controls_layout.addWidget(task_color)
        controls_layout.addWidget(QLabel("Task"))
        
        # Event color
        event_color = QFrame()
        event_color.setFixedSize(16, 16)
        event_color.setStyleSheet("background-color: #818CF8; border-radius: 8px;")
        controls_layout.addWidget(event_color)
        controls_layout.addWidget(QLabel("Event"))
        
        # Habit color
        habit_color = QFrame()
        habit_color.setFixedSize(16, 16)
        habit_color.setStyleSheet("background-color: #34D399; border-radius: 8px;")
        controls_layout.addWidget(habit_color)
        controls_layout.addWidget(QLabel("Habit"))
        
        main_layout.addWidget(controls_panel)
        
        # Create the weekly view in a graphics scene
        self.view = QGraphicsView()
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # Set nice background
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor("#F9FAFB")))
        self.view.setScene(self.scene)
        
        # Add a border to the view
        self.view.setFrameShape(QFrame.Shape.StyledPanel)
        self.view.setStyleSheet("""
            border: 1px solid #D1D5DB;
            background-color: #F9FAFB;
            border-radius: 8px;
        """)
        
        main_layout.addWidget(self.view, 1)
        
        # Status message
        self.status_label = QLabel("Click and drag to pan, use Ctrl+scroll to zoom")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #6B7280; font-style: italic;")
        main_layout.addWidget(self.status_label)
    
    def getStartOfWeek(self, date):
        """Get the first day (Monday) of the week containing the given date."""
        days_to_monday = date.dayOfWeek() - 1  # Qt's Monday is 1, Sunday is 7
        return date.addDays(-days_to_monday)
    
    def updateWeekLabel(self):
        """Update the week label to show the current week range."""
        week_end = self.current_week_start.addDays(6)
        
        start_month = self.current_week_start.toString("MMM")
        end_month = week_end.toString("MMM")
        
        if start_month == end_month:
            # Same month
            self.week_label.setText(
                f"{start_month} {self.current_week_start.toString('d')} - {week_end.toString('d')}, {week_end.toString('yyyy')}"
            )
        else:
            # Different months
            self.week_label.setText(
                f"{start_month} {self.current_week_start.toString('d')} - {end_month} {week_end.toString('d')}, {week_end.toString('yyyy')}"
            )
    
    def handleZoomSlider(self, value):
        """Handle zoom slider changes."""
        self.zoom_factor = value / 100.0
        self.applyZoom()
        
    def zoomIn(self):
        """Zoom in on the view."""
        self.zoom_factor = min(self.zoom_factor * 1.2, self.max_zoom)
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.applyZoom()
    
    def zoomOut(self):
        """Zoom out on the view."""
        self.zoom_factor = max(self.zoom_factor / 1.2, self.min_zoom)
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.applyZoom()
    
    def applyZoom(self):
        """Apply the current zoom factor to the view."""
        self.view.resetTransform()
        self.view.scale(self.zoom_factor, self.zoom_factor)
        
        # Update status message
        self.status_label.setText(f"Zoom: {int(self.zoom_factor * 100)}% - Click and drag to pan")
    
    def resetView(self):
        """Reset the view to the default state."""
        self.zoom_factor = 1.0
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.view.resetTransform()
        if not self.scene.items():
            return
        self.view.setSceneRect(self.scene.itemsBoundingRect())
        self.view.centerOn(0, 0)
        
        # Update status message
        self.status_label.setText("View reset - Click and drag to pan")
    
    def previousWeek(self):
        """Go to the previous week."""
        self.current_week_start = self.current_week_start.addDays(-7)
        self.updateWeekLabel()
        self.loadActivities()
    
    def nextWeek(self):
        """Go to the next week."""
        self.current_week_start = self.current_week_start.addDays(7)
        self.updateWeekLabel()
        self.loadActivities()
    
    def goToCurrentWeek(self):
        """Go to the current week."""
        self.current_week_start = self.getStartOfWeek(QDate.currentDate())
        self.updateWeekLabel()
        self.loadActivities()
    
    def loadActivities(self):
        """Load activities for the current week and update the view."""
        self.activities = []
        
        # Check if we have an activities manager
        if not hasattr(self, 'activities_manager') or not self.activities_manager:
            print("ERROR: Activities manager not available")
            self.status_label.setText("Error: Activities manager not available")
            return
        
        print(f"Loading activities for week starting {self.current_week_start.toString()}")
        
        # Loop through each day of the week
        for day in range(7):
            current_date = self.current_week_start.addDays(day)
            
            # Get activities for this day
            day_activities = self.activities_manager.get_activities_for_date(current_date)
            
            # Store with additional info for rendering
            for activity in day_activities:
                activity_id = activity.get('id')
                
                # Ensure we have the latest completion status from database
                db_activity = self.activities_manager.get_activity_by_id(activity_id)
                if db_activity and 'completed' in db_activity:
                    activity['completed'] = db_activity.get('completed', False)
                    print(f"Activity {activity_id} completion status: {activity['completed']}")
                
                activity['day_index'] = day
                self.activities.append(activity)
        
        print(f"Loaded {len(self.activities)} activities")
        
        # Update the view
        self.updateWeekView()
    
    def updateWeekView(self):
        """Update the weekly view with current activities."""
        print("Updating week view...")
        
        # Clear current scene
        self.scene.clear()
        self.activity_items = {}
        
        # Draw the weekly grid
        self.drawWeekGrid()
        
        # Add activities to the grid
        self.addActivitiesToGrid()
        
        # Make sure the whole grid is visible
        if self.scene.items():
            self.view.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))
            
        print("Week view updated")
    
    def drawWeekGrid(self):
        """Draw the weekly grid with day columns and hour rows."""
        # Constants for grid
        day_width = 150  # Width of each day column
        hour_height = 180  # Height of each hour row (increased from 60 to 120)
        grid_height = 24 * hour_height  # 24 hours
        grid_width = 7 * day_width  # 7 days
        
        # Add margin for hour labels
        hour_label_width = 90
        hour_label_margin = 10
        
        # Draw day headers
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day in range(7):
            x_pos = day * day_width + hour_label_width
            
            # Day header background
            header_rect = QGraphicsRectItem(x_pos, -50, day_width, 50)
            header_rect.setPen(QPen(QColor("#D1D5DB")))
            
            # Use different background for weekend
            if day >= 5:  # Saturday and Sunday
                header_rect.setBrush(QBrush(QColor("#F3F4F6")))
            else:
                header_rect.setBrush(QBrush(QColor("#E5E7EB")))
                
            self.scene.addItem(header_rect)
            
            # Day name
            current_date = self.current_week_start.addDays(day)
            day_text = f"{day_names[day]}\n{current_date.toString('d MMM')}"
            
            day_label = QGraphicsTextItem(day_text)
            day_label.setPos(x_pos + (day_width - day_label.boundingRect().width()) / 2, -45)
            day_label.setDefaultTextColor(QColor("#1F2937"))
            
            # Highlight today
            if current_date == QDate.currentDate():
                # Draw today with a special style
                today_rect = QGraphicsRectItem(x_pos, -50, day_width, 50)
                today_rect.setPen(QPen(QColor("#4F46E5"), 2))
                today_rect.setBrush(QBrush(QColor(99, 102, 241, 50)))  # Indigo with transparency
                self.scene.addItem(today_rect)
                
                day_label.setDefaultTextColor(QColor("#4F46E5"))
                font = day_label.font()
                font.setBold(True)
                day_label.setFont(font)
            
            self.scene.addItem(day_label)
            
            # Day column borders
            col_line = QGraphicsLineItem(x_pos, 0, x_pos, grid_height)
            col_line.setPen(QPen(QColor("#D1D5DB")))
            self.scene.addItem(col_line)
        
        # Draw the right border of the last column
        right_line = QGraphicsLineItem(grid_width + hour_label_width, 0, grid_width + hour_label_width, grid_height)
        right_line.setPen(QPen(QColor("#D1D5DB")))
        self.scene.addItem(right_line)
        
        # Add time axis background
        time_axis_bg = QGraphicsRectItem(0, -50, hour_label_width, grid_height + 50)
        time_axis_bg.setPen(QPen(Qt.PenStyle.NoPen))
        time_axis_bg.setBrush(QBrush(QColor("#F1F5F9")))
        time_axis_bg.setZValue(-2)
        self.scene.addItem(time_axis_bg)
        
        # Add time axis header
        time_header = QGraphicsTextItem("Time")
        time_header.setPos(10, -35)
        time_header.setDefaultTextColor(QColor("#1F2937"))
        font = time_header.font()
        font.setBold(True)
        time_header.setFont(font)
        self.scene.addItem(time_header)
        
        # Draw hour rows
        for hour in range(25):  # 0 to 24 (include bottom border)
            y_pos = hour * hour_height
            
            # Hour row line
            row_line = QGraphicsLineItem(hour_label_width, y_pos, grid_width + hour_label_width, y_pos)
            
            # Make the lines for 6h, 12h, 18h thicker
            if hour % 6 == 0:
                row_line.setPen(QPen(QColor("#9CA3AF"), 1.5))
            else:
                row_line.setPen(QPen(QColor("#D1D5DB")))
                
            self.scene.addItem(row_line)
            
            # Hour label (except for the bottom border)
            if hour < 24:
                # Format: 00:00, 01:00, etc.
                hour_text = f"{hour:02d}:00"
                
                # Add AM/PM indicator
                if hour == 0:
                    hour_text += " "
                elif hour == 12:
                    hour_text += " "
                elif hour < 12:
                    hour_text += " AM"
                else:
                    hour_text += " PM"
                
                hour_label = QGraphicsTextItem(hour_text)
                # Center the label vertically with the grid line
                hour_label.setPos(hour_label_margin, y_pos - hour_label.boundingRect().height() / 2)
                
                # Highlight important hours
                if hour % 6 == 0:
                    hour_label.setDefaultTextColor(QColor("#1F2937"))
                    font = hour_label.font()
                    font.setBold(True)
                    hour_label.setFont(font)
                else:
                    hour_label.setDefaultTextColor(QColor("#4B5563"))
                
                self.scene.addItem(hour_label)
        
        # Add work hours highlight (e.g., 9 AM to 5 PM)
        work_start = 9
        work_end = 17
        work_highlight = QGraphicsRectItem(hour_label_width, work_start * hour_height, 
                                         grid_width, (work_end - work_start) * hour_height)
        work_highlight.setPen(QPen(Qt.PenStyle.NoPen))
        work_highlight.setBrush(QBrush(QColor(243, 244, 246, 100)))  # Light gray with transparency
        work_highlight.setZValue(-1)
        self.scene.addItem(work_highlight)
        
        # Add half-hour markers
        for hour in range(24):
            y_pos = hour * hour_height + hour_height / 2
            half_hour_line = QGraphicsLineItem(hour_label_width, y_pos, 
                                             hour_label_width + grid_width, y_pos)
            half_hour_line.setPen(QPen(QColor("#E5E7EB"), 1, Qt.PenStyle.DotLine))
            self.scene.addItem(half_hour_line)
        
        # Add now indicator if current week is shown
        if self.isCurrentWeek():
            today = QDate.currentDate()
            today_index = today.dayOfWeek() - 1  # 0 = Monday, 6 = Sunday
            
            current_time = QTime.currentTime()
            hour_decimal = current_time.hour() + current_time.minute() / 60.0
            
            # Only show if today is within view
            if 0 <= today_index <= 6:
                now_x = today_index * day_width + hour_label_width
                now_y = hour_decimal * hour_height
                
                # Add subtle gradient background for current time
                now_rect = QGraphicsRectItem(now_x, now_y - 1, day_width, 2)
                now_rect.setPen(QPen(Qt.PenStyle.NoPen))
                now_rect.setBrush(QBrush(QColor("#EF4444")))  # Red with less opacity
                now_rect.setZValue(3)
                self.scene.addItem(now_rect)
                
                # Add a subtle circle indicator
                now_circle = QGraphicsEllipseItem(now_x - 6, now_y - 6, 12, 12)
                now_circle.setBrush(QBrush(QColor("#EF4444")))
                now_circle.setPen(QPen(QColor("#FFFFFF"), 1.5))
                now_circle.setZValue(4)
                self.scene.addItem(now_circle)
                
                # Add a small "now" text that's more subtle
                now_label = QGraphicsTextItem("now")
                now_label.setDefaultTextColor(QColor("#EF4444"))
                now_label.setPos(now_x - 30, now_y - 6)
                font = now_label.font()
                font.setBold(True)
                font.setPointSize(8)  # Smaller font
                now_label.setFont(font)
                now_label.setZValue(4)
                self.scene.addItem(now_label)
    
    def isCurrentWeek(self):
        """Check if the view is showing the current week."""
        today = QDate.currentDate()
        start_of_week = self.getStartOfWeek(today)
        return self.current_week_start == start_of_week
    
    def addActivitiesToGrid(self):
        """Add activities to the weekly grid."""
        if not self.activities:
            # No activities to display
            self.status_label.setText(f"No activities found for this week ({self.current_week_start.toString('d MMM')} - {self.current_week_start.addDays(6).toString('d MMM')})")
            return
        
        # Constants
        day_width = 150  # Width of each day column
        hour_height = 180  # Height of each hour row
        hour_label_width = 90  # Width of the time axis
        
        # Group activities by day for better overlap handling
        activities_by_day = {}
        for day in range(7):
            activities_by_day[day] = []
        
        # Sort activities by start time and duration (longer activities first)
        sorted_activities = sorted(
            self.activities,
            key=lambda a: (
                a.get('day_index', 0),
                a.get('start_time').hour() if a.get('start_time') else 0,
                a.get('start_time').minute() if a.get('start_time') else 0,
                -(a.get('end_time').hour() * 60 + a.get('end_time').minute() -
                  a.get('start_time').hour() * 60 - a.get('start_time').minute())
                if a.get('start_time') and a.get('end_time') else 0
            )
        )
        
        # Group by day first
        for activity in sorted_activities:
            day_index = activity.get('day_index', 0)
            if 0 <= day_index <= 6:  # Make sure day index is valid
                activities_by_day[day_index].append(activity)
        
        # Process activities by day to handle overlaps better
        for day_index, day_activities in activities_by_day.items():
            # Create time slots to track occupied regions
            time_slots = []  # List of tuples (start_hour, end_hour, column_index)
            
            for activity in day_activities:
                try:
                    start_time = activity.get('start_time')
                    end_time = activity.get('end_time')
                    
                    if not start_time or not end_time:
                        continue
                    
                    # Convert to decimal hours
                    start_hour = start_time.hour() + start_time.minute() / 60.0
                    end_hour = end_time.hour() + end_time.minute() / 60.0
                    
                    # Ensure end time is after start time
                    if end_hour <= start_hour:
                        # Assume it's a short activity if times are equal
                        if end_hour == start_hour:
                            end_hour = start_hour + 0.5
                        else:
                            # Assume it crosses midnight (rare case)
                            end_hour += 24.0
                    
                    # Find available column by checking overlaps
                    column = 0
                    max_columns = 5  # Maximum number of columns to prevent going out of bounds
                    
                    # Find first available column where this activity can fit
                    while column < max_columns:
                        overlap = False
                        for slot_start, slot_end, slot_column in time_slots:
                            # Check if this column and time range overlaps with existing slot
                            if (column == slot_column and 
                                ((start_hour <= slot_end and end_hour >= slot_start) or
                                 (slot_start <= end_hour and slot_end >= start_hour))):
                                overlap = True
                                break
                        
                        if not overlap:
                            break
                        column += 1
                    
                    # Cap column to max_columns - 1 to ensure it doesn't go out of bounds
                    column = min(column, max_columns - 1)
                    
                    # Record this time slot
                    time_slots.append((start_hour, end_hour, column))
                    
                    # Calculate column width based on number of columns we might need
                    max_columns_needed = 1
                    for _, _, existing_column in time_slots:
                        max_columns_needed = max(max_columns_needed, existing_column + 1)
                    max_columns_needed = min(max_columns_needed, max_columns)
                    
                    # Determine position and size
                    x_pos = day_index * day_width + hour_label_width
                    width = day_width / max_columns_needed
                    x_pos += column * width
                    width = min(width, day_width - (column * (day_width / max_columns_needed)))
                    
                    y_pos = start_hour * hour_height
                    height = (end_hour - start_hour) * hour_height
                    
                    # Make sure we don't exceed the grid height
                    if y_pos + height > 24 * hour_height:
                        height = 24 * hour_height - y_pos
                    
                    # Determine activity color
                    if activity.get('color'):
                        color = QColor(activity.get('color'))
                    else:
                        # Use default colors based on type
                        activity_type = activity.get('type', '')
                        if activity_type == 'task':
                            color = QColor("#F87171")  # Red
                        elif activity_type == 'event':
                            color = QColor("#818CF8")  # Indigo
                        elif activity_type == 'habit':
                            color = QColor("#34D399")  # Green
                        else:
                            color = QColor("#9CA3AF")  # Gray
                    
                    # Leave margins for better visual separation
                    margin = 2
                    actual_x = x_pos + margin
                    actual_width = width - 2 * margin
                    
                    # Check completion status
                    is_completed = bool(activity.get('completed', False))
                    
                    # Modify color based on completion status
                    if is_completed:
                        # Make completed activities show a different appearance
                        # Option 1: Add a green color overlay
                        color = color.lighter(110)  # Lighten the base color
                        color.setAlpha(180)
                    else:
                        # Regular transparency for uncompleted activities
                        color.setAlpha(180)
                    
                    # Create rectangle path
                    path = QPainterPath()
                    path.addRoundedRect(QRectF(actual_x, y_pos, actual_width, height), 8, 8)
                    
                    # Add the activity rectangle
                    rounded_rect = self.scene.addPath(path, QPen(color.darker(), 1), QBrush(color))
                    rounded_rect.setData(0, activity.get('id'))
                    rounded_rect.setData(1, activity.get('type'))
                    rounded_rect.setData(2, is_completed)  # Store completion status
                    rounded_rect.setZValue(1)
                    
                    # Add shadow effect
                    shadow_path = QPainterPath()
                    shadow_path.addRoundedRect(QRectF(actual_x + 2, y_pos + 2, actual_width, height), 8, 8)
                    shadow_rect = self.scene.addPath(shadow_path, QPen(Qt.PenStyle.NoPen), 
                                                   QBrush(QColor(0, 0, 0, 20)))
                    shadow_rect.setZValue(0.5)
                    
                    # If date isn't available, calculate it from day_index
                    if not activity.get('date') and 'day_index' in activity:
                        day_index = activity.get('day_index', 0)
                        activity_date = self.current_week_start.addDays(day_index)
                        activity['date'] = activity_date
                    
                    # Enable interactivity for the rectangle
                    rounded_rect.setAcceptHoverEvents(True)
                    rounded_rect.setCursor(Qt.CursorShape.PointingHandCursor)
                    
                    # Add completion indicator
                    if is_completed:
                        # Add a completion indicator - green bar on the left
                        complete_path = QPainterPath()
                        complete_path.addRoundedRect(QRectF(actual_x, y_pos, 6, height), 3, 3)
                        completion_bar = self.scene.addPath(
                            complete_path, 
                            QPen(Qt.PenStyle.NoPen), 
                            QBrush(QColor("#10B981"))
                        )
                        completion_bar.setZValue(2)  # Above the activity rectangle
                    
                    # Add activity title with better text handling
                    title_text = QGraphicsTextItem(activity.get('title', 'Untitled'))
                    title_text.setTextWidth(actual_width - 16)  # Leave some padding
                    
                    # Create HTML text with ellipsis for long titles
                    title = activity.get('title', 'Untitled')
                    if len(title) > 30 and height < 60:  # For small blocks
                        title = title[:27] + "..."
                    
                    # Use HTML formatting for better text control
                    html_text = f'<div style="max-width: {actual_width-16}px; word-wrap: break-word;">{title}</div>'
                    title_text.setHtml(html_text)
                    
                    title_text.setPos(actual_x + 8, y_pos + 5)
                    title_text.setDefaultTextColor(QColor("#FFFFFF"))
                    font = title_text.font()
                    font.setBold(True)
                    
                    # Adjust font size based on available space
                    if actual_width < 70:
                        font.setPointSize(8)  # Smaller font for narrow blocks
                    elif actual_width < 100:
                        font.setPointSize(9)
                    else:
                        font.setPointSize(10)
                        
                    title_text.setFont(font)
                    
                    # Add enhanced background for better text readability
                    text_bg_height = min(title_text.boundingRect().height() + 10, height)
                    text_bg = QGraphicsRectItem(actual_x, y_pos, actual_width, text_bg_height)
                    text_bg.setPen(QPen(Qt.PenStyle.NoPen))
                    
                    # Use a darker background with gradient for better text visibility
                    darker_color = color.darker(150)
                    darker_color.setAlpha(180)
                    text_bg.setBrush(QBrush(darker_color))
                    text_bg.setZValue(1.5)
                    self.scene.addItem(text_bg)
                    
                    title_text.setZValue(2)
                    self.scene.addItem(title_text)
                    
                    # Adjust remaining content based on title height
                    content_start_y = y_pos + text_bg_height + 2
                    
                    # Add time text if enough space
                    remaining_height = y_pos + height - content_start_y
                    if remaining_height > 20 and actual_width > 60:
                        time_format = "HH:mm" if actual_width > 70 else "HH"
                        time_text = QGraphicsTextItem(f"{start_time.toString(time_format)}-{end_time.toString(time_format)}")
                        time_text.setTextWidth(actual_width - 10)
                        time_text.setPos(actual_x + 8, content_start_y)
                        time_text.setDefaultTextColor(QColor("#FFFFFF"))
                        
                        time_font = time_text.font()
                        time_font.setBold(True)
                        if actual_width < 70:
                            time_font.setPointSize(time_font.pointSize() - 1)
                        time_text.setFont(time_font)
                        
                        time_text.setZValue(2)
                        self.scene.addItem(time_text)
                    
                    # Add activity type indicator if there's enough space
                    if height > 60 and actual_width > 50:
                        type_text = QGraphicsTextItem(activity.get('type', '').capitalize())
                        type_text.setTextWidth(actual_width - 10)
                        type_text.setPos(actual_x + 8, y_pos + height - 25)
                        type_text.setDefaultTextColor(QColor("#FFFFFF"))
                        
                        type_font = type_text.font()
                        type_font.setBold(True)
                        if actual_width < 70:
                            type_font.setPointSize(type_font.pointSize() - 1)
                        type_text.setFont(type_font)
                        
                        # Create a rounded background for the type label
                        if height > 80:  # Only add background if there's enough space
                            type_bg = QGraphicsRectItem(actual_x + 6, y_pos + height - 25, 
                                                     type_text.boundingRect().width() + 10, 20)
                            type_bg.setPen(QPen(Qt.PenStyle.NoPen))
                            type_bg.setBrush(QBrush(QColor(0, 0, 0, 60)))  # Semi-transparent black
                            type_bg.setZValue(1.8)
                            self.scene.addItem(type_bg)
                        
                        type_text.setZValue(2)
                        self.scene.addItem(type_text)
                    
                    # Store reference to the activity
                    self.activity_items[activity.get('id')] = {
                        'rect': rounded_rect,
                        'activity': activity
                    }
                    
                except Exception as e:
                    print(f"Error adding activity to grid: {e}")
        
        # Set scene event handler
        self.scene.mousePressEvent = self.handleSceneClick
        
        # Update status
        self.status_label.setText(f"Showing {len(self.activities)} activities")

    def handleSceneClick(self, event):
        """Handle clicks on the scene, showing activity details or toggling completion."""
        try:
            # Check if it's a right-click
            if event.button() == Qt.MouseButton.RightButton:
                self.showContextMenu(event)
                return
                
            # For left clicks, check what was clicked
            items = self.scene.items(event.scenePos())
            
            for item in items:
                # Check if it's an activity rectangle
                if isinstance(item, QPainterPath) and item.data(0):
                    activity_id = item.data(0)
                    activity_type = item.data(1)
                    
                    # Check if Alt key is pressed to toggle completion
                    modifiers = event.modifiers()
                    if modifiers & Qt.KeyboardModifier.AltModifier:
                        # Toggle completion status
                        activity = None
                        if activity_id in self.activity_items:
                            activity = self.activity_items[activity_id]['activity']
                            # Toggle completion state
                            is_completed = not bool(activity.get('completed', False))
                            print(f"Alt+click detected: Toggling activity {activity_id} completion to {is_completed}")
                            self.toggleActivityCompletion(activity_id, is_completed, activity_type)
                        event.accept()
                        return
                    
                    # Regular click - show activity details
                    self.showActivityDetails(activity_id, activity_type)
                    event.accept()
                    return
            
            # If we get here, no activity was clicked
            event.accept()
            
        except Exception as e:
            print(f"Error handling scene click: {e}")
            import traceback
            traceback.print_exc()
            event.accept()
    
    def showContextMenu(self, event):
        """Show a context menu for an activity when right-clicked."""
        try:
            # Get the item under the cursor
            pos = event.scenePos()
            items = self.scene.items(pos)
            
            for item in items:
                # Check if it's an activity rectangle
                if isinstance(item, QPainterPath) and item.data(0):
                    activity_id = item.data(0)
                    activity_type = item.data(1)
                    
                    if activity_id not in self.activity_items:
                        continue
                        
                    activity = self.activity_items[activity_id]['activity']
                    
                    # Make sure activity has a date
                    if not activity.get('date') and 'day_index' in activity:
                        day_index = activity.get('day_index', 0)
                        activity_date = self.current_week_start.addDays(day_index)
                        activity['date'] = activity_date
                    
                    # Get the latest completion status
                    is_completed = bool(activity.get('completed', False))
                    
                    # Create the context menu
                    menu = QMenu()
                    
                    # Add menu actions
                    view_action = menu.addAction("View Details")
                    
                    # Completion toggle option
                    complete_text = "Mark Incomplete" if is_completed else "Mark Complete"
                    complete_action = menu.addAction(complete_text)
                    if is_completed:
                        complete_action.setIcon(QIcon.fromTheme("edit-undo"))
                    else:
                        complete_action.setIcon(QIcon.fromTheme("dialog-ok"))
                    
                    menu.addSeparator()
                    
                    # Edit and delete options
                    edit_action = menu.addAction("Edit Activity")
                    edit_action.setIcon(QIcon.fromTheme("document-edit"))
                    
                    delete_action = menu.addAction("Delete Activity")
                    delete_action.setIcon(QIcon.fromTheme("edit-delete"))
                    
                    # Show the context menu at cursor position
                    # Convert scene position to view position, then to global screen position
                    view_pos = self.view.mapFromScene(pos)
                    global_pos = self.view.viewport().mapToGlobal(view_pos)
                    
                    action = menu.exec(global_pos)
                    
                    # Handle the selected action
                    if action == view_action:
                        self.showActivityDetails(activity_id, activity_type)
                    elif action == complete_action:
                        # Toggle the completion status
                        new_status = not is_completed
                        print(f"Toggling completion from menu: {activity_id} to {new_status}")
                        self.toggleActivityCompletion(activity_id, new_status, activity_type)
                    elif action == edit_action:
                        self.editActivity(activity_id, activity_type)
                    elif action == delete_action:
                        self.deleteActivity(activity_id, activity_type)
                    
                    # Don't propagate the event further
                    event.accept()
                    return
            
            # If we get here, no activity was clicked
            event.accept()
                
        except Exception as e:
            print(f"Error showing context menu: {e}")
            import traceback
            traceback.print_exc()
            event.accept()
    
    def showActivityDetails(self, activity_id, activity_type):
        """Show activity details in a dialog."""
        if activity_id not in self.activity_items:
            print(f"Activity {activity_id} not found")
            return
            
        activity = self.activity_items[activity_id]['activity']
        
        try:
            dialog = ActivityDetailsDialog(activity, self)
            dialog.exec()
        except Exception as e:
            print(f"Error showing activity details: {e}")
            import traceback
            traceback.print_exc()

    def toggleActivityCompletion(self, activity_id, is_completed, activity_type):
        """Toggle the completion status of an activity."""
        try:
            print(f"Weekly Plan View: Toggling activity {activity_id} ({activity_type}) completion to {is_completed}")
            
            # Find the activity
            if activity_id not in self.activity_items:
                print(f"Activity {activity_id} not found in activity_items")
                return
                
            activity_item = self.activity_items[activity_id]
            activity = activity_item['activity']
            
            # Update the activity's completion status
            activity['completed'] = is_completed
            
            # Get the activity date - this is critical for the database update
            activity_date = None
            if activity.get('date'):
                activity_date = activity.get('date')
            elif 'day_index' in activity:
                day_index = activity.get('day_index', 0)
                activity_date = self.current_week_start.addDays(day_index)
            
            if not activity_date:
                print("ERROR: Could not determine activity date - database update will fail")
                return
                
            # Always emit our own signal for other components to listen to
            print(f"Emitting activityCompletionChanged signal: {activity_id}, {is_completed}, {activity_type}")
            self.activityCompletionChanged.emit(activity_id, is_completed, activity_type)
            
            # DIRECT DATABASE UPDATE - most reliable method
            # Try all possible ways to get to an activities_manager
            activities_manager = None
            
            # Priority 1: direct access
            if hasattr(self, 'activities_manager') and self.activities_manager:
                activities_manager = self.activities_manager
                print(f"Using self.activities_manager")
            # Priority 2: parent's activities_manager
            elif hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'activities_manager'):
                activities_manager = self.parent.activities_manager
                print(f"Using parent.activities_manager")
            
            # Now use the activities_manager we found
            if activities_manager:
                print(f"Calling toggle_activity_completion with date={activity_date.toString()}")
                # Use the correct method signature with date parameter
                success = activities_manager.toggle_activity_completion(
                    activity_id,
                    is_completed,
                    activity_date
                )
                
                if success:
                    print(f"Database update successful")
                else:
                    print(f"Database update failed")
            else:
                print("ERROR: No activities_manager found - cannot update database")
                
            # Update the visuals for this activity
            self.updateActivityVisuals(activity_id, is_completed)
            
            # If parent has onActivityCompleted handler, call it
            if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'onActivityCompleted'):
                print(f"Calling parent.onActivityCompleted")
                self.parent.onActivityCompleted(activity_id, is_completed, activity_type)
            
            # If this is in the parent, update parent's activities view
            if hasattr(self, 'parent') and self.parent:
                if hasattr(self.parent, 'activities_view') and self.parent.activities_view:
                    print(f"Refreshing parent's activities view")
                    self.parent.activities_view.refresh()
            
            # If activities view exists directly, refresh it
            if hasattr(self, 'activities_view') and self.activities_view:
                print(f"Refreshing self.activities_view")
                self.activities_view.refresh()
                
        except Exception as e:
            print(f"Error toggling activity completion: {e}")
            import traceback
            traceback.print_exc()

    def updateActivityVisuals(self, activity_id, is_completed):
        """Update the visual appearance of an activity without refreshing the whole view."""
        try:
            print(f"Updating visuals for activity {activity_id}, completed={is_completed}")
            
            if activity_id not in self.activity_items:
                print(f"Activity {activity_id} not found in activity_items")
                return
                
            activity_item = self.activity_items[activity_id]
            activity_rect = activity_item['rect']
            activity = activity_item['activity']
            
            # Update the stored completion state
            activity['completed'] = is_completed
            activity_rect.setData(2, is_completed)
            
            # Get the rectangle's properties
            rect = activity_rect.path().boundingRect()
            actual_x = rect.x()
            y_pos = rect.y()
            height = rect.height()
            actual_width = rect.width()
            
            # Determine the activity color - same logic as in addActivitiesToGrid
            if activity.get('color'):
                color = QColor(activity.get('color'))
            else:
                # Use default colors based on type
                activity_type = activity.get('type', '')
                if activity_type == 'task':
                    color = QColor("#F87171")  # Red
                elif activity_type == 'event':
                    color = QColor("#818CF8")  # Indigo
                elif activity_type == 'habit':
                    color = QColor("#34D399")  # Green
                else:
                    color = QColor("#9CA3AF")  # Gray
            
            # Modify color based on completion status
            if is_completed:
                # Lighten for completed activities
                color = color.lighter(110)
                color.setAlpha(180)
            else:
                # Regular alpha for uncompleted
                color.setAlpha(180)
                
            # Update the activity rectangle's color
            activity_rect.setBrush(QBrush(color))
            activity_rect.setPen(QPen(color.darker(), 1))
            
            # Remove any existing completion indicators
            print("Removing old completion indicators")
            for item in self.scene.items():
                try:
                    # Remove green bar indicators
                    if (isinstance(item, QPainterPath) and
                        item != activity_rect and
                        abs(item.pos().x() - actual_x) < 10 and  # Close to the activity
                        abs(item.pos().y() - y_pos) < 10 and     # Close to the top of the activity
                        item.zValue() >= 2):                    # Completion indicators have high Z values
                        self.scene.removeItem(item)
                        print(f"Removed an indicator item at z={item.zValue()}")
                except Exception as e:
                    print(f"Error checking item: {e}")
            
            # Add new completion indicators if completed
            if is_completed:
                print("Adding new completion indicator")
                
                # Add the green bar on the left
                complete_path = QPainterPath()
                complete_path.addRoundedRect(QRectF(actual_x, y_pos, 6, height), 3, 3)
                completion_bar = self.scene.addPath(
                    complete_path, 
                    QPen(Qt.PenStyle.NoPen), 
                    QBrush(QColor("#10B981"))
                )
                completion_bar.setZValue(2)  # Above the activity rectangle
            
            # Force a scene update for this area
            self.scene.update(rect.adjusted(-20, -20, 20, 20))
            print("Scene updated")
                
        except Exception as e:
            print(f"Error updating activity visuals: {e}")
            import traceback
            traceback.print_exc()

    def connectParentSignals(self):
        """Connect signals from the parent to this view."""
        try:
            print("Connecting parent signals...")
            
            # Check if parent exists
            if not hasattr(self, 'parent') or not self.parent:
                print("No parent found to connect signals")
                return
                
            # Connect to standard activity signals if parent has them
            if hasattr(self.parent, 'activityCompleted') and hasattr(self.parent.activityCompleted, 'connect'):
                print("Connected to parent.activityCompleted signal")
                self.parent.activityCompleted.connect(self.onActivityCompletedFromParent)
            
            # Connect to unified activities widget signals if available
            if hasattr(self.parent, 'activities_view'):
                activity_view = self.parent.activities_view
                if hasattr(activity_view, 'activityCompleted') and hasattr(activity_view.activityCompleted, 'connect'):
                    print("Connected to activities_view.activityCompleted signal")
                    activity_view.activityCompleted.connect(self.onActivityCompletedFromParent)
                    
            # Connect our signals to parent and activities view for two-way synchronization
            # First to parent
            if hasattr(self.parent, 'onActivityCompleted'):
                print("Connected activityCompletionChanged to parent.onActivityCompleted")
                self.activityCompletionChanged.connect(self.parent.onActivityCompleted)
                
            # Then to activities view
            if hasattr(self.parent, 'activities_view'):
                activity_view = self.parent.activities_view
                if hasattr(activity_view, 'onActivityCompletedFromOtherView'):
                    print("Connected activityCompletionChanged to activities_view.onActivityCompletedFromOtherView")
                    self.activityCompletionChanged.connect(activity_view.onActivityCompletedFromOtherView)
                    
        except Exception as e:
            print(f"Error connecting parent signals: {e}")
            import traceback
            traceback.print_exc()

    def onActivityCompletedFromParent(self, activity_id, completed, activity_type):
        """Handle activity completion signals from parent."""
        try:
            print(f"Received activity completion update from parent: {activity_id}, {completed}, {activity_type}")
            
            # Update our activity state
            for activity in self.activities:
                if activity.get('id') == activity_id:
                    activity['completed'] = completed
                    print(f"Updated local activity status to {completed}")
                    break
            
            # Update the activity visualization
            self.updateActivityVisuals(activity_id, completed)
                
        except Exception as e:
            print(f"Error handling activity completion from parent: {e}")
            import traceback
            traceback.print_exc()
            # If there's an error, refresh the whole view to ensure sync
            self.updateWeekView()

    def markActivityComplete(self, activity_id, activity_type):
        """Mark an activity as complete."""
        if hasattr(self.parent, 'activities_manager'):
            # Find the activity to get its date
            activity_date = None
            for activity in self.activities:
                if activity.get('id') == activity_id:
                    # Get the date for this activity
                    activity_date = activity.get('date')
                    
                    # If date isn't available, calculate it from day_index
                    if not activity_date and 'day_index' in activity:
                        day_index = activity.get('day_index', 0)
                        activity_date = self.current_week_start.addDays(day_index)
                        activity['date'] = activity_date
                    
                    # Update local completion status
                    activity['completed'] = True
                    break
            
            # Toggle the activity completion with the specific date
            if activity_date:
                self.parent.activities_manager.toggle_activity_completion(
                    activity_id, 
                    True,
                    activity_date
                )
            
            # Refresh the view to reflect the changes
            self.updateWeekView()
            
            # Also refresh the activities view if it exists
            if hasattr(self.parent, 'activities_view') and self.parent.activities_view:
                self.parent.activities_view.refresh()
                
            # If the parent has an activity completion handler, call it
            if hasattr(self.parent, 'onActivityCompleted'):
                self.parent.onActivityCompleted(activity_id, True, activity_type)
    
    def editActivity(self, activity_id, activity_type):
        """Open edit dialog for an activity."""
        # This will be implemented by connecting to the appropriate method in UnifiedActivitiesWidget
        if hasattr(self.parent, 'showEditActivityDialog'):
            self.parent.showEditActivityDialog(activity_id, activity_type)
            self.loadActivities()  # Reload after edit
    
    def deleteActivity(self, activity_id, activity_type):
        """Delete an activity."""
        if hasattr(self.parent, 'activities_manager'):
            self.parent.activities_manager.delete_activity(activity_id)
            self.loadActivities()  # Reload to reflect changes
    
    def refresh(self):
        """Refresh the view data."""
        self.loadActivities()
