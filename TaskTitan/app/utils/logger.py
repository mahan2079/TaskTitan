"""
Centralized logging system for TaskTitan.

This module provides a structured logging system with rotation,
multiple handlers, and configurable log levels.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


class TaskTitanLogger:
    """Centralized logger for TaskTitan application."""
    
    _instance: Optional['TaskTitanLogger'] = None
    _initialized = False
    
    def __init__(self):
        """Initialize the logger with file and console handlers."""
        if TaskTitanLogger._initialized:
            return
            
        self.logger = logging.getLogger('TaskTitan')
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
            
        # Create logs directory
        self.log_dir = self._get_log_directory()
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Setup handlers
        self._setup_file_handler()
        self._setup_console_handler()
        
        TaskTitanLogger._initialized = True
        
    def _get_log_directory(self) -> str:
        """Get the directory for log files."""
        if getattr(sys, 'frozen', False):
            # Running as executable
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        log_dir = os.path.join(base_dir, 'data', 'logs')
        return log_dir
    
    def _setup_file_handler(self):
        """Setup rotating file handler."""
        log_file = os.path.join(self.log_dir, 'tasktitan.log')
        
        # Rotating file handler: 10MB max, keep 5 backup files
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        file_handler.setLevel(logging.DEBUG)
        
        # Detailed format for file logs
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def _setup_console_handler(self):
        """Setup console handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Less verbose for console
        
        # Simpler format for console
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger
    
    @classmethod
    def get_instance(cls) -> 'TaskTitanLogger':
        """Get singleton instance of TaskTitanLogger."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_logger_instance(cls) -> logging.Logger:
        """Get the logger instance (convenience classmethod)."""
        instance = cls.get_instance()
        return instance.get_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the given module name.
    
    Args:
        name: Optional module name. If None, uses 'TaskTitan'.
        
    Returns:
        Configured logger instance.
    """
    if name:
        return logging.getLogger(f'TaskTitan.{name}')
    return TaskTitanLogger.get_logger_instance()


def setup_logging(level: int = logging.INFO):
    """
    Setup logging with the specified level.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    # Get instance first to ensure initialization
    logger_instance = TaskTitanLogger.get_instance()
    logger = logger_instance.get_logger()
    logger.setLevel(level)
    
    # Update console handler level
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.handlers.RotatingFileHandler):
            handler.setLevel(level)

