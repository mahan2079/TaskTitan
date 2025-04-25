"""
Goal widget for TaskTitan.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QScrollArea, QFrame, QTreeWidget, 
                           QTreeWidgetItem, QDialog, QLineEdit, QDateEdit, 
                           QTimeEdit, QComboBox, QDialogButtonBox, QMessageBox, QMenu,
                           QTabWidget, QGraphicsView, QGraphicsScene, QGraphicsRectItem, 
                           QGraphicsTextItem, QGraphicsLineItem, QSlider, QGraphicsItem,
                           QGraphicsSceneWheelEvent, QGraphicsPathItem, QGraphicsEllipseItem,
                           QGraphicsDropShadowEffect, QProgressBar)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QRectF, QPointF, QTimer, QEvent, QPoint
from PyQt6.QtGui import QIcon, QFont, QColor, QPen, QBrush, QWheelEvent, QPainter, QPainterPath, QAction, QFontMetrics
from datetime import datetime, timedelta
import random

from app.resources import get_icon

# Add import for circular progress chart if we're in a different file
try:
    from app.views.main_window import CircularProgressChart
except ImportError:
    # Define it here if it doesn't exist in main_window
    class CircularProgressChart(QWidget):
        """A circular progress chart widget that displays percentage completion."""
        
        def __init__(self, title, value, max_value=100, parent=None):
            super().__init__(parent)
            self.title = title
            self.value = value
            self.max_value = max_value
            self.percentage = (value / max_value) * 100 if max_value > 0 else 0
            self.setMinimumSize(140, 180)
            self.setMaximumWidth(200)
            
            # Create layout and add title and value labels
            layout = QVBoxLayout(self)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.value_label = QLabel(f"{int(self.percentage)}%")
            self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4F46E5;")
            
            self.title_label = QLabel(self.title)
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_label.setStyleSheet("font-size: 14px; color: #64748B;")
            
            # Add spacer at top to position labels below the chart
            layout.addSpacing(100)
            layout.addWidget(self.value_label)
            layout.addWidget(self.title_label)
            
        def updateValue(self, value):
            """Update the progress value and redraw."""
            self.value = value
            self.percentage = (value / self.max_value) * 100 if self.max_value > 0 else 0
            self.value_label.setText(f"{int(self.percentage)}%")
            self.update()
            
        def paintEvent(self, event):
            """Draw the circular progress chart."""
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Define the rectangle for the chart
            rect = QRectF(20, 10, 100, 100)
            
            # Calculate the span angle for the progress arc (360 * percentage / 100)
            span_angle = int(360 * self.percentage / 100) * 16  # Qt uses 16ths of a degree
            
            # Draw background circle
            painter.setPen(QPen(QColor("#E2E8F0"), 10, Qt.PenStyle.SolidLine))
            painter.drawArc(rect, 0, 360 * 16)  # Full circle (360 degrees)
            
            # Draw progress arc
            if self.percentage > 0:
                # Use different colors based on completion percentage
                if self.percentage < 30:
                    color = QColor("#EF4444")  # Red for low progress
                elif self.percentage < 70:
                    color = QColor("#F59E0B")  # Orange/Yellow for medium progress
                else:
                    color = QColor("#10B981")  # Green for high progress
                    
                painter.setPen(QPen(color, 10, Qt.PenStyle.SolidLine))
                painter.drawArc(rect, 90 * 16, -span_angle)  # Start from top (90 degrees)
            
            painter.end()

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # Track current dialog to avoid multiple dialogs
        self.active_dialog = None
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom with Ctrl+Wheel
            factor = 1.1
            if event.angleDelta().y() < 0:
                factor = 1.0 / factor
            
            # Get the zoom factor from parent
            if hasattr(self.parent, 'zoom_factor'):
                self.parent.zoom_factor = max(
                    min(self.parent.zoom_factor * factor, 
                        self.parent.max_zoom), 
                    self.parent.min_zoom
                )
                self.parent.zoom_slider.setValue(int(self.parent.zoom_factor * 100))
                self.parent.applyZoom()
        else:
            # Normal scrolling
            super().wheelEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events to show goal details."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get the item under mouse
            scene_pos = self.mapToScene(event.pos())
            items = self.scene().items(scene_pos)
            
            # Find the goal rectangle item (filter for QGraphicsRectItem)
            goal_rect = None
            for item in items:
                if isinstance(item, QGraphicsRectItem) and hasattr(item, 'data') and item.data(0):
                    goal_rect = item
                    break
            
            if goal_rect:
                # Get the goal data
                goal_id = goal_rect.data(0)
                if hasattr(self.parent, 'parent') and hasattr(self.parent.parent, 'goals'):
                    # Find goal data
                    goal = None
                    for g in self.parent.parent.goals:
                        if g['id'] == goal_id:
                            goal = g
                            break
                            
                    if goal:
                        self.showGoalDetailsDialog(goal, event.globalPosition().toPoint())
                        return  # Don't pass to parent handler
        
        # Default handling for other cases
        super().mousePressEvent(event)
    
    def showGoalDetailsDialog(self, goal, position):
        """Show a custom dialog with goal details at the specified position."""
        # Close existing dialog if present
        if self.active_dialog and self.active_dialog.isVisible():
            self.active_dialog.close()
        
        # Create a custom dialog
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set fixed position near the mouse position
        dialog.move(position + QPoint(10, 10))
        
        # Create layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create content frame
        content = QFrame()
        content.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
            }
            QLabel {
                color: #000000;
                padding: 4px 0px;
            }
            QLabel#titleLabel {
                font-size: 14px;
                font-weight: bold;
                color: #000000;
            }
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        
        # Add goal details
        title_label = QLabel(goal['title'])
        title_label.setObjectName("titleLabel")
        content_layout.addWidget(title_label)
        
        # Calculate progress
        progress = 0
        if hasattr(self.parent, 'parent'):
            parent_widget = self.parent.parent
            if hasattr(parent_widget, 'calculateGoalProgress'):
                progress = parent_widget.calculateGoalProgress(goal)
        
        # Format goal information
        due_date_str = f"Due: {goal['due_date']} {goal['due_time']}"
        progress_str = f"Progress: {progress}%"
        status_str = "Status: Completed" if goal['completed'] else "Status: In Progress"
        
        due_label = QLabel(due_date_str)
        progress_label = QLabel(progress_str)
        status_label = QLabel(status_str)
        
        # Style status label based on completion
        if goal['completed']:
            status_label.setStyleSheet("color: #10B981; font-weight: bold;")  # Green for completed
        else:
            status_label.setStyleSheet("color: #3B82F6; font-weight: bold;")  # Blue for in progress
        
        content_layout.addWidget(due_label)
        content_layout.addWidget(progress_label)
        content_layout.addWidget(status_label)
        
        layout.addWidget(content)
        
        # Track this dialog
        self.active_dialog = dialog
        
        # Auto-close the dialog when clicked outside
        dialog.installEventFilter(self)
        
        # Show dialog
        dialog.show()
    
    def eventFilter(self, obj, event):
        """Event filter to close dialog when clicked outside."""
        if obj == self.active_dialog and event.type() == QEvent.Type.MouseButtonPress:
            obj.close()
            return True
        return super().eventFilter(obj, event)

class AddGoalDialog(QDialog):
    """Dialog for adding or editing goals with start date."""
    
    def __init__(self, parent=None, title="Add New Goal", goal_data=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.goal_data = goal_data or {}
        
        # Set dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
            QLabel {
                color: #000000;
                font-weight: bold;
            }
            QLineEdit, QDateEdit, QTimeEdit, QComboBox {
                background-color: #F9FAFB;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 6px;
                color: #000000;
                font-weight: 500;
            }
            QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QComboBox:focus {
                border: 1px solid #4F46E5;
            }
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4338CA;
            }
            QPushButton:pressed {
                background-color: #3730A3;
            }
            QDialogButtonBox {
                background-color: #F9FAFB;
                border-top: 1px solid #E5E7EB;
                padding: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #000000;
                selection-background-color: #EEF2FF;
                selection-color: #000000;
            }
        """)
        
        self.setupUI()
        
    def setupUI(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_layout.addWidget(title_label)
        self.title_input = QLineEdit(self.goal_data.get('title', ''))
        title_layout.addWidget(self.title_input)
        layout.addLayout(title_layout)
        
        # Parent goal (for sub-goals)
        parent_layout = QHBoxLayout()
        parent_label = QLabel("Parent Goal:")
        parent_layout.addWidget(parent_label)
        self.parent_input = QComboBox()
        self.parent_input.addItem("None", None)
        
        # Will be populated by caller
        parent_layout.addWidget(self.parent_input)
        layout.addLayout(parent_layout)
        
        # Start date
        start_date_layout = QHBoxLayout()
        start_date_label = QLabel("Start Date:")
        start_date_layout.addWidget(start_date_label)
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        
        if 'created_date' in self.goal_data and self.goal_data['created_date']:
            self.start_date_input.setDate(QDate.fromString(self.goal_data['created_date'], "yyyy-MM-dd"))
        else:
            self.start_date_input.setDate(QDate.currentDate())
            
        start_date_layout.addWidget(self.start_date_input)
        layout.addLayout(start_date_layout)
        
        # Due date
        due_date_layout = QHBoxLayout()
        due_date_label = QLabel("Due Date:")
        due_date_layout.addWidget(due_date_label)
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        
        if 'due_date' in self.goal_data and self.goal_data['due_date']:
            self.due_date_input.setDate(QDate.fromString(self.goal_data['due_date'], "yyyy-MM-dd"))
        else:
            self.due_date_input.setDate(QDate.currentDate().addDays(7))
            
        due_date_layout.addWidget(self.due_date_input)
        layout.addLayout(due_date_layout)
        
        # Due time
        time_layout = QHBoxLayout()
        time_label = QLabel("Due Time:")
        time_layout.addWidget(time_label)
        self.time_input = QTimeEdit()
        
        if 'due_time' in self.goal_data and self.goal_data['due_time']:
            self.time_input.setTime(QTime.fromString(self.goal_data['due_time'], "HH:mm"))
        else:
            self.time_input.setTime(QTime(12, 0))  # Default to noon
            
        time_layout.addWidget(self.time_input)
        layout.addLayout(time_layout)
        
        # Priority
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Priority:")
        priority_layout.addWidget(priority_label)
        self.priority_input = QComboBox()
        self.priority_input.addItems(["Low", "Medium", "High"])
        
        if 'priority' in self.goal_data:
            self.priority_input.setCurrentIndex(self.goal_data['priority'])
            
        priority_layout.addWidget(self.priority_input)
        layout.addLayout(priority_layout)
        
        # Add buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    
    def getGoalData(self):
        """Get the goal data from the dialog inputs."""
        return {
            'title': self.title_input.text().strip(),
            'parent_id': self.parent_input.currentData(),
            'created_date': self.start_date_input.date().toString("yyyy-MM-dd"),
            'due_date': self.due_date_input.date().toString("yyyy-MM-dd"),
            'due_time': self.time_input.time().toString("HH:mm"),
            'priority': self.priority_input.currentIndex()
        }

class GoalTimelineWidget(QWidget):
    """Widget for visualizing goals in a zoomable timeline view."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Timeline view settings
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 3.0
        self.timeline_start = None
        self.timeline_end = None
        
        # Map of goal IDs to their graphical items
        self.goal_items = {}
        
        # Set up the UI
        self.setupUI()
        
        # Set background color
        self.setStyleSheet("background-color: #F9FAFB;")
    
    def setupUI(self):
        """Set up the user interface components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Controls for the timeline
        controls_layout = QHBoxLayout()
        
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
        
        # Show today button
        today_btn = QPushButton("Go to Today")
        today_btn.clicked.connect(self.goToToday)
        controls_layout.addWidget(today_btn)
        
        # Legend for colors
        controls_layout.addStretch(1)
        
        legend_label = QLabel("Legend:")
        legend_label.setStyleSheet("font-weight: bold;")
        controls_layout.addWidget(legend_label)
        
        # Priority colors
        low_color = QFrame()
        low_color.setFixedSize(16, 16)
        low_color.setStyleSheet("background-color: #60A5FA; border: 1px solid #3B82F6;")
        controls_layout.addWidget(low_color)
        controls_layout.addWidget(QLabel("Low"))
        
        med_color = QFrame()
        med_color.setFixedSize(16, 16)
        med_color.setStyleSheet("background-color: #FBBF24; border: 1px solid #D97706;")
        controls_layout.addWidget(med_color)
        controls_layout.addWidget(QLabel("Medium"))
        
        high_color = QFrame()
        high_color.setFixedSize(16, 16)
        high_color.setStyleSheet("background-color: #EF4444; border: 1px solid #B91C1C;")
        controls_layout.addWidget(high_color)
        controls_layout.addWidget(QLabel("High"))
        
        # Completed color
        done_color = QFrame()
        done_color.setFixedSize(16, 16)
        done_color.setStyleSheet("background-color: #10B981; border: 1px solid #059669;")
        controls_layout.addWidget(done_color)
        controls_layout.addWidget(QLabel("Completed"))
        
        main_layout.addLayout(controls_layout)
        
        # Timeline view in a scroll area
        self.view = CustomGraphicsView(self)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Set nice background
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor("#F9FAFB")))
        self.view.setScene(self.scene)
        
        # Add a border to the view
        self.view.setFrameShape(QFrame.Shape.StyledPanel)
        self.view.setStyleSheet("""
            border: 1px solid #D1D5DB;
            background-color: #F9FAFB;
        """)
        
        main_layout.addWidget(self.view, 1)
        
        # Status message
        self.status_label = QLabel("Click and drag to pan, use Ctrl+scroll to zoom")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #6B7280; font-style: italic;")
        main_layout.addWidget(self.status_label)
    
    def goToToday(self):
        """Center the view on today's date."""
        if not self.timeline_start or not self.timeline_end:
            return
            
        today = datetime.now().date()
        if today < self.timeline_start or today > self.timeline_end:
            # Today is outside the current view range
            self.status_label.setText("Today's date is outside the goal timeline range")
            return
            
        # Calculate position for today
        days_from_start = (today - self.timeline_start).days
        x_pos = days_from_start * 30
        
        # Center on this position
        self.view.centerOn(x_pos, 0)
        
        # Indicate today in the scene
        today_indicator = self.scene.addRect(x_pos - 1, -50, 2, 1000, 
                                          QPen(QColor("#4F46E5"), 2, Qt.PenStyle.DashLine))
        
        # Fade out the indicator after 3 seconds
        QTimer.singleShot(3000, lambda: self.scene.removeItem(today_indicator) if today_indicator in self.scene.items() else None)
    
    def handleZoomSlider(self, value):
        """Handle zoom slider changes."""
        self.zoom_factor = value / 100.0
        self.applyZoom()
        
    def zoomIn(self):
        """Zoom in on the timeline."""
        self.zoom_factor = min(self.zoom_factor * 1.2, self.max_zoom)
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.applyZoom()
    
    def zoomOut(self):
        """Zoom out on the timeline."""
        self.zoom_factor = max(self.zoom_factor / 1.2, self.min_zoom)
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.applyZoom()
    
    def applyZoom(self):
        """Apply the current zoom factor to the view."""
        self.view.resetTransform()
        self.view.scale(self.zoom_factor, self.zoom_factor)
        
        # Update status message
        self.status_label.setText(f"Zoom: {int(self.zoom_factor * 100)}% - Click and drag to pan, use Ctrl+scroll to zoom")
    
    def resetView(self):
        """Reset the timeline view to the default state."""
        self.zoom_factor = 1.0
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.view.resetTransform()
        if not self.scene.items():
            return
        self.view.setSceneRect(self.scene.itemsBoundingRect())
        self.view.centerOn(0, 0)
        
        # Update status message
        self.status_label.setText("View reset - Click and drag to pan, use Ctrl+scroll to zoom")

    def updateTimeline(self, goals):
        """Update the timeline with the current goals."""
        self.scene.clear()
        self.goal_items = {}
        
        if not goals:
            # No goals to display
            no_goals_text = self.scene.addSimpleText("No goals found")
            no_goals_text.setPos(0, 0)
            self.status_label.setText("No goals to display")
            return
        
        # Calculate the time range for all goals
        self.calculateTimeRange(goals)
        
        # Draw time axis
        self.drawTimeAxis()
        
        # Add goals to the timeline
        self.addGoalsToTimeline(goals)
        
        # Adjust view to show all items
        if self.scene.items():
            self.view.setSceneRect(self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50))
            self.view.fitInView(self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50), 
                               Qt.AspectRatioMode.KeepAspectRatio)
            
        # Reset zoom and position
        self.resetView()
        
        # Update status
        self.status_label.setText(f"Showing {len(goals)} goals from {self.timeline_start.strftime('%b %d, %Y')} to {self.timeline_end.strftime('%b %d, %Y')}")
    
    def calculateTimeRange(self, goals):
        """Calculate the start and end dates for the timeline."""
        dates = []
        for goal in goals:
            try:
                date_str = goal['due_date']
                goal_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                dates.append(goal_date)
            except (ValueError, KeyError):
                continue
        
        if dates:
            # Set timeline range with padding
            min_date = min(dates)
            max_date = max(dates)
            
            # Add padding of 10% of the range on each side
            date_range = (max_date - min_date).days
            padding = max(7, date_range // 10)  # at least 7 days padding
            
            self.timeline_start = min_date - timedelta(days=padding)
            self.timeline_end = max_date + timedelta(days=padding)
        else:
            # Default to a range of 30 days centered around today
            today = datetime.now().date()
            self.timeline_start = today - timedelta(days=15)
            self.timeline_end = today + timedelta(days=15)
    
    def drawTimeAxis(self):
        """Draw the time axis for the timeline."""
        if not self.timeline_start or not self.timeline_end:
            return
        
        # Draw the main axis
        days = (self.timeline_end - self.timeline_start).days
        pixels_per_day = 50  # Increased from 30 to 50 pixels per day for better spacing
        axis_width = days * pixels_per_day
        
        # Draw background grid
        for i in range(0, days + 1, 7):  # Weekly grid
            x_pos = i * pixels_per_day
            # Vertical grid line
            grid_line = QGraphicsLineItem(x_pos, -50, x_pos, 1000)
            grid_line.setPen(QPen(QColor("#E5E7EB"), 1, Qt.PenStyle.DotLine))
            self.scene.addItem(grid_line)
        
        # Draw horizontal grid at standard y positions
        for y_pos in range(50, 1000, 50):
            grid_line = QGraphicsLineItem(0, y_pos, axis_width, y_pos)
            grid_line.setPen(QPen(QColor("#E5E7EB"), 1, Qt.PenStyle.DotLine))
            self.scene.addItem(grid_line)
        
        # Draw the axis line
        axis_line = QGraphicsLineItem(0, 0, axis_width, 0)
        axis_line.setPen(QPen(QColor("#333333"), 2))
        self.scene.addItem(axis_line)
        
        # Add date markers
        current_date = self.timeline_start
        month_label = None
        current_month = None
        
        while current_date <= self.timeline_end:
            # Position based on days from start
            days_from_start = (current_date - self.timeline_start).days
            x_pos = days_from_start * pixels_per_day
            
            # Draw tick
            tick = QGraphicsLineItem(x_pos, -5, x_pos, 5)
            tick.setPen(QPen(QColor("#333333"), 1))
            self.scene.addItem(tick)
            
            # Add month label for the first day of each month
            if current_date.day == 1 or current_month != current_date.month:
                month_label = QGraphicsTextItem(current_date.strftime("%b %Y"))
                month_label.setPos(x_pos - 20, -30)
                month_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                month_label.setDefaultTextColor(QColor("#000000"))
                self.scene.addItem(month_label)
                current_month = current_date.month
            
            # Add date label
            if current_date.day == 1 or current_date.day % 2 == 0:  # Show dates every 2 days
                date_label = QGraphicsTextItem(current_date.strftime("%d"))
                date_label.setPos(x_pos - 5, 10)
                date_label.setFont(QFont("Arial", 8))
                date_label.setDefaultTextColor(QColor("#000000"))
                self.scene.addItem(date_label)
            
            # Highlight weekends
            if current_date.weekday() >= 5:  # Saturday or Sunday
                weekend_rect = QGraphicsRectItem(x_pos, -50, pixels_per_day, 1000)
                weekend_rect.setPen(QPen(Qt.PenStyle.NoPen))
                weekend_rect.setBrush(QBrush(QColor(240, 240, 240, 100)))
                weekend_rect.setZValue(-1)
                self.scene.addItem(weekend_rect)
            
            # Move to next date
            current_date += timedelta(days=1)
    
    def addGoalsToTimeline(self, goals):
        """Add goals to the timeline visualization."""
        if not self.timeline_start or not self.timeline_end:
            return
        
        # Group goals by parent_id
        root_goals = [g for g in goals if g['parent_id'] is None]
        
        # Place root goals first
        y_offset = 50
        for i, goal in enumerate(root_goals):
            # Add alternating background for better readability
            if i % 2 == 0:
                bg_rect = self.scene.addRect(0, y_offset, 10000, 50, 
                                          QPen(Qt.PenStyle.NoPen),
                                          QBrush(QColor(240, 248, 255, 100)))  # Light blue with transparency
                bg_rect.setZValue(-2)  # Put it behind other items
            
            y_offset = self.addGoalToTimeline(goal, goals, 0, y_offset) + 30
    
    def addGoalToTimeline(self, goal, all_goals, level=0, y_pos=30):
        """Add a single goal and its sub-goals to the timeline."""
        try:
            # Define colors array at the beginning of the method to make it available throughout
            colors = ["#60A5FA", "#FBBF24", "#EF4444"]  # Blue, Yellow, Red for low, medium, high
            
            # Get or derive start date and due date
            due_date = datetime.strptime(goal['due_date'], "%Y-%m-%d").date()
            
            # Use created_date if available, otherwise default to 7 days before due date
            if 'created_date' in goal and goal['created_date']:
                start_date = datetime.strptime(goal['created_date'], "%Y-%m-%d").date()
            else:
                # Default: start 7 days before due date
                start_date = due_date - timedelta(days=7)
            
            # Calculate positions
            pixels_per_day = 50  # Match the value used in drawTimeAxis
            start_days_from_timeline_start = max(0, (start_date - self.timeline_start).days)
            end_days_from_timeline_start = (due_date - self.timeline_start).days
            
            x_start = start_days_from_timeline_start * pixels_per_day
            x_end = end_days_from_timeline_start * pixels_per_day
            width = max(80, x_end - x_start)  # Minimum width of 80px for better text visibility
            
            # Apply indentation for subgoals based on level
            indent = level * 20
            if level > 0:
                x_start += indent
                width = min(width, x_end - x_start)  # Ensure width doesn't exceed due date
            
            # Create goal rectangle spanning from start to due date
            rect_height = 30
            
            # Calculate progress percentage for this goal (get from parent widget if possible)
            progress_percentage = 0
            if hasattr(self.parent, 'calculateGoalProgress'):
                progress_percentage = self.parent.calculateGoalProgress(goal)
            elif goal['completed']:
                progress_percentage = 100
            
            # Choose color based on priority and completion
            if goal['completed']:
                color = QColor("#10B981")  # Green for completed
            else:
                color = QColor(colors[goal['priority']])
            
            # Create the goal item
            rect = QGraphicsRectItem(x_start, y_pos, width, rect_height)
            rect.setPen(QPen(color.darker(), 1))
            rect.setBrush(QBrush(color.lighter()))
            
            # Store goal ID as item data for identification in click handler
            rect.setData(0, goal['id'])
            
            # Add goal text with ellipsis if too long
            text = QGraphicsTextItem()
            text.setDefaultTextColor(QColor("#1F2937"))
            
            # Calculate available width for text (accounting for progress circle if needed)
            text_width = width - 30 if not goal['completed'] and progress_percentage > 0 else width - 10
            
            # Create a font for the text
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            text.setFont(font)
            
            # Elide text if it's too long
            metrics = QFontMetrics(font)
            elidedText = metrics.elidedText(goal['title'], Qt.TextElideMode.ElideRight, text_width)
            text.setPlainText(elidedText)
            
            # Position text
            text.setPos(x_start + 5, y_pos + 5)
            
            # Add white text outline for better contrast on any background
            text_effect = QGraphicsDropShadowEffect()
            text_effect.setColor(QColor("#FFFFFF"))
            text_effect.setBlurRadius(0)
            text_effect.setOffset(1, 1)
            text.setGraphicsEffect(text_effect)
            
            # Include progress percentage in the tooltip
            tooltip_html = f"""
            <div style='background-color:#FFFFFF; color:#000000; padding:8px; border:1px solid #D1D5DB; border-radius:4px; font-weight:bold;'>
                <span style='font-size:14px;'>{goal['title']}</span><br/>
                <span style='font-size:12px;'>Due: {goal['due_date']} {goal['due_time']}</span><br/>
                <span style='font-size:12px;'>Progress: {progress_percentage}%</span>
            </div>
            """
            rect.setToolTip(tooltip_html)
            
            # Add special indicator for subgoals (small badge or marker)
            if level > 0:
                # Add a small triangular marker on the left to indicate it's a subgoal
                marker_size = 10
                path = QPainterPath()
                path.moveTo(x_start - marker_size, y_pos + rect_height/2)
                path.lineTo(x_start, y_pos + rect_height/2 - marker_size/2)
                path.lineTo(x_start, y_pos + rect_height/2 + marker_size/2)
                path.closeSubpath()
                
                # Create a marker with parent's color
                parent_goal = next((g for g in all_goals if g['id'] == goal['parent_id']), None)
                if parent_goal:
                    if parent_goal['completed']:
                        marker_color = QColor("#10B981")
                    else:
                        marker_color = QColor(colors[parent_goal['priority']])
                else:
                    marker_color = color
                    
                marker = QGraphicsPathItem(path)
                marker.setPen(QPen(marker_color.darker(), 1))
                marker.setBrush(QBrush(marker_color))
                self.scene.addItem(marker)
            
            # Add a small circular progress indicator if not completed
            if not goal['completed'] and progress_percentage > 0:
                # Draw a small circular progress indicator
                progress_diameter = 20
                circle_x = x_start + width - progress_diameter - 5
                circle_y = y_pos + (rect_height - progress_diameter) / 2
                
                # Create progress circle
                progress_circle = QGraphicsEllipseItem(circle_x, circle_y, progress_diameter, progress_diameter)
                progress_circle.setPen(QPen(Qt.PenStyle.NoPen))
                progress_circle.setBrush(QBrush(QColor("#FFFFFF")))
                
                # Add progress arc
                span_angle = int(360 * progress_percentage / 100) * 16  # Qt uses 16ths of a degree
                
                # Create a path for the progress arc
                path = QPainterPath()
                path.moveTo(circle_x + progress_diameter/2, circle_y + progress_diameter/2)
                path.arcTo(circle_x, circle_y, progress_diameter, progress_diameter, 90, -span_angle)
                path.closeSubpath()
                
                # Choose color based on progress
                if progress_percentage < 30:
                    progress_color = QColor("#EF4444")  # Red for low progress
                elif progress_percentage < 70:
                    progress_color = QColor("#F59E0B")  # Orange/Yellow for medium progress
                else:
                    progress_color = QColor("#10B981")  # Green for high progress
                
                progress_arc = QGraphicsPathItem(path)
                progress_arc.setPen(QPen(Qt.PenStyle.NoPen))
                progress_arc.setBrush(QBrush(progress_color))
                
                # Add percentage text
                progress_text = QGraphicsTextItem(f"{progress_percentage}%")
                progress_text.setPos(circle_x - 5, circle_y + progress_diameter + 2)
                progress_text.setFont(QFont("Arial", 7))
                progress_text.setDefaultTextColor(QColor("#000000"))
                
                self.scene.addItem(progress_circle)
                self.scene.addItem(progress_arc)
                self.scene.addItem(progress_text)
            
            # Add to scene
            self.scene.addItem(rect)
            self.scene.addItem(text)
            
            # Store reference to the item
            self.goal_items[goal['id']] = rect
            
            # Find sub-goals
            sub_goals = [g for g in all_goals if g['parent_id'] == goal['id']]
            
            if sub_goals:
                # Calculate positions for sub-goals layout
                current_y = y_pos + rect_height + 10  # Reduced spacing from 20 to 10
                
                # Create a colored group background for all subgoals
                # Using a very light version of the parent's color
                bg_color = QColor(color)
                bg_color.setAlpha(15)  # Very transparent
                
                # First calculate the total height needed for all subgoals
                temp_y = current_y
                last_end_date = start_date
                
                # Add a small vertical connection from parent to subgoal group
                connector = QGraphicsRectItem(x_start + width/2 - 1, y_pos + rect_height, 
                                            2, 10)  # 2px wide connector line
                connector.setPen(QPen(Qt.PenStyle.NoPen))
                connector.setBrush(QBrush(color))
                self.scene.addItem(connector)
                
                for i, sub_goal in enumerate(sub_goals):
                    # Modify subgoal's created_date to start after previous subgoal ends
                    if not 'created_date' in sub_goal or not sub_goal['created_date']:
                        if i == 0:
                            # First subgoal starts at parent's start
                            sub_goal['created_date'] = start_date.strftime("%Y-%m-%d")
                        else:
                            # Subsequent subgoals start when previous one ends
                            sub_goal['created_date'] = last_end_date.strftime("%Y-%m-%d")
                    
                    # Calculate height for this subgoal and its descendants
                    sub_height = self.calculateSubgoalHeight(sub_goal, all_goals)
                    temp_y += sub_height + 10  # Reduced spacing from 20 to 10
                    
                    # Update last_end_date for next subgoal
                    sub_due_date = datetime.strptime(sub_goal['due_date'], "%Y-%m-%d").date()
                    last_end_date = sub_due_date
                
                total_height = temp_y - current_y
                
                # Limit the width of the background to avoid extending too far
                # Use the maximum right edge of the parent or its longest subgoal
                max_right_edge = x_start + width + 20  # Parent width plus some padding
                
                # Create a background rectangle to visually group subgoals
                group_bg = QGraphicsRectItem(x_start - 5, current_y, 
                                           max_right_edge - x_start + 10, total_height)
                group_bg.setPen(QPen(Qt.PenStyle.NoPen))
                group_bg.setBrush(QBrush(bg_color))
                group_bg.setZValue(-2)  # Place behind everything
                self.scene.addItem(group_bg)
                
                # Create a vertical indicator line on the left side of the subgoal group
                # Make it slightly shorter to avoid touching the parent goal
                indicator_line = QGraphicsRectItem(x_start - 5, current_y, 
                                                3, total_height)
                indicator_line.setPen(QPen(Qt.PenStyle.NoPen))
                indicator_line.setBrush(QBrush(color))
                indicator_line.setZValue(-1)
                self.scene.addItem(indicator_line)
                
                # Reset for actual subgoal placement
                last_end_date = start_date
                original_current_y = current_y
                
                # Now add each subgoal
                for i, sub_goal in enumerate(sub_goals):
                    # Modify subgoal's created_date to start after previous subgoal ends
                    if not 'created_date' in sub_goal or not sub_goal['created_date']:
                        if i == 0:
                            sub_goal['created_date'] = start_date.strftime("%Y-%m-%d")
                        else:
                            sub_goal['created_date'] = last_end_date.strftime("%Y-%m-%d")
                    
                    # Add the sub-goal and get updated y position
                    current_y = self.addGoalToTimeline(sub_goal, all_goals, level + 1, current_y)
                    
                    # Update last_end_date for next subgoal
                    sub_due_date = datetime.strptime(sub_goal['due_date'], "%Y-%m-%d").date()
                    last_end_date = sub_due_date
                
                # Add padding after the last subgoal to prevent overlap with the next goal
                return current_y + 15
            
            return y_pos + rect_height
        
        except (ValueError, KeyError) as e:
            print(f"Error adding goal to timeline: {e}")
            return y_pos + 30

    def calculateSubgoalHeight(self, goal, all_goals):
        """
        Calculate the height needed for a goal and all its subgoals.
        
        Args:
            goal (dict): The goal to calculate height for
            all_goals (list): List of all goals
            
        Returns:
            int: The total height needed for the goal and its subgoals
        """
        # Base height for the goal itself
        base_height = 40  # Standard rect height
        
        # Find all direct subgoals
        sub_goals = [g for g in all_goals if g['parent_id'] == goal['id']]
        if not sub_goals:
            return base_height
            
        # For each subgoal, add its own height plus spacing
        total_height = base_height
        for sub_goal in sub_goals:
            # Recursively calculate height for this subgoal and its descendants
            sub_height = self.calculateSubgoalHeight(sub_goal, all_goals)
            total_height += sub_height + 20  # Add spacing between subgoals
            
        return total_height

class GoalWidget(QWidget):
    """Widget for managing goals and tracking progress."""
    
    # Signals
    goalAdded = pyqtSignal(dict)
    goalCompleted = pyqtSignal(int, bool)
    goalDeleted = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store parent to access database
        
        # Goals data
        self.goals = []
        
        # Setup UI
        self.setupUI()
        
        # Load initial data
        self.loadGoals()
    
    def setupUI(self):
        """Set up the user interface components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("goalHeader")
        header.setMinimumHeight(70)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 15, 25, 15)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # Add goal icon
        icon_label = QLabel()
        goal_icon = get_icon("goals")
        if not goal_icon.isNull():
            icon_label.setPixmap(goal_icon.pixmap(32, 32))
        else:
            # Fallback icon text
            icon_label.setText("🎯")
            icon_label.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(icon_label)
        
        # Title text
        title = QLabel("My Goals")
        title.setObjectName("goalTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title_layout.addWidget(title)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch(1)
        
        # Add goal button
        self.add_btn = QPushButton("Add Goal")
        self.add_btn.setObjectName("addGoalButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setMinimumWidth(120)
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.showAddGoalDialog)
        
        # Add icon to button
        add_icon = get_icon("add")
        if not add_icon.isNull():
            self.add_btn.setIcon(add_icon)
        
        # Style the button
        self.add_btn.setStyleSheet("""
            QPushButton#addGoalButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton#addGoalButton:hover {
                background-color: #2563EB;
            }
            QPushButton#addGoalButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        
        header_layout.addWidget(self.add_btn)
        
        # Style the header
        header.setStyleSheet("""
            QWidget#goalHeader {
                background-color: white;
                border-bottom: 1px solid #E2E8F0;
            }
            QLabel#goalTitle {
                color: #1E293B;
            }
        """)
        
        main_layout.addWidget(header)
        
        # Create tab widget for different goal views
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("goalTabWidget")
        
        # Tree view tab with modern styling
        self.tree_tab = QWidget()
        tree_layout = QVBoxLayout(self.tree_tab)
        tree_layout.setContentsMargins(25, 25, 25, 25)
        tree_layout.setSpacing(15)
        
        # Filter/search section
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        # Search input field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search goals...")
        self.search_input.setMinimumWidth(250)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.handleSearchTextChanged)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px 12px;
                color: #1E293B;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
        """)
        filter_layout.addWidget(self.search_input)
        
        # Search button
        search_btn = QPushButton("Search")
        search_icon = get_icon("search")
        if not search_icon.isNull():
            search_btn.setIcon(search_icon)
        search_btn.clicked.connect(self.handleSearchButtonClicked)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #64748B;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
        filter_layout.addWidget(search_btn)
        
        # Filter dropdown
        self.filter_menu = QMenu(self)
        
        # Filter by completion status
        filter_status_menu = QMenu("Completion Status", self.filter_menu)
        self.filter_menu.addMenu(filter_status_menu)
        
        # All goals action
        self.action_all_goals = QAction("All Goals", self)
        self.action_all_goals.setCheckable(True)
        self.action_all_goals.setChecked(True)
        self.action_all_goals.triggered.connect(lambda: self.filterByCompletionStatus(None))
        filter_status_menu.addAction(self.action_all_goals)
        
        # Completed goals action
        self.action_completed = QAction("Completed", self)
        self.action_completed.setCheckable(True)
        self.action_completed.triggered.connect(lambda: self.filterByCompletionStatus(True))
        filter_status_menu.addAction(self.action_completed)
        
        # Incomplete goals action
        self.action_incomplete = QAction("Incomplete", self)
        self.action_incomplete.setCheckable(True)
        self.action_incomplete.triggered.connect(lambda: self.filterByCompletionStatus(False))
        filter_status_menu.addAction(self.action_incomplete)
        
        # Filter by priority
        filter_priority_menu = QMenu("Priority", self.filter_menu)
        self.filter_menu.addMenu(filter_priority_menu)
        
        # All priorities action
        self.action_all_priorities = QAction("All Priorities", self)
        self.action_all_priorities.setCheckable(True)
        self.action_all_priorities.setChecked(True)
        self.action_all_priorities.triggered.connect(lambda: self.filterByPriority(None))
        filter_priority_menu.addAction(self.action_all_priorities)
        
        # Low priority action
        self.action_low_priority = QAction("Low Priority", self)
        self.action_low_priority.setCheckable(True)
        self.action_low_priority.triggered.connect(lambda: self.filterByPriority(0))
        filter_priority_menu.addAction(self.action_low_priority)
        
        # Medium priority action
        self.action_medium_priority = QAction("Medium Priority", self)
        self.action_medium_priority.setCheckable(True)
        self.action_medium_priority.triggered.connect(lambda: self.filterByPriority(1))
        filter_priority_menu.addAction(self.action_medium_priority)
        
        # High priority action
        self.action_high_priority = QAction("High Priority", self)
        self.action_high_priority.setCheckable(True)
        self.action_high_priority.triggered.connect(lambda: self.filterByPriority(2))
        filter_priority_menu.addAction(self.action_high_priority)
        
        # Reset filters action
        self.filter_menu.addSeparator()
        self.action_reset_filters = QAction("Reset All Filters", self)
        self.action_reset_filters.triggered.connect(self.resetFilters)
        self.filter_menu.addAction(self.action_reset_filters)
        
        # Filter button
        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #64748B;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
        self.filter_btn.clicked.connect(self.showFilterMenu)
        filter_layout.addWidget(self.filter_btn)
        
        # Add a clear filters button
        self.clear_filters_btn = QPushButton("Clear Filters")
        self.clear_filters_btn.setVisible(False)
        self.clear_filters_btn.clicked.connect(self.resetFilters)
        self.clear_filters_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        filter_layout.addWidget(self.clear_filters_btn)
        
        filter_layout.addStretch(1)
        
        tree_layout.addLayout(filter_layout)
        
        # Filter status label to show active filters
        self.filter_status_label = QLabel("")
        self.filter_status_label.setVisible(False)
        self.filter_status_label.setStyleSheet("color: #4B5563; font-style: italic;")
        tree_layout.addWidget(self.filter_status_label)
        
        # Goal tree widget with modern styling
        self.goal_tree = QTreeWidget()
        self.goal_tree.setObjectName("goalTree")
        self.goal_tree.setColumnCount(5)  # Goal, Due Date, Due Time, Progress, Status
        self.goal_tree.setHeaderLabels(["Goal", "Due Date", "Due Time", "Progress", "Status"])
        self.goal_tree.setAlternatingRowColors(False)  # Disable alternating row colors
        self.goal_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.goal_tree.setAnimated(True)
        self.goal_tree.setIndentation(24)
        self.goal_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.goal_tree.customContextMenuRequested.connect(self.showContextMenu)
        self.goal_tree.itemChanged.connect(self.handleItemStatusChanged)
        
        # Apply modern styling to the tree widget
        self.goal_tree.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 8px;
                font-size: 13px;
            }
            QTreeWidget::item {
                border-bottom: 1px solid #F1F5F9;
                padding: 10px 2px;
                margin: 2px 0;
                background-color: transparent;
            }
            QTreeWidget::item:selected {
                background-color: rgba(235, 244, 255, 0.7);
                color: #1E293B;
                border: none;
                border-radius: 6px;
            }
            QTreeWidget::item:hover {
                background-color: rgba(247, 250, 252, 0.7);
                border-radius: 6px;
            }
            QTreeWidget::item:alternate {
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                padding: 12px 8px;
                border: none;
                font-weight: bold;
                color: #334155;
                font-size: 13px;
            }
            QTreeWidget::item:focus {
                border: none;
                outline: none;
            }
            QTreeView::branch {
                background-color: transparent;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                image: url(app/resources/icons/chevron-right.png);
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                image: url(app/resources/icons/chevron-down.png);
            }
        """)
        
        # Set column widths
        self.goal_tree.setColumnWidth(0, 300)  # Goal title
        self.goal_tree.setColumnWidth(1, 100)  # Due date
        self.goal_tree.setColumnWidth(2, 80)   # Due time
        self.goal_tree.setColumnWidth(3, 120)  # Progress
        self.goal_tree.setColumnWidth(4, 80)   # Status
        
        tree_layout.addWidget(self.goal_tree)
        
        # Timeline view tab
        self.timeline_widget = GoalTimelineWidget(self)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.tree_tab, "List View")
        self.tab_widget.addTab(self.timeline_widget, "Timeline")
        self.tab_widget.currentChanged.connect(self.handleTabChange)
        
        # Apply tab style
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: white;
            }
            QTabBar::tab {
                background: #F1F5F9;
                color: #64748B;
                min-width: 150px;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #3B82F6;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #CBD5E1;
            }
        """)
        
        main_layout.addWidget(self.tab_widget)
        
        # Load initial data
        self.loadGoals()
        
        # Expand all items by default for better visibility
        self.goal_tree.expandAll()
    
    def handleTabChange(self, index):
        """Handle tab changes."""
        if index == 1:  # Timeline tab
            # Update the timeline view
            self.timeline_widget.updateTimeline(self.goals)
    
    def showAddGoalDialog(self):
        """Show the dialog to add a new goal."""
        dialog = AddGoalDialog(self)
        
        # Add existing goals as potential parents
        for goal in self.goals:
            dialog.parent_input.addItem(goal['title'], goal['id'])
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.addGoal(dialog.getGoalData())
    
    def addGoal(self, goal_data):
        """Add a new goal from the dialog data."""
        title = goal_data['title']
        parent_id = goal_data['parent_id']
        created_date = goal_data['created_date']
        due_date = goal_data['due_date']
        due_time = goal_data['due_time']
        priority = goal_data['priority']
        
        if not title:
            QMessageBox.warning(self, "Error", "Goal title cannot be empty")
            return
        
        # Save to database if connection exists
        goal_id = None
        if hasattr(self.parent, 'conn') and self.parent.conn:
            try:
                # Check if created_date column exists, if not add it
                try:
                    self.parent.cursor.execute("SELECT created_date FROM goals LIMIT 1")
                except:
                    self.parent.cursor.execute("ALTER TABLE goals ADD COLUMN created_date TEXT")
                    self.parent.conn.commit()
                    
                self.parent.cursor.execute("""
                    INSERT INTO goals (title, parent_id, created_date, due_date, due_time, priority, completed)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (title, parent_id, created_date, due_date, due_time, priority))
                self.parent.conn.commit()
                goal_id = self.parent.cursor.lastrowid
            except Exception as e:
                print(f"Error saving goal to database: {e}")
                # Fall back to random ID
                goal_id = random.randint(1000, 9999)
        else:
            # For testing when no database connection
            goal_id = random.randint(1000, 9999)
        
        # Create the goal dictionary
        goal = {
            'id': goal_id,
            'title': title,
            'parent_id': parent_id,
            'created_date': created_date,
            'due_date': due_date,
            'due_time': due_time,
            'priority': priority,
            'completed': False
        }
        
        # Add to our list
        self.goals.append(goal)
        
        # Refresh the entire tree to ensure proper parent-child relationships
        self.refreshGoalTree()
        
        # Emit signal
        self.goalAdded.emit(goal)
    
    def addGoalToTree(self, goal, parent_item=None):
        """Add a goal to the tree widget.
        
        Args:
            goal: Dictionary with goal data
            parent_item: Parent QTreeWidgetItem or None if this is a top-level item
            
        Returns:
            The created QTreeWidgetItem
        """
        # Create a new tree item
        item = QTreeWidgetItem()
        item.setText(0, goal['title'])
        item.setText(1, goal['due_date'])
        item.setText(2, goal['due_time'])
        item.setData(0, Qt.ItemDataRole.UserRole, goal['id'])
        
        # Calculate progress percentage
        progress = self.calculateGoalProgress(goal)
        progress_text = f"{progress}%"
        item.setText(3, progress_text)
        
        # Set the status checkbox
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        status = Qt.CheckState.Checked if goal['completed'] else Qt.CheckState.Unchecked
        item.setCheckState(4, status)
        
        # Set progress text color based on percentage
        if progress < 30:
            item.setForeground(3, QColor("#EF4444"))  # Red for low progress
        elif progress < 70:
            item.setForeground(3, QColor("#F59E0B"))  # Orange/Yellow for medium progress
        else:
            item.setForeground(3, QColor("#10B981"))  # Green for high progress
        
        # Set priority color
        if goal['priority'] == 0:  # Low
            item.setBackground(0, QColor("#D1FAE5"))  # Light green
        elif goal['priority'] == 1:  # Medium
            item.setBackground(0, QColor("#FEF3C7"))  # Light yellow
        else:  # High
            item.setBackground(0, QColor("#FEE2E2"))  # Light red
        
        # Add to parent or root
        if parent_item:
            # If parent is provided, add as child of parent
            parent_item.addChild(item)
        else:
            # No parent item provided, add at top level
            self.goal_tree.addTopLevelItem(item)
        
        # Apply visual indication for a goal with subgoals
        font = item.font(0)
        if any(g['parent_id'] == goal['id'] for g in self.goals):
            font.setBold(True)
            item.setFont(0, font)
        
        return item
    
    def calculateGoalProgress(self, goal):
        """Calculate the progress percentage for a goal based on subgoals and time.
        
        Args:
            goal: The goal to calculate progress for
            
        Returns:
            int: Progress percentage (0-100)
        """
        # If goal is completed, return 100%
        if goal['completed']:
            return 100
        
        # Find all subgoals for this goal
        subgoals = [g for g in self.goals if g['parent_id'] == goal['id']]
        
        # If there are no subgoals, calculate progress based on time
        if not subgoals:
            return self.calculateTimeBasedProgress(goal)
        
        # If there are subgoals, calculate based on subgoal completion and weighted by duration
        total_duration = 0
        completed_duration = 0
        
        for subgoal in subgoals:
            try:
                # Get the start and end dates for duration calculation
                if 'created_date' in subgoal and subgoal['created_date']:
                    start_date = datetime.strptime(subgoal['created_date'], "%Y-%m-%d").date()
                else:
                    due_date = datetime.strptime(subgoal['due_date'], "%Y-%m-%d").date()
                    start_date = due_date - timedelta(days=7)  # Default 1 week duration if no start date
                
                due_date = datetime.strptime(subgoal['due_date'], "%Y-%m-%d").date()
                
                # Calculate duration in days (minimum 1 day)
                duration = max(1, (due_date - start_date).days)
                
                # Add to total duration
                total_duration += duration
                
                # If completed, add to completed duration
                if subgoal['completed']:
                    completed_duration += duration
                else:
                    # For incomplete subgoals that have their own subgoals, 
                    # calculate their progress recursively
                    subgoal_progress = self.calculateGoalProgress(subgoal) / 100.0
                    completed_duration += duration * subgoal_progress
            except (ValueError, TypeError, KeyError):
                # Skip if there are issues with the dates
                continue
        
        # Calculate progress based on weighted subgoal completion
        if total_duration > 0:
            progress = (completed_duration / total_duration) * 100
        else:
            progress = 0
            
        return int(progress)
    
    def calculateTimeBasedProgress(self, goal):
        """Calculate progress based on time elapsed.
        
        Args:
            goal: The goal to calculate progress for
            
        Returns:
            int: Progress percentage (0-100)
        """
        try:
            # Get the start and due dates
            if 'created_date' in goal and goal['created_date']:
                start_date = datetime.strptime(goal['created_date'], "%Y-%m-%d").date()
            else:
                # Default to 2 weeks before due date
                due_date = datetime.strptime(goal['due_date'], "%Y-%m-%d").date()
                start_date = due_date - timedelta(days=14)
            
            due_date = datetime.strptime(goal['due_date'], "%Y-%m-%d").date()
            today = datetime.now().date()
            
            # Calculate total duration and elapsed duration
            total_days = (due_date - start_date).days
            if total_days <= 0:  # Guard against invalid dates
                return 0
                
            elapsed_days = (today - start_date).days
            
            # Calculate progress percentage
            if elapsed_days < 0:  # Goal hasn't started yet
                progress = 0
            elif elapsed_days >= total_days:  # Goal is overdue
                progress = 90  # Almost complete but not 100% until actually marked complete
            else:
                progress = (elapsed_days / total_days) * 100
                
            return int(progress)
        except (ValueError, TypeError):
            # Return 0 if there are date parsing errors
            return 0
    
    def handleItemStatusChanged(self, item, column):
        """Handle when a goal's status is changed."""
        if column == 4:  # Status column
            try:
                # Temporarily block signals to prevent recursion
                self.goal_tree.blockSignals(True)
                
                goal_id = item.data(0, Qt.ItemDataRole.UserRole)
                if goal_id is None:
                    return  # No goal ID associated with this item
                    
                completed = item.checkState(4) == Qt.CheckState.Checked
                
                # Update database if connection exists
                if hasattr(self.parent, 'conn') and self.parent.conn:
                    try:
                        self.parent.cursor.execute("""
                            UPDATE goals
                            SET completed = ?
                            WHERE id = ?
                        """, (1 if completed else 0, goal_id))
                        self.parent.conn.commit()
                    except Exception as e:
                        print(f"Error updating goal status in database: {e}")
                
                # Update our data
                for goal in self.goals:
                    if goal['id'] == goal_id:
                        goal['completed'] = completed
                        break
                
                # Emit signal
                self.goalCompleted.emit(goal_id, completed)
                
                # If parent is completed, complete all children
                if completed:
                    self.updateChildrenStatus(item, Qt.CheckState.Checked)
                    
                # Check if this is a subgoal and determine what to do with the parent
                parent_item = item.parent()
                if parent_item:
                    if completed:
                        # If completed, check if all siblings are completed too
                        self.checkParentIfAllChildrenCompleted(parent_item)
                    else:
                        # If unchecked, ensure parent is unchecked too
                        self.uncheckParent(parent_item)
                
                # Unblock signals
                self.goal_tree.blockSignals(False)
                
                # Update visual appearance of this item and its progress
                self.updateItemAppearance(item, completed)
                
                # Update the progress indicators
                self.updateAffectedProgressBars(goal_id)
                
                # Also update timeline if it's active
                if self.tab_widget.currentIndex() == 1:
                    self.timeline_widget.updateTimeline(self.goals)
                    
            except Exception as e:
                # Re-enable signals in case of exception
                self.goal_tree.blockSignals(False)
                print(f"Error in handleItemStatusChanged: {e}")
                import traceback
                traceback.print_exc()

    def updateItemAppearance(self, item, completed):
        """Update the visual appearance of an item after status change."""
        try:
            # Get goal ID
            goal_id = item.data(0, Qt.ItemDataRole.UserRole)
            
            # Find goal data
            goal = None
            for g in self.goals:
                if g['id'] == goal_id:
                    goal = g
                    break
                    
            if not goal:
                return
                
            # Update text color based on completion status
            if completed:
                item.setForeground(0, QColor("#047857"))  # Dark green text
                
                # Add checkmark icon
                check_icon = QIcon.fromTheme("emblem-ok", QIcon())
                if not check_icon.isNull():
                    item.setIcon(0, check_icon)
            else:
                # Reset to black text
                item.setForeground(0, QColor("#000000"))  # Black text
                item.setIcon(0, QIcon())  # Remove icon
            
            # Recalculate progress
            progress = self.calculateGoalProgress(goal)
            
            # Store progress for the progress bar
            item.setData(3, Qt.ItemDataRole.UserRole, progress)
            
            # Update the progress text
            item.setText(3, f"{progress}%")
            
            # Re-create the progress bar widget
            self._processTreeItemProgress(item)
        except Exception as e:
            print(f"Error updating item appearance: {e}")

    def updateAffectedProgressBars(self, goal_id):
        """Update progress bars for a goal and its parents."""
        try:
            # First find the goal
            goal = None
            for g in self.goals:
                if g['id'] == goal_id:
                    goal = g
                    break
                    
            if not goal:
                return
                
            # If it has a parent, update parent progress bars recursively
            if goal['parent_id'] is not None:
                parent_item = self.findParentItem(goal['parent_id'])
                if parent_item:
                    self.updateItemProgressBar(parent_item)
                    self.updateAffectedProgressBars(goal['parent_id'])
        except Exception as e:
            print(f"Error updating affected progress bars: {e}")

    def updateItemProgressBar(self, item):
        """Update the progress bar for a specific item."""
        try:
            goal_id = item.data(0, Qt.ItemDataRole.UserRole)
            
            # Find goal
            goal = None
            for g in self.goals:
                if g['id'] == goal_id:
                    goal = g
                    break
                    
            if not goal:
                return
                
            # Recalculate progress
            progress = self.calculateGoalProgress(goal)
            
            # Store progress for the progress bar
            item.setData(3, Qt.ItemDataRole.UserRole, progress)
            
            # Update the progress text
            item.setText(3, f"{progress}%")
            
            # Re-create the progress bar widget
            self._processTreeItemProgress(item)
        except Exception as e:
            print(f"Error updating item progress bar: {e}")
    
    def uncheckParent(self, parent_item):
        """Uncheck parent and propagate up the hierarchy when a child is unchecked."""
        try:
            # Only need to uncheck if parent is currently checked
            if parent_item.checkState(4) == Qt.CheckState.Checked:
                # Set parent to unchecked
                parent_item.setCheckState(4, Qt.CheckState.Unchecked)
                
                # Update the parent goal in our data
                parent_id = parent_item.data(0, Qt.ItemDataRole.UserRole)
                for goal in self.goals:
                    if goal['id'] == parent_id:
                        goal['completed'] = False
                        break
                
                # Update parent in database
                if hasattr(self.parent, 'conn') and self.parent.conn:
                    try:
                        self.parent.cursor.execute("""
                            UPDATE goals
                            SET completed = 0
                            WHERE id = ?
                        """, (parent_id,))
                        self.parent.conn.commit()
                    except Exception as e:
                        print(f"Error updating parent goal status in database: {e}")
                
                # Recursively uncheck grandparent if needed
                grandparent_item = parent_item.parent()
                if grandparent_item:
                    self.uncheckParent(grandparent_item)
        except Exception as e:
            print(f"Error in uncheckParent: {e}")
    
    def checkParentIfAllChildrenCompleted(self, parent_item):
        """Check parent item if all children are checked."""
        try:
            # Check if all children are completed
            all_children_completed = True
            for i in range(parent_item.childCount()):
                if parent_item.child(i).checkState(4) != Qt.CheckState.Checked:
                    all_children_completed = False
                    break
            
            # If all children are completed, check the parent
            if all_children_completed:
                parent_item.setCheckState(4, Qt.CheckState.Checked)
                
                # Update the parent goal in our data
                parent_id = parent_item.data(0, Qt.ItemDataRole.UserRole)
                for goal in self.goals:
                    if goal['id'] == parent_id:
                        goal['completed'] = True
                        break
                
                # Update parent in database
                if hasattr(self.parent, 'conn') and self.parent.conn:
                    try:
                        self.parent.cursor.execute("""
                            UPDATE goals
                            SET completed = 1
                            WHERE id = ?
                        """, (parent_id,))
                        self.parent.conn.commit()
                    except Exception as e:
                        print(f"Error updating parent goal status in database: {e}")
                
                # Recursively check grandparent if needed
                grandparent_item = parent_item.parent()
                if grandparent_item:
                    self.checkParentIfAllChildrenCompleted(grandparent_item)
        except Exception as e:
            print(f"Error in checkParentIfAllChildrenCompleted: {e}")
    
    def updateChildrenStatus(self, parent_item, status):
        """Update the status of all children when parent status changes."""
        try:
            # Collect all goal IDs to update
            updated_goal_ids = []
            
            def collectChildrenIds(item, child_ids):
                try:
                    for i in range(item.childCount()):
                        child = item.child(i)
                        child.setCheckState(4, status)
                        
                        # Get goal ID
                        goal_id = child.data(0, Qt.ItemDataRole.UserRole)
                        if goal_id:
                            child_ids.append(goal_id)
                        
                        # Recurse for sub-goals
                        if child.childCount() > 0:
                            collectChildrenIds(child, child_ids)
                except Exception as e:
                    print(f"Error collecting child IDs: {e}")
                
            # Collect all goal IDs to update
            collectChildrenIds(parent_item, updated_goal_ids)
            
            if not updated_goal_ids:
                return  # No children to update
            
            # Batch update goals in memory
            completed_value = (status == Qt.CheckState.Checked)
            for goal_id in updated_goal_ids:
                for goal in self.goals:
                    if goal['id'] == goal_id:
                        goal['completed'] = completed_value
                        # Emit signal
                        self.goalCompleted.emit(goal_id, completed_value)
                        break
            
            # Batch update database if connection exists
            if updated_goal_ids and hasattr(self.parent, 'conn') and self.parent.conn:
                try:
                    # Use a parameterized query with multiple value sets
                    completed_int = 1 if completed_value else 0
                    for goal_id in updated_goal_ids:
                        self.parent.cursor.execute("""
                            UPDATE goals
                            SET completed = ?
                            WHERE id = ?
                        """, (completed_int, goal_id))
                    self.parent.conn.commit()
                except Exception as e:
                    print(f"Error batch updating goal statuses in database: {e}")
        except Exception as e:
            print(f"Error in updateChildrenStatus: {e}")
    
    def updateParentProgress(self, goal_id):
        """Update the parent goal's progress when a subgoal status changes."""
        # Find the goal
        goal = None
        for g in self.goals:
            if g['id'] == goal_id:
                goal = g
                break
        
        if not goal or goal['parent_id'] is None:
            return
            
        # Find the parent goal
        parent_id = goal['parent_id']
        parent_goal = None
        for g in self.goals:
            if g['id'] == parent_id:
                parent_goal = g
                break
                
        if not parent_goal:
            return
        
        # Find parent item in the tree
        parent_item = self.findParentItem(parent_id)
        if parent_item:
            # Recalculate parent progress
            parent_progress = self.calculateGoalProgress(parent_goal)
            parent_item.setText(3, f"{parent_progress}%")
            
            # Update color based on progress
            if parent_progress < 30:
                parent_item.setForeground(3, QColor("#EF4444"))  # Red for low progress
            elif parent_progress < 70:
                parent_item.setForeground(3, QColor("#F59E0B"))  # Orange/Yellow for medium progress
            else:
                parent_item.setForeground(3, QColor("#10B981"))  # Green for high progress
            
            # Recursively update grandparent if needed
            self.updateParentProgress(parent_id)
    
    def showContextMenu(self, position):
        """Show a context menu for the selected goal."""
        item = self.goal_tree.itemAt(position)
        if not item:
            return
            
        goal_id = item.data(0, Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        edit_action = menu.addAction("Edit Goal")
        edit_action.triggered.connect(lambda: self.showEditGoalDialog(goal_id))
        
        delete_action = menu.addAction("Delete Goal")
        delete_action.triggered.connect(lambda: self.deleteGoal(goal_id))
        
        add_subgoal_action = menu.addAction("Add Sub-Goal")
        add_subgoal_action.triggered.connect(lambda: self.showAddSubGoalDialog(goal_id))
        
        menu.exec(self.goal_tree.viewport().mapToGlobal(position))
    
    def showEditGoalDialog(self, goal_id):
        """Show dialog to edit an existing goal."""
        # Find the goal
        goal = None
        for g in self.goals:
            if g['id'] == goal_id:
                goal = g
                break
        
        if not goal:
            return
        
        dialog = AddGoalDialog(self, f"Edit Goal: {goal['title']}", goal)
        
        # Add existing goals as potential parents (except self and descendants)
        for g in self.goals:
            if g['id'] != goal_id and g['id'] not in self.findSubGoalIds(goal_id):
                dialog.parent_input.addItem(g['title'], g['id'])
        
        # Set current parent
        index = dialog.parent_input.findData(goal['parent_id'])
        if index >= 0:
            dialog.parent_input.setCurrentIndex(index)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.updateGoal(goal_id, dialog.getGoalData())
    
    def updateGoal(self, goal_id, goal_data):
        """Update an existing goal."""
        title = goal_data['title']
        parent_id = goal_data['parent_id']
        created_date = goal_data['created_date']
        due_date = goal_data['due_date']
        due_time = goal_data['due_time']
        priority = goal_data['priority']
        
        if not title:
            QMessageBox.warning(self, "Error", "Goal title cannot be empty")
            return
        
        # Update in database if connection exists
        if hasattr(self.parent, 'conn') and self.parent.conn:
            try:
                # Check if created_date column exists, if not add it
                try:
                    self.parent.cursor.execute("SELECT created_date FROM goals LIMIT 1")
                except:
                    self.parent.cursor.execute("ALTER TABLE goals ADD COLUMN created_date TEXT")
                    self.parent.conn.commit()
                    
                self.parent.cursor.execute("""
                    UPDATE goals
                    SET title = ?, parent_id = ?, created_date = ?, due_date = ?, due_time = ?, priority = ?
                    WHERE id = ?
                """, (title, parent_id, created_date, due_date, due_time, priority, goal_id))
                self.parent.conn.commit()
            except Exception as e:
                print(f"Error updating goal in database: {e}")
                
        # Update the goal in our list
        for goal in self.goals:
            if goal['id'] == goal_id:
                goal['title'] = title
                goal['parent_id'] = parent_id
                goal['created_date'] = created_date
                goal['due_date'] = due_date
                goal['due_time'] = due_time
                goal['priority'] = priority
                break
        
        # Refresh the tree
        self.refreshGoalTree()
        
        # Update timeline if it's the current tab
        if self.tab_widget.currentIndex() == 1:
            self.timeline_widget.updateTimeline(self.goals)
    
    def deleteGoal(self, goal_id):
        """Delete a goal and its sub-goals."""
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            "Are you sure you want to delete this goal and all its sub-goals?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Find all sub-goals
        sub_goal_ids = self.findSubGoalIds(goal_id)
        all_ids = [goal_id] + sub_goal_ids
        
        # Delete from database if connection exists
        if hasattr(self.parent, 'conn') and self.parent.conn:
            try:
                # Delete all subgoals and the main goal
                for gid in all_ids:
                    self.parent.cursor.execute("DELETE FROM goals WHERE id = ?", (gid,))
                self.parent.conn.commit()
            except Exception as e:
                print(f"Error deleting goals from database: {e}")
        
        # Delete the goal and sub-goals from our list
        self.goals = [g for g in self.goals if g['id'] not in all_ids]
        
        # Refresh the tree
        self.refreshGoalTree()
        
        # Emit signal
        self.goalDeleted.emit(goal_id)
    
    def findSubGoalIds(self, parent_id):
        """Find all sub-goal IDs for a given parent ID."""
        sub_goal_ids = []
        
        for goal in self.goals:
            if goal['parent_id'] == parent_id:
                sub_goal_ids.append(goal['id'])
                # Recursively find sub-sub-goals
                sub_goal_ids.extend(self.findSubGoalIds(goal['id']))
        
        return sub_goal_ids
    
    def showAddSubGoalDialog(self, parent_id):
        """Show dialog to add a sub-goal."""
        # Find parent goal to get defaults
        parent_goal = None
        for g in self.goals:
            if g['id'] == parent_id:
                parent_goal = g
                break

        if not parent_goal:
            return
        
        # Create a goal data object with parent's dates as defaults
        parent_due_date = QDate.fromString(parent_goal['due_date'], "yyyy-MM-dd")
        
        # Default created_date based on existing subgoals
        sub_goals = [g for g in self.goals if g['parent_id'] == parent_id]
        
        if sub_goals:
            # Start after the last subgoal ends
            last_subgoal = max(sub_goals, key=lambda g: g['due_date'])
            created_date = QDate.fromString(last_subgoal['due_date'], "yyyy-MM-dd")
            due_date = created_date.addDays(7)  # End a week after start
        else:
            # First subgoal starts at parent's start and ends halfway to parent's end
            if 'created_date' in parent_goal and parent_goal['created_date']:
                created_date = QDate.fromString(parent_goal['created_date'], "yyyy-MM-dd")
            else:
                created_date = parent_due_date.addDays(-14)  # Default 2 weeks before due
            
            # End halfway between start and parent due date
            days_span = created_date.daysTo(parent_due_date)
            due_date = created_date.addDays(days_span // 2)
        
        default_data = {
            'parent_id': parent_id,
            'created_date': created_date.toString("yyyy-MM-dd"),
            'due_date': due_date.toString("yyyy-MM-dd"),
            'priority': parent_goal['priority']
        }
        
        dialog = AddGoalDialog(self, "Add Sub-Goal", default_data)
        
        # Set parent as readonly
        dialog.parent_input.clear()
        dialog.parent_input.addItem(parent_goal['title'], parent_id)
        dialog.parent_input.setEnabled(False)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.addGoal(dialog.getGoalData())
    
    def refreshGoalTree(self):
        """Refresh the entire goal tree."""
        try:
            # Block signals temporarily while rebuilding the tree
            self.goal_tree.blockSignals(True)
            
            # Store current expanded state if needed
            expanded_items = {}
            selection = self.goal_tree.selectedItems()
            selected_id = None
            if selection:
                selected_id = selection[0].data(0, Qt.ItemDataRole.UserRole)
            
            # Clear existing items
            self.goal_tree.clear()
            
            # Pre-calculate progress for all goals to avoid redundant calculations
            goal_progress = {}
            try:
                for goal in self.goals:
                    goal_progress[goal['id']] = self.calculateGoalProgress(goal)
            except Exception as e:
                print(f"Error calculating goal progress: {e}")
            
            # Keep track of already added goals to prevent duplicates
            added_goal_ids = set()
            
            # First add all root goals
            root_goals = [g for g in self.goals if g['parent_id'] is None]
            for goal in root_goals:
                try:
                    item = self.addGoalToTreeOptimized(goal, None, goal_progress)
                    added_goal_ids.add(goal['id'])
                    
                    # Then add their sub-goals recursively (tracking added IDs)
                    self.addSubGoalsToTreeOptimized(goal['id'], item, added_goal_ids, goal_progress)
                except Exception as e:
                    print(f"Error adding root goal {goal['id']} to tree: {e}")
            
            # Create progress bar widgets for all items
            self.postProcessTreeItems()
                
            # Reselect previously selected item if it exists
            if selected_id:
                self.selectGoalItemById(selected_id)
            
            # Restore expanded state if needed
            
            # Finally, ensure everything is visible
            self.goal_tree.expandAll()
            
        except Exception as e:
            print(f"Error refreshing goal tree: {e}")
        finally:
            # Unblock signals
            self.goal_tree.blockSignals(False)

    def postProcessTreeItems(self):
        """Process all tree items to add custom widgets for progress."""
        # Create a custom progress widget for each item
        for i in range(self.goal_tree.topLevelItemCount()):
            top_item = self.goal_tree.topLevelItem(i)
            self._processTreeItemProgress(top_item)
            
    def _processTreeItemProgress(self, item):
        """Recursively process tree items to add progress bars."""
        try:
            # Get the progress value stored in the item data
            progress = item.data(3, Qt.ItemDataRole.UserRole)
            
            if progress is not None:
                # Create a progress bar widget
                progress_widget = QWidget()
                progress_layout = QHBoxLayout(progress_widget)
                progress_layout.setContentsMargins(4, 2, 4, 2)
                progress_layout.setSpacing(8)
                
                # Create the progress bar using QProgressBar
                progress_bar = QProgressBar(progress_widget)
                progress_bar.setFixedHeight(12)
                progress_bar.setTextVisible(False)
                progress_bar.setMinimumWidth(60)
                progress_bar.setValue(int(progress))
                
                # Set color based on progress
                if progress < 30:
                    # Red for low progress
                    style_color = """
                        QProgressBar {
                            background-color: #FEE2E2;
                            border-radius: 6px;
                            border: none;
                        }
                        QProgressBar::chunk {
                            background-color: #EF4444;
                            border-radius: 6px;
                        }
                    """
                    text_color = "#EF4444"
                elif progress < 70:
                    # Yellow/Orange for medium progress
                    style_color = """
                        QProgressBar {
                            background-color: #FEF3C7;
                            border-radius: 6px;
                            border: none;
                        }
                        QProgressBar::chunk {
                            background-color: #F59E0B;
                            border-radius: 6px;
                        }
                    """
                    text_color = "#F59E0B"
                else:
                    # Green for high progress
                    style_color = """
                        QProgressBar {
                            background-color: #D1FAE5;
                            border-radius: 6px;
                            border: none;
                        }
                        QProgressBar::chunk {
                            background-color: #10B981;
                            border-radius: 6px;
                        }
                    """
                    text_color = "#10B981"
                    
                # Apply styling
                progress_bar.setStyleSheet(style_color)
                
                # Add progress bar to layout
                progress_layout.addWidget(progress_bar, 7)  # 70% width for bar
                
                # Add text label
                text_label = QLabel(f"{int(progress)}%")
                text_label.setStyleSheet(f"color: {text_color}; font-weight: bold;")
                progress_layout.addWidget(text_label, 3)  # 30% width for text
                
                # Set the widget in the tree
                self.goal_tree.setItemWidget(item, 3, progress_widget)
            
            # Process children recursively
            for i in range(item.childCount()):
                child = item.child(i)
                self._processTreeItemProgress(child)
        except Exception as e:
            print(f"Error processing tree item progress: {e}")
    
    def selectGoalItemById(self, goal_id):
        """Find and select a goal item by ID."""
        try:
            # Search in all top-level items
            for i in range(self.goal_tree.topLevelItemCount()):
                top_item = self.goal_tree.topLevelItem(i)
                if self.findAndSelectItem(top_item, goal_id):
                    return True
            return False
        except Exception as e:
            print(f"Error selecting goal item: {e}")
            return False
    
    def findAndSelectItem(self, item, goal_id):
        """Recursively search for and select an item by goal ID."""
        try:
            # Check if this is the item we're looking for
            if item.data(0, Qt.ItemDataRole.UserRole) == goal_id:
                self.goal_tree.setCurrentItem(item)
                return True
                
            # Search children
            for i in range(item.childCount()):
                if self.findAndSelectItem(item.child(i), goal_id):
                    return True
                    
            return False
        except Exception as e:
            print(f"Error finding item: {e}")
            return False

    def addGoalToTreeOptimized(self, goal, parent_item=None, goal_progress=None):
        """Add a goal to the tree widget with optimized progress calculation.
        
        Args:
            goal: The goal to add
            parent_item: The parent tree item (if any)
            goal_progress: Pre-calculated progress values (optimization)
            
        Returns:
            QTreeWidgetItem: The created tree item
        """
        # Create item
        item = QTreeWidgetItem()
        
        # Get progress
        progress = goal_progress.get(goal['id']) if goal_progress is not None else self.calculateGoalProgress(goal)
        
        # Set item data
        item.setData(0, Qt.ItemDataRole.UserRole, goal['id'])
        item.setText(0, goal['title'])
        item.setText(1, goal.get('due_date', ''))
        item.setText(2, goal.get('due_time', ''))
        
        # Create a custom progress display with visual indicator and text
        progress_text = f"{progress}%"
        item.setText(3, progress_text)
        
        # Create status checkbox (column 4)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        check_state = Qt.CheckState.Checked if goal['completed'] else Qt.CheckState.Unchecked
        item.setCheckState(4, check_state)
        
        # Set progress text color based on percentage
        if progress < 30:
            progress_color = QColor("#EF4444")  # Red for low progress
        elif progress < 70:
            progress_color = QColor("#F59E0B")  # Orange/Yellow for medium progress
        else:
            progress_color = QColor("#10B981")  # Green for high progress
        
        item.setForeground(3, progress_color)
        
        # Create and set a custom progress widget for the progress column
        # (This will be created when item is added to tree in postProcessTreeItems)
        item.setData(3, Qt.ItemDataRole.UserRole, progress)
        
        # Apply custom styling based on completion status but without backgrounds
        if goal['completed']:
            # Set completed item text to dark green without background
            item.setForeground(0, QColor("#047857"))  # Dark green text
            
            # Add a checkmark icon to column 0
            check_icon = QIcon.fromTheme("emblem-ok", QIcon())
            if not check_icon.isNull():
                item.setIcon(0, check_icon)
        else:
            # Set text to black for all other items
            item.setForeground(0, QColor("#000000"))  # Black text
        
        # Add to parent or root
        if parent_item:
            # If parent is provided, add as child of parent
            parent_item.addChild(item)
        else:
            # No parent item provided, add at top level
            self.goal_tree.addTopLevelItem(item)
        
        # Apply visual indication for a goal with subgoals
        font = item.font(0)
        if any(g['parent_id'] == goal['id'] for g in self.goals):
            font.setBold(True)
            item.setFont(0, font)
        
        return item
        
    def addSubGoalsToTreeOptimized(self, parent_id, parent_item, added_goal_ids=None, goal_progress=None):
        """Optimized version of addSubGoalsToTree using pre-calculated progress."""
        # Initialize tracking set if not provided
        if added_goal_ids is None:
            added_goal_ids = set()
        
        # Get all direct sub-goals of the parent
        sub_goals = [g for g in self.goals if g['parent_id'] == parent_id]
        
        # Sort by due date
        sub_goals.sort(key=lambda g: g['due_date'])
        
        # Add each sub-goal to the tree (if not already added)
        for goal in sub_goals:
            if goal['id'] in added_goal_ids:
                print(f"Warning: Skipping duplicate goal: {goal['title']} (ID: {goal['id']})")
                continue
            
            # Add the sub-goal as a child of the parent item
            item = self.addGoalToTreeOptimized(goal, parent_item, goal_progress)
            added_goal_ids.add(goal['id'])
            
            # Recursively add this goal's sub-goals
            self.addSubGoalsToTreeOptimized(goal['id'], item, added_goal_ids, goal_progress)
            
    def loadGoals(self):
        """Load goals from the database."""
        if hasattr(self.parent, 'cursor') and self.parent.cursor:
            try:
                # Check if created_date column exists, if not add it
                try:
                    self.parent.cursor.execute("SELECT created_date FROM goals LIMIT 1")
                except:
                    self.parent.cursor.execute("ALTER TABLE goals ADD COLUMN created_date TEXT")
                    self.parent.conn.commit()
                
                # Execute SQL to get all goals
                self.parent.cursor.execute("""
                    SELECT id, title, parent_id, created_date, due_date, due_time, priority, completed 
                    FROM goals
                    ORDER BY due_date
                """)
                
                # Process results
                results = self.parent.cursor.fetchall()
                
                # Clear existing goals
                self.goals = []
                
                # Process results
                for row in results:
                    goal = {
                        'id': row[0],
                        'title': row[1],
                        'parent_id': row[2],
                        'created_date': row[3],
                        'due_date': row[4],
                        'due_time': row[5],
                        'priority': row[6],
                        'completed': bool(row[7])
                    }
                    self.goals.append(goal)
                
                # Refresh the tree
                self.refreshGoalTree()
            except Exception as e:
                print(f"Error loading goals: {e}")
                # Add some sample goals for testing
                self.addSampleGoals()
        else:
            # Add some sample goals for testing
            self.addSampleGoals()
    
    def addSampleGoals(self):
        """Add sample goals for testing."""
        # Add sample goals
        self.goals = [
            {
                'id': 1,
                'parent_id': None,
                'title': 'Learn Python',
                'created_date': '2023-01-01',
                'due_date': '2023-12-31',
                'due_time': '23:59',
                'priority': 2,
                'completed': False
            },
            {
                'id': 2,
                'parent_id': 1,
                'title': 'Complete Python Tutorial',
                'created_date': '2023-01-15',
                'due_date': '2023-06-30',
                'due_time': '23:59',
                'priority': 1,
                'completed': True
            },
            {
                'id': 3,
                'parent_id': 1,
                'title': 'Build a Python Project',
                'created_date': '2023-07-01',
                'due_date': '2023-09-30',
                'due_time': '23:59',
                'priority': 1,
                'completed': False
            }
        ]
        
        # Refresh the tree with these goals
        self.refreshGoalTree()
        
    def selectGoalById(self, goal_id):
        """Find and select a goal by its ID in the goal tree.
        
        Args:
            goal_id: The ID of the goal to select
            
        Returns:
            bool: True if the goal was found and selected, False otherwise
        """
        # Switch to the tree tab first
        self.tab_widget.setCurrentIndex(0)
        
        # Iterate through top-level items
        for i in range(self.goal_tree.topLevelItemCount()):
            top_item = self.goal_tree.topLevelItem(i)
            item_id = top_item.data(0, Qt.ItemDataRole.UserRole)
            
            if item_id == goal_id:
                self.goal_tree.setCurrentItem(top_item)
                self.goal_tree.scrollToItem(top_item)
                return True
            
            # Check children recursively
            if self.findAndSelectItem(top_item, goal_id):
                return True
                
        return False
    
    def refresh(self):
        """Refresh the widget's data."""
        # Load all goals from the database
        self.loadGoals()
        
        # Make sure tree is expanded to show all items
        self.goal_tree.expandAll()
        
        # If timeline tab is active, update the timeline view
        if self.tab_widget.currentIndex() == 1:
            self.timeline_widget.updateTimeline(self.goals) 

    def findParentItem(self, parent_id):
        """Find a parent item by ID in the entire tree.
        
        Args:
            parent_id: The ID of the parent goal to find
            
        Returns:
            The QTreeWidgetItem if found, or None
        """
        # Search in all top level items
        for i in range(self.goal_tree.topLevelItemCount()):
            top_item = self.goal_tree.topLevelItem(i)
            if top_item.data(0, Qt.ItemDataRole.UserRole) == parent_id:
                return top_item
            
            # Search in children recursively
            found_item = self._findParentItemRecursive(top_item, parent_id)
            if found_item:
                return found_item
            
        return None

    def _findParentItemRecursive(self, item, parent_id):
        """Recursively search for parent item by ID.
        
        Args:
            item: The QTreeWidgetItem to search in
            parent_id: The ID of the parent goal to find
            
        Returns:
            The QTreeWidgetItem if found, or None
        """
        # Check if this item is the parent
        if item.data(0, Qt.ItemDataRole.UserRole) == parent_id:
            return item
        
        # Search in children
        for i in range(item.childCount()):
            child = item.child(i)
            found_item = self._findParentItemRecursive(child, parent_id)
            if found_item:
                return found_item
        
        return None

    def addSubGoal(self, dialog, parent_id):
        """Add a sub-goal."""
        title = self.subgoal_title_input.text().strip()
        due_date = self.subgoal_date_input.date().toString("yyyy-MM-dd")
        due_time = self.subgoal_time_input.time().toString("HH:mm")
        priority = self.subgoal_priority_input.currentIndex()
        
        if not title:
            QMessageBox.warning(dialog, "Error", "Goal title cannot be empty")
            return
        
        # Save to database if connection exists
        goal_id = None
        if hasattr(self.parent, 'conn') and self.parent.conn:
            try:
                self.parent.cursor.execute("""
                    INSERT INTO goals (title, parent_id, due_date, due_time, priority, completed)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (title, parent_id, due_date, due_time, priority))
                self.parent.conn.commit()
                goal_id = self.parent.cursor.lastrowid
            except Exception as e:
                print(f"Error saving subgoal to database: {e}")
                # Fall back to random ID
                goal_id = random.randint(1000, 9999)
        else:
            # For testing when no database connection
            goal_id = random.randint(1000, 9999)
        
        # Create the goal dictionary
        goal = {
            'id': goal_id,
            'title': title,
            'parent_id': parent_id,
            'due_date': due_date,
            'due_time': due_time,
            'priority': priority,
            'completed': False
        }
        
        # Add to our list
        self.goals.append(goal)
        
        # Refresh the tree
        self.refreshGoalTree()
        
        # Emit signal
        self.goalAdded.emit(goal)
        
        # Close the dialog
        dialog.accept() 

    def handleSearchTextChanged(self, text):
        """Handle search input changes and filter goals accordingly."""
        if text.strip():
            self.applyFilters()
        else:
            # If search field is cleared, reapply any other active filters
            # or reset if no other filters
            if not self.hasActiveFilters():
                self.resetFilters()
            else:
                self.applyFilters()

    def handleSearchButtonClicked(self):
        """Handle search button clicks."""
        search_text = self.search_input.text().strip()
        if search_text:
            self.applyFilters()
            
    def showFilterMenu(self):
        """Show the filter menu when filter button is clicked."""
        self.filter_menu.exec(self.filter_btn.mapToGlobal(QPoint(0, self.filter_btn.height())))

    def filterByCompletionStatus(self, completed):
        """Filter goals by completion status."""
        # Uncheck other status actions
        for action in [self.action_all_goals, self.action_completed, self.action_incomplete]:
            action.setChecked(False)
            
        # Check the selected action
        if completed is None:
            self.action_all_goals.setChecked(True)
        elif completed:
            self.action_completed.setChecked(True)
        else:
            self.action_incomplete.setChecked(True)
            
        # Apply the filter
        self.applyFilters()
        
    def filterByPriority(self, priority):
        """Filter goals by priority level."""
        # Uncheck other priority actions
        for action in [self.action_all_priorities, self.action_low_priority, 
                      self.action_medium_priority, self.action_high_priority]:
            action.setChecked(False)
            
        # Check the selected action
        if priority is None:
            self.action_all_priorities.setChecked(True)
        elif priority == 0:
            self.action_low_priority.setChecked(True)
        elif priority == 1:
            self.action_medium_priority.setChecked(True)
        else:
            self.action_high_priority.setChecked(True)
            
        # Apply the filter
        self.applyFilters()
        
    def resetFilters(self):
        """Reset all filters to default values."""
        # Clear search field
        self.search_input.clear()
        
        # Reset completion status
        self.action_all_goals.setChecked(True)
        self.action_completed.setChecked(False)
        self.action_incomplete.setChecked(False)
        
        # Reset priority
        self.action_all_priorities.setChecked(True)
        self.action_low_priority.setChecked(False)
        self.action_medium_priority.setChecked(False)
        self.action_high_priority.setChecked(False)
        
        # Hide filter indicators
        self.clear_filters_btn.setVisible(False)
        self.filter_status_label.setVisible(False)
        
        # Refresh the tree with all goals
        self.refreshGoalTree()
        
    def hasActiveFilters(self):
        """Check if any filters are currently active."""
        # Check search text
        if self.search_input.text().strip():
            return True
            
        # Check completion status
        if not self.action_all_goals.isChecked():
            return True
            
        # Check priority
        if not self.action_all_priorities.isChecked():
            return True
            
        return False
        
    def applyFilters(self):
        """Apply all active filters to the goal tree."""
        try:
            # Get filter values
            search_text = self.search_input.text().lower().strip()
            
            # Get completion status filter
            if self.action_completed.isChecked():
                completion_filter = True
            elif self.action_incomplete.isChecked():
                completion_filter = False
            else:
                completion_filter = None
                
            # Get priority filter
            if self.action_low_priority.isChecked():
                priority_filter = 0
            elif self.action_medium_priority.isChecked():
                priority_filter = 1
            elif self.action_high_priority.isChecked():
                priority_filter = 2
            else:
                priority_filter = None
                
            # Update filter status UI
            self.updateFilterStatusUI(search_text, completion_filter, priority_filter)
            
            # Filter the goals
            self.filterGoalTree(search_text, completion_filter, priority_filter)
            
        except Exception as e:
            print(f"Error applying filters: {e}")
            import traceback
            traceback.print_exc()
            
    def updateFilterStatusUI(self, search_text, completion_filter, priority_filter):
        """Update UI to reflect active filters."""
        has_filters = False
        filter_descriptions = []
        
        # Check search filter
        if search_text:
            has_filters = True
            filter_descriptions.append(f'Search: "{search_text}"')
            
        # Check completion filter
        if completion_filter is not None:
            has_filters = True
            status = "Completed" if completion_filter else "Incomplete"
            filter_descriptions.append(f"Status: {status}")
            
        # Check priority filter
        if priority_filter is not None:
            has_filters = True
            priority_names = {0: "Low", 1: "Medium", 2: "High"}
            filter_descriptions.append(f"Priority: {priority_names[priority_filter]}")
            
        # Update UI based on filter state
        if has_filters:
            self.clear_filters_btn.setVisible(True)
            self.filter_status_label.setText("Active filters: " + ", ".join(filter_descriptions))
            self.filter_status_label.setVisible(True)
        else:
            self.clear_filters_btn.setVisible(False)
            self.filter_status_label.setVisible(False)
            
    def filterGoalTree(self, search_text, completion_filter, priority_filter):
        """Filter the goal tree based on the given criteria."""
        try:
            # Block signals temporarily while rebuilding the tree
            self.goal_tree.blockSignals(True)
            
            # Store current expanded state if needed
            expanded_items = {}
            selection = self.goal_tree.selectedItems()
            selected_id = None
            if selection:
                selected_id = selection[0].data(0, Qt.ItemDataRole.UserRole)
            
            # Clear existing items
            self.goal_tree.clear()
            
            # Filter goals based on criteria
            filtered_goals = self.filterGoals(search_text, completion_filter, priority_filter)
            
            # Find root goals after filtering (those with parent_id None or parent not in filtered list)
            root_goals = [g for g in filtered_goals if g['parent_id'] is None]
            
            # Also include goals whose parents aren't in the filtered list as roots
            parent_ids = {g['id'] for g in filtered_goals}
            orphaned_goals = [g for g in filtered_goals 
                             if g['parent_id'] is not None and g['parent_id'] not in parent_ids]
            root_goals.extend(orphaned_goals)
            
            # Pre-calculate progress for all filtered goals
            goal_progress = {}
            for goal in filtered_goals:
                goal_progress[goal['id']] = self.calculateGoalProgress(goal)
            
            # Add root goals to tree
            added_goal_ids = set()
            for goal in root_goals:
                try:
                    item = self.addGoalToTreeOptimized(goal, None, goal_progress)
                    added_goal_ids.add(goal['id'])
                    
                    # Find all children for this goal that are in the filtered list
                    children = [g for g in filtered_goals if g['parent_id'] == goal['id']]
                    
                    # Add children recursively
                    for child in children:
                        self.addFilteredSubGoals(child, item, filtered_goals, added_goal_ids, goal_progress)
                except Exception as e:
                    print(f"Error adding root goal {goal['id']} to tree: {e}")
                    
            # Create progress bar widgets for all items
            self.postProcessTreeItems()
                    
            # Reselect previously selected item if it exists
            if selected_id:
                self.selectGoalItemById(selected_id)
            
            # Expand all to show filtered results
            self.goal_tree.expandAll()
            
        except Exception as e:
            print(f"Error filtering goal tree: {e}")
        finally:
            # Unblock signals
            self.goal_tree.blockSignals(False)
            
    def addFilteredSubGoals(self, goal, parent_item, filtered_goals, added_goal_ids, goal_progress):
        """Add filtered subgoals to the tree."""
        try:
            # Add this goal as a child of parent_item
            if goal['id'] not in added_goal_ids:
                item = self.addGoalToTreeOptimized(goal, parent_item, goal_progress)
                added_goal_ids.add(goal['id'])
                
                # Find all children for this goal that are in the filtered list
                children = [g for g in filtered_goals if g['parent_id'] == goal['id']]
                
                # Add each child and its descendants
                for child in children:
                    self.addFilteredSubGoals(child, item, filtered_goals, added_goal_ids, goal_progress)
        except Exception as e:
            print(f"Error adding filtered subgoal {goal['id']}: {e}")
            
    def filterGoals(self, search_text, completion_filter, priority_filter):
        """Filter goals based on search text, completion status, and priority."""
        filtered_goals = []
        
        for goal in self.goals:
            # Apply search filter
            passes_search = True
            if search_text:
                # Search in title (could expand to search in description, etc.)
                if search_text not in goal['title'].lower():
                    passes_search = False
                    
            # Apply completion filter
            passes_completion = True
            if completion_filter is not None:
                if goal['completed'] != completion_filter:
                    passes_completion = False
                    
            # Apply priority filter
            passes_priority = True
            if priority_filter is not None:
                if goal['priority'] != priority_filter:
                    passes_priority = False
                    
            # Add to filtered list if passes all filters
            if passes_search and passes_completion and passes_priority:
                filtered_goals.append(goal)
                
        return filtered_goals