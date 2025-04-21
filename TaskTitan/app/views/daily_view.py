"""
Daily planning view for TaskTitan with timeline visualization.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QScrollArea, QFrame, QSplitter, QTabWidget, QListWidget, 
                           QListWidgetItem, QDialog, QLineEdit, QTimeEdit, QDateEdit,
                           QTextEdit, QCheckBox, QComboBox, QDialogButtonBox, QMessageBox, QMenu,
                           QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
                           QGraphicsItem, QSizePolicy, QApplication, QGraphicsDropShadowEffect,
                           QGraphicsLineItem, QGraphicsEllipseItem)
from PyQt6.QtCore import Qt, QDate, QTime, QSize, pyqtSignal, QRectF, QMargins, QTimer
from PyQt6.QtGui import QIcon, QColor, QBrush, QPen, QFont, QPainter, QCursor, QFontMetrics, QLinearGradient
from datetime import datetime, timedelta
import sqlite3

from app.resources import get_icon
from app.models.activities_manager import ActivitiesManager

# Constants for timeline rendering
HOUR_HEIGHT = 180  # Triple the height (was 60)
TIMELINE_LEFT_MARGIN = 60
TIMELINE_WIDTH = 1000
TIMELINE_START_HOUR = 0
TIMELINE_END_HOUR = 23

class ActivityTimelineItem(QGraphicsRectItem):
    """Graphical representation of an activity in the timeline."""
    
    def __init__(self, activity, x, y, width, height, parent=None):
        super().__init__(x, y, width, height, parent)
        self.activity = activity
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        # Set appearance based on activity type and completion
        self.setupAppearance()
    
    def setupAppearance(self):
        """Configure the visual appearance of the activity box."""
        activity_type = self.activity.get('type', 'task')
        is_completed = self.activity.get('completed', False)
        
        # Get activity color (or use default based on type)
        if 'color' in self.activity and self.activity['color']:
            # Use exact color from activity without any modification
            base_color = QColor(self.activity['color'])
        else:
            # Default colors by activity type
            if activity_type == 'task':
                base_color = QColor("#F87171")  # Red
            elif activity_type == 'event':
                base_color = QColor("#818CF8")  # Purple/Blue
            elif activity_type == 'habit':
                base_color = QColor("#34D399")  # Green
            else:
                base_color = QColor("#6B7280")  # Gray
        
        # Use pattern for completed activities but preserve the exact color
        if is_completed:
            brush = QBrush(base_color, Qt.BrushStyle.Dense4Pattern)
        else:
            brush = QBrush(base_color)  # Use exact color, no lightening
        
        # Set brush and pen with exact color
        self.setBrush(brush)
        self.setPen(QPen(base_color, 2))
        
        # Store color for text contrast calculations
        self.base_color = base_color
        
        # Set rounded corners
        self.setData(0, "activity")
        self.setData(1, self.activity['id'])
        self.setData(2, activity_type)
    
    def paint(self, painter, option, widget):
        """Paint the activity item with custom appearance."""
        # Setup painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the background
        if self.isSelected():
            painter.setBrush(QBrush(QColor(self.base_color).lighter(120)))
        else:
            painter.setBrush(QBrush(self.base_color))
        
        # No border for a cleaner look
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 5, 5)
        
        # Draw completion indicator if applicable
        if self.activity.get('completed', False):
            checkmark_rect = QRectF(self.rect().right() - 20, self.rect().top() + 5, 15, 15)
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(checkmark_rect)
            
            # Draw checkmark
            painter.setPen(QPen(QColor("#4CAF50"), 2))
            painter.drawLine(
                checkmark_rect.left() + 3, checkmark_rect.center().y(),
                checkmark_rect.center().x(), checkmark_rect.bottom() - 3
            )
            painter.drawLine(
                checkmark_rect.center().x(), checkmark_rect.bottom() - 3,
                checkmark_rect.right() - 3, checkmark_rect.top() + 3
            )
        
        # Set text color based on background color brightness
        background_color = QColor(self.base_color)
        brightness = (background_color.red() * 299 + background_color.green() * 587 + background_color.blue() * 114) / 1000
        if brightness > 128:
            text_color = QColor("#333333")
        else:
            text_color = QColor("#FFFFFF")
        
        # Draw title text
        painter.setPen(QPen(text_color))
        title_font = QFont()
        title_font.setBold(True)
        painter.setFont(title_font)
        
        # Calculate text rectangles with proper margins
        margin = 5
        content_rect = self.rect().adjusted(margin, margin, -margin, -margin)
        
        # Draw title with text truncation if needed
        title_rect = QRectF(content_rect.left(), content_rect.top(), 
                           content_rect.width(), min(content_rect.height() / 2, 20))
        
        # Get the title and truncate if necessary
        title = self.activity.get('title', 'Untitled')
        font_metrics = QFontMetrics(title_font)
        title_width = font_metrics.horizontalAdvance(title)
        
        if title_width > title_rect.width():
            title = font_metrics.elidedText(title, Qt.TextElideMode.ElideRight, int(title_rect.width()))
        
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, title)
        
        # Draw time info
        time_font = QFont()
        time_font.setPointSize(8)
        painter.setFont(time_font)
        
        # Use formatted time strings if available, otherwise fall back to basic formatting
        start_time = self.activity.get('formatted_start_time', '')
        end_time = self.activity.get('formatted_end_time', '')
        
        # If formatted times aren't available, try to format from the time objects
        if not start_time and isinstance(self.activity.get('start_time'), QTime):
            start_time = self.activity.get('start_time').toString("h:mm AP")
        
        if not end_time and isinstance(self.activity.get('end_time'), QTime):
            end_time = self.activity.get('end_time').toString("h:mm AP")
            
        # Fallback to string representation but catch raw QTime objects
        if not start_time and self.activity.get('start_time'):
            start_time_obj = self.activity.get('start_time')
            if "QTime" in str(start_time_obj):
                if hasattr(start_time_obj, 'toString'):
                    start_time = start_time_obj.toString("h:mm AP")
                else:
                    start_time = "Start time"
            else:
                start_time = str(start_time_obj)
                
        if not end_time and self.activity.get('end_time'):
            end_time_obj = self.activity.get('end_time')
            if "QTime" in str(end_time_obj):
                if hasattr(end_time_obj, 'toString'):
                    end_time = end_time_obj.toString("h:mm AP")
                else:
                    end_time = "End time"
            else:
                end_time = str(end_time_obj)
        
        time_text = f"{start_time} - {end_time}" if start_time and end_time else start_time or end_time or ""
        
        time_rect = QRectF(content_rect.left(), title_rect.bottom(), 
                          content_rect.width(), 15)
        
        # Truncate time text if necessary
        font_metrics = QFontMetrics(time_font)
        time_width = font_metrics.horizontalAdvance(time_text)
        
        if time_width > time_rect.width():
            time_text = font_metrics.elidedText(time_text, Qt.TextElideMode.ElideRight, int(time_rect.width()))
        
        painter.drawText(time_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, time_text)
        
        # Draw description if available
        description = self.activity.get('description', '')
        if description and content_rect.height() > 50:  # Only if we have enough space
            desc_font = QFont()
            desc_font.setPointSize(8)
            painter.setFont(desc_font)
            
            desc_rect = QRectF(content_rect.left(), time_rect.bottom() + 5, 
                              content_rect.width(), content_rect.bottom() - time_rect.bottom() - 5)
            
            # Create a bounded text document to properly wrap and truncate text
            font_metrics = QFontMetrics(desc_font)
            available_lines = max(1, int((desc_rect.height() - 5) / font_metrics.height()))
            
            # Skip rendering if description is a QTime object 
            if "QTime" in description:
                description = ""
                
            # Split description into words
            words = description.split()
            current_line = ""
            lines = []
            
            # Group words into lines that fit within width
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if font_metrics.horizontalAdvance(test_line) <= desc_rect.width():
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
                    
                    # Stop if we've reached the maximum number of lines
                    if len(lines) >= available_lines - 1:  # -1 for current line
                        break
            
            # Add the last line
            if current_line and len(lines) < available_lines:
                lines.append(current_line)
                
            # Add ellipsis if we couldn't fit all text
            if len(lines) < available_lines and len(words) > 0 and ' '.join(lines).count(' ') < description.count(' '):
                if lines:
                    lines[-1] = font_metrics.elidedText(lines[-1], Qt.TextElideMode.ElideRight, int(desc_rect.width()))
                else:
                    lines.append(font_metrics.elidedText(description, Qt.TextElideMode.ElideRight, int(desc_rect.width())))
            
            # Draw each line
            for i, line in enumerate(lines):
                if i >= available_lines:
                    break
                line_y = desc_rect.top() + i * font_metrics.height()
                line_rect = QRectF(desc_rect.left(), line_y, desc_rect.width(), font_metrics.height())
                painter.drawText(line_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, line)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click event to show activity details."""
        parent_view = self.scene().views()[0]
        
        if hasattr(parent_view, 'parent') and parent_view.parent and hasattr(parent_view.parent, 'onActivityClicked'):
            parent_view.parent.onActivityClicked(self.activity)
        
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
        
        # Enable context menu policy
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showTimelineContextMenu)
        
        # Track if user is dragging to create a new event
        self.drag_start_pos = None
        self.drag_current_pos = None
        self.drag_rect_item = None
        self.is_dragging = False
        
        # Hour guide lines and labels
        self.hour_lines = []
        self.hour_labels = []
        self.half_hour_lines = []
        
        # Setup initial view
        self.setupHourGuides()
        
        # Set initial scroll position to morning hours (8 AM)
        self.morning_hour = 8  # 8 AM
        QTimer.singleShot(100, self.scrollToMorningHours)
        
        # Current time indicator items
        self.time_line = None
        self.time_dot = None
        self.time_label = None
        
        # Activity items dictionary
        self.activity_items = {}
        
        # Update current time indicator every minute
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.updateCurrentTimeIndicator)
        self.time_timer.start(60000)  # Update every minute
        
        # Set up a timer to refresh activities every 5 seconds
        self.activity_refresh_timer = QTimer(self)
        self.activity_refresh_timer.timeout.connect(self.refreshActivityPositions)
        self.activity_refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def scrollToMorningHours(self):
        """Scroll to show the morning hours (8 AM) after initialization."""
        # Calculate the position for 8 AM
        morning_pos = 8 * HOUR_HEIGHT
        # Set the scroll position to center on 8 AM
        self.centerOn(TIMELINE_WIDTH / 2, morning_pos)
    
    def updateCurrentTimeIndicator(self):
        """Update the position of the current time indicator."""
        if hasattr(self, 'time_line') and self.time_line is not None:
            # Remove old time line
            self.scene.removeItem(self.time_line)
            self.scene.removeItem(self.time_dot)
            self.scene.removeItem(self.time_text)
        
        # Add current time indicator
        self.addCurrentTimeIndicator()
    
    def addCurrentTimeIndicator(self):
        """Add a visual indicator for the current time on the timeline."""
        current_time = QTime.currentTime()
        hour = current_time.hour()
        minute = current_time.minute()
        
        # Calculate position based on time
        y_position = (hour + minute / 60.0) * HOUR_HEIGHT
        
        # Create the gradient for the line
        gradient = QLinearGradient(0, 0, TIMELINE_WIDTH, 0)
        gradient.setColorAt(0.0, QColor(255, 0, 0, 200))  # Solid red at start
        gradient.setColorAt(1.0, QColor(255, 0, 0, 30))   # Transparent red at end
        
        # Create the line
        self.time_line = QGraphicsLineItem(0, y_position, TIMELINE_WIDTH, y_position)
        pen = QPen(QBrush(gradient), 2)
        self.time_line.setPen(pen)
        self.scene.addItem(self.time_line)
        
        # Add a dot at the start of the line
        self.time_dot = QGraphicsEllipseItem(-6, y_position - 6, 12, 12)
        self.time_dot.setBrush(QBrush(QColor(255, 0, 0)))
        self.time_dot.setPen(QPen(QColor(255, 255, 255), 1))
        
        # Add a glow effect to the dot
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(255, 0, 0, 150))
        glow.setOffset(0, 0)
        glow.setBlurRadius(10)
        self.time_dot.setGraphicsEffect(glow)
        
        self.scene.addItem(self.time_dot)
        
        # Add current time text
        time_string = current_time.toString("h:mm AP")
        self.time_text = QGraphicsTextItem(time_string)
        self.time_text.setDefaultTextColor(QColor(255, 0, 0))
        
        # Add a semi-transparent white background to the text for better visibility
        rect = self.time_text.boundingRect()
        bg_rect = QGraphicsRectItem(rect.adjusted(-4, -2, 4, 2))
        bg_rect.setBrush(QBrush(QColor(255, 255, 255, 180)))
        bg_rect.setPen(QPen(Qt.PenStyle.NoPen))
        bg_rect.setParentItem(self.time_text)
        
        # Position the text to the right of the dot
        self.time_text.setPos(15, y_position - 12)
        self.scene.addItem(self.time_text)
        
        # Ensure the current time indicator is visible
        self.ensureVisible(self.time_line, 50, 100)
    
    def refreshActivityPositions(self):
        """Refresh the positioning of activities to avoid overlaps while maintaining consistent widths."""
        # Group activities by time overlap
        overlap_groups = []
        
        # Available width for positioning - VERY WIDE, ALMOST FULL TIMELINE WIDTH
        available_width = TIMELINE_WIDTH - TIMELINE_LEFT_MARGIN - 40
        max_columns = 1  # Single column for maximum width
        fixed_column_width = available_width
        
        # First pass: find all overlapping groups
        for item_id, item in self.activity_items.items():
            if item not in self.scene.items():
                continue
                
            item_rect = item.rect()
            item_y = item_rect.y()
            item_height = item_rect.height()
            item_bottom = item_y + item_height
            
            # Check which group this activity belongs to
            found_group = False
            for group in overlap_groups:
                # Check if this item overlaps with any item in the group
                overlaps_with_group = False
                for group_item in group:
                    group_rect = group_item.rect()
                    group_y = group_rect.y()
                    group_bottom = group_y + group_rect.height()
                    
                    if (item_y <= group_bottom and group_y <= item_bottom):
                        overlaps_with_group = True
                        break
                
                if overlaps_with_group:
                    group.append(item)
                    found_group = True
                    break
            
            # If not in any group, create a new group
            if not found_group:
                overlap_groups.append([item])
        
        # Second pass: reposition items while maintaining width
        for group in overlap_groups:
            if len(group) <= 1:
                continue  # No need to adjust single items
                
            # Single column layout
            columns = 1  # Always use 1 column
            
            # Sort items by start time to ensure consistent ordering
            group.sort(key=lambda x: x.rect().y())
            
            # Fixed very wide item width with small margins
            item_width = fixed_column_width - 20
            
            for item in group:
                item_rect = item.rect()
                
                # Set X position with small margin on both sides
                x_pos = TIMELINE_LEFT_MARGIN + 10
                
                # Only update X position and width, keep Y position and height
                item.setRect(x_pos, item_rect.y(), item_width, item_rect.height())
                item.column_index = 0  # Always use column 0

    def closeEvent(self, event):
        """Handle close event to stop timer."""
        self.time_timer.stop()
        self.activity_refresh_timer.stop()
        super().closeEvent(event)
    
    def setupHourGuides(self):
        """Set up hour guide lines and labels for the timeline."""
        # Remove any existing hour lines
        for item in self.hour_lines:
            self.scene.removeItem(item)
        self.hour_lines.clear()
        
        # Remove any existing hour labels
        for item in self.hour_labels:
            self.scene.removeItem(item)
        self.hour_labels.clear()
        
        # Add new hour lines and labels
        for hour in range(TIMELINE_START_HOUR, TIMELINE_END_HOUR + 1):
            # Calculate y position
            y_pos = hour * HOUR_HEIGHT
            
            # Create hour line
            hour_line = QGraphicsLineItem(0, y_pos, TIMELINE_WIDTH, y_pos)
            hour_line.setPen(QPen(QColor("#E2E8F0"), 1))  # Light gray line
            self.scene.addItem(hour_line)
            self.hour_lines.append(hour_line)
            
            # Format hour for AM/PM display
            if hour == 0:
                hour_display = "12 AM"
            elif hour < 12:
                hour_display = f"{hour} AM"
            elif hour == 12:
                hour_display = "12 PM"
            else:
                hour_display = f"{hour-12} PM"
            
            # Create hour label
            hour_label = QGraphicsTextItem(hour_display)
            hour_label.setDefaultTextColor(QColor("#64748B"))
            hour_label.setPos(5, y_pos - 12)
            self.scene.addItem(hour_label)
            self.hour_labels.append(hour_label)
            
            # Add minor interval lines (every 20 minutes)
            for minute in [20, 40]:
                minor_y = y_pos + (minute / 60) * HOUR_HEIGHT
                minor_line = QGraphicsLineItem(0, minor_y, TIMELINE_WIDTH, minor_y)
                minor_line.setPen(QPen(QColor("#E2E8F0"), 0.5, Qt.PenStyle.DashLine))  # Lighter dashed line
                self.scene.addItem(minor_line)
                self.hour_lines.append(minor_line)  # Store in the same list for cleanup
                
                # Add minute label
                minute_label = QGraphicsTextItem(f"{minute}")
                minute_label.setDefaultTextColor(QColor("#94A3B8"))  # Lighter color for minutes
                minute_label.setFont(QFont("Arial", 7))  # Smaller font
                minute_label.setPos(30, minor_y - 10)
                self.scene.addItem(minute_label)
                self.hour_labels.append(minute_label)  # Store in the same list for cleanup
    
    def addActivity(self, activity):
        """Add an activity to the timeline."""
        # Skip if missing required data
        if (not activity.get('id') or
            not activity.get('title') or
            not activity.get('start_time')):
            print(f"Warning: Activity missing required data: {activity}")
            return
        
        # Handle start time conversion
        start_time = activity.get('start_time')
        if isinstance(start_time, str):
            try:
                # Try to parse time string in format "HH:MM" or "H:MM AM/PM"
                if ":" in start_time:
                    if "AM" in start_time.upper() or "PM" in start_time.upper():
                        # Parse 12-hour format
                        start_time = QTime.fromString(start_time, "h:mm AP")
                    else:
                        # Parse 24-hour format
                        start_time = QTime.fromString(start_time, "HH:mm")
                else:
                    print(f"Warning: Could not parse start time: {start_time}")
                    return
            except Exception as e:
                print(f"Error parsing start time: {e}")
                return
            
        # Handle end time conversion
        end_time = activity.get('end_time')
        if isinstance(end_time, str):
            try:
                # Try to parse time string
                if ":" in end_time:
                    if "AM" in end_time.upper() or "PM" in end_time.upper():
                        # Parse 12-hour format
                        end_time = QTime.fromString(end_time, "h:mm AP")
                    else:
                        # Parse 24-hour format
                        end_time = QTime.fromString(end_time, "HH:mm")
                else:
                    print(f"Warning: Could not parse end time: {end_time}")
                    # Use start time + 1 hour as fallback
                    if isinstance(start_time, QTime):
                        end_time = start_time.addSecs(3600)
            except Exception as e:
                print(f"Error parsing end time: {e}")
                # Use start time + 1 hour as fallback
                if isinstance(start_time, QTime):
                    end_time = start_time.addSecs(3600)
        
        # If we still don't have a valid end time, use start + 1 hour
        if not end_time or (isinstance(end_time, QTime) and not end_time.isValid()):
            if isinstance(start_time, QTime):
                end_time = start_time.addSecs(3600)
            else:
                print(f"Warning: Could not determine end time for activity: {activity}")
                return
            
        # Format time strings for display
        if isinstance(start_time, QTime):
            activity['formatted_start_time'] = start_time.toString("h:mm AP")
        if isinstance(end_time, QTime):
            activity['formatted_end_time'] = end_time.toString("h:mm AP")
            
        # Calculate time positions
        start_hour = start_time.hour()
        start_minute = start_time.minute()
        start_y = (start_hour + start_minute / 60.0) * HOUR_HEIGHT
        
        end_hour = end_time.hour()
        end_minute = end_time.minute()
        end_y = (end_hour + end_minute / 60.0) * HOUR_HEIGHT
        
        # Handle end time being earlier than start time (spans to next day)
        if end_y <= start_y:
            end_y = (24 + end_hour + end_minute / 60.0) * HOUR_HEIGHT
        
        # Ensure minimum height for visibility
        height = max(end_y - start_y, 30)
        
        # Find a suitable x position (handle overlapping activities)
        x_pos = TIMELINE_LEFT_MARGIN
        width = 200  # Default width
        
        # Create the activity item
        item = ActivityTimelineItem(activity, x_pos, start_y, width, height)
        self.scene.addItem(item)
        self.activity_items[activity.get('id')] = item
        
        print(f"Added activity {activity.get('title')} with extra wide width {width}")
        
        # Don't refresh positions to maintain consistent sizing
    
    def clearActivities(self):
        """Remove all activities from the timeline."""
        for item_id, item in list(self.activity_items.items()):
            if item in self.scene.items():
                self.scene.removeItem(item)
        self.activity_items.clear()
    
    def showTimelineContextMenu(self, pos):
        """Show context menu at the specified position."""
        scene_pos = self.mapToScene(pos)
        
        # Only show context menu in the activity area (right of the time axis)
        if scene_pos.x() < TIMELINE_LEFT_MARGIN:
            return
        
        # Calculate the time at the clicked position
        y_pos = scene_pos.y()
        minutes_on_timeline = (y_pos / HOUR_HEIGHT) * 60
        minutes_since_start = minutes_on_timeline + (TIMELINE_START_HOUR * 60)
        
        # Convert to hours and minutes
        hours = int(minutes_since_start / 60)
        minutes = int(minutes_since_start % 60)
        
        # Round minutes to the nearest 5
        minutes = round(minutes / 5) * 5
        if minutes == 60:
            hours += 1
            minutes = 0
            
        # Create time string to show in the menu
        clicked_time = QTime(hours, minutes)
        time_str = clicked_time.toString("h:mm AP")
        
        menu = QMenu(self)
        
        # Add action to add different activity types
        menu.addSection(f"At {time_str}")
        add_task_action = menu.addAction("Add Task Here")
        add_event_action = menu.addAction("Add Event Here")
        add_habit_action = menu.addAction("Add Habit Here")
        
        # Show menu and handle selection
        action = menu.exec(self.mapToGlobal(pos))
        
        # Find the DailyView parent - might not be the direct parent
        daily_view = None
        parent = self.parent()
        
        # Walk up the parent chain until we find a DailyView
        while parent:
            if isinstance(parent, DailyView):
                daily_view = parent
                break
            # Try to get the parent's parent
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                break
        
        # Create activity at the clicked time if we found the DailyView
        if daily_view:
            if action == add_task_action:
                daily_view.addActivity('task', scene_pos.x(), scene_pos.y())
            elif action == add_event_action:
                daily_view.addActivity('event', scene_pos.x(), scene_pos.y())
            elif action == add_habit_action:
                daily_view.addActivity('habit', scene_pos.x(), scene_pos.y())
        else:
            print("Error: Could not find DailyView parent to add activity")
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            
            # Only start drag in the activity area (right of the time axis)
            if scene_pos.x() > TIMELINE_LEFT_MARGIN:
                item = self.itemAt(event.pos())
                
                # If we clicked on an empty area, start dragging to create a new activity
                if not item or (not isinstance(item, ActivityTimelineItem) and 
                               (not item.parentItem() or not isinstance(item.parentItem(), ActivityTimelineItem))):
                    self.drag_start_pos = scene_pos
                    self.is_dragging = True
                    
                    # Create a temporary rectangle to show the dragging area
                    self.drag_rect_item = self.scene.addRect(
                        scene_pos.x(), scene_pos.y(), 10, 10,
                        QPen(QColor("#6366F1"), 2, Qt.PenStyle.DashLine),
                        QBrush(QColor(99, 102, 241, 50))  # Semi-transparent indigo
                    )
                    return
                
                # If we clicked on an activity, handle selection
                if isinstance(item, ActivityTimelineItem) or (item and item.parentItem() and isinstance(item.parentItem(), ActivityTimelineItem)):
                    # If we clicked on a text item, get its parent
                    if item and not isinstance(item, ActivityTimelineItem):
                        item = item.parentItem()
                    
                    # Emit signal with the activity data
                    if item and hasattr(item, 'activity'):
                        self.activityClicked.emit(item.activity)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move event."""
        if self.is_dragging and self.drag_start_pos:
            scene_pos = self.mapToScene(event.pos())
            self.drag_current_pos = scene_pos
            
            # Update the drag rectangle
            if self.drag_rect_item:
                x = min(self.drag_start_pos.x(), scene_pos.x())
                y = min(self.drag_start_pos.y(), scene_pos.y())
                width = abs(scene_pos.x() - self.drag_start_pos.x())
                height = abs(scene_pos.y() - self.drag_start_pos.y())
                
                # Ensure minimum dimensions
                width = max(width, 100)
                height = max(height, 30)
                
                self.drag_rect_item.setRect(x, y, width, height)
            
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            if self.drag_start_pos and self.drag_current_pos:
                # Only create activity if drag was significant (not just a click)
                distance = ((self.drag_current_pos.x() - self.drag_start_pos.x()) ** 2 + 
                           (self.drag_current_pos.y() - self.drag_start_pos.y()) ** 2) ** 0.5
                
                if distance > 10:  # Minimum drag distance
                    # Calculate the start and end times from the drag rectangle
                    start_y = min(self.drag_start_pos.y(), self.drag_current_pos.y())
                    end_y = max(self.drag_start_pos.y(), self.drag_current_pos.y())
                    
                    # Calculate minutes with precision
                    start_minutes_on_timeline = (start_y / HOUR_HEIGHT) * 60
                    start_minutes_since_start = start_minutes_on_timeline + (TIMELINE_START_HOUR * 60)
                    
                    end_minutes_on_timeline = (end_y / HOUR_HEIGHT) * 60
                    end_minutes_since_start = end_minutes_on_timeline + (TIMELINE_START_HOUR * 60)
                    
                    # Convert to hours and minutes
                    start_hour = int(start_minutes_since_start / 60)
                    start_minute = int(start_minutes_since_start % 60)
                    
                    end_hour = int(end_minutes_since_start / 60)
                    end_minute = int(end_minutes_since_start % 60)
                    
                    # Snap to nearest 5-minute interval
                    start_minute = (start_minute // 5) * 5
                    end_minute = ((end_minute + 4) // 5) * 5
                    
                    # Create QTime objects with bounds checking
                    start_hour = min(23, max(0, start_hour))
                    start_minute = min(59, max(0, start_minute))
                    end_hour = min(23, max(0, end_hour))
                    end_minute = min(59, max(0, end_minute))
                    
                    start_time = QTime(start_hour, start_minute)
                    end_time = QTime(end_hour, end_minute)
                    
                    # Ensure end time is after start time
                    if end_time <= start_time:
                        end_time = start_time.addSecs(1800)  # Add 30 minutes
                    
                    # Get the current date from the DailyView parent
                    # Find the DailyView parent - might not be the direct parent
                    daily_view = None
                    parent = self.parent()
                    
                    # Walk up the parent chain until we find a DailyView
                    while parent:
                        if isinstance(parent, DailyView):
                            daily_view = parent
                            break
                        # Try to get the parent's parent
                        if hasattr(parent, 'parent'):
                            parent = parent.parent()
                        else:
                            break
                    
                    # Use the found DailyView or fallback to current date
                    current_date = QDate.currentDate()
                    if daily_view and hasattr(daily_view, 'current_date'):
                        current_date = daily_view.current_date
                    
                    # Show dialog to create new event
                    initial_data = {
                        'date': current_date,
                        'start_time': start_time,
                        'end_time': end_time
                    }
                    
                    # Ask what type of activity to create
                    menu = QMenu()
                    
                    task_action = menu.addAction("Add Task")
                    event_action = menu.addAction("Add Event")
                    habit_action = menu.addAction("Add Habit")
                    
                    # Show menu at cursor position
                    action = menu.exec(QCursor.pos())
                    
                    if action == task_action:
                        activity_type = 'task'
                    elif action == event_action:
                        activity_type = 'event'
                    elif action == habit_action:
                        activity_type = 'habit'
                    else:
                        activity_type = None
                    
                    if activity_type and daily_view:
                        daily_view.addActivity(activity_type, None, None, initial_data)
                    elif activity_type:
                        # Try to find another way to add the activity
                        parent = self.parent()
                        if parent and hasattr(parent, 'addActivity'):
                            parent.addActivity(activity_type, None, None, initial_data)
            
            # Clean up
        if  self.drag_rect_item:
            self.scene.removeItem(self.drag_rect_item)
            self.drag_rect_item = None
        
            self.drag_start_pos = None
            self.drag_current_pos = None
            self.is_dragging = False
        
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Enhanced wheel event to support vertical scrolling only without zooming."""
        # Just use normal scrolling, no zooming to avoid resizing blocks
        super().wheelEvent(event)

