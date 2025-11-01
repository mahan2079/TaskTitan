"""
Loading Indicator Widget for TaskTitan.

Provides reusable loading spinners for async operations.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QSize, QRect
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen


class LoadingSpinner(QWidget):
    """A circular loading spinner widget."""
    
    def __init__(self, parent=None, size=40):
        """
        Initialize the loading spinner.
        
        Args:
            parent: Parent widget
            size: Size of the spinner in pixels
        """
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Animation
        self.rotation = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_rotation)
        self.animation_timer.start(50)  # Update every 50ms
    
    def update_rotation(self):
        """Update rotation angle."""
        self.rotation = (self.rotation + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """Paint the spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get theme colors
        from app.themes import ThemeManager
        theme_colors = ThemeManager.get_current_palette()
        primary_color = QColor(theme_colors.get("primary", "#6366F1"))
        
        # Draw spinning circle
        pen = QPen()
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        center = QRect(0, 0, self.size, self.size).center()
        radius = self.size // 2 - 5
        
        # Draw multiple arcs to create spinner effect
        for i in range(8):
            angle = (self.rotation + i * 45) % 360
            alpha = int(255 * (1 - i / 8))
            color = QColor(primary_color)
            color.setAlpha(alpha)
            pen.setColor(color)
            painter.setPen(pen)
            
            # Draw arc
            start_angle = angle * 16
            span_angle = 45 * 16
            painter.drawArc(
                center.x() - radius,
                center.y() - radius,
                radius * 2,
                radius * 2,
                start_angle,
                span_angle
            )
    
    def stop(self):
        """Stop the animation."""
        self.animation_timer.stop()
    
    def start(self):
        """Start the animation."""
        self.animation_timer.start(50)


class LoadingOverlay(QWidget):
    """A full-screen overlay with loading spinner."""
    
    def __init__(self, parent=None, message="Loading..."):
        """
        Initialize the loading overlay.
        
        Args:
            parent: Parent widget
            message: Message to display
        """
        super().__init__(parent)
        self.message = message
        self.setupUI()
    
    def setupUI(self):
        """Set up the UI components."""
        # Make overlay cover parent
        if self.parent():
            parent_rect = self.parent().geometry()
            self.setGeometry(0, 0, parent_rect.width(), parent_rect.height())
        
        # Set semi-transparent background
        from app.themes import ThemeManager
        theme_colors = ThemeManager.get_current_palette()
        bg_color = theme_colors.get("bg", "#FFFFFF")
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(0, 0, 0, 0.3);
            }}
        """)
        
        # Create container
        container = QFrame()
        container.setObjectName("loadingOverlayContainer")
        
        from app.themes import ThemeManager
        theme_colors = ThemeManager.get_current_palette()
        container.setStyleSheet(f"""
            QFrame#loadingOverlayContainer {{
                background-color: {theme_colors.get('surface', '#FFFFFF')};
                border: 1px solid {theme_colors.get('border', '#E2E8F0')};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        # Loading spinner
        self.spinner = LoadingSpinner(container, size=50)
        layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Message label
        if self.message:
            message_label = QLabel(self.message)
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet("""
                font-size: 14px;
                color: #6B7280;
            """)
            layout.addWidget(message_label)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Update geometry when shown
        if self.parent():
            parent_rect = self.parent().geometry()
            self.setGeometry(0, 0, parent_rect.width(), parent_rect.height())
    
    def close(self):
        """Close the overlay."""
        self.spinner.stop()
        super().close()


def show_loading_overlay(parent, message="Loading..."):
    """
    Show a loading overlay on the parent widget.
    
    Args:
        parent: Parent widget
        message: Message to display
        
    Returns:
        LoadingOverlay instance
    """
    overlay = LoadingOverlay(parent, message)
    overlay.show()
    overlay.raise_()
    overlay.activateWindow()
    return overlay

