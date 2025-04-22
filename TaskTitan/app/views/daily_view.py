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
                           QGraphicsLineItem, QGraphicsEllipseItem, QProgressBar, QSpinBox,
                           QToolButton, QSlider, QRadioButton, QButtonGroup, QFormLayout,
                           QColorDialog, QScrollBar, QCalendarWidget, QStackedWidget,
                           QStyledItemDelegate, QStyleOptionViewItem, QStyle, QAbstractItemView)
from PyQt6.QtCore import Qt, QDate, QTime, QSize, pyqtSignal, QRectF, QMargins, QTimer, QPointF, QEasingCurve, QPropertyAnimation, QRect
from PyQt6.QtGui import QIcon, QColor, QBrush, QPen, QFont, QPainter, QCursor, QFontMetrics, QLinearGradient, QPolygonF, QPainterPath, QPixmap, QRadialGradient, QConicalGradient, QTransform, QPalette, QTextDocument, QAbstractTextDocumentLayout
from datetime import datetime, timedelta
import sqlite3
import math
import random

from app.resources import get_icon
from app.models.activities_manager import ActivitiesManager

# Modern color palette
COLORS = {
    "primary": "#6200EA",  # Deep purple
    "secondary": "#03DAC6",  # Teal
    "accent": "#FF4081",  # Pink
    "success": "#4CAF50",  # Green
    "warning": "#FB8C00",  # Orange
    "error": "#F44336",  # Red
    "info": "#2196F3",  # Blue
    "light": "#F5F5F5",  # Light gray
    "dark": "#212121",  # Dark gray
    "background": "#FAFAFA",  # Very light gray
    "card": "#FFFFFF",  # White
    "text_primary": "#212121",  # Dark gray
    "text_secondary": "#757575",  # Medium gray
    "border": "#E0E0E0",  # Light gray
    
    # Activity type colors
    "task": "#FF7043",  # Deep orange
    "event": "#7C4DFF",  # Deep purple
    "habit": "#00BFA5",  # Teal
    
    # Status colors
    "completed": "#66BB6A",  # Green
    "skipped": "#BDBDBD",  # Gray
}

# Timeline constants
HOUR_HEIGHT = 150  # Increased height for more visible timeline rows (was 120)
TIMELINE_LEFT_MARGIN = 85  # Adjusted to match time column width
TIMELINE_WIDTH = 1500  # Increased to provide more horizontal space (was 1000)
TIMELINE_START_HOUR = 0
TIMELINE_END_HOUR = 23
ACTIVITY_STANDARD_WIDTH = 800  # Significantly widened for better visibility and more content

