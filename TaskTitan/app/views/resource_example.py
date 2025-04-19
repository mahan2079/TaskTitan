"""
Example file demonstrating how to use the resources in TaskTitan.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize

from app.resources import (
    get_icon, get_pixmap, get_component_style, ColorPalette,
    APP_NAME, VIEW_NAMES, DASHBOARD_VIEW, TASKS_VIEW
)

class ResourceExampleWidget(QWidget):
    """Example widget demonstrating the use of resources."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = ColorPalette(is_dark_mode=False)
        self.setupUI()
        
    def setupUI(self):
        """Set up the UI with example resource usage."""
        layout = QVBoxLayout(self)
        
        # Example title
        title_label = QLabel(f"{APP_NAME} Resources Example")
        title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {self.colors.get_hex('primary')};")
        layout.addWidget(title_label)
        
        # Icons example
        icons_frame = QFrame()
        icons_frame.setProperty("class", "card")
        icons_frame.setStyleSheet(get_component_style("dashboard_card"))
        icons_layout = QVBoxLayout(icons_frame)
        
        icons_title = QLabel("Icons Example")
        icons_title.setProperty("class", "dashboard-widget-header")
        icons_layout.addWidget(icons_title)
        
        # Icons grid
        icons_grid = QGridLayout()
        icons = [
            ("dashboard", VIEW_NAMES[DASHBOARD_VIEW]),
            ("tasks", VIEW_NAMES[TASKS_VIEW]),
            ("goals", "Goals"),
            ("habits", "Habits"),
            ("productivity", "Productivity"),
            ("pomodoro", "Pomodoro"),
            ("add", "Add Item"),
            ("edit", "Edit Item"),
            ("delete", "Delete Item"),
            ("search", "Search"),
            ("user", "User Profile"),
        ]
        
        for i, (icon_name, label_text) in enumerate(icons):
            row, col = divmod(i, 4)
            
            icon_container = QWidget()
            icon_layout = QVBoxLayout(icon_container)
            
            # Icon label
            icon_label = QLabel()
            icon_pixmap = get_pixmap(icon_name, (32, 32))
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Text label
            text_label = QLabel(label_text)
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            icon_layout.addWidget(icon_label)
            icon_layout.addWidget(text_label)
            
            icons_grid.addWidget(icon_container, row, col)
        
        icons_layout.addLayout(icons_grid)
        layout.addWidget(icons_frame)
        
        # Colors example
        colors_frame = QFrame()
        colors_frame.setProperty("class", "card")
        colors_frame.setStyleSheet(get_component_style("dashboard_card"))
        colors_layout = QVBoxLayout(colors_frame)
        
        colors_title = QLabel("Colors Example")
        colors_title.setProperty("class", "dashboard-widget-header")
        colors_layout.addWidget(colors_title)
        
        # Color swatches
        colors_grid = QGridLayout()
        color_examples = [
            ("primary", "Primary"),
            ("secondary", "Secondary"),
            ("accent", "Accent"),
            ("info", "Info"),
            ("success", "Success"),
            ("warning", "Warning"),
            ("danger", "Danger"),
            ("background", "Background"),
            ("text", "Text"),
            ("border", "Border"),
        ]
        
        for i, (color_attr, label_text) in enumerate(color_examples):
            row, col = divmod(i, 5)
            
            color_container = QWidget()
            color_layout = QVBoxLayout(color_container)
            
            # Color swatch
            color_swatch = QFrame()
            color_swatch.setFixedSize(60, 40)
            if hasattr(self.colors, color_attr):
                color = getattr(self.colors, color_attr)
                color_swatch.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #CBD5E1; border-radius: 4px;")
            
            # Text label
            text_label = QLabel(label_text)
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            color_layout.addWidget(color_swatch)
            color_layout.addWidget(text_label)
            
            colors_grid.addWidget(color_container, row, col)
        
        colors_layout.addLayout(colors_grid)
        layout.addWidget(colors_frame)
        
        # Style example
        styles_frame = QFrame()
        styles_frame.setProperty("class", "card")
        styles_frame.setStyleSheet(get_component_style("dashboard_card"))
        styles_layout = QVBoxLayout(styles_frame)
        
        styles_title = QLabel("Component Styles Example")
        styles_title.setProperty("class", "dashboard-widget-header")
        styles_layout.addWidget(styles_title)
        
        # Task items
        task_frame = QFrame()
        task_frame.setProperty("class", "task-item")
        task_frame.setStyleSheet(get_component_style("task_item"))
        task_layout = QVBoxLayout(task_frame)
        
        task_title = QLabel("Example Task")
        task_title.setProperty("class", "task-title")
        task_date = QLabel("Today at 2:00 PM")
        task_date.setProperty("class", "task-date")
        
        task_layout.addWidget(task_title)
        task_layout.addWidget(task_date)
        
        styles_layout.addWidget(task_frame)
        
        # Completed task
        completed_task_frame = QFrame()
        completed_task_frame.setProperty("class", "task-item-completed")
        completed_task_frame.setStyleSheet(get_component_style("task_item"))
        completed_task_layout = QVBoxLayout(completed_task_frame)
        
        completed_task_title = QLabel("Completed Task")
        completed_task_title.setProperty("class", "task-title-completed")
        completed_task_date = QLabel("Today at 10:00 AM")
        completed_task_date.setProperty("class", "task-date")
        
        completed_task_layout.addWidget(completed_task_title)
        completed_task_layout.addWidget(completed_task_date)
        
        styles_layout.addWidget(completed_task_frame)
        
        layout.addWidget(styles_frame)
        
        # Add spacer at the bottom
        layout.addStretch()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = ResourceExampleWidget()
    window.setWindowTitle("Resource Example")
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec()) 