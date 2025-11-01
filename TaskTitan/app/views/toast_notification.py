"""
Toast Notification System for TaskTitan.

Provides non-intrusive toast notifications for user feedback.
"""
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QFont, QPainter, QBrush, QPen
from enum import Enum


class ToastType(Enum):
    """Types of toast notifications."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ToastNotification(QWidget):
    """A single toast notification widget."""
    
    def __init__(self, message, toast_type=ToastType.INFO, duration=3000, parent=None):
        """
        Initialize a toast notification.
        
        Args:
            message: The message to display
            toast_type: Type of toast (SUCCESS, ERROR, WARNING, INFO)
            duration: Duration in milliseconds before auto-dismiss
            parent: Parent widget
        """
        super().__init__(parent)
        self.message = message
        self.toast_type = toast_type
        self.duration = duration
        
        self.setupUI()
        self.setupAnimations()
        
    def setupUI(self):
        """Set up the UI components."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Get theme colors
        from app.themes import ThemeManager
        theme_colors = ThemeManager.get_current_palette()
        
        # Determine colors based on type
        if self.toast_type == ToastType.SUCCESS:
            bg_color = theme_colors.get("success", "#10B981")
            icon_text = "✓"
        elif self.toast_type == ToastType.ERROR:
            bg_color = theme_colors.get("error", "#EF4444")
            icon_text = "✕"
        elif self.toast_type == ToastType.WARNING:
            bg_color = theme_colors.get("warning", "#F59E0B")
            icon_text = "⚠"
        else:  # INFO
            bg_color = theme_colors.get("primary", "#6366F1")
            icon_text = "ℹ"
        
        # Main container
        container = QFrame()
        container.setObjectName("toastContainer")
        container.setStyleSheet(f"""
            QFrame#toastContainer {{
                background-color: {bg_color};
                border-radius: 8px;
                padding: 12px;
                min-width: 300px;
                max-width: 400px;
            }}
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: 500;
            background: transparent;
        """)
        layout.addWidget(message_label, 1)
        
        # Close button (X)
        close_btn = QLabel("×")
        close_btn.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: white;
            background: transparent;
            padding: 0px 4px;
        """)
        close_btn.setFixedSize(20, 20)
        close_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.mousePressEvent = lambda e: self.close()
        layout.addWidget(close_btn)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
        # Set fixed size based on content
        self.adjustSize()
        
    def setupAnimations(self):
        """Set up slide-in and fade-out animations."""
        # Start position (off-screen to the right)
        self.setGeometry(0, 0, self.width(), self.height())
        
        # Fade-out animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.deleteLater)
        
        # Auto-dismiss timer
        if self.duration > 0:
            self.dismiss_timer = QTimer(self)
            self.dismiss_timer.setSingleShot(True)
            self.dismiss_timer.timeout.connect(self.dismiss)
            self.dismiss_timer.start(self.duration)
    
    def dismiss(self):
        """Dismiss the toast with animation."""
        self.fade_animation.start()
    
    def mousePressEvent(self, event):
        """Dismiss on click."""
        self.dismiss()


class ToastManager(QWidget):
    """Manager for displaying multiple toast notifications."""
    
    def __init__(self, parent=None):
        """Initialize the toast manager."""
        super().__init__(parent)
        self.parent_window = parent
        self.toasts = []
        self.spacing = 10
        self.position = "top-right"  # or "bottom-right"
        
        # Set up as overlay
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
    def show_toast(self, message, toast_type=ToastType.INFO, duration=3000):
        """
        Show a toast notification.
        
        Args:
            message: Message to display
            toast_type: Type of toast
            duration: Duration in milliseconds
        """
        toast = ToastNotification(message, toast_type, duration, self)
        self.toasts.append(toast)
        
        # Position the toast
        self.update_positions()
        
        # Show the toast
        toast.show()
        
        # Animate slide-in
        toast.setWindowOpacity(0.0)
        fade_in = QPropertyAnimation(toast, b"windowOpacity")
        fade_in.setDuration(300)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade_in.start()
        
        # Connect dismissal to cleanup
        toast.destroyed.connect(lambda: self.remove_toast(toast))
        
    def remove_toast(self, toast):
        """Remove toast from list."""
        if toast in self.toasts:
            self.toasts.remove(toast)
            self.update_positions()
    
    def update_positions(self):
        """Update positions of all toasts."""
        if not self.parent_window:
            return
        
        parent_rect = self.parent_window.geometry()
        
        if self.position == "top-right":
            start_y = parent_rect.top() + 20
            start_x = parent_rect.right() - 20
        else:  # bottom-right
            start_y = parent_rect.bottom() - 20
            start_x = parent_rect.right() - 20
        
        current_y = start_y
        
        for toast in reversed(self.toasts):  # Stack from top to bottom
            toast_x = start_x - toast.width()
            toast.move(toast_x, current_y)
            current_y += toast.height() + self.spacing
    
    def success(self, message, duration=3000):
        """Show a success toast."""
        self.show_toast(message, ToastType.SUCCESS, duration)
    
    def error(self, message, duration=4000):
        """Show an error toast."""
        self.show_toast(message, ToastType.ERROR, duration)
    
    def warning(self, message, duration=3500):
        """Show a warning toast."""
        self.show_toast(message, ToastType.WARNING, duration)
    
    def info(self, message, duration=3000):
        """Show an info toast."""
        self.show_toast(message, ToastType.INFO, duration)


def show_toast(parent, message, toast_type=ToastType.INFO, duration=3000):
    """
    Convenience function to show a toast notification.
    
    Args:
        parent: Parent widget (usually main window)
        message: Message to display
        toast_type: Type of toast
        duration: Duration in milliseconds
    """
    # Get or create toast manager
    if not hasattr(parent, '_toast_manager'):
        parent._toast_manager = ToastManager(parent)
        parent._toast_manager.setGeometry(parent.geometry())
    
    # Update manager geometry if parent moved
    parent._toast_manager.setGeometry(parent.geometry())
    parent._toast_manager.update_positions()
    
    # Show toast
    if toast_type == ToastType.SUCCESS:
        parent._toast_manager.success(message, duration)
    elif toast_type == ToastType.ERROR:
        parent._toast_manager.error(message, duration)
    elif toast_type == ToastType.WARNING:
        parent._toast_manager.warning(message, duration)
    else:
        parent._toast_manager.info(message, duration)

