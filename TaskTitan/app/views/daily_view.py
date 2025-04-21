"""
Daily planning view for TaskTitan with timeline visualization.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QScrollArea, QFrame, QSplitter, QTabWidget, QListWidget, 
                           QListWidgetItem, QDialog, QLineEdit, QTimeEdit, QDateEdit,
                           QTextEdit, QCheckBox, QComboBox, QDialogButtonBox, QMessageBox, QMenu,
                           QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
                           QGraphicsItem, QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QDate, QTime, QSize, pyqtSignal, QRectF, QMargins, QTimer
from PyQt6.QtGui import QIcon, QColor, QBrush, QPen, QFont, QPainter
from datetime import datetime, timedelta
import sqlite3

from app.resources import get_icon
from app.models.activities_manager import ActivitiesManager

# Constants for timeline rendering
HOUR_HEIGHT = 60  # Height in pixels for one hour
TIMELINE_LEFT_MARGIN = 80  # Width of left margin for hour labels
TIMELINE_WIDTH = 800  # Width of the timeline view
TIMELINE_START_HOUR = 0  # Start at 12 AM (midnight)
TIMELINE_END_HOUR = 23  # End at 11 PM

class ActivityTimelineItem(QGraphicsRectItem):
    """Graphical representation of an activity in the timeline."""
    
    def __init__(self, activity, x, y, width, height, parent=None):
        super().__init__(x, y, width, height, parent)
        self.activity = activity
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        # Set appearance based on activity type and completion
        self.setupAppearance()
        
        # Add text for the activity
        self.setupText()
    
    def setupAppearance(self):
        """Configure the visual appearance of the activity box."""
        activity_type = self.activity.get('type', 'task')
        is_completed = self.activity.get('completed', False)
        
        # Get activity color (or use default based on type)
        if 'color' in self.activity and self.activity['color']:
            color = QColor(self.activity['color'])
        else:
            # Default colors by activity type
            if activity_type == 'task':
                color = QColor("#F87171")  # Red
            elif activity_type == 'event':
                color = QColor("#818CF8")  # Purple/Blue
            elif activity_type == 'habit':
                color = QColor("#34D399")  # Green
            else:
                color = QColor("#6B7280")  # Gray
        
        # Lighter color if completed
        if is_completed:
            color = color.lighter(150)
            brush = QBrush(color, Qt.BrushStyle.Dense4Pattern)
        else:
            brush = QBrush(color.lighter(130))
        
        # Set brush and pen
        self.setBrush(brush)
        self.setPen(QPen(color.darker(120), 2))
        
        # Set rounded corners
        self.setData(0, "activity")
        self.setData(1, self.activity['id'])
        self.setData(2, activity_type)
    
    def setupText(self):
        """Add text information to the activity box."""
        text_item = QGraphicsTextItem(self)
        
        # Extract activity information
        title = self.activity.get('title', 'Untitled')
        activity_type = self.activity.get('type', '').capitalize()
        category = self.activity.get('category', '')
        description = self.activity.get('description', '')
        start_time = self.activity.get('start_time')
        end_time = self.activity.get('end_time')
        
        # Format time range if available
        time_str = ""
        if start_time and end_time:
            start_str = start_time.toString("h:mm AP") if isinstance(start_time, QTime) else str(start_time)
            end_str = end_time.toString("h:mm AP") if isinstance(end_time, QTime) else str(end_time)
            time_str = f"{start_str} - {end_str}"
        
        # Create HTML formatted text
        html = f"""
            <div style="margin: 0; padding: 0;">
                <div style="margin-bottom: 3px;">
                    <span style="font-weight: bold; font-size: 13px;">{title}</span>
                </div>
                <div style="margin-bottom: 4px;">
                    <span style="color: #4B5563; font-size: 11px;">{activity_type}</span>
                    {f'<span style="color: #6B7280; font-size: 11px;"> • {category}</span>' if category else ''}
                    {f'<span style="color: #6B7280; font-size: 11px;"> • {time_str}</span>' if time_str else ''}
                </div>
                {f'<div style="color: #374151; font-size: 12px;">{description}</div>' if description else ''}
            </div>
        """
        
        text_item.setHtml(html)
        
        # Position the text inside the rect with padding
        text_item.setPos(10, 5)
        text_item.setTextWidth(self.rect().width() - 20)
        
        # Adjust text color if completed
        if self.activity.get('completed', False):
            text_item.setDefaultTextColor(QColor(100, 100, 100))
    
    def paint(self, painter, option, widget):
        """Custom painting for the activity item."""
        # Set rendering hints for smoother appearance
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Save the painter state
        painter.save()
        
        # Draw a rounded rectangle
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        # Draw a small status indicator for task completion if needed
        if self.activity.get('type') == 'task':
            completed = self.activity.get('completed', False)
            status_rect = QRectF(self.rect().right() - 20, self.rect().top() + 5, 15, 15)
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            
            if completed:
                # Checkmark for completed
                painter.setBrush(QBrush(QColor("#34D399")))  # Green
                painter.drawEllipse(status_rect)
                
                # Draw checkmark
                painter.setPen(QPen(QColor("white"), 2))
                painter.drawLine(
                    status_rect.left() + 3, status_rect.center().y(),
                    status_rect.center().x(), status_rect.bottom() - 3
                )
                painter.drawLine(
                    status_rect.center().x(), status_rect.bottom() - 3,
                    status_rect.right() - 3, status_rect.top() + 3
                )
            else:
                # Empty circle for not completed
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.setPen(QPen(QColor("#6B7280"), 1.5))
                painter.drawEllipse(status_rect)
        
        # Draw activity type indicator in the top-left corner
        activity_type = self.activity.get('type', '').lower()
        indicator_text = ""
        
        if activity_type == 'task':
            indicator_text = "⚑"  # Flag symbol for tasks
        elif activity_type == 'event':
            indicator_text = "📅"  # Calendar symbol for events
        elif activity_type == 'habit':
            indicator_text = "↻"  # Recycle symbol for habits
        
        if indicator_text:
            painter.setFont(QFont("Arial", 10))
            painter.setPen(QPen(QColor("#374151")))
            painter.drawText(QRectF(self.rect().left() + 5, self.rect().top() + 5, 20, 20), 
                             Qt.AlignmentFlag.AlignCenter, indicator_text)
        
        # Restore the painter state
        painter.restore()
    
    def hoverEnterEvent(self, event):
        """Handle mouse hover enter event."""
        # Create a glow effect
        self.setPen(QPen(self.pen().color().lighter(120), 3))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle mouse hover leave event."""
        # Remove the glow effect
        self.setPen(QPen(self.pen().color().darker(100), 2))
        super().hoverLeaveEvent(event)
        
    def mouseDoubleClickEvent(self, event):
        """Handle double-click event."""
        # This could be used to show an edit dialog
        super().mouseDoubleClickEvent(event)

