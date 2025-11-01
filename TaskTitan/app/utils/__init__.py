"""
Utility modules for TaskTitan.
"""

from app.utils.logger import get_logger, setup_logging, TaskTitanLogger
from app.utils.error_handler import (
    GlobalExceptionHandler,
    ErrorReportDialog,
    handle_database_error,
    handle_file_error,
    safe_execute,
    show_error_dialog
)

__all__ = [
    'get_logger',
    'setup_logging',
    'TaskTitanLogger',
    'GlobalExceptionHandler',
    'ErrorReportDialog',
    'handle_database_error',
    'handle_file_error',
    'safe_execute',
    'show_error_dialog'
]