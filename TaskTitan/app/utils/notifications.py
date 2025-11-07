"""
System notifications for TaskTitan.

This module provides system-level notifications for reminders,
deadlines, backups, and other important events.
"""

import os
import platform
from typing import Optional
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QSystemTrayIcon, QApplication
from app.utils.logger import get_logger
from app.core.config import get_config

logger = get_logger(__name__)


class NotificationManager(QObject):
    """Manages system notifications."""
    
    notification_sent = pyqtSignal(str, str)  # Emits (title, message)
    
    def __init__(self, parent=None):
        """Initialize notification manager."""
        super().__init__(parent)
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self._setup_tray_icon()
    
    def _setup_tray_icon(self):
        """Setup system tray icon if available."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            try:
                self.tray_icon = QSystemTrayIcon(self)
                # Set icon if available
                from app.resources import get_icon
                icon = get_icon("task")
                if not icon.isNull():
                    self.tray_icon.setIcon(icon)
                self.tray_icon.setToolTip("TaskTitan")
            except Exception as e:
                logger.warning(f"Could not setup system tray icon: {e}")
    
    def show_notification(self, title: str, message: str, 
                         duration: int = 5000, icon: int = QSystemTrayIcon.MessageIcon.Information):
        """
        Show a system notification.
        
        Args:
            title: Notification title
            message: Notification message
            duration: Duration in milliseconds
            icon: Icon type (Information, Warning, Critical)
        """
        try:
            # Check if notifications are enabled
            if not get_config('notifications.enabled', True):
                return
            
            # Use system tray icon if available
            if self.tray_icon and self.tray_icon.isSystemTrayAvailable():
                self.tray_icon.showMessage(title, message, icon, duration)
            else:
                # Fallback: log notification
                logger.info(f"Notification: {title} - {message}")
            
            self.notification_sent.emit(title, message)
            
        except Exception as e:
            logger.error(f"Error showing notification: {e}", exc_info=True)
    
    def notify_task_reminder(self, task_title: str, due_time: Optional[str] = None):
        """Show task reminder notification."""
        if not get_config('notifications.task_reminders', True):
            return
        
        message = f"Reminder: {task_title}"
        if due_time:
            message += f" (Due: {due_time})"
        
        self.show_notification(
            "Task Reminder",
            message,
            icon=QSystemTrayIcon.MessageIcon.Information
        )
    
    def notify_deadline(self, item_title: str, deadline: str):
        """Show deadline alert notification."""
        if not get_config('notifications.deadline_alerts', True):
            return
        
        self.show_notification(
            "Deadline Alert",
            f"{item_title} is due: {deadline}",
            icon=QSystemTrayIcon.MessageIcon.Warning
        )
    
    def notify_backup_completed(self, backup_path: str):
        """Show backup completion notification."""
        if not get_config('notifications.backup_notifications', True):
            return
        
        filename = os.path.basename(backup_path)
        self.show_notification(
            "Backup Completed",
            f"Backup saved: {filename}",
            icon=QSystemTrayIcon.MessageIcon.Information
        )
    
    def notify_update_available(self, version: str):
        """Show update available notification."""
        self.show_notification(
            "Update Available",
            f"TaskTitan {version} is now available!",
            icon=QSystemTrayIcon.MessageIcon.Information
        )


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get singleton instance of NotificationManager."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager


def notify(title: str, message: str, duration: int = 5000):
    """Show notification (convenience function)."""
    manager = get_notification_manager()
    manager.show_notification(title, message, duration)