class TimelineView(QGraphicsView):
    """Custom view for displaying a timeline of activities."""
    
    activityClicked = pyqtSignal(dict)  # Signal emitted when activity is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setViewportMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Enable scrolling
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create scene with appropriate size for full 24 hours
        self.scene = QGraphicsScene(self)
        total_height = HOUR_HEIGHT * (TIMELINE_END_HOUR - TIMELINE_START_HOUR + 1)
        self.scene.setSceneRect(0, 0, TIMELINE_WIDTH, total_height)
        self.setScene(self.scene)
        
        # Setup initial view
        self.setupHourGuides()
        
        # Set initial scroll position to morning hours (8 AM)
        self.morning_hour = 8  # 8 AM
        QTimer.singleShot(100, self.scrollToMorningHours)
        
        # Current time indicator items
        self.time_line = None
        self.time_dot = None
        
        # Update current time indicator every minute
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.updateCurrentTimeIndicator)
        self.time_timer.start(60000)  # Update every minute
    
    def scrollToMorningHours(self):
        """Scroll to the morning hours (around 8 AM) after initialization."""
        morning_y_pos = (self.morning_hour - TIMELINE_START_HOUR) * HOUR_HEIGHT
        self.verticalScrollBar().setValue(morning_y_pos - 100)  # Position with some space above
    
    def updateCurrentTimeIndicator(self):
        """Update the current time indicator position."""
        # Remove existing indicator
        if self.time_line:
            self.scene.removeItem(self.time_line)
            self.time_line = None
        if self.time_dot:
            self.scene.removeItem(self.time_dot)
            self.time_dot = None
            
        # Add new indicator
        self.addCurrentTimeIndicator()
    
    def addCurrentTimeIndicator(self):
        """Add a horizontal line indicating the current time."""
        current_time = QTime.currentTime()
        try:
            parent_widget = self.parent().parent()
            is_today = QDate.currentDate() == parent_widget.current_date
        except:
            is_today = QDate.currentDate() == QDate.currentDate()  # Fallback
            
        if is_today:
            # Calculate position
            minutes_since_start = current_time.hour() * 60 + current_time.minute()
            minutes_since_timeline_start = minutes_since_start - (TIMELINE_START_HOUR * 60)
            y_pos = (minutes_since_timeline_start / 60) * HOUR_HEIGHT
            
            # Draw the time indicator line
            self.time_line = self.scene.addLine(
                TIMELINE_LEFT_MARGIN, y_pos,
                TIMELINE_WIDTH, y_pos,
                QPen(QColor("#EF4444"), 2)  # Red line
            )
            
            # Add small circle at the start of the line
            self.time_dot = self.scene.addEllipse(
                TIMELINE_LEFT_MARGIN - 4, y_pos - 4, 8, 8,
                QPen(QColor("#EF4444")),
                QBrush(QColor("#EF4444"))
            )
            
            # Add time text
            time_text = self.scene.addText(
                current_time.toString("h:mm AP"),
                QFont("Arial", 9, QFont.Weight.Bold)
            )
            time_text.setDefaultTextColor(QColor("#EF4444"))
            time_text.setPos(TIMELINE_LEFT_MARGIN - 75, y_pos - 10)
    
    def closeEvent(self, event):
        """Handle close event to stop timer."""
        self.time_timer.stop()
        super().closeEvent(event)
    
    def setupHourGuides(self):
        """Draw the hour lines and labels."""
        self.scene.clear()
        
        # Draw hour lines and labels
        for hour in range(TIMELINE_START_HOUR, TIMELINE_END_HOUR + 1):
            y_pos = (hour - TIMELINE_START_HOUR) * HOUR_HEIGHT
            
            # Draw horizontal line
            self.scene.addLine(
                TIMELINE_LEFT_MARGIN, y_pos,
                TIMELINE_WIDTH, y_pos,
                QPen(QColor("#E5E7EB"), 1)
            )
            
            # Format hour for 12-hour display with AM/PM
            if hour == 0:
                hour_text = "12 AM"
            elif hour < 12:
                hour_text = f"{hour} AM"
            elif hour == 12:
                hour_text = "12 PM"
            else:
                hour_text = f"{hour-12} PM"
                
            # Add hour label
            time_label = self.scene.addText(
                hour_text,
                QFont("Arial", 10)
            )
            time_label.setPos(5, y_pos - 10)
            time_label.setDefaultTextColor(QColor("#64748B"))
            
            # Add half-hour line (lighter)
            if hour < TIMELINE_END_HOUR:
                half_hour_y = y_pos + (HOUR_HEIGHT / 2)
                self.scene.addLine(
                    TIMELINE_LEFT_MARGIN, half_hour_y,
                    TIMELINE_WIDTH, half_hour_y,
                    QPen(QColor("#E5E7EB"), 0.5, Qt.PenStyle.DashLine)
                )
        
        # Draw vertical time axis line
        self.scene.addLine(
            TIMELINE_LEFT_MARGIN, 0,
            TIMELINE_LEFT_MARGIN, (TIMELINE_END_HOUR - TIMELINE_START_HOUR + 1) * HOUR_HEIGHT,
            QPen(QColor("#94A3B8"), 1)
        )
        
        # Add current time indicator
        self.addCurrentTimeIndicator()
    
    def addActivity(self, activity):
        """Add an activity to the timeline.
        
        Args:
            activity: Dictionary containing activity data
        """
        # Extract time information
        start_time = activity.get('start_time')
        end_time = activity.get('end_time')
        
        # Skip activities with no valid time
        if not start_time or not end_time:
            print(f"Skipping activity with missing time: {activity.get('title', 'Unknown')}")
            return
            
        # Make sure we have QTime objects
        if not isinstance(start_time, QTime):
            try:
                if isinstance(start_time, str):
                    start_time = QTime.fromString(start_time, "HH:mm")
                    activity['start_time'] = start_time
            except Exception as e:
                print(f"Error converting start time: {e}")
                return
                
        if not isinstance(end_time, QTime):
            try:
                if isinstance(end_time, str):
                    end_time = QTime.fromString(end_time, "HH:mm")
                    activity['end_time'] = end_time
            except Exception as e:
                print(f"Error converting end time: {e}")
                return
        
        # Calculate position and size
        start_minutes = start_time.hour() * 60 + start_time.minute()
        end_minutes = end_time.hour() * 60 + end_time.minute()
        
        # Handle activities that span to the next day
        if end_minutes <= start_minutes:
            # Assume it ends on the next day
            end_minutes = 24 * 60 - 1  # End at 23:59
            print(f"Activity spans to next day, capped at midnight: {activity.get('title')}")
        
        # Calculate timeline coordinates
        start_minutes_on_timeline = start_minutes - (TIMELINE_START_HOUR * 60)
        end_minutes_on_timeline = end_minutes - (TIMELINE_START_HOUR * 60)
        
        # Calculate y-position and height
        y_pos = (start_minutes_on_timeline / 60) * HOUR_HEIGHT
        height = ((end_minutes_on_timeline - start_minutes_on_timeline) / 60) * HOUR_HEIGHT
        
        # Ensure minimum height for visibility
        height = max(height, 30)
        
        print(f"Positioning activity {activity.get('title')} at y={y_pos}, height={height}")
        
        # Create the item and add to scene
        item = ActivityTimelineItem(
            activity,
            TIMELINE_LEFT_MARGIN + 10,  # Add some padding from the axis
            y_pos,
            TIMELINE_WIDTH - TIMELINE_LEFT_MARGIN - 30,  # Width with some margin
            height,
            None
        )
        self.scene.addItem(item)
    
    def clearActivities(self):
        """Remove all activities from the timeline."""
        for item in self.scene.items():
            if isinstance(item, ActivityTimelineItem):
                self.scene.removeItem(item)
    
    def mousePressEvent(self, event):
        """Handle mouse press event to select activities."""
        super().mousePressEvent(event)
        item = self.itemAt(event.pos())
        
        if isinstance(item, ActivityTimelineItem) or (item and item.parentItem() and isinstance(item.parentItem(), ActivityTimelineItem)):
            # If we clicked on a text item, get its parent
            if item and not isinstance(item, ActivityTimelineItem):
                item = item.parentItem()
            
            # Emit signal with the activity data
            if item and hasattr(item, 'activity'):
                self.activityClicked.emit(item.activity)
    
    def wheelEvent(self, event):
        """Enhanced wheel event to support both vertical and horizontal scrolling."""
        # If Ctrl key is pressed, zoom in/out
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.scale(1.2, 1.2)
            else:
                self.scale(0.8, 0.8)
        else:
            # Otherwise, use normal scrolling
            super().wheelEvent(event)