# Make sure DailyView is accessible for isinstance checks in TimelineView
# This needs to be placed here before DailyView is used in any isinstance checks

class DailyView(QWidget):
    """Widget for daily planning with timeline visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store parent to access database
        
        # Initialize activities manager
        self.activities_manager = None
        self.initializeActivitiesManager()
        
        self.current_date = QDate.currentDate()
        self.setupUI()
        
        # Connect to the main application's signals if available
        self.connectApplicationSignals()
    
    def initializeActivitiesManager(self):
        """Initialize the activities manager with proper fallbacks."""
        # Try different methods to get a valid activities manager
        if self.parent and hasattr(self.parent, 'activities_manager'):
            # Direct connection to parent's activities manager
            self.activities_manager = self.parent.activities_manager
            print("Using parent's activities manager")
        elif self.parent and hasattr(self.parent, 'conn') and self.parent.conn:
            # Create our own activities manager using parent's connection
            from app.models.activities_manager import ActivitiesManager
            self.activities_manager = ActivitiesManager(self.parent.conn, self.parent.cursor)
            print("Created activities manager from parent's connection")
        else:
            # Try to access activities manager from main application if it exists
            try:
                # Look for the main application window in the application objects
                from PyQt6.QtWidgets import QApplication
                for widget in QApplication.topLevelWidgets():
                    if hasattr(widget, 'activities_manager'):
                        self.activities_manager = widget.activities_manager
                        print("Found activities manager from top-level application")
                        break
                
                # If still not found, create a new one
                if not self.activities_manager:
                    from app.models.database import initialize_db
                    conn, cursor = initialize_db()
                    from app.models.activities_manager import ActivitiesManager
                    self.activities_manager = ActivitiesManager(conn, cursor)
                    self.activities_manager.create_tables()  # Ensure tables exist
                    print("Created standalone activities manager with new connection")
            except Exception as e:
                print(f"Could not initialize activities manager: {e}")
                import traceback
                traceback.print_exc()
    
    def connectApplicationSignals(self):
        """Connect to signals from the main application to refresh data when changes occur."""
        try:
            # Try to connect to the main window's signals if available
            main_app = None
            
            # First try parent
            if self.parent and hasattr(self.parent, 'activityAdded'):
                main_app = self.parent
            else:
                # Look for the main application window
                from PyQt6.QtWidgets import QApplication
                for widget in QApplication.topLevelWidgets():
                    if hasattr(widget, 'activityAdded') and hasattr(widget, 'activityCompleted') and hasattr(widget, 'activityDeleted'):
                        main_app = widget
                        break
            
            if main_app:
                # Connect to activity signals
                main_app.activityAdded.connect(self.onActivityChanged)
                main_app.activityCompleted.connect(self.onActivityChanged)
                main_app.activityDeleted.connect(self.onActivityChanged)
                print("Connected to main application signals for auto-refresh")
            
            # Also connect to the activities view directly if we can find it
            if self.parent and hasattr(self.parent, 'activitiesView'):
                activities_view = self.parent.activitiesView
                if hasattr(activities_view, 'activityAdded'):
                    activities_view.activityAdded.connect(self.onActivityChanged)
                if hasattr(activities_view, 'activityCompleted'):
                    activities_view.activityCompleted.connect(self.onActivityChanged)
                if hasattr(activities_view, 'activityDeleted'):
                    activities_view.activityDeleted.connect(self.onActivityChanged)
                print("Connected to activities view signals for auto-refresh")
        except Exception as e:
            print(f"Could not connect to application signals: {e}")
    
    def onActivityChanged(self, *args):
        """Handle activity changes from anywhere in the application."""
        print("Activity changed signal received, refreshing daily view")
        self.refresh()
    
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
            # Try to re-initialize the activities manager as a last resort
            self.initializeActivitiesManager()
            if not self.activities_manager:
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
                    print(f"  - {act.get('title')} ({act.get('type')}): " +
                          f"{act.get('start_time').toString('HH:mm') if act.get('start_time') else 'No start time'} to " +
                          f"{act.get('end_time').toString('HH:mm') if act.get('end_time') else 'No end time'}")
                    
                    # Print description for debugging
                    if 'description' in act and act['description']:
                        print(f"    Description: {act['description']}")
            
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
        from PyQt6.QtWidgets import QMenu
        
        # Create a menu for activity types
        menu = QMenu(self)
        
        task_action = menu.addAction("Add Task")
        task_action.triggered.connect(lambda: self.addActivity('task'))
        
        event_action = menu.addAction("Add Event")
        event_action.triggered.connect(lambda: self.addActivity('event'))
        
        habit_action = menu.addAction("Add Habit")
        habit_action.triggered.connect(lambda: self.addActivity('habit'))
        
        # Show menu at cursor position
        menu.exec(QCursor.pos())
    
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
        # Check if the activities manager is still valid
        if not self.activities_manager:
            self.initializeActivitiesManager()
        
        self.loadTimelineData()
        self.loadNotes() 

    def addActivity(self, activity_type, x=None, y=None, initial_data=None):
        """Add a new activity.
        
        Args:
            activity_type: Type of activity to add ('task', 'event', or 'habit')
            x: X coordinate in the timeline (optional)
            y: Y coordinate in the timeline (optional)
            initial_data: Initial data to populate the dialog (optional)
        """
        if not initial_data:
            initial_data = {'date': self.current_date}
        
        # If position is provided, calculate the time
        if x is not None and y is not None and not initial_data.get('start_time'):
            # Convert y position to time
            hour = int(y / HOUR_HEIGHT) + TIMELINE_START_HOUR
            minute = int((y % HOUR_HEIGHT) / HOUR_HEIGHT * 60)
            
            # Create QTime objects
            start_time = QTime(hour, minute)
            end_time = QTime(hour + 1, minute)  # Default to 1 hour duration
            
            # Add to initial data
            initial_data['start_time'] = start_time
            initial_data['end_time'] = end_time
        
        # If parent has an activities view with a dialog, use that
        if self.parent and hasattr(self.parent, 'activitiesView') and hasattr(self.parent.activitiesView, 'showAddActivityDialog'):
            # Pass the initial data to ensure correct date and times are used
            self.parent.activitiesView.showAddActivityDialog(activity_type, initial_data)
            # Refresh will happen via signals
        else:
            # Try to add directly using activities manager if available
            if self.activities_manager:
                try:
                    self.showAddActivityDirectly(activity_type, initial_data)
                except Exception as e:
                    print(f"Error adding activity directly: {e}")
                    QMessageBox.warning(self, "Error", f"Could not add activity: {str(e)}")
            else:
                QMessageBox.information(self, "Not Available", "Activity management is not available")
    
    def showAddActivityDirectly(self, activity_type, initial_data=None):
        """Show a dialog to add an activity directly using this view."""
        from PyQt6.QtWidgets import QDialog, QTimeEdit, QDateEdit, QDialogButtonBox
        from PyQt6.QtWidgets import QFormLayout, QLineEdit, QTextEdit, QComboBox, QCheckBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Add {activity_type.capitalize()}")
        
        layout = QFormLayout(dialog)
        
        # Title field
        title_edit = QLineEdit()
        layout.addRow("Title:", title_edit)
        
        # Date field
        date_edit = QDateEdit()
        date_edit.setDate(initial_data.get('date', QDate.currentDate()))
        date_edit.setCalendarPopup(True)
        layout.addRow("Date:", date_edit)
        
        # Time fields
        start_time_edit = QTimeEdit()
        if 'start_time' in initial_data:
            start_time_edit.setTime(initial_data['start_time'])
        else:
            start_time_edit.setTime(QTime.currentTime())
        layout.addRow("Start Time:", start_time_edit)
        
        end_time_edit = QTimeEdit()
        if 'end_time' in initial_data:
            end_time_edit.setTime(initial_data['end_time'])
        else:
            end_time = QTime.currentTime().addSecs(3600)  # Add 1 hour
            end_time_edit.setTime(end_time)
        layout.addRow("End Time:", end_time_edit)
        
        # Description field
        description_edit = QTextEdit()
        description_edit.setPlaceholderText("Enter a description...")
        layout.addRow("Description:", description_edit)
        
        # Category field
        category_edit = QLineEdit()
        layout.addRow("Category:", category_edit)
        
        # Priority for tasks
        priority_combo = QComboBox()
        priority_combo.addItems(["Low", "Medium", "High"])
        priority_combo.setCurrentIndex(1)  # Medium by default
        if activity_type == 'task':
            layout.addRow("Priority:", priority_combo)
        
        # Days of week for habits
        days_widget = QWidget()
        days_layout = QHBoxLayout(days_widget)
        day_checkboxes = []
        
        if activity_type == 'habit':
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for day in days:
                checkbox = QCheckBox(day)
                day_checkboxes.append(checkbox)
                days_layout.addWidget(checkbox)
            layout.addRow("Repeat on:", days_widget)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Collect data
            activity_data = {
                'title': title_edit.text(),
                'date': date_edit.date(),
                'start_time': start_time_edit.time(),
                'end_time': end_time_edit.time(),
                'description': description_edit.toPlainText(),
                'category': category_edit.text(),
                'type': activity_type,
                'completed': False
            }
            
            # Add type-specific data
            if activity_type == 'task':
                activity_data['priority'] = priority_combo.currentIndex()
            elif activity_type == 'habit':
                days_list = []
                for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
                    if day_checkboxes[i].isChecked():
                        days_list.append(day)
                activity_data['days_of_week'] = ",".join(days_list)
            
            # Add to database
            try:
                self.activities_manager.add_activity(activity_data)
                self.refresh()
            except Exception as e:
                print(f"Error adding activity: {e}")
                QMessageBox.warning(self, "Error", f"Could not add activity: {str(e)}") 