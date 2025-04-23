"""
Weekly Plan view for TaskTitan.

This module provides a weekly view of activities with an hourly breakdown.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QGraphicsView, QGraphicsScene, 
                           QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem,
                           QGraphicsEllipseItem, QSlider, QSizePolicy, QScrollArea, QMenu, QDialog)
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
            if hasattr(self.parent_widget, 'parent') and self.parent_widget.parent:
                if hasattr(self.parent_widget.parent, 'markActivityComplete'):
                    self.parent_widget.parent.markActivityComplete(self.activity.get('id'), self.activity.get('type'))
                    self.close()
                    return
                    
            # If that fails, try getting the main window through the scene
            if isinstance(self.parent_widget, QGraphicsView):
                view = self.parent_widget
                if hasattr(view, 'parent') and view.parent:
                    view_parent = view.parent
                    if hasattr(view_parent, 'activities_manager'):
                        view_parent.activities_manager.toggle_activity_completion(
                            self.activity.get('id'), True)
                        self.close()
                        return
            
            # As a fallback, try to find the activities manager through any parent
            parent = self.parent_widget
            while parent:
                if hasattr(parent, 'activities_manager'):
                    parent.activities_manager.toggle_activity_completion(
                        self.activity.get('id'), True)
                    self.close()
                    break
                if hasattr(parent, 'parent'):
                    parent = parent.parent
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
            if hasattr(self.parent_widget, 'editActivity'):
                self.parent_widget.editActivity(self.activity.get('id'), self.activity.get('type'))
                self.close()
                return
            
            # Then try parent's parent which is more likely the WeeklyPlanView
            if hasattr(self.parent_widget, 'parent') and self.parent_widget.parent:
                if hasattr(self.parent_widget.parent, 'editActivity'):
                    self.parent_widget.parent.editActivity(self.activity.get('id'), self.activity.get('type'))
                    self.close()
                    return
                    
            # If that fails, try getting the main window through the scene
            if isinstance(self.parent_widget, QGraphicsView):
                view = self.parent_widget
                if hasattr(view, 'parent') and view.parent:
                    view_parent = view.parent
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
                if hasattr(parent, 'parent'):
                    parent = parent.parent
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
            if hasattr(self.parent_widget, 'parent') and self.parent_widget.parent:
                if hasattr(self.parent_widget.parent, 'deleteActivity'):
                    self.parent_widget.parent.deleteActivity(self.activity.get('id'), self.activity.get('type'))
                    self.close()
                    return
                    
            # If that fails, try getting the main window through the scene
            if isinstance(self.parent_widget, QGraphicsView):
                view = self.parent_widget
                if hasattr(view, 'parent') and view.parent:
                    view_parent = view.parent
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
                if hasattr(parent, 'parent'):
                    parent = parent.parent
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
            self.activities_manager = parent.activities_manager
        else:
            # Create our own manager if needed
            self.activities_manager = ActivitiesManager()
            if hasattr(parent, 'conn') and hasattr(parent, 'cursor'):
                self.activities_manager.set_connection(parent.conn, parent.cursor)
        
        # Set up the UI
        self.setupUI()
        
        # Load initial data
        self.loadActivities()
        
        # Set background color
        self.setStyleSheet("background-color: #F9FAFB;")

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
        
        # Today button
        today_btn = QPushButton("Today")
        today_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #4F46E5;
                font-weight: bold;
                border: none;
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
        
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setFixedSize(30, 30)
        zoom_out_btn.clicked.connect(self.zoomOut)
        controls_layout.addWidget(zoom_out_btn)
        
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(30, 30)
        zoom_in_btn.clicked.connect(self.zoomIn)
        controls_layout.addWidget(zoom_in_btn)
        
        reset_btn = QPushButton("Reset View")
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
        if not hasattr(self, 'activities_manager'):
            self.status_label.setText("Error: Activities manager not available")
            return
        
        # Loop through each day of the week
        for day in range(7):
            current_date = self.current_week_start.addDays(day)
            
            # Get activities for this day
            day_activities = self.activities_manager.get_activities_for_date(current_date)
            
            # Store with additional info for rendering
            for activity in day_activities:
                activity['day_index'] = day
                self.activities.append(activity)
        
        # Update the view
        self.updateWeekView()
    
    def updateWeekView(self):
        """Update the weekly view with current activities."""
        # Clear current view
        self.scene.clear()
        self.activity_items = {}
        
        # Draw the weekly grid
        self.drawWeekGrid()
        
        # Add activities to the grid
        self.addActivitiesToGrid()
        
        # Make sure the whole grid is visible
        if self.scene.items():
            self.view.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))
    
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
                    
                    # Make the color transparent
                    color.setAlpha(180)
                    
                    # Leave margins for better visual separation
                    margin = 2
                    actual_x = x_pos + margin
                    actual_width = width - 2 * margin
                    
                    # Set rounded corners for the rectangle with a shadow effect
                    path = QPainterPath()
                    path.addRoundedRect(QRectF(actual_x, y_pos, actual_width, height), 8, 8)
                    rounded_rect = self.scene.addPath(path, QPen(color.darker(), 1), QBrush(color))
                    rounded_rect.setData(0, activity.get('id'))
                    rounded_rect.setZValue(1)
                    
                    # Add shadow effect (lighter shadow for better performance)
                    shadow_path = QPainterPath()
                    shadow_path.addRoundedRect(QRectF(actual_x + 2, y_pos + 2, actual_width, height), 8, 8)
                    shadow_rect = self.scene.addPath(shadow_path, QPen(Qt.PenStyle.NoPen), 
                                                   QBrush(QColor(0, 0, 0, 20)))
                    shadow_rect.setZValue(0.5)
                    
                    # Add modern completion indicator
                    if activity.get('completed'):
                        # Create a vertical bar on the left
                        complete_path = QPainterPath()
                        complete_path.addRoundedRect(QRectF(actual_x, y_pos, 4, height), 2, 2)
                        self.scene.addPath(complete_path, QPen(Qt.PenStyle.NoPen), QBrush(QColor("#10B981")))
                        
                        # Add a small checkmark icon
                        if width > 30:  # Only add if there's enough space
                            check_label = QGraphicsTextItem("✓")
                            check_label.setPos(actual_x + actual_width - 20, y_pos + 5)
                            check_label.setDefaultTextColor(QColor(255, 255, 255, 200))
                            font = check_label.font()
                            font.setBold(True)
                            check_label.setFont(font)
                            check_label.setZValue(2)
                            self.scene.addItem(check_label)
                    
                    # Add activity title with better font
                    title_text = QGraphicsTextItem(activity.get('title', 'Untitled'))
                    title_text.setTextWidth(actual_width - 10)
                    title_text.setPos(actual_x + 6, y_pos + 5)
                    title_text.setDefaultTextColor(QColor("#FFFFFF"))
                    font = title_text.font()
                    font.setBold(True)
                    
                    # Adjust font size based on available width
                    if actual_width < 70:
                        font.setPointSize(font.pointSize() - 1)
                    else:
                        font.setPointSize(font.pointSize() + 1)
                        
                    title_text.setFont(font)
                    
                    # Add enhanced background for better text readability
                    text_bg_height = min(30, height)
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
                    
                    # Add time text if enough space
                    if height > 40 and actual_width > 60:
                        time_format = "HH:mm" if actual_width > 70 else "HH"
                        time_text = QGraphicsTextItem(f"{start_time.toString(time_format)}-{end_time.toString(time_format)}")
                        time_text.setTextWidth(actual_width - 10)
                        time_text.setPos(actual_x + 6, y_pos + 30)
                        # Use white color with drop shadow effect for better readability
                        time_text.setDefaultTextColor(QColor("#FFFFFF"))
                        # Add a slight outline to the text
                        time_font = time_text.font()
                        time_font.setBold(True)  # Make time bold for better visibility
                        if actual_width < 70:
                            time_font.setPointSize(time_font.pointSize() - 1)
                        time_text.setFont(time_font)
                        
                        time_text.setZValue(2)
                        self.scene.addItem(time_text)
                    
                    # Add activity type indicator only if there's enough space
                    if height > 60 and actual_width > 50:
                        type_text = QGraphicsTextItem(activity.get('type', '').capitalize())
                        type_text.setTextWidth(actual_width - 10)
                        type_text.setPos(actual_x + 6, y_pos + height - 25)
                        type_text.setDefaultTextColor(QColor("#FFFFFF"))
                        
                        # Make type text more visible
                        type_font = type_text.font()
                        type_font.setBold(True)
                        if actual_width < 70:
                            type_font.setPointSize(type_font.pointSize() - 1)
                        type_text.setFont(type_font)
                        
                        # Create a rounded background for the type label
                        if height > 80:  # Only add background if there's enough space
                            type_bg = QGraphicsRectItem(actual_x + 4, y_pos + height - 25, 
                                                     type_text.boundingRect().width() + 10, 20)
                            type_bg.setPen(QPen(Qt.PenStyle.NoPen))
                            type_bg.setBrush(QBrush(QColor(0, 0, 0, 60)))  # Semi-transparent black
                            type_bg.setZValue(1.8)
                            self.scene.addItem(type_bg)
                        
                        type_text.setZValue(2)
                        self.scene.addItem(type_text)
                    
                    # Make the rectangle clickable
                    rounded_rect.setAcceptHoverEvents(True)
                    rounded_rect.setCursor(Qt.CursorShape.PointingHandCursor)
                    
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
        """Handle clicks on the scene."""
        # Find the item under the cursor
        items = self.scene.items(event.scenePos())
        
        # Look for activity rectangles
        for item in items:
            if hasattr(item, 'data') and item.data(0):
                activity_id = item.data(0)
                if activity_id in self.activity_items:
                    activity = self.activity_items[activity_id]['activity']
                    
                    # Show activity details dialog
                    dialog = ActivityDetailsDialog(activity, self.view)
                    dialog.show()
                    
                    # Emit signal
                    self.activityClicked.emit(activity)
                    return
        
        # If no activity was clicked, continue with default handling
        QGraphicsScene.mousePressEvent(self.scene, event)
    
    def markActivityComplete(self, activity_id, activity_type):
        """Mark an activity as complete."""
        if hasattr(self.parent, 'activities_manager'):
            # Toggle the activity completion
            self.parent.activities_manager.toggle_activity_completion(activity_id, True)
            
            # Update the activity in our local cache
            for activity in self.activities:
                if activity.get('id') == activity_id:
                    activity['completed'] = True
                    break
            
            # Refresh the view to reflect the changes
            self.updateWeekView()
            
            # If the parent has an activity completion handler, call it
            if hasattr(self.parent, 'onActivityCompleted'):
                self.parent.onActivityCompleted(activity_id, activity_type)
    
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