class DailyView(QWidget):
    """Widget for daily planning with timeline visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store parent to access database
        
        # Initialize activities manager
        self.activities_manager = None
        if parent and hasattr(parent, 'activities_manager'):
            # Direct connection to parent's activities manager
            self.activities_manager = parent.activities_manager
            print("Using parent's activities manager")
        elif parent and hasattr(parent, 'conn') and parent.conn:
            # Create our own activities manager using parent's connection
            self.activities_manager = ActivitiesManager(parent.conn, parent.cursor)
            print("Created activities manager from parent's connection")
        else:
            # Try to access activities manager from main application if it exists
            try:
                import sys
                main_app = None
                
                # Look for the main application window in the application objects
                for widget in QApplication.topLevelWidgets():
                    if hasattr(widget, 'activities_manager'):
                        main_app = widget
                        self.activities_manager = main_app.activities_manager
                        print("Found activities manager from top-level application")
                        break
                
                # If still not found, create a new one
                if not self.activities_manager:
                    from app.models.database import initialize_db
                    conn, cursor = initialize_db()
                    self.activities_manager = ActivitiesManager(conn, cursor)
                    self.activities_manager.create_tables()  # Ensure tables exist
                    print("Created standalone activities manager with new connection")
            except Exception as e:
                print(f"Could not initialize activities manager: {e}")
                import traceback
                traceback.print_exc()
        
        self.current_date = QDate.currentDate()
        self.setupUI()
        
    def setupUI(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        
        # Header with date navigation
        header_layout = QHBoxLayout()
        
        # Previous day button
        prev_btn = QPushButton()
        prev_btn.setIcon(get_icon("arrow-left"))
        prev_btn.setFixedSize(36, 36)
        prev_btn.clicked.connect(self.previousDay)
        header_layout.addWidget(prev_btn)
        
        # Date display and today button
        date_layout = QVBoxLayout()
        date_layout.setSpacing(2)
        
        self.date_label = QLabel(self.current_date.toString('dddd, MMMM d, yyyy'))
        self.date_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_layout.addWidget(self.date_label)
        
        today_btn = QPushButton("Today")
        today_btn.setFixedWidth(100)
        today_btn.clicked.connect(self.goToToday)
        today_btn.setStyleSheet("font-size: 12px;")
        
        today_layout = QHBoxLayout()
        today_layout.addStretch()
        today_layout.addWidget(today_btn)
        today_layout.addStretch()
        date_layout.addLayout(today_layout)
        
        header_layout.addLayout(date_layout, 1)  # Stretch in middle
        
        # Next day button
        next_btn = QPushButton()
        next_btn.setIcon(get_icon("arrow-right"))
        next_btn.setFixedSize(36, 36)
        next_btn.clicked.connect(self.nextDay)
        header_layout.addWidget(next_btn)
        
        main_layout.addLayout(header_layout)
        
        # Create a horizontal splitter with timeline and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Timeline view on the left (takes about 2/3 of the width)
        timeline_container = QWidget()
        timeline_layout = QVBoxLayout(timeline_container)
        timeline_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add button for adding activities
        add_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ Add Activity")
        add_btn.setIcon(get_icon("add"))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
        """)
        add_btn.clicked.connect(self.showAddActivityDialog)
        add_layout.addWidget(add_btn)
        
        add_layout.addStretch()
        timeline_layout.addLayout(add_layout)
        
        # Add the timeline view
        self.timeline_view = TimelineView()
        self.timeline_view.activityClicked.connect(self.onActivityClicked)
        timeline_layout.addWidget(self.timeline_view)
        
        splitter.addWidget(timeline_container)
        
        # Add info panel on the right (takes about 1/3 of the width)
        info_panel = QTabWidget()
        
        # Notes tab
        self.notes_widget = QWidget()
        self.setupNotesTab()
        info_panel.addTab(self.notes_widget, "Notes")
        
        # Activities list tab (shows all activities for the day in a list)
        self.activities_list_widget = QWidget()
        self.setupActivitiesListTab()
        info_panel.addTab(self.activities_list_widget, "Activities")
        
        splitter.addWidget(info_panel)
        
        # Set the initial sizes of the splitter
        splitter.setSizes([700, 300])  # Adjust as needed
        
        main_layout.addWidget(splitter)
        
        # Load data for current date
        self.loadTimelineData()
    
    def setupNotesTab(self):
        """Set up the notes tab."""
        layout = QVBoxLayout(self.notes_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Text editor for notes
        self.notes_editor = QTextEdit()
        self.notes_editor.setPlaceholderText("Enter your notes for this day...")
        layout.addWidget(self.notes_editor)
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        save_btn = QPushButton("Save Notes")
        save_btn.setIcon(get_icon("save"))
        save_btn.clicked.connect(self.saveNotes)
        save_layout.addWidget(save_btn)
        
        layout.addLayout(save_layout)
        
        # Load notes for current date
        self.loadNotes()
    
    def setupActivitiesListTab(self):
        """Set up the activities list tab."""
        layout = QVBoxLayout(self.activities_list_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create list widget
        self.activities_list = QListWidget()
        self.activities_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 5px;
                background-color: #F9FAFB;
            }
            QListWidget::item {
                border-bottom: 1px solid #E5E7EB;
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
        """)
        self.activities_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.activities_list.customContextMenuRequested.connect(self.showActivityContextMenu)
        layout.addWidget(self.activities_list)
    
    def loadTimelineData(self):
        """Load activities for the current date and display them in the timeline."""
        self.timeline_view.clearActivities()
        
        if not self.activities_manager:
            print("No activities manager available - cannot load activities")
            return
        
        try:
            # Get activities for the current date
            print(f"Fetching activities for date: {self.current_date.toString('yyyy-MM-dd')}")
            activities = self.activities_manager.get_activities_for_date(self.current_date)
            
            if not activities:
                print(f"No activities found for date {self.current_date.toString('yyyy-MM-dd')}")
            else:
                print(f"Found {len(activities)} activities for date {self.current_date.toString('yyyy-MM-dd')}")
                for act in activities:
                    print(f"  - {act.get('title')} ({act.get('type')}): {act.get('start_time').toString('HH:mm')} to {act.get('end_time').toString('HH:mm')}")
            
            # Add activities to the timeline
            for activity in activities:
                self.timeline_view.addActivity(activity)
            
            # Also update the activities list
            self.updateActivitiesList(activities)
            
            # Make sure current time indicator is visible if viewing today
            if self.current_date == QDate.currentDate():
                self.timeline_view.addCurrentTimeIndicator()
                
        except Exception as e:
            print(f"Error loading timeline data: {e}")
            import traceback
            traceback.print_exc()
    
    def updateActivitiesList(self, activities):
        """Update the activities list with the given activities."""
        self.activities_list.clear()
        
        # Sort activities by start time
        sorted_activities = sorted(activities, key=lambda x: x['start_time'].toString("HH:mm"))
        
        for activity in sorted_activities:
            item = QListWidgetItem()
            
            # Format time range
            start_time = activity['start_time'].toString("HH:mm")
            end_time = activity['end_time'].toString("HH:mm")
            time_range = f"{start_time} - {end_time}"
            
            # Format title with activity type
            title = activity['title']
            activity_type = activity['type'].capitalize()
            
            # Set item text with HTML formatting
            if activity.get('completed', False):
                item.setText(f"<span style='text-decoration: line-through; color: #9CA3AF;'><b>{time_range}</b> - {title} ({activity_type})</span>")
            else:
                item.setText(f"<b>{time_range}</b> - {title} ({activity_type})")
            
            # Store activity data in the item
            item.setData(Qt.ItemDataRole.UserRole, activity)
            
            # Add the item to the list
            self.activities_list.addItem(item)
    
    def loadNotes(self):
        """Load notes for the current date."""
        if not self.parent or not hasattr(self.parent, 'cursor'):
            return
        
        try:
            self.parent.cursor.execute(
                "SELECT note FROM daily_notes WHERE date = ?",
                (self.current_date.toString("yyyy-MM-dd"),)
            )
            result = self.parent.cursor.fetchone()
            
            if result:
                self.notes_editor.setPlainText(result[0])
            else:
                self.notes_editor.clear()
        except Exception as e:
            print(f"Error loading notes: {e}")
            self.notes_editor.clear()
    
    def saveNotes(self):
        """Save notes for the current date."""
        if not self.parent or not hasattr(self.parent, 'conn'):
            QMessageBox.warning(self, "Error", "Database connection not available")
            return
        
        note_text = self.notes_editor.toPlainText()
        date_str = self.current_date.toString("yyyy-MM-dd")
        
        try:
            # Check if there's already a note for this date
            self.parent.cursor.execute(
                "SELECT 1 FROM daily_notes WHERE date = ?",
                (date_str,)
            )
            exists = self.parent.cursor.fetchone()
            
            if exists:
                # Update existing note
                self.parent.cursor.execute(
                    "UPDATE daily_notes SET note = ? WHERE date = ?",
                    (note_text, date_str)
                )
            else:
                # Insert new note
                self.parent.cursor.execute(
                    "INSERT INTO daily_notes (date, note) VALUES (?, ?)",
                    (date_str, note_text)
                )
            
            self.parent.conn.commit()
            QMessageBox.information(self, "Success", "Notes saved successfully")
        except Exception as e:
            print(f"Error saving notes: {e}")
            QMessageBox.warning(self, "Error", f"Could not save notes: {str(e)}")
    
    def showAddActivityDialog(self):
        """Show dialog to add a new activity."""
        if not self.parent:
            return
            
        # If parent has an activities view with a dialog, use that
        if hasattr(self.parent, 'activitiesView') and hasattr(self.parent.activitiesView, 'showAddActivityDialog'):
            # Set the date first
            self.parent.activitiesView.current_date = self.current_date
            # Show the dialog
            self.parent.activitiesView.showAddActivityDialog()
            # Refresh the timeline after adding
            self.loadTimelineData()
        else:
            QMessageBox.information(self, "Not Available", "Activity management is not available")
    
    def showActivityContextMenu(self, position):
        """Show context menu for activities list."""
        item = self.activities_list.itemAt(position)
        if not item:
            return
        
        activity = item.data(Qt.ItemDataRole.UserRole)
        if not activity:
            return
        
        menu = QMenu(self)
        
        # Add menu actions
        edit_action = menu.addAction("Edit Activity")
        edit_action.setIcon(get_icon("edit"))
        
        toggle_action = menu.addAction(
            "Mark as Incomplete" if activity.get('completed', False) else "Mark as Complete"
        )
        toggle_action.setIcon(get_icon("check"))
        
        delete_action = menu.addAction("Delete Activity")
        delete_action.setIcon(get_icon("delete"))
        
        # Show menu and handle selection
        action = menu.exec(self.activities_list.mapToGlobal(position))
        
        if action == edit_action:
            self.editActivity(activity)
        elif action == toggle_action:
            self.toggleActivityStatus(activity)
        elif action == delete_action:
            self.deleteActivity(activity)
    
    def onActivityClicked(self, activity):
        """Handle clicks on timeline activities."""
        # Select the corresponding item in the list
        for i in range(self.activities_list.count()):
            item = self.activities_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole).get('id') == activity.get('id'):
                self.activities_list.setCurrentItem(item)
                break
    
    def editActivity(self, activity):
        """Show dialog to edit an activity."""
        if not self.parent:
            return
            
        # If parent has an activities view with a dialog, use that
        if hasattr(self.parent, 'activitiesView') and hasattr(self.parent.activitiesView, 'showEditActivityDialog'):
            # Show the dialog
            self.parent.activitiesView.showEditActivityDialog(activity['id'], activity['type'])
            # Refresh the timeline after editing
            self.loadTimelineData()
        else:
            QMessageBox.information(self, "Not Available", "Activity editing is not available")
    
    def toggleActivityStatus(self, activity):
        """Toggle the completion status of an activity."""
        if not self.activities_manager:
            return
        
        try:
            # Toggle the status
            new_status = not activity.get('completed', False)
            
            # Update in database
            self.activities_manager.toggle_activity_completion(activity['id'], new_status)
            
            # Refresh the view
            self.loadTimelineData()
        except Exception as e:
            print(f"Error toggling activity status: {e}")
            QMessageBox.warning(self, "Error", f"Could not update activity: {str(e)}")
    
    def deleteActivity(self, activity):
        """Delete an activity."""
        if not self.activities_manager:
            return
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{activity['title']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # Delete from database
                self.activities_manager.delete_activity(activity['id'])
                
                # Refresh the view
                self.loadTimelineData()
            except Exception as e:
                print(f"Error deleting activity: {e}")
                QMessageBox.warning(self, "Error", f"Could not delete activity: {str(e)}")
    
    def setDate(self, date):
        """Set the current date and refresh the view."""
        self.current_date = date
        self.date_label.setText(date.toString('dddd, MMMM d, yyyy'))
        
        # Reload data for the new date
        self.loadTimelineData()
        self.loadNotes()
        
        # Scroll to morning hours
        QTimer.singleShot(100, self.timeline_view.scrollToMorningHours)
    
    def previousDay(self):
        """Go to the previous day."""
        self.setDate(self.current_date.addDays(-1))
    
    def nextDay(self):
        """Go to the next day."""
        self.setDate(self.current_date.addDays(1))
    
    def goToToday(self):
        """Go to today's date."""
        self.setDate(QDate.currentDate())
    
    def refresh(self):
        """Refresh the view with current data."""
        print(f"Refreshing daily view for date: {self.current_date.toString('yyyy-MM-dd')}")
        self.loadTimelineData()
        self.loadNotes() 