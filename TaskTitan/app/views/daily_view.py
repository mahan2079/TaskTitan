"""
Daily planning view for TaskTitan with timeline visualization.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QScrollArea, QFrame, QSplitter, QTabWidget, QListWidget, 
                           QListWidgetItem, QDialog, QLineEdit, QTimeEdit, QDateEdit,
                           QTextEdit, QCheckBox, QComboBox, QDialogButtonBox, QMessageBox, QMenu,
                           QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
                           QGraphicsItem, QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QDate, QTime, QSize, pyqtSignal, QRectF, QMargins, QTimer
from PyQt6.QtGui import QIcon, QColor, QBrush, QPen, QFont, QPainter, QCursor, QFontMetrics
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
        
        # Store color for text contrast calculations
        self.base_color = color
        
        # Set rounded corners
        self.setData(0, "activity")
        self.setData(1, self.activity['id'])
        self.setData(2, activity_type)
    
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
        
        # Extract activity information for displaying
        title = self.activity.get('title', 'Untitled')
        description = self.activity.get('description', '')
        activity_type = self.activity.get('type', '').capitalize()
        category = self.activity.get('category', '')
        start_time = self.activity.get('start_time')
        end_time = self.activity.get('end_time')
        priority = self.activity.get('priority', 0)
        is_completed = self.activity.get('completed', False)

        # Format time range for display
        time_str = ""
        if start_time and end_time:
            if isinstance(start_time, QTime):
                start_str = start_time.toString("h:mm AP")
            else:
                start_str = str(start_time)
                
            if isinstance(end_time, QTime):
                end_str = end_time.toString("h:mm AP")
            else:
                end_str = str(end_time)
                
            time_str = f"{start_str} - {end_str}"
        
        # Format priority text
        priority_text = ""
        if activity_type.lower() == 'task' and priority is not None:
            priority_labels = ["Low", "Medium", "High"]
            if 0 <= priority < len(priority_labels):
                priority_text = f"{priority_labels[priority]} Priority"
        
        # Create formatted line of metadata
        meta_parts = []
        if activity_type:
            meta_parts.append(activity_type)
        if time_str:
            meta_parts.append(time_str)
        if priority_text:
            meta_parts.append(priority_text)
        if category:
            meta_parts.append(category)
            
        meta_text = " • ".join(meta_parts)
        
        # Set up fonts
        title_font = QFont("Arial", 10, QFont.Weight.Bold)
        meta_font = QFont("Arial", 8)
        desc_font = QFont("Arial", 9)
        
        # Calculate text layout positions
        padding = 10
        content_x = self.rect().left() + padding
        content_width = self.rect().width() - (padding * 2)
        
        # Calculate text color based on background brightness
        bg_color = self.brush().color()
        brightness = (bg_color.red() * 299 + bg_color.green() * 587 + bg_color.blue() * 114) / 1000
        
        # Use dark text on light backgrounds, light text on dark backgrounds
        title_color = QColor(33, 33, 33) if brightness > 128 else QColor(240, 240, 240)
        meta_color = QColor(75, 85, 99) if brightness > 128 else QColor(200, 200, 200)
        desc_color = QColor(75, 85, 99) if brightness > 128 else QColor(200, 200, 200)
        
        # Draw title (bold)
        painter.setFont(title_font)
        painter.setPen(title_color)
        title_rect = QRectF(
            content_x, 
            self.rect().top() + padding,
            content_width, 
            25
        )
        
        # Add ellipsis if title too long
        title_metrics = painter.fontMetrics()
        if title_metrics.horizontalAdvance(title) > content_width:
            title = title_metrics.elidedText(title, Qt.TextElideMode.ElideRight, content_width)
            
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, title)
        
        # Draw metadata line below title
        painter.setFont(meta_font)
        painter.setPen(meta_color)
        meta_rect = QRectF(
            content_x, 
            title_rect.bottom(),
            content_width, 
            20
        )
        
        # Simplify metadata if space is limited
        if self.rect().width() < 120:
            # For narrow columns, show minimal info
            if activity_type and time_str:
                meta_text = f"{activity_type}"
            else:
                meta_text = " • ".join(meta_parts[:1])  # Just the first item
                
        # Add ellipsis if metadata too long
        meta_metrics = painter.fontMetrics()
        if meta_metrics.horizontalAdvance(meta_text) > content_width:
            meta_text = meta_metrics.elidedText(meta_text, Qt.TextElideMode.ElideRight, content_width)
            
        painter.drawText(meta_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, meta_text)
        
        # Draw description if available and there's enough height
        if description and self.rect().height() > 60:
            # Add separator line
            separator_y = meta_rect.bottom() + 2
            painter.setPen(QPen(QColor(200, 200, 200, 100), 1))  # Light gray with transparency
            painter.drawLine(
                content_x, separator_y,
                content_x + content_width, separator_y
            )
            
            # Draw description text
            painter.setFont(desc_font)
            painter.setPen(desc_color)
            desc_rect = QRectF(
                content_x, 
                separator_y + 4,
                content_width, 
                self.rect().height() - separator_y - padding
            )
            
            # If very limited space, skip description
            if self.rect().height() < 80 or self.rect().width() < 100:
                painter.restore()
                return
                
            # Handle multiline description with eliding if too long
            desc_metrics = painter.fontMetrics()
            desc_height = desc_rect.height()
            line_height = desc_metrics.height()
            max_lines = int(desc_height / line_height)
            
            if max_lines > 0:
                # Split description into words
                words = description.split()
                lines = []
                current_line = ""
                
                # Build lines that fit within width
                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    if desc_metrics.horizontalAdvance(test_line) <= content_width:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                        # Check if we've reached max lines
                        if len(lines) >= max_lines - 1:  # Save space for last line
                            break
                
                # Add last line
                if current_line:
                    lines.append(current_line)
                
                # If we have more words but limited by max_lines, add ellipsis to last line
                if len(lines) == max_lines and word != words[-1]:
                    last_line = lines[-1]
                    last_line = desc_metrics.elidedText(last_line + "...", Qt.TextElideMode.ElideRight, content_width)
                    lines[-1] = last_line
                
                # Draw each line
                for i, line in enumerate(lines):
                    painter.drawText(
                        QRectF(
                            content_x,
                            separator_y + 4 + (i * line_height),
                            content_width,
                            line_height
                        ),
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                        line
                    )
        
        # Draw completion indicator for tasks
        if activity_type.lower() == 'task':
            status_rect = QRectF(
                self.rect().right() - 25, 
                self.rect().top() + padding, 
                15, 
                15
            )
            
            if is_completed:
                # Checkmark for completed
                painter.setPen(QPen(Qt.PenStyle.NoPen))
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
        
        painter.restore()
    
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
        if self.time_label:
            self.scene.removeItem(self.time_label)
            self.time_label = None
            
        # Add new indicator
        self.addCurrentTimeIndicator()
    
    def addCurrentTimeIndicator(self):
        """Add a horizontal line indicating the current time."""
        current_time = QTime.currentTime()
        try:
            parent_widget = self.parent()
            if hasattr(parent_widget, 'current_date'):
                is_today = QDate.currentDate() == parent_widget.current_date
            else:
                is_today = True  # Fallback
        except:
            is_today = QDate.currentDate() == QDate.currentDate()  # Fallback
            
        if is_today:
            # Calculate position with minute precision
            hours = current_time.hour()
            minutes = current_time.minute()
            minutes_since_start = hours * 60 + minutes
            minutes_since_timeline_start = minutes_since_start - (TIMELINE_START_HOUR * 60)
            y_pos = (minutes_since_timeline_start / 60) * HOUR_HEIGHT
            
            # Draw the time indicator line with a red pen
            pen = QPen(QColor("#EF4444"), 2)  # Red line
            pen.setDashPattern([5, 3])  # Dashed line
            self.time_line = self.scene.addLine(
                TIMELINE_LEFT_MARGIN, y_pos,
                TIMELINE_WIDTH, y_pos,
                pen
            )
            
            # Add small circle at the start of the line
            self.time_dot = self.scene.addEllipse(
                TIMELINE_LEFT_MARGIN - 4, y_pos - 4, 8, 8,
                QPen(QColor("#EF4444")),
                QBrush(QColor("#EF4444"))
            )
            
            # Add time text
            time_text = current_time.toString("h:mm AP")
            time_font = QFont("Arial", 9, QFont.Weight.Bold)
            self.time_label = self.scene.addText(time_text, time_font)
            self.time_label.setDefaultTextColor(QColor("#EF4444"))
            text_width = QFontMetrics(time_font).horizontalAdvance(time_text)
            self.time_label.setPos(TIMELINE_LEFT_MARGIN - 15 - text_width, y_pos - 9)
            
            # Ensure the time indicator is visible
            self.ensureVisible(self.time_line, 50, 200)
    
    def refreshActivityPositions(self):
        """Refresh the positioning of activities to avoid overlaps."""
        # Group activities by time overlap
        overlap_groups = []
        
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
        
        # Second pass: assign columns within each group
        for group in overlap_groups:
            if len(group) <= 1:
                continue  # No need to adjust single items
                
            # Calculate available width
            available_width = TIMELINE_WIDTH - TIMELINE_LEFT_MARGIN - 20
            
            # Determine number of columns needed (max 4 to avoid too narrow items)
            columns = min(len(group), 4)
            column_width = available_width / columns
            
            # Sort items by start time to ensure consistent ordering
            group.sort(key=lambda x: x.rect().y())
            
            # Greedy column assignment
            column_end_times = [0] * columns  # Track the end time of each column
            
            for item in group:
                item_rect = item.rect()
                item_y = item_rect.y()
                item_height = item_rect.height()
                item_bottom = item_y + item_height
                
                # Find the column with earliest end time
                best_column = 0
                for i in range(columns):
                    if column_end_times[i] <= item_y:
                        best_column = i
                        break
                    elif column_end_times[i] < column_end_times[best_column]:
                        best_column = i
                
                # Update column end time
                column_end_times[best_column] = item_bottom
                
                # Calculate new position for the item
                x_pos = TIMELINE_LEFT_MARGIN + 10 + (best_column * column_width)
                width = column_width - 10
                
                # Update item position and width
                item.setRect(x_pos, item_rect.y(), width, item_rect.height())
                item.column_index = best_column  # Store column for future reference

    def closeEvent(self, event):
        """Handle close event to stop timer."""
        self.time_timer.stop()
        self.activity_refresh_timer.stop()
        super().closeEvent(event)
    
    def setupHourGuides(self):
        """Draw the hour lines and labels."""
        self.scene.clear()
        self.hour_lines = []
        self.hour_labels = []
        self.half_hour_lines = []
        self.activity_items = {}
        
        # Draw hour lines and labels
        for hour in range(TIMELINE_START_HOUR, TIMELINE_END_HOUR + 1):
            y_pos = (hour - TIMELINE_START_HOUR) * HOUR_HEIGHT
            
            # Draw horizontal line for the hour
            hour_line = self.scene.addLine(
                TIMELINE_LEFT_MARGIN, y_pos,
                TIMELINE_WIDTH, y_pos,
                QPen(QColor("#E5E7EB"), 1)
            )
            self.hour_lines.append(hour_line)
            
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
                QFont("Arial", 10, QFont.Weight.Bold)
            )
            time_label.setPos(5, y_pos - 10)
            time_label.setDefaultTextColor(QColor("#64748B"))
            self.hour_labels.append(time_label)
            
            # Add 15-minute marks
            for minute in [15, 30, 45]:
                minute_y = y_pos + (HOUR_HEIGHT * minute / 60)
                line_style = Qt.PenStyle.DashLine if minute != 30 else Qt.PenStyle.DashDotLine
                line_width = 0.5 if minute != 30 else 0.7
                minute_line = self.scene.addLine(
                    TIMELINE_LEFT_MARGIN, minute_y,
                    TIMELINE_WIDTH, minute_y,
                    QPen(QColor("#E5E7EB"), line_width, line_style)
                )
                if minute == 30:
                    self.half_hour_lines.append(minute_line)
                
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
        activity_id = activity.get('id')
        
        # Skip activities with no valid time or ID
        if not start_time or not end_time or activity_id is None:
            print(f"Skipping activity with missing time or ID: {activity.get('title', 'Unknown')}")
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
        
        # Calculate position with minute precision
        start_minutes = start_time.hour() * 60 + start_time.minute()
        end_minutes = end_time.hour() * 60 + end_time.minute()
        
        # Handle activities that span to the next day
        if end_minutes <= start_minutes:
            # Assume it ends on the next day
            end_minutes = 24 * 60 - 1  # End at 23:59
            print(f"Activity spans to next day, capped at midnight: {activity.get('title')}")
        
        # Calculate timeline coordinates with minute precision
        start_minutes_on_timeline = start_minutes - (TIMELINE_START_HOUR * 60)
        end_minutes_on_timeline = end_minutes - (TIMELINE_START_HOUR * 60)
        
        # Calculate y-position and height
        y_pos = (start_minutes_on_timeline / 60) * HOUR_HEIGHT
        height = ((end_minutes_on_timeline - start_minutes_on_timeline) / 60) * HOUR_HEIGHT
        
        # Ensure minimum height for visibility (30 pixels)
        height = max(height, 30)
        
        # Calculate available width
        available_width = TIMELINE_WIDTH - TIMELINE_LEFT_MARGIN - 20  # Leave some margin
        
        # Check for overlapping activities and organize them in columns
        overlapping_items = []
        column_assignments = {}  # To track which column each overlapping item is in
        
        # First pass: identify all overlapping activities
        for item_id, item in self.activity_items.items():
            if item_id != activity_id and item in self.scene.items():
                item_rect = item.rect()
                
                # Check if the activity overlaps with this one
                item_top = item_rect.y()
                item_bottom = item_rect.y() + item_rect.height()
                
                # If there's any overlap in the vertical space
                if (y_pos <= item_bottom and item_top <= y_pos + height):
                    overlapping_items.append(item)
                    # Remember existing column assignment
                    if hasattr(item, 'column_index'):
                        column_assignments[item] = item.column_index
                    else:
                        column_assignments[item] = 0  # Default
        
        # Second pass: determine best column for this activity
        used_columns = set(column_assignments.values())
        column_index = 0
        max_columns = 4  # Limit number of columns to avoid too narrow activities
        
        # Find first available column
        while column_index < max_columns and column_index in used_columns:
            column_index += 1
        
        # If we're beyond max columns, reuse columns with fewest overlaps
        if column_index >= max_columns:
            column_counts = {}
            for col in range(max_columns):
                column_counts[col] = sum(1 for c in column_assignments.values() if c == col)
            column_index = min(column_counts, key=column_counts.get)
        
        # Calculate total columns needed
        columns = max(len(set(column_assignments.values())) + 1, column_index + 1)
        columns = min(columns, max_columns)  # Enforce max columns limit
        
        # Calculate width for each column
        column_width = available_width / columns
        x_pos = TIMELINE_LEFT_MARGIN + 10 + (column_index * column_width)
        width = column_width - 10  # Leave a small gap between columns
        
        print(f"Positioning activity {activity.get('title')}: start={start_time.toString()}, "
              f"end={end_time.toString()}, y={y_pos}, h={height}, col={column_index}/{columns}")
        
        # Create the item and add to scene
        item = ActivityTimelineItem(
            activity,
            x_pos,
            y_pos,
            width,
            height,
            None
        )
        item.column_index = column_index  # Store column index for future reference
        self.scene.addItem(item)
        self.activity_items[activity_id] = item
        
        # Refresh positions to ensure proper layout
        if overlapping_items and len(overlapping_items) > 2:
            self.refreshActivityPositions()
    
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