class ActivityTimelineItem(QGraphicsRectItem):
    """Graphical representation of an activity in the timeline."""
    
    def __init__(self, activity, x, y, width, height, parent=None):
        super().__init__(x, y, width, height, parent)
        self.activity = activity
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)  # Allow moving activities
        
        # Add shadow effect for depth
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(10)
        self.shadow_effect.setOffset(2, 2)
        self.shadow_effect.setColor(QColor(0, 0, 0, 50))  # Semi-transparent black
        self.setGraphicsEffect(self.shadow_effect)
        
        # Animation properties
        self.hover_animation = None
        self.original_rect = QRectF(x, y, width, height)
        self.hovered = False
        self.animation_running = False
        
        # Set appearance based on activity type and completion
        self.setupAppearance()
        
        # Track if this activity is locally hidden (skipped for today)
        self.is_locally_hidden = activity.get('locally_hidden', False)
    
    def setupAppearance(self):
        """Configure the visual appearance of the activity box."""
        activity_type = self.activity.get('type', 'task')
        is_completed = self.activity.get('completed', False)
        is_locally_hidden = self.activity.get('locally_hidden', False)
        
        # Get activity color (or use default based on type)
        if 'color' in self.activity and self.activity['color']:
            # Use exact color from activity without any modification
            base_color = QColor(self.activity['color'])
        else:
            # Use modern color palette based on activity type
            if activity_type == 'task':
                base_color = QColor(COLORS["task"])
            elif activity_type == 'event':
                base_color = QColor(COLORS["event"])
            elif activity_type == 'habit':
                base_color = QColor(COLORS["habit"])
            else:
                base_color = QColor(COLORS["info"])
        
        # Create gradient for more visual appeal
        self.gradient = QLinearGradient(0, 0, 0, self.rect().height())
        self.gradient.setColorAt(0, base_color.lighter(110))
        self.gradient.setColorAt(1, base_color)
        
        # Set brush and state based on activity status
        if is_completed:
            # Completed: use checkered pattern with success color blended
            completed_color = QColor(COLORS["completed"])
            blended_color = QColor(
                (base_color.red() + completed_color.red()) // 2,
                (base_color.green() + completed_color.green()) // 2,
                (base_color.blue() + completed_color.blue()) // 2,
            )
            self.gradient.setColorAt(0, blended_color.lighter(110))
            self.gradient.setColorAt(1, blended_color)
            brush = QBrush(self.gradient)
            
        elif is_locally_hidden:
            # Hidden: use pattern and reduced opacity
            skipped_color = QColor(COLORS["skipped"])
            self.gradient.setColorAt(0, skipped_color.lighter(110))
            self.gradient.setColorAt(1, skipped_color)
            brush = QBrush(self.gradient)
            # Make it semi-transparent
            brush.setColor(QColor(brush.color().red(), brush.color().green(), brush.color().blue(), 120))
        else:
            # Normal state: use gradient
            brush = QBrush(self.gradient)
        
        # Set brush and pen
        self.setBrush(brush)
        self.setPen(QPen(base_color.darker(120), 1))
        
        # Store color for text contrast calculations
        self.base_color = base_color
        
        # Set rounded corners
        self.setData(0, "activity")
        self.setData(1, self.activity['id'])
        self.setData(2, activity_type)
        self.setData(3, is_locally_hidden)  # Store locally_hidden state in item data
    
    def paint(self, painter, option, widget):
        """Paint the activity item with custom appearance."""
        # Setup painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get the rect for drawing
        rect = self.rect()
        
        # Create rounded rect path
        path = QPainterPath()
        path.addRoundedRect(rect, 8, 8)
        
        # Fill with gradient brush
        if self.isSelected():
            # Highlight selected items with a brighter gradient
            gradient = QLinearGradient(0, 0, 0, rect.height())
            gradient.setColorAt(0, self.base_color.lighter(140))
            gradient.setColorAt(1, self.base_color.lighter(120))
            painter.fillPath(path, QBrush(gradient))
        else:
            painter.fillPath(path, self.brush())
        
        # Draw border
        painter.setPen(QPen(self.base_color.darker(120), 1.5))
        painter.drawPath(path)
        
        # Draw status indicators and icons
        self.drawStatusIndicators(painter, rect)
        
        # Draw content
        self.drawContent(painter, rect)
    
    def drawStatusIndicators(self, painter, rect):
        """Draw status indicators and icons for the activity."""
        # Status icons at top-right corner
        icon_size = 16
        icon_margin = 5
        icon_x = rect.right() - icon_size - icon_margin
        icon_y = rect.top() + icon_margin
        
        # Draw completion indicator if applicable
        if self.activity.get('completed', False):
            # Draw completion checkmark in a circle
            check_rect = QRectF(icon_x, icon_y, icon_size, icon_size)
            
            # Draw circle background
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(COLORS["completed"])))
            painter.drawEllipse(check_rect)
            
            # Draw checkmark
            painter.setPen(QPen(QColor("white"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawLine(
                check_rect.left() + 4, check_rect.center().y(),
                check_rect.center().x(), check_rect.bottom() - 4
            )
            painter.drawLine(
                check_rect.center().x(), check_rect.bottom() - 4,
                check_rect.right() - 4, check_rect.top() + 4
            )
            
            # Adjust position for next icon
            icon_y += icon_size + icon_margin
        
        # Draw locally hidden indicator if applicable
        if self.activity.get('locally_hidden', False):
            # Draw eye-slash icon in a circle
            eye_rect = QRectF(icon_x, icon_y, icon_size, icon_size)
            
            # Draw circle background
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(COLORS["skipped"])))
            painter.drawEllipse(eye_rect)
            
            # Draw eye slash
            painter.setPen(QPen(QColor("white"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawLine(
                eye_rect.left() + 3, eye_rect.center().y(),
                eye_rect.right() - 3, eye_rect.center().y()
            )
            
            # Adjust position for next icon
            icon_y += icon_size + icon_margin
        
        # Draw priority indicator for tasks
        if self.activity.get('type') == 'task' and 'priority' in self.activity:
            priority = self.activity.get('priority', 1)
            priority_rect = QRectF(icon_x, icon_y, icon_size, icon_size)
            
            # Choose color based on priority
            if priority == 2:  # High
                priority_color = QColor(COLORS["error"])
            elif priority == 0:  # Low
                priority_color = QColor(COLORS["info"])
            else:  # Medium
                priority_color = QColor(COLORS["warning"])
            
            # Draw priority indicator
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(priority_color))
            
            # High: triangle, Medium: circle, Low: square
            if priority == 2:
                # Triangle for high priority
                points = [
                    QPointF(priority_rect.center().x(), priority_rect.top() + 2),
                    QPointF(priority_rect.right() - 2, priority_rect.bottom() - 2),
                    QPointF(priority_rect.left() + 2, priority_rect.bottom() - 2)
                ]
                painter.drawPolygon(QPolygonF(points))
            elif priority == 0:
                # Square for low priority
                painter.drawRect(QRectF(
                    priority_rect.left() + 3, 
                    priority_rect.top() + 3, 
                    priority_rect.width() - 6, 
                    priority_rect.height() - 6
                ))
            else:
                # Circle for medium priority
                painter.drawEllipse(priority_rect)
    
    def drawContent(self, painter, rect):
        """Draw the content of the activity item."""
        # Set text color based on background color brightness
        background_color = self.base_color
        brightness = (background_color.red() * 299 + background_color.green() * 587 + background_color.blue() * 114) / 1000
        if brightness > 128:
            text_color = QColor(COLORS["text_primary"])
        else:
            text_color = QColor("white")
        
        # Calculate text rectangles with proper margins
        margin = 10
        content_rect = rect.adjusted(margin, margin, -margin - 25, -margin)  # Extra space for icons
        
        # Draw activity type icon
        icon_size = 16
        activity_type = self.activity.get('type', 'task')
        type_icon_rect = QRectF(content_rect.left(), content_rect.top(), icon_size, icon_size)
        
        painter.setPen(QPen(text_color))
        painter.setBrush(QBrush(text_color))
        
        # Draw different icon based on activity type
        if activity_type == 'task':
            # Task icon (checkbox)
            painter.drawRect(QRectF(
                type_icon_rect.left() + 2, 
                type_icon_rect.top() + 2, 
                type_icon_rect.width() - 4, 
                type_icon_rect.height() - 4
            ))
        elif activity_type == 'event':
            # Event icon (calendar)
            painter.drawRect(QRectF(
                type_icon_rect.left() + 2, 
                type_icon_rect.top() + 2, 
                type_icon_rect.width() - 4, 
                type_icon_rect.height() / 3
            ))
            painter.drawRect(QRectF(
                type_icon_rect.left() + 2, 
                type_icon_rect.top() + 2 + type_icon_rect.height() / 3, 
                type_icon_rect.width() - 4, 
                type_icon_rect.height() * 2/3 - 4
            ))
        elif activity_type == 'habit':
            # Habit icon (repeat)
            painter.setPen(QPen(text_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(
                type_icon_rect.left() + 2, 
                type_icon_rect.top() + 2, 
                type_icon_rect.width() - 4, 
                type_icon_rect.height() - 4
            ))
            painter.drawLine(
                QPointF(type_icon_rect.center().x(), type_icon_rect.top() + 4),
                QPointF(type_icon_rect.center().x(), type_icon_rect.center().y())
            )
        
        # Draw title with text truncation if needed
        title_rect = QRectF(
            content_rect.left() + icon_size + 5, 
            content_rect.top(), 
            content_rect.width() - icon_size - 5, 
            min(content_rect.height() / 2, 20)
        )
        
        # Set bold font for title
        title_font = QFont()
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QPen(text_color))
        
        # Get the title and truncate if necessary
        title = self.activity.get('title', 'Untitled')
        font_metrics = QFontMetrics(title_font)
        title_width = font_metrics.horizontalAdvance(title)
        
        if title_width > title_rect.width():
            title = font_metrics.elidedText(title, Qt.TextElideMode.ElideRight, int(title_rect.width()))
        
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, title)
        
        # Draw time info with a clock icon
        time_font = QFont()
        time_font.setPointSize(8)
        painter.setFont(time_font)
        
        # Use formatted time strings if available
        start_time = self.activity.get('formatted_start_time', '')
        if not start_time and isinstance(self.activity.get('start_time'), QTime):
            start_time = self.activity.get('start_time').toString("h:mm AP")
        
        end_time = self.activity.get('formatted_end_time', '')  
        if not end_time and isinstance(self.activity.get('end_time'), QTime):
            end_time = self.activity.get('end_time').toString("h:mm AP")
            
        time_text = f"{start_time} - {end_time}" if start_time and end_time else start_time or end_time or ""
        
        # Draw clock icon
        clock_size = 12
        clock_rect = QRectF(content_rect.left(), title_rect.bottom() + 5, clock_size, clock_size)
        
        painter.setPen(QPen(text_color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(clock_rect)
        
        # Draw clock hands
        painter.drawLine(
            QPointF(clock_rect.center().x(), clock_rect.center().y()),
            QPointF(
                clock_rect.center().x() + clock_rect.width() * 0.3 * math.cos(math.pi / 4),
                clock_rect.center().y() - clock_rect.height() * 0.3 * math.sin(math.pi / 4)
            )
        )
        painter.drawLine(
            QPointF(clock_rect.center().x(), clock_rect.center().y()),
            QPointF(clock_rect.center().x(), clock_rect.center().y() - clock_rect.height() * 0.3)
        )
        
        # Draw time text
        time_rect = QRectF(
            content_rect.left() + clock_size + 5, 
            title_rect.bottom() + 5, 
            content_rect.width() - clock_size - 5, 
            15
        )
        
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
            
            desc_rect = QRectF(
                content_rect.left(), 
                time_rect.bottom() + 5, 
                content_rect.width(), 
                content_rect.bottom() - time_rect.bottom() - 5
            )
            
            # Create a bounded text document to properly wrap and truncate text
            font_metrics = QFontMetrics(desc_font)
            available_lines = max(1, int((desc_rect.height() - 5) / font_metrics.height()))
            
            # Skip rendering if description is a QTime object 
            if "QTime" in description:
                description = ""
                
            # Split description into words and render with ellipsis if needed
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
            painter.setPen(QPen(text_color.darker(120)))
            for i, line in enumerate(lines):
                if i >= available_lines:
                    break
                line_y = desc_rect.top() + i * font_metrics.height()
                line_rect = QRectF(desc_rect.left(), line_y, desc_rect.width(), font_metrics.height())
                painter.drawText(line_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, line)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        self.hovered = True
        
        # Highlight the item
        self.shadow_effect.setBlurRadius(15)
        self.shadow_effect.setOffset(3, 3)
        self.shadow_effect.setColor(QColor(0, 0, 0, 80))
        
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        self.hovered = False
        
        # Reset the highlight
        self.shadow_effect.setBlurRadius(10)
        self.shadow_effect.setOffset(2, 2)
        self.shadow_effect.setColor(QColor(0, 0, 0, 50))
        
        super().hoverLeaveEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click event to show activity details."""
        parent_view = self.scene().views()[0]
        
        if hasattr(parent_view, 'parent') and parent_view.parent and hasattr(parent_view.parent, 'onActivityClicked'):
            parent_view.parent.onActivityClicked(self.activity)
        
        super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event):
        """Handle context menu event directly for each activity."""
        menu = QMenu()
        
        # Add menu actions
        edit_action = menu.addAction("Edit Activity")
        
        # Toggle completion action
        if self.activity.get('completed', False):
            complete_action = menu.addAction("Mark as Incomplete")
        else:
            complete_action = menu.addAction("Mark as Complete")
        
        # Toggle local visibility action (for today only)
        if self.activity.get('locally_hidden', False):
            hide_action = menu.addAction("Show Today")
        else:
            hide_action = menu.addAction("Skip Today")
        
        menu.addSeparator()
        duplicate_action = menu.addAction("Duplicate")
        
        menu.addSeparator()
        delete_action = menu.addAction("Delete Activity")
        
        # Show the menu
        action = menu.exec(event.screenPos())
        
        # Find the DailyView parent to call appropriate methods
        daily_view = None
        parent_view = self.scene().views()[0]
        parent = parent_view.parent()
        
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
        
        if daily_view:
            if action == edit_action:
                daily_view.editActivity(self.activity)
            elif action == complete_action:
                daily_view.toggleActivityStatus(self.activity)
            elif action == hide_action:
                daily_view.toggleActivityLocalVisibility(self.activity)
            elif action == duplicate_action:
                daily_view.duplicateActivity(self.activity)
            elif action == delete_action:
                daily_view.deleteActivity(self.activity)
        
        super().contextMenuEvent(event)

class TimelineView(QGraphicsView):
    """Custom view for displaying a timeline of activities."""
    
    activityClicked = pyqtSignal(dict)  # Signal emitted when activity is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setViewportMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Set a large minimum size to ensure the timeline gets adequate space
        self.setMinimumSize(1200, 800)
        
        # Enable smooth scrolling
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create scene with appropriate size for full 24 hours
        self.scene = QGraphicsScene(self)
        total_height = HOUR_HEIGHT * (TIMELINE_END_HOUR - TIMELINE_START_HOUR + 1)
        self.scene.setSceneRect(0, 0, TIMELINE_WIDTH, total_height)
        self.setScene(self.scene)
        
        # Background style
        self.setBackgroundBrush(QBrush(QColor(COLORS["background"])))
        
        # Configure for smooth drag navigation
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setMouseTracking(True)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemShape)
        
        # Enable context menu policy
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showTimelineContextMenu)
        
        # Zoom control
        self.zoom_factor = 1.0
        self.max_zoom = 2.0
        self.min_zoom = 0.5
        
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
        
        # Create zoom controls as floating buttons
        self.setupZoomControls()
        
        # Initialize the current time indicator
        self.addCurrentTimeIndicator()
    
    def setupZoomControls(self):
        """Add zoom control buttons to the view."""
        # Create zoom buttons as children of the viewport
        zoom_in_btn = QToolButton(self)
        zoom_in_btn.setIcon(QIcon.fromTheme("zoom-in", get_icon("zoom-in")))
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.setStyleSheet("""
            QToolButton {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 15px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #F5F5F5;
            }
        """)
        zoom_in_btn.clicked.connect(self.zoomIn)
        self.zoom_in_btn = zoom_in_btn
        
        zoom_out_btn = QToolButton(self)
        zoom_out_btn.setIcon(QIcon.fromTheme("zoom-out", get_icon("zoom-out")))
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.setStyleSheet("""
            QToolButton {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 15px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #F5F5F5;
            }
        """)
        zoom_out_btn.clicked.connect(self.zoomOut)
        self.zoom_out_btn = zoom_out_btn
        
        # Position the buttons
        self.positionZoomControls()
    
    def positionZoomControls(self):
        """Position the zoom controls in the bottom-right corner."""
        btn_size = 30
        margin = 10
        
        # Position zoom buttons at the bottom-right corner
        rect = self.viewport().rect()
        self.zoom_in_btn.setFixedSize(btn_size, btn_size)
        self.zoom_out_btn.setFixedSize(btn_size, btn_size)
        
        self.zoom_in_btn.move(rect.right() - btn_size - margin, 
                             rect.bottom() - 2 * btn_size - 2 * margin)
        self.zoom_out_btn.move(rect.right() - btn_size - margin, 
                              rect.bottom() - btn_size - margin)
    
    def resizeEvent(self, event):
        """Handle resize event to reposition controls."""
        super().resizeEvent(event)
        self.positionZoomControls()
    
    def zoomIn(self):
        """Zoom in the timeline view."""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor *= 1.2
            self.updateZoom()
    
    def zoomOut(self):
        """Zoom out the timeline view."""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor /= 1.2
            self.updateZoom()
    
    def updateZoom(self):
        """Apply zoom factor to the view."""
        # Center point to maintain in view
        center_point = self.mapToScene(self.viewport().rect().center())
        
        # Apply zoom transformation
        transform = QTransform()
        transform.scale(1.0, self.zoom_factor)
        self.setTransform(transform)
        
        # Maintain the center point
        self.centerOn(center_point)
        
        # Update the hour guides to adjust for new scale
        self.setupHourGuides()
    
    def scrollToMorningHours(self):
        """Scroll to show the morning hours (8 AM) after initialization."""
        # Calculate the position for 8 AM
        morning_pos = self.morning_hour * HOUR_HEIGHT
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
        
        # Get the time column width
        time_column_width = 85  # Match with refreshActivityPositions
        
        # Add current time dot at the edge of the time column
        self.time_dot = QGraphicsEllipseItem(time_column_width - 8, y_position - 8, 16, 16)
        self.time_dot.setBrush(QBrush(QColor("#EA4335")))  # Bright red for visibility
        self.time_dot.setPen(QPen(QColor("white"), 2))
        
        # Add a glow effect to the dot
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(234, 67, 53, 150))  # Red glow
        glow.setOffset(0, 0)
        glow.setBlurRadius(15)
        self.time_dot.setGraphicsEffect(glow)
        
        self.scene.addItem(self.time_dot)
        
        # Add a horizontal current time line
        self.time_line = QGraphicsLineItem(time_column_width, y_position, TIMELINE_WIDTH, y_position)
        self.time_line.setPen(QPen(QColor("#EA4335"), 2, Qt.PenStyle.DashLine))  # Thicker, red line
        self.scene.addItem(self.time_line)
        
        # Add current time text
        time_string = current_time.toString("h:mm AP")
        self.time_text = QGraphicsTextItem(time_string)
        self.time_text.setDefaultTextColor(QColor("#EA4335"))
        
        # Make the time text stand out
        time_font = QFont("Arial", 10)
        time_font.setBold(True)
        self.time_text.setFont(time_font)
        
        # Add a semi-transparent white background to the text for better visibility
        rect = self.time_text.boundingRect()
        bg_rect = QGraphicsRectItem(rect.adjusted(-4, -2, 4, 2))
        bg_rect.setBrush(QBrush(QColor(255, 255, 255, 230)))
        bg_rect.setPen(QPen(Qt.PenStyle.NoPen))
        bg_rect.setParentItem(self.time_text)
        
        # Position the text in the time column
        self.time_text.setPos(10, y_position - 12)
        self.scene.addItem(self.time_text)
        
        # Add "NOW" label on the right side
        now_label = QGraphicsTextItem("NOW")
        now_label.setDefaultTextColor(QColor("#EA4335"))
        
        # Style the NOW label
        now_font = QFont("Arial", 8)
        now_font.setBold(True)
        now_label.setFont(now_font)
        
        # Add a semi-transparent white background
        now_rect = now_label.boundingRect()
        now_bg_rect = QGraphicsRectItem(now_rect.adjusted(-4, -2, 4, 2))
        now_bg_rect.setBrush(QBrush(QColor(255, 255, 255, 230)))
        now_bg_rect.setPen(QPen(Qt.PenStyle.NoPen))
        now_bg_rect.setParentItem(now_label)
        
        # Position at the right end of the timeline
        now_label.setPos(
            TIMELINE_WIDTH - now_rect.width() - 10,
            y_position - now_rect.height()/2
        )
        self.scene.addItem(now_label)
        
        # Ensure the current time indicator is visible
        self.ensureVisible(self.time_dot, 50, 100)
    
    def refreshActivityPositions(self):
        """Refresh the positioning of activities to ensure they all have the same width."""
        # Set up standard width for all activities
        fixed_width = ACTIVITY_STANDARD_WIDTH
        
        # Get the time column width
        time_column_width = 85  # Match with refreshActivityPositions
        
        # Position all items in a single column with standard width
        for item_id, item in self.activity_items.items():
            if item not in self.scene.items():
                continue
                
            item_rect = item.rect()
            
            # Set X position to just after the time column with more margin
            x_pos = time_column_width + 20
            
            # Update item position and width - make it wider for better readability
            item.setRect(x_pos, item_rect.y(), fixed_width, item_rect.height())

    def closeEvent(self, event):
        """Handle close event to stop timer."""
        self.time_timer.stop()
        self.activity_refresh_timer.stop()
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
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
        
        # Hour band width
        time_column_width = 85
        
        # Add a background band for the time column
        time_band = QGraphicsRectItem(0, 0, time_column_width, (TIMELINE_END_HOUR - TIMELINE_START_HOUR + 1) * HOUR_HEIGHT)
        time_band.setBrush(QBrush(QColor("#F1F5F9")))  # Light blue-gray background
        time_band.setPen(QPen(Qt.PenStyle.NoPen))
        self.scene.addItem(time_band)
        self.hour_lines.append(time_band)
        
        # Add new hour lines and labels
        for hour in range(TIMELINE_START_HOUR, TIMELINE_END_HOUR + 1):
            # Calculate y position
            y_pos = hour * HOUR_HEIGHT
            
            # Create hour band highlight for alternating hours
            if hour % 2 == 0:
                hour_band = QGraphicsRectItem(0, y_pos, TIMELINE_WIDTH, HOUR_HEIGHT)
                hour_band.setBrush(QBrush(QColor(245, 247, 250, 70)))  # Very light background
                hour_band.setPen(QPen(Qt.PenStyle.NoPen))
                self.scene.addItem(hour_band)
                self.hour_lines.append(hour_band)
            
            # Create hour line
            hour_line = QGraphicsLineItem(0, y_pos, TIMELINE_WIDTH, y_pos)
            hour_line.setPen(QPen(QColor("#CBD5E1"), 1))  # Medium gray line
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
            
            # Make the font larger and bolder
            font = QFont("Arial", 10)
            font.setBold(True)
            hour_label.setFont(font)
            
            # Set text color to a dark blue-gray
            hour_label.setDefaultTextColor(QColor("#334155"))
            
            # Position the hour label
            hour_label.setPos(10, y_pos - 15)
            
            # Add a time circle marker
            time_marker = QGraphicsEllipseItem(time_column_width - 15, y_pos - 4, 8, 8)
            time_marker.setBrush(QBrush(QColor("#6366F1")))  # Indigo color
            time_marker.setPen(QPen(QColor("#4F46E5"), 1))
            self.scene.addItem(time_marker)
            self.hour_labels.append(time_marker)
            
            self.scene.addItem(hour_label)
            self.hour_labels.append(hour_label)
            
            # Add minor interval lines (every 15 minutes) with shorter labels
            for minute in [15, 30, 45]:
                minor_y = y_pos + (minute / 60) * HOUR_HEIGHT
                
                # Minor gridlines
                minor_line = QGraphicsLineItem(time_column_width, minor_y, TIMELINE_WIDTH, minor_y)
                minor_line.setPen(QPen(QColor("#E2E8F0"), 0.75, Qt.PenStyle.DashLine))  # Lighter dashed line
                self.scene.addItem(minor_line)
                self.hour_lines.append(minor_line)
                
                # Add minute markers (smaller than hour markers)
                if minute == 30:  # Make 30-minute marker more visible
                    minute_marker = QGraphicsEllipseItem(time_column_width - 12, minor_y - 3, 6, 6)
                    minute_marker.setBrush(QBrush(QColor("#94A3B8")))  # Gray color for 30-min marker
                    minute_marker.setPen(QPen(QColor("#64748B"), 1))
                    self.scene.addItem(minute_marker)
                    self.hour_labels.append(minute_marker)
                
                    # Add minute label for half-hour marks
                    minute_label = QGraphicsTextItem(f":{minute}")
                    minute_label.setDefaultTextColor(QColor("#64748B"))
                    minute_label.setFont(QFont("Arial", 8))
                    minute_label.setPos(25, minor_y - 10)
                    self.scene.addItem(minute_label)
                    self.hour_labels.append(minute_label)
                else:
                    # Just add small tick marks for 15 and 45 minutes
                    tick_width = 5
                    tick_mark = QGraphicsLineItem(time_column_width - tick_width, minor_y, time_column_width, minor_y)
                    tick_mark.setPen(QPen(QColor("#94A3B8"), 1.5))
                    self.scene.addItem(tick_mark)
                    self.hour_labels.append(tick_mark)
    
    def addActivity(self, activity):
        """Add an activity to the timeline."""
        # Skip adding locally hidden activities if viewing current date
        daily_view = None
        parent = self.parent()
        while parent:
            if isinstance(parent, DailyView):
                daily_view = parent
                break
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                break
        
        # Check if we should skip rendering this activity (if it's hidden for today's view)
        if daily_view and hasattr(daily_view, 'current_date'):
            if activity.get('locally_hidden', False) and daily_view.current_date == QDate.currentDate():
                # Still add to the dictionary but with reduced opacity
                pass
        
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
        
        # Use the time column width for positioning
        time_column_width = 85  # Match with refreshActivityPositions
        
        # Find a suitable x position
        x_pos = time_column_width + 10
        width = ACTIVITY_STANDARD_WIDTH  # Use the standard width
        
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
        """Show context menu for the timeline."""
        scene_pos = self.mapToScene(pos)
        
        # Check if we clicked on an activity
        item = self.scene.itemAt(scene_pos, self.transform())
        
        if item and item.data(0) == "activity":
            # Context menu for an activity
            activity_id = item.data(1)
            activity_type = item.data(2)
            locally_hidden = item.data(3)
            
            # Get the actual activity data
            activity = None
            for act_id, act_item in self.activity_items.items():
                if act_id == activity_id:
                    activity = act_item.activity
                    break
            
            if activity:
                menu = QMenu()
                edit_action = menu.addAction("Edit Activity")
                
                # Toggle completion action
                if activity.get('completed', False):
                    complete_action = menu.addAction("Mark as Incomplete")
                else:
                    complete_action = menu.addAction("Mark as Complete")
                
                # Toggle local visibility action (for today only)
                if activity.get('locally_hidden', False):
                    hide_action = menu.addAction("Show Today")
                else:
                    hide_action = menu.addAction("Skip Today")
                
                delete_action = menu.addAction("Delete Activity")
                
                # Show menu and handle action
                action = menu.exec(self.mapToGlobal(pos))
                
                # Find the DailyView parent to call appropriate methods
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
                
                if daily_view:
                    if action == edit_action:
                        daily_view.editActivity(activity)
                    elif action == complete_action:
                        daily_view.toggleActivityStatus(activity)
                    elif action == hide_action:
                        daily_view.toggleActivityLocalVisibility(activity)
                    elif action == delete_action:
                        daily_view.deleteActivity(activity)
        else:
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
        
            # Context menu for the timeline itself
        menu = QMenu()
        menu.addSection(f"At {time_str}")
        add_task_action = menu.addAction("Add Task Here")
        add_event_action = menu.addAction("Add Event Here")
        add_habit_action = menu.addAction("Add Habit Here")
        
            # Show menu and handle action
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
        """Set up the UI components with a modern, colorful design."""
        # Apply a clean base stylesheet
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                background-color: #FAFAFA;
            }
            QLabel {
                color: #212121;
            }
            QPushButton {
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
            }
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #6200EA;
            }
            QScrollBar:vertical {
                background: #F5F5F5;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #BDBDBD;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9E9E9E;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Top Panel: Header with date navigation and tools
        top_panel = QFrame()
        top_panel.setObjectName("topPanel")
        top_panel.setStyleSheet("""
            #topPanel {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)
        top_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
        top_layout = QVBoxLayout(top_panel)
        top_layout.setSpacing(8)
        
        # Date Navigation Row
        date_nav_layout = QHBoxLayout()
        date_nav_layout.setContentsMargins(5, 5, 5, 5)
        
        # Previous day button with custom styling
        prev_btn = QPushButton()
        prev_btn.setIcon(get_icon("arrow-left"))
        prev_btn.setFixedSize(40, 40)
        prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                border-radius: 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
        """)
        prev_btn.clicked.connect(self.previousDay)
        prev_btn.setToolTip("Previous Day")
        date_nav_layout.addWidget(prev_btn)
        
        # Center date display with calendar button
        date_container = QFrame()
        date_container.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-radius: 8px;
            }
        """)
        date_container_layout = QHBoxLayout(date_container)
        date_container_layout.setContentsMargins(10, 5, 10, 5)
        
        # Calendar icon
        calendar_btn = QToolButton()
        calendar_btn.setIcon(get_icon("calendar"))
        calendar_btn.setIconSize(QSize(24, 24))
        calendar_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
            }
            QToolButton:hover {
                background-color: #EEEEEE;
                border-radius: 4px;
            }
        """)
        calendar_btn.clicked.connect(self.showDatePicker)
        calendar_btn.setToolTip("Open Calendar")
        date_container_layout.addWidget(calendar_btn)
        
        # Date display
        self.date_label = QLabel(self.current_date.toString('dddd, MMMM d, yyyy'))
        self.date_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 500;
            color: #212121;
            padding: 0 10px;
        """)
        date_container_layout.addWidget(self.date_label)
        
        # Today button
        today_btn = QPushButton("Today")
        today_btn.setStyleSheet("""
            QPushButton {
                background-color: #6200EA;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5600E8;
            }
        """)
        today_btn.clicked.connect(self.goToToday)
        today_btn.setToolTip("Jump to Today")
        date_container_layout.addWidget(today_btn)
        
        date_nav_layout.addWidget(date_container, 1)  # Stretch in middle
        
        # Next day button
        next_btn = QPushButton()
        next_btn.setIcon(get_icon("arrow-right"))
        next_btn.setFixedSize(40, 40)
        next_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                border-radius: 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
        """)
        next_btn.clicked.connect(self.nextDay)
        next_btn.setToolTip("Next Day")
        date_nav_layout.addWidget(next_btn)
        
        top_layout.addLayout(date_nav_layout)
        
        # Action Buttons Row
        actions_layout = QHBoxLayout()
        
        # Plan Day Button
        plan_day_btn = QPushButton("Plan My Day")
        plan_day_btn.setIcon(get_icon("calendar"))
        plan_day_btn.setStyleSheet("""
            QPushButton {
                background-color: #6200EA;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5600E8;
            }
        """)
        plan_day_btn.clicked.connect(self.showPlanDayWizard)
        plan_day_btn.setToolTip("Open the Day Planning Wizard")
        actions_layout.addWidget(plan_day_btn)
        
        # Add Task Button
        add_task_btn = QPushButton("Task")
        add_task_btn.setIcon(get_icon("add"))
        add_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF7043;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F4511E;
            }
        """)
        add_task_btn.clicked.connect(lambda: self.addActivity('task'))
        add_task_btn.setToolTip("Add a new task")
        actions_layout.addWidget(add_task_btn)
        
        # Add Event Button
        add_event_btn = QPushButton("Event")
        add_event_btn.setIcon(get_icon("add"))
        add_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #7C4DFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #651FFF;
            }
        """)
        add_event_btn.clicked.connect(lambda: self.addActivity('event'))
        add_event_btn.setToolTip("Add a new event")
        actions_layout.addWidget(add_event_btn)
        
        # Add Habit Button
        add_habit_btn = QPushButton("Habit")
        add_habit_btn.setIcon(get_icon("add"))
        add_habit_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BFA5;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #00AFA5;
            }
        """)
        add_habit_btn.clicked.connect(lambda: self.addActivity('habit'))
        add_habit_btn.setToolTip("Add a new habit")
        actions_layout.addWidget(add_habit_btn)
        
        actions_layout.addStretch()
        
        # View Options - Compact/Full View Toggle
        view_toggle_group = QButtonGroup(self)
        
        view_container = QFrame()
        view_container.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-radius: 4px;
            }
        """)
        view_container_layout = QHBoxLayout(view_container)
        view_container_layout.setContentsMargins(2, 2, 2, 2)
        view_container_layout.setSpacing(0)
        
        compact_view_btn = QToolButton()
        compact_view_btn.setText("Compact")
        compact_view_btn.setCheckable(True)
        compact_view_btn.setChecked(False)
        compact_view_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        compact_view_btn.setIcon(get_icon("compact"))
        compact_view_btn.setStyleSheet("""
            QToolButton {
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: transparent;
            }
            QToolButton:checked {
                background-color: white;
                border: 1px solid #E0E0E0;
            }
        """)
        
        full_view_btn = QToolButton()
        full_view_btn.setText("Full")
        full_view_btn.setCheckable(True)
        full_view_btn.setChecked(True)
        full_view_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        full_view_btn.setIcon(get_icon("full"))
        full_view_btn.setStyleSheet("""
            QToolButton {
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: transparent;
            }
            QToolButton:checked {
                background-color: white;
                border: 1px solid #E0E0E0;
            }
        """)
        
        view_toggle_group.addButton(compact_view_btn)
        view_toggle_group.addButton(full_view_btn)
        
        view_container_layout.addWidget(compact_view_btn)
        view_container_layout.addWidget(full_view_btn)
        
        compact_view_btn.clicked.connect(lambda: self.setViewMode("compact"))
        full_view_btn.clicked.connect(lambda: self.setViewMode("full"))
        
        actions_layout.addWidget(view_container)
        
        top_layout.addLayout(actions_layout)
        
        # Progress Summary Row
        progress_layout = QHBoxLayout()
        
        # Create progress summary widgets with modern styling
        # Tasks progress
        tasks_frame = QFrame()
        tasks_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["task"]};
                color: white;
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        tasks_layout = QVBoxLayout(tasks_frame)
        tasks_layout.setContentsMargins(10, 8, 10, 8)
        tasks_layout.setSpacing(4)
        
        tasks_title = QLabel("Tasks")
        tasks_title.setStyleSheet("font-size: 12px; font-weight: 500; color: white;")
        tasks_layout.addWidget(tasks_title)
        
        self.tasks_summary = QLabel("0/0")
        self.tasks_summary.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        tasks_layout.addWidget(self.tasks_summary)
        
        self.tasks_progress = QProgressBar()
        self.tasks_progress.setRange(0, 100)
        self.tasks_progress.setValue(0)
        self.tasks_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 2px;
                background-color: rgba(255, 255, 255, 100);
                height: 6px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: white;
                border-radius: 2px;
            }}
        """)
        tasks_layout.addWidget(self.tasks_progress)
        
        progress_layout.addWidget(tasks_frame)
        
        # Events progress
        events_frame = QFrame()
        events_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["event"]};
                color: white;
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        events_layout = QVBoxLayout(events_frame)
        events_layout.setContentsMargins(10, 8, 10, 8)
        events_layout.setSpacing(4)
        
        events_title = QLabel("Events")
        events_title.setStyleSheet("font-size: 12px; font-weight: 500; color: white;")
        events_layout.addWidget(events_title)
        
        self.events_summary = QLabel("0/0")
        self.events_summary.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        events_layout.addWidget(self.events_summary)
        
        self.events_progress = QProgressBar()
        self.events_progress.setRange(0, 100)
        self.events_progress.setValue(0)
        self.events_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 2px;
                background-color: rgba(255, 255, 255, 100);
                height: 6px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: white;
                border-radius: 2px;
            }}
        """)
        events_layout.addWidget(self.events_progress)
        
        progress_layout.addWidget(events_frame)
        
        # Habits progress
        habits_frame = QFrame()
        habits_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["habit"]};
                color: white;
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        habits_layout = QVBoxLayout(habits_frame)
        habits_layout.setContentsMargins(10, 8, 10, 8)
        habits_layout.setSpacing(4)
        
        habits_title = QLabel("Habits")
        habits_title.setStyleSheet("font-size: 12px; font-weight: 500; color: white;")
        habits_layout.addWidget(habits_title)
        
        self.habits_summary = QLabel("0/0")
        self.habits_summary.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        habits_layout.addWidget(self.habits_summary)
        
        self.habits_progress = QProgressBar()
        self.habits_progress.setRange(0, 100)
        self.habits_progress.setValue(0)
        self.habits_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 2px;
                background-color: rgba(255, 255, 255, 100);
                height: 6px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: white;
                border-radius: 2px;
            }}
        """)
        habits_layout.addWidget(self.habits_progress)
        
        progress_layout.addWidget(habits_frame)
        
        # Day progress
        day_frame = QFrame()
        day_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["primary"]};
                color: white;
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        day_layout = QVBoxLayout(day_frame)
        day_layout.setContentsMargins(10, 8, 10, 8)
        day_layout.setSpacing(4)
        
        day_title = QLabel("Day Progress")
        day_title.setStyleSheet("font-size: 12px; font-weight: 500; color: white;")
        day_layout.addWidget(day_title)
        
        self.day_time_label = QLabel(QTime.currentTime().toString("h:mm AP"))
        self.day_time_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        day_layout.addWidget(self.day_time_label)
        
        self.day_progress_bar = QProgressBar()
        self.day_progress_bar.setRange(0, 100)
        self.day_progress_bar.setValue(0)
        self.day_progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 2px;
                background-color: rgba(255, 255, 255, 100);
                height: 6px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: white;
                border-radius: 2px;
            }}
        """)
        day_layout.addWidget(self.day_progress_bar)
        
        progress_layout.addWidget(day_frame)
        
        top_layout.addLayout(progress_layout)
        
        main_layout.addWidget(top_panel)
        
        # Main Content: Timeline + Sidebar
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setObjectName("contentSplitter")
        content_splitter.setStyleSheet("""
            #contentSplitter {
                border: none;
            }
            QSplitter::handle {
                background-color: #E0E0E0;
                width: 1px;
            }
        """)
        
        # Timeline view on the left (main content)
        timeline_container = QFrame()
        timeline_container.setObjectName("timelineContainer")
        timeline_container.setStyleSheet("""
            #timelineContainer {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)
        
        timeline_layout = QVBoxLayout(timeline_container)
        timeline_layout.setContentsMargins(0, 0, 0, 0)
        timeline_layout.setSpacing(0)
        
        # Timeline header
        timeline_header = QWidget()
        timeline_header.setStyleSheet("""
            background-color: #F5F5F5;
            border-bottom: 1px solid #E0E0E0;
            padding: 8px;
        """)
        timeline_header_layout = QHBoxLayout(timeline_header)
        timeline_header_layout.setContentsMargins(10, 5, 10, 5)
        
        timeline_title = QLabel("Daily Timeline")
        timeline_title.setStyleSheet("""
            font-size: 16px;
                font-weight: bold;
            color: #333333;
        """)
        timeline_header_layout.addWidget(timeline_title)
        
        # Add zoom controls
        zoom_out_btn = QPushButton()
        zoom_out_btn.setIcon(get_icon("zoom-out"))
        zoom_out_btn.setFixedSize(32, 32)
        zoom_out_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F0F0;
                border-radius: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)
        zoom_out_btn.clicked.connect(lambda: self.timeline_view.zoomOut())
        zoom_out_btn.setToolTip("Zoom Out")
        
        zoom_in_btn = QPushButton()
        zoom_in_btn.setIcon(get_icon("zoom-in"))
        zoom_in_btn.setFixedSize(32, 32)
        zoom_in_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F0F0;
                border-radius: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)
        zoom_in_btn.clicked.connect(lambda: self.timeline_view.zoomIn())
        zoom_in_btn.setToolTip("Zoom In")
        
        timeline_header_layout.addStretch()
        timeline_header_layout.addWidget(zoom_out_btn)
        timeline_header_layout.addWidget(zoom_in_btn)
        
        timeline_layout.addWidget(timeline_header)
        
        # Add the timeline view
        self.timeline_view = TimelineView()
        self.timeline_view.activityClicked.connect(self.onActivityClicked)
        timeline_layout.addWidget(self.timeline_view)
        
        content_splitter.addWidget(timeline_container)
        
        # Right sidebar for notes and activities list
        sidebar_container = QFrame()
        sidebar_container.setObjectName("sidebarContainer")
        sidebar_container.setStyleSheet("""
            #sidebarContainer {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)
        sidebar_container.setMaximumWidth(250)  # Limit sidebar width
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Tabbed widget for sidebar content
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        tab_widget.setDocumentMode(True)
        tab_widget.setElideMode(Qt.TextElideMode.ElideRight)
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                background-color: #F5F5F5;
                border: none;
                border-bottom: 2px solid transparent;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #6200EA;
                color: #6200EA;
            }
        """)
        
        # Activities List Tab
        self.activities_list_widget = QWidget()
        self.setupActivitiesListTab()
        tab_widget.addTab(self.activities_list_widget, "Activities")
        
        # Notes Tab
        self.notes_widget = QWidget()
        self.setupNotesTab()
        tab_widget.addTab(self.notes_widget, "Notes")
        
        # Focus Mode Tab
        self.focus_widget = QWidget()
        self.setupFocusTab()
        tab_widget.addTab(self.focus_widget, "Focus")
        
        sidebar_layout.addWidget(tab_widget)
        content_splitter.addWidget(sidebar_container)
        
        # Set the initial sizes of the splitter - give more space to timeline
        content_splitter.setSizes([int(self.width() * 0.95), int(self.width() * 0.05)])
        
        main_layout.addWidget(content_splitter, 1)  # Give content area maximum stretch
        
        # Start timers for updates
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.updateDayProgress)
        self.progress_timer.start(60000)  # Update every minute
        
        # Set up adaptive layout
        self.view_mode = "full"
        
        # Load data for current date
        self.loadTimelineData()
        self.updateDayProgress()
    
    def setupFocusTab(self):
        """Set up the focus mode tab for deep work sessions."""
        layout = QVBoxLayout(self.focus_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Focus mode header
        focus_header = QLabel("Focus Mode")
        focus_header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #212121;
        """)
        layout.addWidget(focus_header)
        
        # Description
        focus_desc = QLabel("Use Focus Mode to eliminate distractions and track your deep work sessions.")
        focus_desc.setWordWrap(True)
        focus_desc.setStyleSheet("color: #757575;")
        layout.addWidget(focus_desc)
        
        # Session setup frame
        session_frame = QFrame()
        session_frame.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        quick_plan_layout = QVBoxLayout(session_frame)
        
        # Time selection
        focus_layout = QHBoxLayout()
        focus_layout.addWidget(QLabel("Duration:"))
        
        focus_duration = QComboBox()
        focus_duration.addItems(["25 min", "50 min", "90 min", "2 hours", "Custom"])
        focus_duration.setCurrentIndex(1)  # Default to 50 min
        quick_plan_layout.addLayout(focus_layout)
        
        # Task selection
        task_layout = QHBoxLayout()
        task_layout.addWidget(QLabel("Focus on:"))
        
        self.focus_task = QComboBox()
        self.focus_task.addItem("Select a task...")
        
        # Populate with current tasks
        if self.activities_manager:
            activities = self.activities_manager.get_activities_for_date(self.current_date)
            for activity in activities:
                if activity.get('type') == 'task' and not activity.get('completed', False):
                    self.focus_task.addItem(activity.get('title', 'Untitled Task'))
        
        task_layout.addWidget(self.focus_task, 1)
        quick_plan_layout.addLayout(task_layout)
        
        # Start button
        start_focus_btn = QPushButton("Start Focus Session")
        start_focus_btn.setStyleSheet("""
            QPushButton {
                background-color: #6200EA;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5600E8;
            }
        """)
        start_focus_btn.clicked.connect(self.startFocusSession)
        quick_plan_layout.addWidget(start_focus_btn)
        
        layout.addWidget(session_frame)
        
        # Focus history
        history_label = QLabel("Recent Focus Sessions")
        history_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #212121;
            margin-top: 10px;
        """)
        layout.addWidget(history_label)
        
        # Focus session history list
        self.focus_history = QListWidget()
        self.focus_history.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F5F5F5;
            }
            QListWidget::item:selected {
                background-color: #EDE7F6;
                color: #6200EA;
            }
        """)
        layout.addWidget(self.focus_history)
        
        # Add some placeholder history items
        today = QDate.currentDate()
        self.focus_history.addItem("Today - 50 min - Project planning")
        self.focus_history.addItem(f"Today - 25 min - Email processing")
        self.focus_history.addItem(f"Yesterday - 90 min - Report writing")
        
        layout.addStretch()
    
    def startFocusSession(self):
        """Start a focus session."""
        # In a real implementation, this would start a timer and track the focus session
        duration_text = self.focus_duration.currentText()
        task_text = self.focus_task.currentText()
        
        if task_text == "Select a task...":
            QMessageBox.warning(self, "Focus Mode", "Please select a task to focus on.")
            return
        
        # Extract minutes from duration text
        duration_mins = 50  # Default
        if "min" in duration_text:
            duration_mins = int(duration_text.split()[0])
        elif "hours" in duration_text or "hour" in duration_text:
            hours = float(duration_text.split()[0])
            duration_mins = int(hours * 60)
        
        # In a real implementation, we would start a timer here
        # For now, just show a message
        QMessageBox.information(
            self, 
            "Focus Session Started", 
            f"Starting a {duration_mins} minute focus session on:\n{task_text}"
        )
        
        # Add to history
        self.focus_history.insertItem(
            0, 
            f"Today - {duration_mins} min - {task_text}"
        )
    
    def setViewMode(self, mode):
        """Set the view mode between compact and full."""
        self.view_mode = mode
        
        # Global declaration at the beginning of the method
        global HOUR_HEIGHT
        
        # In a real implementation, this would adjust the layout
        # For now, just show a message
        if mode == "compact":
            # Reduce hour height for more compact view
            old_height = HOUR_HEIGHT
            HOUR_HEIGHT = 90  # Smaller height for compact view
            
            # Update the timeline
            if hasattr(self, 'timeline_view'):
                # Adjust zoom to compensate for height change
                self.timeline_view.zoom_factor *= old_height / HOUR_HEIGHT
                self.timeline_view.updateZoom()
                self.timeline_view.setupHourGuides()
                self.timeline_view.addCurrentTimeIndicator()
                self.timeline_view.refreshActivityPositions()
        else:
            # Restore original hour height
            old_height = HOUR_HEIGHT
            HOUR_HEIGHT = 120  # Default height
            
            # Update the timeline
            if hasattr(self, 'timeline_view'):
                # Adjust zoom to compensate for height change
                self.timeline_view.zoom_factor *= old_height / HOUR_HEIGHT
                self.timeline_view.updateZoom()
                self.timeline_view.setupHourGuides()
                self.timeline_view.addCurrentTimeIndicator()
                self.timeline_view.refreshActivityPositions()
    
    def showDatePicker(self):
        """Show a calendar dialog to pick a date."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Date")
        dialog.setFixedSize(300, 350)
        
        layout = QVBoxLayout(dialog)
        
        calendar = QCalendarWidget()
        calendar.setSelectedDate(self.current_date)
        calendar.setGridVisible(True)
        calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)
        
        # Highlight today
        calendar.setDateTextFormat(
            QDate.currentDate(),
            calendar.dateTextFormat(QDate.currentDate())
        )
        
        layout.addWidget(calendar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(dialog.accept)
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #6200EA;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5600E8;
            }
        """)
        button_layout.addWidget(select_btn)
        
        layout.addLayout(button_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.setDate(calendar.selectedDate())
    
    def setupNotesTab(self):
        """Set up the notes tab with a modern UI."""
        layout = QVBoxLayout(self.notes_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Notes header
        header_layout = QHBoxLayout()
        
        notes_header = QLabel("Daily Notes")
        notes_header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #212121;
        """)
        header_layout.addWidget(notes_header)
        
        # Date indicator
        self.notes_date_label = QLabel()
        self.updateNotesDateLabel()
        self.notes_date_label.setStyleSheet("""
            font-size: 14px;
            color: #757575;
        """)
        header_layout.addWidget(self.notes_date_label)
        
        header_layout.addStretch()
        
        # Text formatting toolbar
        formatting_layout = QHBoxLayout()
        
        bold_btn = QToolButton()
        bold_btn.setIcon(get_icon("bold"))
        bold_btn.setToolTip("Bold")
        bold_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 3px;
                margin: 2px;
            }
            QToolButton:hover {
                background-color: #F5F5F5;
                border-color: #BDBDBD;
            }
        """)
        formatting_layout.addWidget(bold_btn)
        
        italic_btn = QToolButton()
        italic_btn.setIcon(get_icon("italic"))
        italic_btn.setToolTip("Italic")
        italic_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 3px;
                margin: 2px;
            }
            QToolButton:hover {
                background-color: #F5F5F5;
                border-color: #BDBDBD;
            }
        """)
        formatting_layout.addWidget(italic_btn)
        
        bullet_btn = QToolButton()
        bullet_btn.setIcon(get_icon("bullet-list"))
        bullet_btn.setToolTip("Bullet List")
        bullet_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 3px;
                margin: 2px;
            }
            QToolButton:hover {
                background-color: #F5F5F5;
                border-color: #BDBDBD;
            }
        """)
        formatting_layout.addWidget(bullet_btn)
        
        header_layout.addLayout(formatting_layout)
        
        layout.addLayout(header_layout)
        
        # Notes editor
        self.notes_editor = QTextEdit()
        self.notes_editor.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        self.notes_editor.setPlaceholderText("Enter your notes for this day...")
        layout.addWidget(self.notes_editor, 1)  # Give stretch
        
        # Connect formatting buttons
        bold_btn.clicked.connect(self.toggleBold)
        italic_btn.clicked.connect(self.toggleItalic)
        bullet_btn.clicked.connect(self.insertBulletList)
        
        # Save button row
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        save_btn = QPushButton("Save Notes")
        save_btn.setIcon(get_icon("save"))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6200EA;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5600E8;
            }
        """)
        save_btn.clicked.connect(self.saveNotes)
        save_layout.addWidget(save_btn)
        
        layout.addLayout(save_layout)
        
        # Load notes for current date
        self.loadNotes()
    
    def updateNotesDateLabel(self):
        """Update the date label in the notes tab."""
        self.notes_date_label.setText(self.current_date.toString('dddd, MMMM d, yyyy'))
    
    def toggleBold(self):
        """Toggle bold formatting in the notes editor."""
        cursor = self.notes_editor.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontWeight(QFont.Weight.Bold if fmt.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal)
        cursor.mergeCharFormat(fmt)
        self.notes_editor.setTextCursor(cursor)
    
    def toggleItalic(self):
        """Toggle italic formatting in the notes editor."""
        cursor = self.notes_editor.textCursor()
        fmt = cursor.charFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        cursor.mergeCharFormat(fmt)
        self.notes_editor.setTextCursor(cursor)
    
    def insertBulletList(self):
        """Insert a bullet point in the notes editor."""
        cursor = self.notes_editor.textCursor()
        cursor.insertText("• ")
        self.notes_editor.setTextCursor(cursor)
    
    def setupActivitiesListTab(self):
        """Set up the activities list tab."""
        layout = QVBoxLayout(self.activities_list_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Filter and sort controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Filter buttons
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("font-weight: 500;")
        controls_layout.addWidget(filter_label)
        
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(5)
        
        # Create a button group for filter selection
        self.filter_group = QButtonGroup()
        self.filter_group.setExclusive(True)
        
        # All filter
        all_btn = QPushButton("All")
        all_btn.setCheckable(True)
        all_btn.setChecked(True)
        all_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #333333;
                border: none;
                border-radius: 15px;
                padding: 5px 15px;
                font-weight: 500;
            }
            QPushButton:checked {
                background-color: #E0E0E0;
                color: #212121;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
        """)
        all_btn.clicked.connect(lambda: self.filterActivities(None))
        self.filter_group.addButton(all_btn)
        filter_layout.addWidget(all_btn)
        
        # Tasks filter
        tasks_btn = QPushButton("Tasks")
        tasks_btn.setCheckable(True)
        tasks_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["task"]};
                color: white;
                border: none;
                border-radius: 15px;
                padding: 5px 15px;
                font-weight: 500;
            }}
            QPushButton:checked {{
                background-color: {QColor(COLORS["task"]).darker(120).name()};
            }}
            QPushButton:hover {{
                background-color: {QColor(COLORS["task"]).darker(110).name()};
            }}
        """)
        tasks_btn.clicked.connect(lambda: self.filterActivities('task'))
        self.filter_group.addButton(tasks_btn)
        filter_layout.addWidget(tasks_btn)
        
        # Events filter
        events_btn = QPushButton("Events")
        events_btn.setCheckable(True)
        events_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["event"]};
                color: white;
                border: none;
                border-radius: 15px;
                padding: 5px 15px;
                font-weight: 500;
            }}
            QPushButton:checked {{
                background-color: {QColor(COLORS["event"]).darker(120).name()};
            }}
            QPushButton:hover {{
                background-color: {QColor(COLORS["event"]).darker(110).name()};
            }}
        """)
        events_btn.clicked.connect(lambda: self.filterActivities('event'))
        self.filter_group.addButton(events_btn)
        filter_layout.addWidget(events_btn)
        
        # Habits filter
        habits_btn = QPushButton("Habits")
        habits_btn.setCheckable(True)
        habits_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["habit"]};
                color: white;
                border: none;
                border-radius: 15px;
                padding: 5px 15px;
                font-weight: 500;
            }}
            QPushButton:checked {{
                background-color: {QColor(COLORS["habit"]).darker(120).name()};
            }}
            QPushButton:hover {{
                background-color: {QColor(COLORS["habit"]).darker(110).name()};
            }}
        """)
        habits_btn.clicked.connect(lambda: self.filterActivities('habit'))
        self.filter_group.addButton(habits_btn)
        filter_layout.addWidget(habits_btn)
        
        controls_layout.addLayout(filter_layout)
        controls_layout.addStretch()
        
        # Sorting control
        sort_layout = QHBoxLayout()
        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet("font-weight: 500;")
        sort_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Time", "Priority", "Type"])
        self.sort_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 4px 10px;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        self.sort_combo.currentIndexChanged.connect(self.sortActivities)
        sort_layout.addWidget(self.sort_combo)
        
        controls_layout.addLayout(sort_layout)
        
        # View mode buttons (list vs card)
        view_label = QLabel("View:")
        view_label.setStyleSheet("font-weight: 500;")
        controls_layout.addWidget(view_label)
        
        view_layout = QHBoxLayout()
        view_layout.setSpacing(2)
        
        # List view button
        list_view_btn = QToolButton()
        list_view_btn.setIcon(get_icon("list"))
        list_view_btn.setCheckable(True)
        list_view_btn.setChecked(True)
        list_view_btn.setToolTip("List View")
        list_view_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QToolButton:checked {
                background-color: #E0E0E0;
            }
        """)
        list_view_btn.clicked.connect(lambda: self.setActivitiesViewMode("list"))
        view_layout.addWidget(list_view_btn)
        
        # Card view button
        card_view_btn = QToolButton()
        card_view_btn.setIcon(get_icon("card"))
        card_view_btn.setCheckable(True)
        card_view_btn.setToolTip("Card View")
        card_view_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QToolButton:checked {
                background-color: #E0E0E0;
            }
        """)
        card_view_btn.clicked.connect(lambda: self.setActivitiesViewMode("card"))
        view_layout.addWidget(card_view_btn)
        
        controls_layout.addLayout(view_layout)
        
        layout.addLayout(controls_layout)
        
        # Activities list
        self.activities_list = QListWidget()
        
        # Custom item delegate for proper text rendering
        class HTMLDelegate(QStyledItemDelegate):
            def paint(self, painter, option, index):
                options = QStyleOptionViewItem(option)
                self.initStyleOption(options, index)
                
                style = options.widget.style() if options.widget else QApplication.style()
                
                doc = QTextDocument()
                doc.setHtml(options.text)
                
                options.text = ""
                style.drawControl(QStyle.ControlElement.CE_ItemViewItem, options, painter)
                
                ctx = QAbstractTextDocumentLayout.PaintContext()
                ctx.palette = options.palette
                
                text_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, options)
                painter.save()
                painter.translate(text_rect.topLeft())
                
                # Adjust width for correct rendering
                doc.setTextWidth(text_rect.width())
                doc.documentLayout().draw(painter, ctx)
                
                painter.restore()
            
            def sizeHint(self, option, index):
                options = QStyleOptionViewItem(option)
                self.initStyleOption(options, index)
                
                doc = QTextDocument()
                doc.setHtml(options.text)
                doc.setTextWidth(options.rect.width())
                
                # Convert float values to integers for QSize
                width = int(doc.idealWidth())
                height = int(doc.size().height())
                return QSize(width, height)
        
        self.activities_list.setItemDelegate(HTMLDelegate())
        
        self.activities_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #F5F5F5;
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #F5F5F5;
                color: #212121;
            }
            QListWidget::item:hover {
                background-color: #FAFAFA;
            }
        """)
        self.activities_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.activities_list.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.activities_list.doubleClicked.connect(lambda idx: self.onActivityClicked(self.activities_list.itemFromIndex(idx).data(Qt.ItemDataRole.UserRole)))
        
        # Add context menu support
        self.activities_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.activities_list.customContextMenuRequested.connect(self.showActivityContextMenu)
        
        layout.addWidget(self.activities_list, 1)  # 1 for stretch factor
        
        # Add activity button
        add_activity_btn = QPushButton("Add Activity")
        add_activity_btn.setIcon(get_icon("plus"))
        add_activity_btn.setStyleSheet("""
            QPushButton {
                background-color: #6200EA;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5600E8;
            }
        """)
        add_activity_btn.clicked.connect(self.showAddActivityDialog)
        layout.addWidget(add_activity_btn)
        
        # Set initial view mode
        self.activities_view_mode = "list"
    
    def filterActivities(self, activity_type):
        """Filter activities in the list by type."""
        # Show/hide items based on filter
        for i in range(self.activities_list.count()):
            item = self.activities_list.item(i)
            activity = item.data(Qt.ItemDataRole.UserRole)
            
            # If filter is None, show all activities
            if activity_type is None:
                item.setHidden(False)
            else:
                # Hide items that don't match the filter
                item.setHidden(activity.get('type', 'task') != activity_type)
    
    def sortActivities(self, index):
        """Sort activities based on selected criteria."""
        sort_by = self.sort_combo.currentText().lower()
        
        # Get activities (filtered if needed)
        activities = self.activities_manager.get_activities_for_date(self.current_date)
        if self.activities_filter != "all":
            activities = [a for a in activities if a.get('type') == self.activities_filter]
        
        # Sort activities
        if sort_by == "time":
            activities = sorted(activities, key=lambda x: x['start_time'].toString("HH:mm"))
        elif sort_by == "priority":
            # Higher priority (2) comes first
            activities = sorted(activities, key=lambda x: -(x.get('priority', 1) if x.get('type') == 'task' else 0))
        elif sort_by == "name":
            activities = sorted(activities, key=lambda x: x.get('title', '').lower())
        elif sort_by == "status":
            # Completed items come last
            activities = sorted(activities, key=lambda x: (x.get('completed', False), x['start_time'].toString("HH:mm")))
        
        # Update activities list
        self.updateActivitiesList(activities)
    
    def setActivitiesViewMode(self, mode):
        """Switch between list and card view for activities."""
        self.activities_view_mode = mode
        
        # Re-render activities list with current filter and sort
        activities = self.activities_manager.get_activities_for_date(self.current_date)
        if self.activities_filter != "all":
            activities = [a for a in activities if a.get('type') == self.activities_filter]
        
        # Sort activities based on current sort option
        sort_by = self.sort_combo.currentText().lower()
        if sort_by == "time":
            activities = sorted(activities, key=lambda x: x['start_time'].toString("HH:mm"))
        elif sort_by == "priority":
            activities = sorted(activities, key=lambda x: -(x.get('priority', 1) if x.get('type') == 'task' else 0))
        elif sort_by == "name":
            activities = sorted(activities, key=lambda x: x.get('title', '').lower())
        elif sort_by == "status":
            activities = sorted(activities, key=lambda x: (x.get('completed', False), x['start_time'].toString("HH:mm")))
        
        # Update activities list
        self.updateActivitiesList(activities)
    
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
                    # Safely extract values with type checking to prevent errors
                    title = act.get('title', 'Untitled')
                    activity_type = act.get('type', 'task')
                    
                    # Format start time safely
                    start_time_str = "No start time"
                    if act.get('start_time'):
                        if isinstance(act['start_time'], QTime):
                            start_time_str = act['start_time'].toString('HH:mm')
                        else:
                            try:
                                # Try to convert string to QTime if needed
                                start_time_str = act['start_time']
                            except:
                                pass
                    
                    # Format end time safely
                    end_time_str = "No end time"
                    if act.get('end_time'):
                        if isinstance(act['end_time'], QTime):
                            end_time_str = act['end_time'].toString('HH:mm')
                        else:
                            try:
                                # Try to convert string to QTime if needed
                                end_time_str = act['end_time']
                            except:
                                pass
                    
                    print(f"  - {title} ({activity_type}): {start_time_str} to {end_time_str}")
                    
                    # Print description for debugging
                    if 'description' in act and act['description']:
                        desc = act['description']
                        if not isinstance(desc, str):
                            desc = str(desc)
                        print(f"    Description: {desc}")
            
            # Add activities to the timeline
            for activity in activities:
                try:
                    self.timeline_view.addActivity(activity)
                except Exception as e:
                    print(f"Error adding activity {activity.get('title', 'unknown')}: {e}")
            
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
        
        # In card view mode, we use custom widgets for each item
        if self.activities_view_mode == "card":
            for activity in activities:
                try:
                    # Create item and custom widget
                    item = QListWidgetItem()
                    card = self.createActivityCard(activity)
                    
                    # Calculate appropriate size based on content
                    item.setSizeHint(QSize(card.sizeHint().width(), 100))
                    
                    # Add to list and set widget
                    self.activities_list.addItem(item)
                    self.activities_list.setItemWidget(item, card)
                    
                    # Store activity data in the item
                    item.setData(Qt.ItemDataRole.UserRole, activity)
                except Exception as e:
                    print(f"Error adding activity card: {e}")
        else:
            # List view - use styled text items
            for activity in activities:
                
                    item = QListWidgetItem()
                    
                    # Format time range - safely handle different time formats
                    start_time = "N/A"
                    if 'start_time' in activity:
                        if isinstance(activity['start_time'], QTime):
                            start_time = activity['start_time'].toString("HH:mm")
                        else:
                            start_time = str(activity['start_time'])
                    
                    end_time = "N/A"
                    if 'end_time' in activity:
                        if isinstance(activity['end_time'], QTime):
                            end_time = activity['end_time'].toString("HH:mm")
                        else:
                            end_time = str(activity['end_time'])
                            
                    time_range = f"{start_time} - {end_time}"
                    
                    # Format title with activity type
                    title = activity.get('title', 'Untitled')
                    activity_type = activity.get('type', 'task')
                    
                    # Choose color based on activity type
                    if activity_type == 'task':
                        color = COLORS["task"]
                        type_icon = "⬜"  # Square for task
                    elif activity_type == 'event':
                        color = COLORS["event"]
                        type_icon = "📅"  # Calendar for event
                    else:  # habit
                        color = COLORS["habit"]
                        type_icon = "🔄"  # Repeat for habit
                    
                    # Set priority indicator for tasks
                    priority_indicator = ""
                    if activity_type == 'task' and 'priority' in activity:
                        priority = activity.get('priority', 1)
                        if priority == 2:  # High
                            priority_indicator = " ⚠️"  # Warning icon for high priority
                        elif priority == 0:  # Low
                            priority_indicator = " 🔽"  # Down arrow for low priority
            
            # Set item text with HTML formatting
                    if activity.get('completed', False):
                        # Strikethrough for completed items
                        item.setText(
                            f"<div style='display:flex; align-items:center;'>"
                            f"<span style='font-weight:bold; color:#9E9E9E; min-width:95px; text-decoration:line-through;'>{time_range}</span> "
                            f"<span style='text-decoration:line-through; color:#9E9E9E;'>{type_icon} {title}{priority_indicator}</span> "
                            f"<span style='color:#4CAF50; margin-left:auto; font-weight:bold;'>✓</span>"
                            f"</div>"
                        )
                    elif activity.get('locally_hidden', False):
                        # Italic and gray for skipped/hidden items
                        item.setText(
                            f"<div style='display:flex; align-items:center;'>"
                            f"<span style='font-weight:bold; color:#9E9E9E; min-width:95px;'>{time_range}</span> "
                            f"<span style='font-style:italic; color:#9E9E9E;'>{type_icon} {title}{priority_indicator}</span> "
                            f"<span style='color:#9E9E9E; margin-left:auto;'>skipped</span>"
                            f"</div>"
                        )
            else:
                        # Normal styling for active items
                        item.setText(
                            f"<div style='display:flex; align-items:center;'>"
                            f"<span style='font-weight:bold; color:#616161; min-width:95px;'>{time_range}</span> "
                            f"<span style='color:{color};'>{type_icon} {title}{priority_indicator}</span>"
                            f"</div>"
                        )
            
            # Store activity data in the item
            item.setData(Qt.ItemDataRole.UserRole, activity)
            
                    # Set background color based on status
            if activity.get('completed', False):
                item.setBackground(QBrush(QColor("#F5F5F5")))
            elif activity.get('locally_hidden', False):
                item.setBackground(QBrush(QColor("#FAFAFA")))
            
            # Add the item to the list
                self.activities_list.addItem(item)
            
    
    def createActivityCard(self, activity):
        """Create a card widget for the activity in card view mode."""
        # Create a frame container for the card
        card = QFrame()
        card.setObjectName("activityCard")
        
        # Determine background color based on activity type and status
        activity_type = activity.get('type', 'task')
        is_completed = activity.get('completed', False)
        is_hidden = activity.get('locally_hidden', False)
        
        if is_completed:
            bg_color = "#F5F5F5"
            border_color = "#E0E0E0"
        elif is_hidden:
            bg_color = "#FAFAFA"
            border_color = "#EEEEEE"
        else:
            # Use a lighter shade of the activity type color
            if activity_type == 'task':
                base_color = COLORS["task"]
            elif activity_type == 'event':
                base_color = COLORS["event"]
            else:  # habit
                base_color = COLORS["habit"]
                
            # Convert to QColor for manipulation
            base_qcolor = QColor(base_color)
            bg_color = base_qcolor.lighter(180).name()
            border_color = base_qcolor.name()
        
        # Style the card
        card.setStyleSheet(f"""
            #activityCard {{
                background-color: {bg_color};
                border-radius: 8px;
                border-left: 3px solid {border_color};
            }}
        """)
        
        # Layout for card content
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Top row: Title and checkbox/status
        top_row = QHBoxLayout()
        
        # Title with icon based on type
        title_text = activity.get('title', 'Untitled')
        
        # Choose icon and color based on activity type
        if activity_type == 'task':
            type_icon = "□"  # Square for task
            type_color = COLORS["task"]
        elif activity_type == 'event':
            type_icon = "📅"  # Calendar for event
            type_color = COLORS["event"]
        else:  # habit
            type_icon = "↻"  # Repeat for habit
            type_color = COLORS["habit"]
        
        title_label = QLabel(f"{type_icon} {title_text}")
        
        # Style title based on completion status
        if is_completed:
            title_label.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #9E9E9E;
                text-decoration: line-through;
            """)
        elif is_hidden:
            title_label.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #9E9E9E;
                font-style: italic;
            """)
        else:
            title_label.setStyleSheet(f"""
                font-size: 14px;
                font-weight: bold;
                color: {COLORS["text_primary"]};
            """)
        
        top_row.addWidget(title_label, 1)  # Give stretch to title
        
        # Status indicator
        if is_completed:
            status_label = QLabel("✓")
            status_label.setStyleSheet(f"""
                font-size: 16px;
                color: {COLORS["completed"]};
                font-weight: bold;
            """)
            top_row.addWidget(status_label)
        elif is_hidden:
            status_label = QLabel("skipped")
            status_label.setStyleSheet(f"""
                font-size: 12px;
                color: {COLORS["skipped"]};
            """)
            top_row.addWidget(status_label)
        
        layout.addLayout(top_row)
        
        # Middle row: Time info
        time_layout = QHBoxLayout()
        
        # Format time range
        start_time = activity['start_time'].toString("h:mm AP")
        end_time = activity['end_time'].toString("h:mm AP")
        time_range = f"{start_time} - {end_time}"
        
        time_label = QLabel(f"⏱️ {time_range}")
        time_label.setStyleSheet("""
            font-size: 12px;
            color: #757575;
        """)
        time_layout.addWidget(time_label)
        
        # For tasks, add priority indicator
        if activity_type == 'task' and 'priority' in activity:
            priority = activity.get('priority', 1)
            priority_text = ""
            priority_color = ""
            
            if priority == 2:  # High
                priority_text = "High Priority"
                priority_color = COLORS["error"]
            elif priority == 1:  # Medium
                priority_text = "Medium Priority"
                priority_color = COLORS["warning"]
            else:  # Low
                priority_text = "Low Priority"
                priority_color = COLORS["info"]
            
            priority_label = QLabel(priority_text)
            priority_label.setStyleSheet(f"""
                font-size: 11px;
                color: {priority_color};
                font-weight: 500;
                padding: 2px 6px;
                background-color: {QColor(priority_color).lighter(180).name()};
                border-radius: 4px;
            """)
            
            time_layout.addWidget(priority_label)
        
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
        # Bottom row: Description (truncated)
        if 'description' in activity and activity['description']:
            desc_text = activity['description']
            
            # Truncate description if too long
            if len(desc_text) > 50:
                desc_text = desc_text[:47] + "..."
            
            desc_label = QLabel(desc_text)
            desc_label.setStyleSheet("""
                font-size: 12px;
                color: #616161;
            """)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        return card
    
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
        
        # Add toggle visibility action
        visibility_action = menu.addAction(
            "Show Today" if activity.get('locally_hidden', False) else "Skip Today"
        )
        visibility_action.setIcon(get_icon("eye"))
        
        delete_action = menu.addAction("Delete Activity")
        delete_action.setIcon(get_icon("delete"))
        
        # Show menu and handle selection
        action = menu.exec(self.activities_list.mapToGlobal(position))
        
        if action == edit_action:
            self.editActivity(activity)
        elif action == toggle_action:
            self.toggleActivityStatus(activity)
        elif action == visibility_action:
            self.toggleActivityLocalVisibility(activity)
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
    
    def toggleActivityLocalVisibility(self, activity):
        """Toggle the local visibility of an activity (skip for today only)."""
        if not self.activities_manager:
            return
        
        try:
            # Toggle the locally hidden state
            new_hidden_state = not activity.get('locally_hidden', False)
            
            # We don't persist this to the database as it's only for the current view/day
            # Just update the activity in memory
            activity['locally_hidden'] = new_hidden_state
            
            # Update the UI
            for act_id, item in self.timeline_view.activity_items.items():
                if act_id == activity['id']:
                    item.activity['locally_hidden'] = new_hidden_state
                    item.setupAppearance()  # Update appearance
                    item.update()  # Force redraw
                    break
            
            # Also update the activities list
            self.updateActivitiesList(self.activities_manager.get_activities_for_date(self.current_date))
            
        except Exception as e:
            print(f"Error toggling activity visibility: {e}")
            QMessageBox.warning(self, "Error", f"Could not update activity visibility: {str(e)}")
    
    def updateDayProgress(self):
        """Update the day progress indicators."""
        if not self.activities_manager:
            return
            
        try:
            # Update current time
            current_time = QTime.currentTime()
            if hasattr(self, 'day_time_label'):
                self.day_time_label.setText(current_time.toString("h:mm AP"))
            
            # Update day progress bar based on current time
            day_percentage = int((current_time.hour() * 60 + current_time.minute()) / (24 * 60) * 100)
            self.day_progress_bar.setValue(day_percentage)
            
            # Get activities for the current date
            activities = self.activities_manager.get_activities_for_date(self.current_date)
            
            # Count tasks, events, and habits
            tasks = [a for a in activities if a.get('type') == 'task']
            events = [a for a in activities if a.get('type') == 'event']
            habits = [a for a in activities if a.get('type') == 'habit']
            
            completed_tasks = len([t for t in tasks if t.get('completed', False)])
            completed_events = len([e for e in events if e.get('completed', False)])
            completed_habits = len([h for h in habits if h.get('completed', False)])
            
            # Update summary labels
            self.tasks_summary.setText(f"{completed_tasks}/{len(tasks)}")
            self.events_summary.setText(f"{completed_events}/{len(events)}")
            self.habits_summary.setText(f"{completed_habits}/{len(habits)}")
            
            # Update progress bars
            if len(tasks) > 0:
                self.tasks_progress.setValue(int(completed_tasks / len(tasks) * 100))
            else:
                self.tasks_progress.setValue(0)
                
            if len(events) > 0:
                self.events_progress.setValue(int(completed_events / len(events) * 100))
            else:
                self.events_progress.setValue(0)
                
            if len(habits) > 0:
                self.habits_progress.setValue(int(completed_habits / len(habits) * 100))
            else:
                self.habits_progress.setValue(0)
                
        except Exception as e:
            print(f"Error updating day progress: {e}")
            import traceback
            traceback.print_exc()
    
    def showPlanDayWizard(self):
        """Show the day planning wizard dialog."""
        # Create a dialog for the planning wizard
        wizard = QDialog(self)
        wizard.setWindowTitle("Plan My Day")
        wizard.setMinimumWidth(600)
        wizard.setMinimumHeight(500)
        
        layout = QVBoxLayout(wizard)
        
        # Add tabs for different planning methods
        tabs = QTabWidget()
        
        # Quick Plan tab
        quick_plan_widget = QWidget()
        quick_plan_layout = QVBoxLayout(quick_plan_widget)
        
        quick_plan_layout.addWidget(QLabel("<h3>Quick Day Plan</h3>"))
        quick_plan_layout.addWidget(QLabel("Automatically schedule your day based on your priorities and available time."))
        
        # Time range selector
        time_range_layout = QHBoxLayout()
        time_range_layout.addWidget(QLabel("Available Time:"))
        
        start_time_edit = QTimeEdit()
        start_time_edit.setTime(QTime(8, 0))  # Default 8:00 AM
        time_range_layout.addWidget(start_time_edit)
        
        time_range_layout.addWidget(QLabel("to"))
        
        end_time_edit = QTimeEdit()
        end_time_edit.setTime(QTime(18, 0))  # Default 6:00 PM
        time_range_layout.addWidget(end_time_edit)
        
        quick_plan_layout.addLayout(time_range_layout)
        
        # Planning preferences
        quick_plan_layout.addWidget(QLabel("<h4>Planning Preferences:</h4>"))
        
        # Focus time
        focus_layout = QHBoxLayout()
        focus_layout.addWidget(QLabel("Focus Time Duration:"))
        focus_duration = QComboBox()
        focus_duration.addItems(["25 min", "50 min", "90 min", "2 hours", "Custom"])
        focus_duration.setCurrentIndex(1)  # Default to 50 min
        focus_layout.addWidget(focus_duration)
        
        quick_plan_layout.addLayout(focus_layout)
        
        # Break time
        break_layout = QHBoxLayout()
        break_layout.addWidget(QLabel("Break Duration:"))
        break_duration = QComboBox()
        break_duration.addItems(["5 min", "10 min", "15 min", "20 min", "Custom"])
        break_duration.setCurrentIndex(1)  # Default to 10 min
        break_layout.addWidget(break_duration)
        quick_plan_layout.addLayout(break_layout)
        
        # Add priority ordering
        quick_plan_layout.addWidget(QLabel("<h4>Task Priority:</h4>"))
        
        # List of pending tasks with drag-drop reordering
        task_list = QListWidget()
        task_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        
        # Populate with current tasks
        if self.activities_manager:
            activities = self.activities_manager.get_activities_for_date(self.current_date)
            for activity in activities:
                if activity.get('type') == 'task' and not activity.get('completed', False):
                    item = QListWidgetItem(activity.get('title', 'Untitled Task'))
                    item.setData(Qt.ItemDataRole.UserRole, activity)
                    task_list.addItem(item)
        
        quick_plan_layout.addWidget(task_list)
        
        # Generate Plan button
        generate_btn = QPushButton("Generate Day Plan")
        generate_btn.setStyleSheet("""
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
        generate_btn.clicked.connect(lambda: self.generateDayPlan(
            wizard, 
            start_time_edit.time(), 
            end_time_edit.time(), 
            focus_duration.value(), 
            break_duration.value(),
            task_list
        ))
        quick_plan_layout.addWidget(generate_btn)
        
        tabs.addTab(quick_plan_widget, "Quick Plan")
        
        # Templates tab
        templates_widget = QWidget()
        templates_layout = QVBoxLayout(templates_widget)
        
        templates_layout.addWidget(QLabel("<h3>Day Templates</h3>"))
        templates_layout.addWidget(QLabel("Apply a pre-defined template to quickly plan your day."))
        
        # Template selector
        template_combo = QComboBox()
        template_combo.addItems([
            "Productive Work Day", 
            "Meeting Heavy Day", 
            "Focus Day", 
            "Learning Day",
            "Self-Care Day"
        ])
        templates_layout.addWidget(template_combo)
        
        # Template description
        template_desc = QTextEdit()
        template_desc.setReadOnly(True)
        template_desc.setPlaceholderText("Select a template to see its description")
        template_desc.setMaximumHeight(100)
        templates_layout.addWidget(template_desc)
        
        # Update description when template changes
        def update_template_description():
            template = template_combo.currentText()
            descriptions = {
                "Productive Work Day": "A balanced day with focused work sessions, breaks, and planning time. Includes 4 focus blocks, with short breaks and a lunch break.",
                "Meeting Heavy Day": "Optimized for days with multiple meetings. Includes preparation time before meetings and processing time after.",
                "Focus Day": "Maximum focus time with minimal interruptions. Includes longer deep work sessions with breaks designed for optimal concentration.",
                "Learning Day": "Structured for learning new skills. Alternates study sessions with practice and reflection time.",
                "Self-Care Day": "Prioritizes well-being with balanced work, exercise, meditation, and recreation blocks."
            }
            template_desc.setText(descriptions.get(template, ""))
        
        template_combo.currentTextChanged.connect(update_template_description)
        update_template_description()  # Initialize with first description
        
        # Template customization
        templates_layout.addWidget(QLabel("<h4>Customize Template:</h4>"))
        
        # Start time
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start Time:"))
        template_start_time = QTimeEdit()
        template_start_time.setTime(QTime(8, 0))
        start_layout.addWidget(template_start_time)
        templates_layout.addLayout(start_layout)
        
        # Apply button
        apply_template_btn = QPushButton("Apply Template")
        apply_template_btn.setStyleSheet("""
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
        apply_template_btn.clicked.connect(lambda: self.applyDayTemplate(
            wizard,
            template_combo.currentText(),
            template_start_time.time()
        ))
        templates_layout.addWidget(apply_template_btn)
        
        templates_layout.addStretch()
        tabs.addTab(templates_widget, "Templates")
        
        layout.addWidget(tabs)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(wizard.reject)
        layout.addWidget(button_box)
        
        wizard.exec()

    def generateDayPlan(self, dialog, start_time, end_time, focus_duration, break_duration, task_list):
        """Generate a day plan based on the given parameters."""
        if not self.activities_manager:
            QMessageBox.warning(dialog, "Error", "Activities manager not available")
            return
            
        try:
            # Calculate available time in minutes
            start_minutes = start_time.hour() * 60 + start_time.minute()
            end_minutes = end_time.hour() * 60 + end_time.minute()
            
            if end_minutes <= start_minutes:
                QMessageBox.warning(dialog, "Error", "End time must be after start time")
                return
                
            total_minutes = end_minutes - start_minutes
            
            # Get prioritized tasks
            prioritized_tasks = []
            for i in range(task_list.count()):
                item = task_list.item(i)
                task = item.data(Qt.ItemDataRole.UserRole)
                if task:
                    prioritized_tasks.append(task)
            
            # If no tasks, show warning
            if not prioritized_tasks:
                QMessageBox.warning(dialog, "Error", "No tasks available to schedule")
                return
            
            # Plan the day
            current_time = start_time
            schedule = []
            
            # First, delete any existing planned activities
            existing_activities = self.activities_manager.get_activities_for_date(self.current_date)
            for activity in existing_activities:
                if activity.get('category') == 'Auto-Planned':
                    self.activities_manager.delete_activity(activity['id'])
            
            # Now create new activities based on the plan
            task_index = 0
            while current_time.hour() * 60 + current_time.minute() < end_minutes:
                # Schedule a focus block if we have time and tasks left
                if task_index < len(prioritized_tasks) and current_time.hour() * 60 + current_time.minute() + focus_duration <= end_minutes:
                    task = prioritized_tasks[task_index]
                    
                    # Create a focus block for this task
                    end_time = current_time.addSecs(focus_duration * 60)
                    
                    # Create activity
                    activity_data = {
                        'title': f"Focus: {task.get('title', 'Task')}",
                        'date': self.current_date,
                        'start_time': current_time,
                        'end_time': end_time,
                        'description': f"Auto-planned focus time for: {task.get('title', 'Task')}",
                        'category': 'Auto-Planned',
                        'type': 'task',
                        'completed': False,
                        'color': '#4F46E5'  # Indigo color for focus blocks
                    }
                    
                    # Add to database
                    self.activities_manager.add_activity(activity_data)
                    schedule.append(activity_data)
                    
                    # Move to next time slot
                    current_time = end_time
                    task_index += 1
                    
                    # Add a break after focus time (if there's time left)
                    if current_time.hour() * 60 + current_time.minute() + break_duration <= end_minutes:
                        break_end_time = current_time.addSecs(break_duration * 60)
                        
                        # Create break activity
                        break_data = {
                            'title': "Break",
                            'date': self.current_date,
                            'start_time': current_time,
                            'end_time': break_end_time,
                            'description': "Scheduled break time",
                            'category': 'Auto-Planned',
                            'type': 'event',
                            'completed': False,
                            'color': '#34D399'  # Green color for breaks
                        }
                        
                        # Add to database
                        self.activities_manager.add_activity(break_data)
                        schedule.append(break_data)
                        
                        # Move to next time slot
                        current_time = break_end_time
                else:
                    # We're out of tasks or time
                    break
            
            # Refresh the view
            self.refresh()
            
            # Show completion message
            QMessageBox.information(dialog, "Plan Generated", 
                                   f"Successfully planned your day with {len(schedule) // 2} focus sessions!")
            
            # Close the dialog
            dialog.accept()
            
        except Exception as e:
            print(f"Error generating day plan: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(dialog, "Error", f"Could not generate plan: {str(e)}")

    def applyDayTemplate(self, dialog, template_name, start_time):
        """Apply a day template starting at the given time."""
        if not self.activities_manager:
            QMessageBox.warning(dialog, "Error", "Activities manager not available")
            return
            
        try:
            # Define templates
            templates = {
                "Productive Work Day": [
                    {"title": "Day Planning", "duration": 15, "type": "task", "color": "#6366F1"},
                    {"title": "Email & Communications", "duration": 30, "type": "task", "color": "#F87171"},
                    {"title": "Focus Block 1", "duration": 90, "type": "task", "color": "#4F46E5"},
                    {"title": "Break", "duration": 15, "type": "event", "color": "#34D399"},
                    {"title": "Focus Block 2", "duration": 90, "type": "task", "color": "#4F46E5"},
                    {"title": "Lunch Break", "duration": 60, "type": "event", "color": "#FB923C"},
                    {"title": "Focus Block 3", "duration": 90, "type": "task", "color": "#4F46E5"},
                    {"title": "Break", "duration": 15, "type": "event", "color": "#34D399"},
                    {"title": "Focus Block 4", "duration": 90, "type": "task", "color": "#4F46E5"},
                    {"title": "Day Review", "duration": 15, "type": "task", "color": "#6366F1"}
                ],
                "Meeting Heavy Day": [
                    {"title": "Day Planning", "duration": 15, "type": "task", "color": "#6366F1"},
                    {"title": "Email & Communications", "duration": 30, "type": "task", "color": "#F87171"},
                    {"title": "Meeting Prep", "duration": 30, "type": "task", "color": "#818CF8"},
                    {"title": "Meeting 1", "duration": 60, "type": "event", "color": "#818CF8"},
                    {"title": "Meeting Notes Processing", "duration": 15, "type": "task", "color": "#818CF8"},
                    {"title": "Focus Time", "duration": 60, "type": "task", "color": "#4F46E5"},
                    {"title": "Lunch Break", "duration": 45, "type": "event", "color": "#FB923C"},
                    {"title": "Meeting Prep", "duration": 15, "type": "task", "color": "#818CF8"},
                    {"title": "Meeting 2", "duration": 60, "type": "event", "color": "#818CF8"},
                    {"title": "Break", "duration": 15, "type": "event", "color": "#34D399"},
                    {"title": "Meeting 3", "duration": 60, "type": "event", "color": "#818CF8"},
                    {"title": "Meeting Notes Processing", "duration": 30, "type": "task", "color": "#818CF8"},
                    {"title": "Day Review", "duration": 15, "type": "task", "color": "#6366F1"}
                ],
                "Focus Day": [
                    {"title": "Day Planning", "duration": 15, "type": "task", "color": "#6366F1"},
                    {"title": "Deep Work Block 1", "duration": 120, "type": "task", "color": "#4F46E5"},
                    {"title": "Break", "duration": 20, "type": "event", "color": "#34D399"},
                    {"title": "Deep Work Block 2", "duration": 120, "type": "task", "color": "#4F46E5"},
                    {"title": "Lunch & Walking Break", "duration": 60, "type": "event", "color": "#FB923C"},
                    {"title": "Deep Work Block 3", "duration": 120, "type": "task", "color": "#4F46E5"},
                    {"title": "Break", "duration": 20, "type": "event", "color": "#34D399"},
                    {"title": "Deep Work Block 4", "duration": 120, "type": "task", "color": "#4F46E5"},
                    {"title": "Day Review", "duration": 15, "type": "task", "color": "#6366F1"}
                ],
                "Learning Day": [
                    {"title": "Day Planning", "duration": 15, "type": "task", "color": "#6366F1"},
                    {"title": "Learning Session 1", "duration": 60, "type": "task", "color": "#38BDF8"},
                    {"title": "Practice/Application", "duration": 60, "type": "task", "color": "#6366F1"},
                    {"title": "Break", "duration": 15, "type": "event", "color": "#34D399"},
                    {"title": "Learning Session 2", "duration": 60, "type": "task", "color": "#38BDF8"},
                    {"title": "Lunch Break", "duration": 45, "type": "event", "color": "#FB923C"},
                    {"title": "Reflection & Notes", "duration": 30, "type": "task", "color": "#6366F1"},
                    {"title": "Learning Session 3", "duration": 60, "type": "task", "color": "#38BDF8"},
                    {"title": "Break", "duration": 15, "type": "event", "color": "#34D399"},
                    {"title": "Practice/Application", "duration": 90, "type": "task", "color": "#6366F1"},
                    {"title": "Day Review", "duration": 15, "type": "task", "color": "#6366F1"}
                ],
                "Self-Care Day": [
                    {"title": "Morning Meditation", "duration": 20, "type": "habit", "color": "#34D399"},
                    {"title": "Journaling", "duration": 15, "type": "habit", "color": "#38BDF8"},
                    {"title": "Exercise", "duration": 45, "type": "habit", "color": "#F87171"},
                    {"title": "Breakfast", "duration": 30, "type": "event", "color": "#FB923C"},
                    {"title": "Light Work Session", "duration": 90, "type": "task", "color": "#6366F1"},
                    {"title": "Nature Walk", "duration": 45, "type": "habit", "color": "#34D399"},
                    {"title": "Lunch", "duration": 45, "type": "event", "color": "#FB923C"},
                    {"title": "Hobby Time", "duration": 90, "type": "event", "color": "#34D399"},
                    {"title": "Rest/Nap", "duration": 30, "type": "habit", "color": "#94A3B8"},
                    {"title": "Light Work Session", "duration": 60, "type": "task", "color": "#6366F1"},
                    {"title": "Evening Reflection", "duration": 20, "type": "habit", "color": "#38BDF8"}
                ]
            }
            
            # Get the selected template
            template = templates.get(template_name)
            if not template:
                QMessageBox.warning(dialog, "Error", "Template not found")
                return
            
            # First, delete any existing planned activities
            existing_activities = self.activities_manager.get_activities_for_date(self.current_date)
            for activity in existing_activities:
                if activity.get('category') == 'Template':
                    self.activities_manager.delete_activity(activity['id'])
            
            # Apply the template
            current_time = start_time
            for block in template:
                end_time = current_time.addSecs(block["duration"] * 60)
                
                # Create activity
                activity_data = {
                    'title': block["title"],
                    'date': self.current_date,
                    'start_time': current_time,
                    'end_time': end_time,
                    'description': f"From {template_name} template",
                    'category': 'Template',
                    'type': block["type"],
                    'completed': False,
                    'color': block["color"]
                }
                
                # Add to database
                self.activities_manager.add_activity(activity_data)
                
                # Move to next time slot
                current_time = end_time
            
            # Refresh the view
            self.refresh()
            
            # Show completion message
            QMessageBox.information(dialog, "Template Applied", 
                                   f"Successfully applied the '{template_name}' template!")
            
            # Close the dialog
            dialog.accept()
            
        except Exception as e:
            print(f"Error applying day template: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(dialog, "Error", f"Could not apply template: {str(e)}") 

    def duplicateActivity(self, activity):
        """Duplicate an existing activity."""
        if not self.activities_manager:
            return
        
        try:
            # Create a copy of the activity data
            new_activity = activity.copy()
            
            # Remove id and set completed to False
            if 'id' in new_activity:
                del new_activity['id']
            new_activity['completed'] = False
            new_activity['title'] = f"Copy of {new_activity.get('title', 'Activity')}"
            
            # If locally hidden, clear that flag
            if 'locally_hidden' in new_activity:
                del new_activity['locally_hidden']
            
            # Add to database
            self.activities_manager.add_activity(new_activity)
            
            # Refresh the view
            self.refresh()
            
        except Exception as e:
            print(f"Error duplicating activity: {e}")
            QMessageBox.warning(self, "Error", f"Could not duplicate activity: {str(e)}")