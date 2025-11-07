
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QFrame, QGraphicsView, QGraphicsScene,
                           QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem,
                           QGraphicsProxyWidget, QMenu, QDialog, QLineEdit,
                           QDialogButtonBox, QCheckBox, QGraphicsEllipseItem, QGraphicsPathItem)
from PyQt6.QtCore import Qt, QDate, QTime, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui import QFont, QColor, QPen, QBrush, QPainter, QPainterPath
from app.resources import get_icon
from app.models.activities_manager import ActivitiesManager
from .todo_item_dialog import TodoItemDialog

class DailyPlanView(QWidget):
    activityClicked = pyqtSignal(dict)
    activityCompletionChanged = pyqtSignal(int, bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_date = QDate.currentDate()
        self.activities = []
        self.activity_items = {}

        if hasattr(parent, 'activities_manager'):
            self.activities_manager = parent.activities_manager
        else:
            self.activities_manager = ActivitiesManager()

        self.setupUI()
        self.loadActivities()

    def setupUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        header_frame = QFrame(objectName="dailyHeader")
        header_frame.setProperty("data-card", "true")
        header_frame.setFixedHeight(70)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 5, 15, 5)

        prev_day_btn = QPushButton("◀ Previous Day")
        prev_day_btn.clicked.connect(self.previousDay)
        header_layout.addWidget(prev_day_btn)

        self.day_label = QLabel()
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day_label.setObjectName("dailyDayLabel")
        self.updateDayLabel()
        header_layout.addWidget(self.day_label, 1)

        next_day_btn = QPushButton("Next Day ▶")
        next_day_btn.clicked.connect(self.nextDay)
        header_layout.addWidget(next_day_btn)

        today_btn = QPushButton("Today")
        today_icon = get_icon("calendar-today")
        if not today_icon.isNull():
            today_btn.setIcon(today_icon)
        today_btn.clicked.connect(self.goToToday)
        header_layout.addWidget(today_btn)

        main_layout.addWidget(header_frame)

        self.view = QGraphicsView()
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # Enable smooth scrolling
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.view.setFrameShape(QFrame.Shape.StyledPanel)

        main_layout.addWidget(self.view, 1)

    def updateDayLabel(self):
        self.day_label.setText(self.current_date.toString("dddd, MMMM d, yyyy"))

    def previousDay(self):
        self.current_date = self.current_date.addDays(-1)
        self.updateDayLabel()
        self.loadActivities()

    def nextDay(self):
        self.current_date = self.current_date.addDays(1)
        self.updateDayLabel()
        self.loadActivities()

    def goToToday(self):
        self.current_date = QDate.currentDate()
        self.updateDayLabel()
        self.loadActivities()

    def loadActivities(self):
        self.activities = self.activities_manager.get_activities_for_date(self.current_date)
        self.updateDayView()

    def updateDayView(self):
        self.scene.clear()
        self.activity_items = {}
        self.drawDayGrid()
        self.addActivitiesToGrid()
        
        # Set scene rect to cover the full grid for proper scrolling
        # Calculate grid dimensions
        hour_height = 180
        grid_height = 24 * hour_height
        day_width = max(self.view.width() - 120, 800)
        hour_label_width = 90
        
        # Set scene rect to include full grid plus headers
        scene_rect = QRectF(0, -50, day_width + hour_label_width, grid_height + 50)
        self.view.setSceneRect(scene_rect)
        
        # Also ensure items bounding rect is included if items extend beyond
        if self.scene.items():
            items_rect = self.scene.itemsBoundingRect()
            # Combine both rects to ensure everything is visible
            combined_rect = scene_rect.united(items_rect)
            self.view.setSceneRect(combined_rect.adjusted(-20, -20, 20, 20))

    def drawDayGrid(self):
        hour_height = 180
        grid_height = 24 * hour_height
        day_width = max(self.view.width() - 120, 800)  # Minimum width for better display

        hour_label_width = 90
        hour_label_margin = 10

        # Day header background
        header_rect = QGraphicsRectItem(hour_label_width, -50, day_width, 50)
        header_rect.setPen(QPen(QColor("#D1D5DB")))
        header_rect.setBrush(QBrush(QColor("#E5E7EB")))
        self.scene.addItem(header_rect)

        # Day name and date in header
        day_text = self.current_date.toString("dddd, MMMM d, yyyy")
        day_label = QGraphicsTextItem(day_text)
        day_label.setPos(hour_label_width + (day_width - day_label.boundingRect().width()) / 2, -45)
        day_label.setDefaultTextColor(QColor("#1F2937"))
        font = day_label.font()
        font.setBold(True)
        font.setPointSize(14)
        day_label.setFont(font)
        
        # Highlight today
        if self.current_date == QDate.currentDate():
            today_rect = QGraphicsRectItem(hour_label_width, -50, day_width, 50)
            today_rect.setPen(QPen(QColor("#4F46E5"), 2))
            today_rect.setBrush(QBrush(QColor(99, 102, 241, 50)))
            self.scene.addItem(today_rect)
            day_label.setDefaultTextColor(QColor("#4F46E5"))
        
        self.scene.addItem(day_label)

        # Time axis background
        time_axis_bg = QGraphicsRectItem(0, -50, hour_label_width, grid_height + 50)
        time_axis_bg.setPen(QPen(Qt.PenStyle.NoPen))
        time_axis_bg.setBrush(QBrush(QColor("#F1F5F9")))
        time_axis_bg.setZValue(-2)
        self.scene.addItem(time_axis_bg)

        # Time axis header
        time_header = QGraphicsTextItem("Time")
        time_header.setPos(10, -35)
        time_header.setDefaultTextColor(QColor("#1F2937"))
        font = time_header.font()
        font.setBold(True)
        time_header.setFont(font)
        self.scene.addItem(time_header)

        # Draw hour rows
        for hour in range(25):
            y_pos = hour * hour_height
            row_line = QGraphicsLineItem(hour_label_width, y_pos, day_width + hour_label_width, y_pos)
            if hour % 6 == 0:
                row_line.setPen(QPen(QColor("#9CA3AF"), 1.5))
            else:
                row_line.setPen(QPen(QColor("#D1D5DB")))
            self.scene.addItem(row_line)

            if hour < 24:
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

        # Add work hours highlight (9 AM to 5 PM)
        work_start = 9
        work_end = 17
        work_highlight = QGraphicsRectItem(hour_label_width, work_start * hour_height, 
                                         day_width, (work_end - work_start) * hour_height)
        work_highlight.setPen(QPen(Qt.PenStyle.NoPen))
        work_highlight.setBrush(QBrush(QColor(243, 244, 246, 100)))
        work_highlight.setZValue(-1)
        self.scene.addItem(work_highlight)

        # Add half-hour markers
        for hour in range(24):
            y_pos = hour * hour_height + hour_height / 2
            half_hour_line = QGraphicsLineItem(hour_label_width, y_pos, 
                                             hour_label_width + day_width, y_pos)
            half_hour_line.setPen(QPen(QColor("#E5E7EB"), 1, Qt.PenStyle.DotLine))
            self.scene.addItem(half_hour_line)

        # Add now indicator if showing today
        if self.current_date == QDate.currentDate():
            current_time = QTime.currentTime()
            hour_decimal = current_time.hour() + current_time.minute() / 60.0
            now_y = hour_decimal * hour_height
            
            # Add subtle gradient background for current time
            now_rect = QGraphicsRectItem(hour_label_width, now_y - 1, day_width, 2)
            now_rect.setPen(QPen(Qt.PenStyle.NoPen))
            now_rect.setBrush(QBrush(QColor("#EF4444")))
            now_rect.setZValue(3)
            self.scene.addItem(now_rect)
            
            # Add a subtle circle indicator
            now_circle = QGraphicsEllipseItem(hour_label_width - 6, now_y - 6, 12, 12)
            now_circle.setBrush(QBrush(QColor("#EF4444")))
            now_circle.setPen(QPen(QColor("#FFFFFF"), 1.5))
            now_circle.setZValue(4)
            self.scene.addItem(now_circle)
            
            # Add a small "now" text
            now_label = QGraphicsTextItem("now")
            now_label.setDefaultTextColor(QColor("#EF4444"))
            now_label.setPos(hour_label_width - 30, now_y - 6)
            font = now_label.font()
            font.setBold(True)
            font.setPointSize(8)
            now_label.setFont(font)
            now_label.setZValue(4)
            self.scene.addItem(now_label)

    def addActivitiesToGrid(self):
        hour_height = 180
        day_width = max(self.view.width() - 120, 800)
        hour_label_width = 90

        # First, create timeboxes for each hour slot (even if empty)
        self.createTimeBoxes(hour_height, day_width, hour_label_width)

        # Then add activities on top of the timeboxes
        if not self.activities:
            return

        for activity in self.activities:
            start_time = activity.get('start_time')
            end_time = activity.get('end_time')

            if not start_time or not end_time:
                continue

            start_hour = start_time.hour() + start_time.minute() / 60.0
            end_hour = end_time.hour() + end_time.minute() / 60.0

            if end_hour <= start_hour:
                if end_hour == start_hour:
                    end_hour = start_hour + 0.5
                else:
                    end_hour += 24.0

            x_pos = hour_label_width
            y_pos = start_hour * hour_height
            height = (end_hour - start_hour) * hour_height

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

            margin = 4
            actual_x = x_pos + margin
            actual_width = day_width - 2 * margin

            is_completed = bool(activity.get('completed', False))

            if is_completed:
                color = color.lighter(110)
                color.setAlpha(180)
            else:
                color.setAlpha(200)

            # Add shadow effect
            shadow_path = QPainterPath()
            shadow_path.addRoundedRect(QRectF(actual_x + 2, y_pos + 2, actual_width, height), 8, 8)
            shadow_rect = self.scene.addPath(shadow_path, QPen(Qt.PenStyle.NoPen), 
                                           QBrush(QColor(0, 0, 0, 20)))
            shadow_rect.setZValue(0.5)

            # Create rounded rectangle path
            path = QPainterPath()
            path.addRoundedRect(QRectF(actual_x, y_pos, actual_width, height), 8, 8)

            rounded_rect = self.scene.addPath(path, QPen(color.darker(), 1.5), QBrush(color))
            rounded_rect.setData(0, activity.get('id'))
            rounded_rect.setData(1, activity.get('type'))
            rounded_rect.setZValue(1)
            rounded_rect.setAcceptHoverEvents(True)
            rounded_rect.setCursor(Qt.CursorShape.PointingHandCursor)

            # Add completion indicator
            if is_completed:
                complete_path = QPainterPath()
                complete_path.addRoundedRect(QRectF(actual_x, y_pos, 6, height), 3, 3)
                completion_bar = self.scene.addPath(
                    complete_path, 
                    QPen(Qt.PenStyle.NoPen), 
                    QBrush(QColor("#10B981"))
                )
                completion_bar.setZValue(2)

            # Add activity title
            title = activity.get('title', 'Untitled')
            title_text = QGraphicsTextItem(title)
            title_text.setTextWidth(actual_width - 20)
            
            # Truncate long titles
            if len(title) > 40:
                title = title[:37] + "..."
            
            html_text = f'<div style="max-width: {actual_width-20}px; word-wrap: break-word; color: white;">{title}</div>'
            title_text.setHtml(html_text)
            title_text.setPos(actual_x + 10, y_pos + 8)
            
            font = title_text.font()
            font.setBold(True)
            font.setPointSize(11)
            title_text.setFont(font)
            title_text.setZValue(2)
            
            # Add text background for better readability
            text_bg_height = min(title_text.boundingRect().height() + 16, height)
            text_bg = QGraphicsRectItem(actual_x, y_pos, actual_width, text_bg_height)
            text_bg.setPen(QPen(Qt.PenStyle.NoPen))
            darker_color = color.darker(150)
            darker_color.setAlpha(200)
            text_bg.setBrush(QBrush(darker_color))
            text_bg.setZValue(1.5)
            self.scene.addItem(text_bg)
            self.scene.addItem(title_text)

            # Add time text if enough space
            content_start_y = y_pos + text_bg_height + 4
            remaining_height = y_pos + height - content_start_y
            
            if remaining_height > 25 and actual_width > 60:
                time_text = QGraphicsTextItem(f"{start_time.toString('HH:mm')} - {end_time.toString('HH:mm')}")
                time_text.setTextWidth(actual_width - 20)
                time_text.setPos(actual_x + 10, content_start_y)
                time_text.setDefaultTextColor(QColor("#FFFFFF"))
                time_font = time_text.font()
                time_font.setBold(True)
                time_font.setPointSize(9)
                time_text.setFont(time_font)
                time_text.setZValue(2)
                self.scene.addItem(time_text)
                content_start_y += 20

            # Display To-Do items in a grid layout
            todo_items = self.activities_manager.get_todo_items(activity.get('id'))
            
            if todo_items:
                # Calculate grid layout: 2 columns for better fit
                items_per_row = 2
                todo_item_height = 22
                todo_item_spacing = 4
                todo_item_width = (actual_width - 16 - todo_item_spacing) // items_per_row
                
                # Calculate how many rows fit
                available_height = y_pos + height - content_start_y - 10
                max_rows = int(available_height / (todo_item_height + todo_item_spacing))
                max_items = max_rows * items_per_row
                
                # Limit items shown
                items_to_show = min(len(todo_items), max_items)
                
                for idx, (item_id, text, completed) in enumerate(todo_items[:items_to_show]):
                    if idx >= max_items:
                        break
                    
                    # Calculate grid position
                    row = idx // items_per_row
                    col = idx % items_per_row
                    
                    todo_x = actual_x + 8 + col * (todo_item_width + todo_item_spacing)
                    todo_y = content_start_y + 4 + row * (todo_item_height + todo_item_spacing)
                    
                    if todo_y + todo_item_height > y_pos + height - 10:
                        break  # Not enough space
                    
                    # Todo item background
                    todo_bg = QGraphicsRectItem(todo_x, todo_y, todo_item_width, todo_item_height)
                    todo_bg.setPen(QPen(QColor(255, 255, 255, 100), 1))
                    todo_bg.setBrush(QBrush(QColor(255, 255, 255, 30)))
                    todo_bg.setZValue(1.8)
                    todo_bg.setData(0, item_id)
                    todo_bg.setData(1, activity.get('id'))
                    todo_bg.setData(2, completed)
                    todo_bg.setData(3, "todo_bg")
                    todo_bg.setAcceptHoverEvents(True)
                    todo_bg.setCursor(Qt.CursorShape.PointingHandCursor)
                    self.scene.addItem(todo_bg)
                    
                    # Completion checkbox indicator (clickable)
                    checkbox_size = 14
                    checkbox_x = todo_x + 4
                    checkbox_y = todo_y + 4
                    
                    checkbox_bg = QGraphicsEllipseItem(checkbox_x, checkbox_y, checkbox_size, checkbox_size)
                    checkbox_bg.setPen(QPen(QColor("#FFFFFF"), 1.5))
                    if completed:
                        checkbox_bg.setBrush(QBrush(QColor("#10B981")))
                    else:
                        checkbox_bg.setBrush(QBrush(QColor(255, 255, 255, 50)))
                    checkbox_bg.setZValue(2.1)
                    checkbox_bg.setData(0, item_id)
                    checkbox_bg.setData(1, activity.get('id'))
                    checkbox_bg.setData(2, completed)
                    checkbox_bg.setData(3, "todo_checkbox")
                    checkbox_bg.setAcceptHoverEvents(True)
                    checkbox_bg.setCursor(Qt.CursorShape.PointingHandCursor)
                    self.scene.addItem(checkbox_bg)
                    
                    # Checkmark for completed items
                    if completed:
                        checkmark = QGraphicsTextItem("✓")
                        # Center the checkmark in the checkbox
                        checkmark_rect = checkmark.boundingRect()
                        checkmark_x = checkbox_x + (checkbox_size - checkmark_rect.width()) / 2
                        checkmark_y = checkbox_y + (checkbox_size - checkmark_rect.height()) / 2
                        checkmark.setPos(checkmark_x, checkmark_y)
                        checkmark.setDefaultTextColor(QColor("#FFFFFF"))
                        check_font = checkmark.font()
                        check_font.setBold(True)
                        check_font.setPointSize(9)  # Slightly smaller to fit better
                        checkmark.setFont(check_font)
                        checkmark.setZValue(2.2)
                        checkmark.setData(0, item_id)
                        checkmark.setData(1, activity.get('id'))
                        checkmark.setData(2, completed)
                        checkmark.setData(3, "todo_checkmark")
                        checkmark.setAcceptHoverEvents(True)
                        checkmark.setCursor(Qt.CursorShape.PointingHandCursor)
                        self.scene.addItem(checkmark)
                    
                    # Todo text (truncate to fit in grid cell)
                    display_text = text
                    max_text_width = todo_item_width - checkbox_size - 12
                    if len(display_text) > 20:  # Approximate character limit
                        display_text = display_text[:17] + "..."
                    
                    todo_text = QGraphicsTextItem(display_text)
                    todo_text.setPos(checkbox_x + checkbox_size + 6, todo_y + 3)
                    todo_text.setTextWidth(max_text_width)
                    if completed:
                        todo_text.setDefaultTextColor(QColor("#D1D5DB"))
                    else:
                        todo_text.setDefaultTextColor(QColor("#FFFFFF"))
                    
                    todo_font = todo_text.font()
                    todo_font.setPointSize(8)
                    if completed:
                        todo_font.setStrikeOut(True)
                    todo_text.setFont(todo_font)
                    todo_text.setZValue(2)
                    todo_text.setData(0, item_id)
                    todo_text.setData(1, activity.get('id'))
                    todo_text.setData(2, completed)
                    todo_text.setData(3, "todo_text")
                    todo_text.setAcceptHoverEvents(True)
                    todo_text.setCursor(Qt.CursorShape.PointingHandCursor)
                    self.scene.addItem(todo_text)
                
                # Update content_start_y for "Add Todo" button
                rows_used = (items_to_show + items_per_row - 1) // items_per_row
                content_start_y = content_start_y + rows_used * (todo_item_height + todo_item_spacing) + 4

            # Add "Add Todo" button if there's space
            if content_start_y + 30 < y_pos + height:
                add_todo_bg = QGraphicsRectItem(actual_x + 8, content_start_y, actual_width - 16, 24)
                add_todo_bg.setPen(QPen(QColor(255, 255, 255, 150), 1.5, Qt.PenStyle.DashLine))
                add_todo_bg.setBrush(QBrush(QColor(255, 255, 255, 20)))
                add_todo_bg.setZValue(1.8)
                add_todo_bg.setData(0, activity.get('id'))
                add_todo_bg.setAcceptHoverEvents(True)
                add_todo_bg.setCursor(Qt.CursorShape.PointingHandCursor)
                self.scene.addItem(add_todo_bg)
                
                add_todo_text = QGraphicsTextItem("+ Add Todo Item")
                add_todo_text.setPos(actual_x + (actual_width - add_todo_text.boundingRect().width()) / 2, 
                                    content_start_y + 4)
                add_todo_text.setDefaultTextColor(QColor("#FFFFFF"))
                add_todo_font = add_todo_text.font()
                add_todo_font.setPointSize(9)
                add_todo_font.setItalic(True)
                add_todo_text.setFont(add_todo_font)
                add_todo_text.setZValue(2)
                add_todo_text.setData(0, activity.get('id'))
                add_todo_text.setAcceptHoverEvents(True)
                add_todo_text.setCursor(Qt.CursorShape.PointingHandCursor)
                self.scene.addItem(add_todo_text)

            # Store reference to the activity
            self.activity_items[activity.get('id')] = {
                'rect': rounded_rect,
                'activity': activity
            }

        # Set scene event handler
        self.scene.mousePressEvent = self.handleSceneClick

    def createTimeBoxes(self, hour_height, day_width, hour_label_width):
        """Create visible timeboxes for each hour slot, even when empty."""
        margin = 4
        actual_x = hour_label_width + margin
        actual_width = day_width - 2 * margin
        
        for hour in range(24):
            y_pos = hour * hour_height
            
            # Create a subtle background for each hour slot
            timebox_bg = QGraphicsRectItem(actual_x, y_pos, actual_width, hour_height)
            timebox_bg.setPen(QPen(QColor("#E5E7EB"), 1, Qt.PenStyle.DashLine))
            timebox_bg.setBrush(QBrush(QColor(255, 255, 255, 30)))  # Very subtle background
            timebox_bg.setZValue(0.3)
            timebox_bg.setAcceptHoverEvents(True)
            timebox_bg.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Store hour information for click handling
            timebox_bg.setData(0, hour)  # Store hour as data
            timebox_bg.setData(1, "timebox")  # Mark as timebox
            
            self.scene.addItem(timebox_bg)
            
            # Add a subtle "Add Todo" hint for empty timeboxes
            # Only show if there's no activity in this hour
            has_activity = False
            for activity in self.activities:
                start_time = activity.get('start_time')
                end_time = activity.get('end_time')
                if start_time and end_time:
                    start_hour = start_time.hour() + start_time.minute() / 60.0
                    end_hour = end_time.hour() + end_time.minute() / 60.0
                    if end_hour <= start_hour:
                        if end_hour == start_hour:
                            end_hour = start_hour + 0.5
                        else:
                            end_hour += 24.0
                    
                    # Check if this hour slot overlaps with activity
                    if start_hour <= hour + 1 and end_hour >= hour:
                        has_activity = True
                        break
            
            # Only show hint if no activity in this slot
            if not has_activity:
                hint_text = QGraphicsTextItem("Click to add todo")
                hint_text.setPos(actual_x + 10, y_pos + hour_height / 2 - 8)
                hint_text.setDefaultTextColor(QColor("#9CA3AF"))
                hint_font = hint_text.font()
                hint_font.setPointSize(8)
                hint_font.setItalic(True)
                hint_text.setFont(hint_font)
                hint_text.setZValue(0.4)
                hint_text.setData(0, hour)
                hint_text.setData(1, "timebox_hint")
                hint_text.setAcceptHoverEvents(True)
                hint_text.setCursor(Qt.CursorShape.PointingHandCursor)
                self.scene.addItem(hint_text)

    def editTodoItem(self, item_id):
        """Edit an existing todo item."""
        item = self.activities_manager.get_todo_item(item_id)
        if not item:
            return

        dialog = TodoItemDialog(self, text=item[1])
        if dialog.exec():
            text = dialog.get_text()
            if text:
                self.activities_manager.update_todo_item(item_id, text, item[2])
                self.updateDayView()
                # Sync with weekly view
                self.syncWithWeeklyView()

    def deleteTodoItem(self, item_id):
        """Delete a todo item."""
        self.activities_manager.delete_todo_item(item_id)
        self.updateDayView()
        # Sync with weekly view
        self.syncWithWeeklyView()

    def handleSceneClick(self, event):
        """Handle clicks on the scene, including todo items and add buttons."""
        try:
            pos = event.scenePos()
            items = self.scene.items(pos)
            
            # Check for todo item clicks first (checkbox, background, text, or checkmark)
            for item in items:
                # Check if it's a todo-related item
                if item.data(3) in ["todo_checkbox", "todo_bg", "todo_text", "todo_checkmark"]:
                    item_id = item.data(0)
                    activity_id = item.data(1)
                    completed = item.data(2)
                    
                    if event.button() == Qt.MouseButton.RightButton:
                        # Right-click: show context menu
                        self.showTodoContextMenu(event, item_id, activity_id)
                        event.accept()
                        return
                    elif event.button() == Qt.MouseButton.LeftButton:
                        # Left-click: toggle completion
                        # Get the actual todo text from the database
                        todo_item = self.activities_manager.get_todo_item(item_id)
                        if todo_item:
                            todo_text = todo_item[1]
                            new_completed = not completed
                            self.activities_manager.update_todo_item(item_id, todo_text, new_completed)
                            self.updateDayView()
                            # Sync with weekly view
                            self.syncWithWeeklyView()
                        event.accept()
                        return
                
                # Check for "Add Todo" button clicks
                if isinstance(item, (QGraphicsRectItem, QGraphicsTextItem)) and item.data(0) and not item.data(1):
                    # This is the add todo button
                    activity_id = item.data(0)
                    if event.button() == Qt.MouseButton.LeftButton:
                        self.addTodoItem(activity_id)
                        event.accept()
                        return
            
            # Check for timebox clicks (empty time slots)
            for item in items:
                if isinstance(item, QGraphicsRectItem) and item.data(1) == "timebox":
                    hour = item.data(0)
                    if event.button() == Qt.MouseButton.LeftButton:
                        # Create a temporary activity for this time slot to add todos
                        self.addTodoToTimeSlot(hour)
                        event.accept()
                        return
                    elif event.button() == Qt.MouseButton.RightButton:
                        # Right-click on timebox: show menu to add activity or todo
                        self.showTimeboxContextMenu(event, hour)
                        event.accept()
                        return
                
                # Check for timebox hint clicks
                if isinstance(item, QGraphicsTextItem) and item.data(1) == "timebox_hint":
                    hour = item.data(0)
                    if event.button() == Qt.MouseButton.LeftButton:
                        self.addTodoToTimeSlot(hour)
                        event.accept()
                        return
            
            # Check for activity rectangle clicks
            if event.button() == Qt.MouseButton.RightButton:
                self.showContextMenu(event)
                return
            
            for item in items:
                # Check if it's a path item (activity rectangle)
                if isinstance(item, QGraphicsPathItem) and item.data(0):
                    activity_id = item.data(0)
                    self.activityClicked.emit(self.get_activity_by_id(activity_id))
                    event.accept()
                    return
            
            event.accept()
        except Exception as e:
            print(f"Error handling scene click: {e}")
            import traceback
            traceback.print_exc()
            event.accept()

    def showTodoContextMenu(self, event, item_id, activity_id):
        """Show context menu for a todo item."""
        menu = QMenu()
        edit_action = menu.addAction("✏️ Edit Todo")
        delete_action = menu.addAction("🗑️ Delete Todo")
        
        # Convert scene position to global screen position
        view_pos = self.view.mapFromScene(event.scenePos())
        global_pos = self.view.viewport().mapToGlobal(view_pos)
        
        action = menu.exec(global_pos)
        
        if action == edit_action:
            self.editTodoItem(item_id)
        elif action == delete_action:
            self.deleteTodoItem(item_id)

    def showTimeboxContextMenu(self, event, hour):
        """Show context menu for an empty timebox."""
        menu = QMenu()
        add_todo_action = menu.addAction("➕ Add Todo Item")
        add_activity_action = menu.addAction("📅 Create Activity")
        
        # Convert scene position to global screen position
        view_pos = self.view.mapFromScene(event.scenePos())
        global_pos = self.view.viewport().mapToGlobal(view_pos)
        
        action = menu.exec(global_pos)
        
        if action == add_todo_action:
            self.addTodoToTimeSlot(hour)
        elif action == add_activity_action:
            # Emit signal or call parent to create activity
            if hasattr(self.parent, 'showCreateActivityDialog'):
                start_time = QTime(hour, 0)
                end_time = QTime(hour, 59)
                self.parent.showCreateActivityDialog(self.current_date, start_time, end_time)
            else:
                from PyQt6.QtWidgets import QMessageBox
                msg = QMessageBox(self)
                msg.setWindowTitle("Create Activity")
                msg.setText("Please use the Activities view to create a new activity.")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()

    def showContextMenu(self, event):
        """Show context menu for adding todo items to an activity."""
        pos = event.scenePos()
        items = self.scene.items(pos)
        
        activity_id = None
        for item in items:
            # Check if it's a path item (activity rectangle)
            if isinstance(item, QGraphicsPathItem) and item.data(0):
                activity_id = item.data(0)
                break
        
        if activity_id is None:
            return
        
        menu = QMenu()
        add_todo_action = menu.addAction("➕ Add Todo Item")
        
        # Convert scene position to global screen position
        view_pos = self.view.mapFromScene(pos)
        global_pos = self.view.viewport().mapToGlobal(view_pos)
        
        action = menu.exec(global_pos)
        
        if action == add_todo_action:
            self.addTodoItem(activity_id)

    def addTodoToTimeSlot(self, hour):
        """Add a todo item to a specific time slot (hour)."""
        start_time = QTime(hour, 0)
        end_time = QTime(hour, 59)
        
        # Check if there's already an activity in this time slot
        activity_id = None
        for activity in self.activities:
            act_start = activity.get('start_time')
            act_end = activity.get('end_time')
            if act_start and act_end:
                act_start_hour = act_start.hour() + act_start.minute() / 60.0
                act_end_hour = act_end.hour() + act_end.minute() / 60.0
                if act_end_hour <= act_start_hour:
                    act_end_hour += 24.0
                # Check if this hour overlaps with the activity
                if act_start_hour <= hour + 1 and act_end_hour >= hour:
                    activity_id = activity.get('id')
                    break
        
        # If no activity exists, create a simple "Todo List" activity for this time slot
        if activity_id is None:
            # First ask for the todo text
            dialog = TodoItemDialog(self)
            if dialog.exec():
                todo_text = dialog.get_text()
                if todo_text:
                    # Create a simple activity for this time slot
                    activity_data = {
                        'title': f'Todo List - {hour:02d}:00',
                        'date': self.current_date,
                        'start_time': start_time,
                        'end_time': end_time,
                        'type': 'task',
                        'completed': False,
                        'priority': 0,
                        'category': 'Personal'
                    }
                    
                    try:
                        # Create the activity
                        activity_id = self.activities_manager.add_activity(activity_data)
                        
                        if activity_id:
                            # Add the todo item to the newly created activity
                            self.activities_manager.add_todo_item(activity_id, todo_text)
                            
                            # Refresh the view
                            self.loadActivities()
                            
                            # Sync with other views
                            self.syncWithWeeklyView()
                            
                            # Refresh parent views if they exist
                            if hasattr(self.parent, 'activities_view'):
                                self.parent.activities_view.refresh()
                    except Exception as e:
                        from PyQt6.QtWidgets import QMessageBox
                        msg = QMessageBox(self)
                        msg.setWindowTitle("Error")
                        msg.setText(f"Failed to create activity: {str(e)}")
                        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                        msg.exec()
        else:
            # Add todo to existing activity
            self.addTodoItem(activity_id)

    def addTodoItem(self, activity_id):
        """Add a new todo item to an activity."""
        dialog = TodoItemDialog(self)
        if dialog.exec():
            text = dialog.get_text()
            if text:
                self.activities_manager.add_todo_item(activity_id, text)
                self.updateDayView()
                # Sync with weekly view
                self.syncWithWeeklyView()

    def get_activity_by_id(self, activity_id):
        for activity in self.activities:
            if activity.get('id') == activity_id:
                return activity
        return None

    def resizeEvent(self, event):
        """Handle widget resize to update grid width."""
        super().resizeEvent(event)
        # Update the view when resized
        if hasattr(self, 'scene') and self.scene.items():
            self.updateDayView()
    
    def refresh(self):
        self.loadActivities()
    
    def setDate(self, date):
        """Set the current date and refresh the view."""
        self.current_date = date
        self.updateDayLabel()
        self.loadActivities()
    
    def syncWithWeeklyView(self):
        """Sync changes with the weekly plan view."""
        if hasattr(self.parent, 'weekly_plan_view') and self.parent.weekly_plan_view:
            self.parent.weekly_plan_view.refresh()
        
        # Also refresh activities view if it exists
        if hasattr(self.parent, 'activities_view') and self.parent.activities_view:
            self.parent.activities_view.refresh()
