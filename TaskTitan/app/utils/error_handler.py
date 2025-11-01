"""
Global error handler for TaskTitan.

This module provides exception handling, crash recovery,
and user-friendly error reporting.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorReportDialog(QDialog):
    """Dialog for displaying error details and allowing user to report."""
    
    def __init__(self, error_msg: str, error_details: str, parent=None):
        """Initialize error dialog."""
        super().__init__(parent)
        self.setWindowTitle("Application Error")
        self.setMinimumSize(500, 400)
        self.error_details = error_details
        
        layout = QVBoxLayout(self)
        
        # Error message
        msg_label = QLabel(f"<b>An error occurred:</b><br>{error_msg}")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        # Error details (collapsible)
        details_label = QLabel("Error Details:")
        layout.addWidget(details_label)
        
        details_text = QTextEdit()
        details_text.setPlainText(error_details)
        details_text.setReadOnly(True)
        details_text.setMaximumHeight(200)
        layout.addWidget(details_text)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        save_button = QPushButton("Save Error Report")
        save_button.clicked.connect(self.save_error_report)
        button_layout.addWidget(save_button)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
    
    def save_error_report(self):
        """Save error report to file."""
        try:
            from app.utils.logger import TaskTitanLogger
            log_dir = TaskTitanLogger.get_instance().log_dir
            error_file = Path(log_dir) / f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"Error Report - {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n\n")
                f.write(self.error_details)
            
            QMessageBox.information(self, "Error Report Saved", 
                                  f"Error report saved to:\n{error_file}")
        except Exception as e:
            logger.error(f"Failed to save error report: {e}")
            QMessageBox.warning(self, "Error", f"Could not save error report: {e}")


class GlobalExceptionHandler(QObject):
    """Global exception handler for uncaught exceptions."""
    
    def __init__(self, app=None):
        """Initialize global exception handler."""
        super().__init__()
        self.app = app
        self.install_exception_handler()
    
    def install_exception_handler(self):
        """Install global exception handler."""
        sys.excepthook = self.handle_exception
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Handle uncaught exceptions.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Traceback object
        """
        # Don't handle KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the exception
        error_msg = f"Uncaught exception: {exc_type.__name__}: {exc_value}"
        logger.critical(error_msg, exc_info=(exc_type, exc_value, exc_traceback))
        
        # Format traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        error_details = ''.join(tb_lines)
        
        # Show error dialog if app is available
        if self.app:
            try:
                dialog = ErrorReportDialog(
                    str(exc_value),
                    error_details,
                    None
                )
                dialog.exec()
            except Exception as e:
                logger.error(f"Failed to show error dialog: {e}")
                # Fallback to console
                print(f"Error: {error_msg}\n{error_details}")
        else:
            # No GUI available, print to console
            print(f"Error: {error_msg}\n{error_details}")
        
        # Attempt to save crash state
        self.save_crash_state(exc_type, exc_value, exc_traceback)
    
    def save_crash_state(self, exc_type, exc_value, exc_traceback):
        """Save crash state for recovery."""
        try:
            from app.utils.logger import TaskTitanLogger
            log_dir = TaskTitanLogger.get_instance().log_dir
            crash_file = Path(log_dir) / f"crash_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(crash_file, 'w', encoding='utf-8') as f:
                f.write(f"Crash State - {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Exception Type: {exc_type.__name__}\n")
                f.write(f"Exception Value: {exc_value}\n\n")
                f.write("Traceback:\n")
                f.write(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            
            logger.info(f"Crash state saved to {crash_file}")
        except Exception as e:
            logger.error(f"Failed to save crash state: {e}")


def handle_database_error(error: Exception, operation: str = "database operation") -> str:
    """
    Handle database errors with user-friendly messages.
    
    Args:
        error: The exception that occurred
        operation: Description of the operation that failed
        
    Returns:
        User-friendly error message
    """
    logger.error(f"Database error during {operation}: {error}", exc_info=True)
    
    error_type = type(error).__name__
    
    if "database is locked" in str(error).lower():
        return "The database is currently in use. Please close other instances of TaskTitan and try again."
    elif "no such table" in str(error).lower():
        return "Database structure error. The application may need to be updated or the database repaired."
    elif "disk i/o error" in str(error).lower():
        return "Unable to access the database file. Check disk space and file permissions."
    elif "integrity constraint" in str(error).lower():
        return "Data integrity error. The operation could not be completed due to invalid data."
    else:
        return f"An error occurred while performing {operation}. Please try again or contact support if the problem persists."


def handle_file_error(error: Exception, operation: str = "file operation", file_path: str = "") -> str:
    """
    Handle file I/O errors with user-friendly messages.
    
    Args:
        error: The exception that occurred
        operation: Description of the operation that failed
        file_path: Path to the file that caused the error
        
    Returns:
        User-friendly error message
    """
    logger.error(f"File error during {operation}: {error}", exc_info=True)
    
    error_type = type(error).__name__
    
    if isinstance(error, PermissionError):
        return f"Permission denied. Cannot access '{file_path}'. Check file permissions."
    elif isinstance(error, FileNotFoundError):
        return f"File not found: '{file_path}'. The file may have been moved or deleted."
    elif isinstance(error, OSError):
        if "No space left" in str(error):
            return "Disk is full. Free up space and try again."
        else:
            return f"File system error: {error}"
    else:
        return f"An error occurred while {operation}. Please try again."


def safe_execute(func, *args, default_return=None, error_message: str = "", **kwargs):
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments
        default_return: Value to return on error
        error_message: Custom error message
        **kwargs: Keyword arguments
        
    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        msg = error_message or f"Error executing {func.__name__}"
        logger.error(f"{msg}: {e}", exc_info=True)
        return default_return


def show_error_dialog(parent, title: str, message: str, details: str = ""):
    """
    Show an error dialog to the user.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Error message
        details: Optional detailed error information
    """
    if details:
        dialog = ErrorReportDialog(message, details, parent)
        dialog.exec()
    else:
        QMessageBox.critical(parent, title, message)

