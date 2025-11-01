"""
Enhanced backup management system for TaskTitan.

This module provides automatic backup scheduling, backup verification,
retention policies, and recovery mechanisms.
"""

import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from app.utils.logger import get_logger
from app.models.database import get_db_path
from app.utils.db_utils import get_backups_dir
from app.core.config import get_config
from app.utils.security import get_file_hash

logger = get_logger(__name__)


class BackupManager(QObject):
    """Manages automatic backups and backup operations."""
    
    backup_completed = pyqtSignal(str)  # Emits backup path when completed
    backup_failed = pyqtSignal(str)  # Emits error message when failed
    
    def __init__(self, parent=None):
        """Initialize backup manager."""
        super().__init__(parent)
        self.db_path = get_db_path()
        self.backups_dir = get_backups_dir()
        self.auto_backup_timer = QTimer(self)
        self.auto_backup_timer.timeout.connect(self.perform_auto_backup)
        self._setup_auto_backup()
    
    def _setup_auto_backup(self):
        """Setup automatic backup based on configuration."""
        enabled = get_config('backup.auto_backup_enabled', False)
        if enabled:
            interval = get_config('backup.auto_backup_interval', 'daily')
            self.start_auto_backup(interval)
        else:
            self.stop_auto_backup()
    
    def create_backup(self, custom_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Create a backup of the database.
        
        Args:
            custom_name: Optional custom name for the backup
            
        Returns:
            Tuple of (success, backup_path_or_error_message)
        """
        try:
            if not os.path.exists(self.db_path):
                error = "Database file not found"
                logger.error(error)
                self.backup_failed.emit(error)
                return False, error
            
            # Generate backup filename
            if custom_name:
                backup_filename = f"{custom_name}.db"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"tasktitan_backup_{timestamp}.db"
            
            backup_path = os.path.join(self.backups_dir, backup_filename)
            
            # Create backup
            shutil.copy2(self.db_path, backup_path)
            
            # Verify backup
            if not self._verify_backup(backup_path):
                error = "Backup verification failed"
                logger.error(error)
                os.remove(backup_path)
                self.backup_failed.emit(error)
                return False, error
            
            # Get backup metadata
            backup_size = os.path.getsize(backup_path)
            logger.info(f"Created backup: {backup_path} ({backup_size} bytes)")
            
            self.backup_completed.emit(backup_path)
            
            # Cleanup old backups based on retention policy
            self._cleanup_old_backups()
            
            return True, backup_path
            
        except Exception as e:
            error = f"Failed to create backup: {e}"
            logger.error(error, exc_info=True)
            self.backup_failed.emit(error)
            return False, error
    
    def _verify_backup(self, backup_path: str) -> bool:
        """
        Verify backup integrity.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if backup is valid, False otherwise
        """
        try:
            # Check file exists and is readable
            if not os.path.exists(backup_path):
                return False
            
            # Try to open and verify database structure
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            
            # Check for essential tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            essential_tables = ['activities', 'goals']
            has_essential = any(table in tables for table in essential_tables)
            
            conn.close()
            
            return has_essential
            
        except Exception as e:
            logger.error(f"Error verifying backup: {e}", exc_info=True)
            return False
    
    def restore_backup(self, backup_path: str) -> Tuple[bool, Optional[str]]:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Verify backup first
            if not self._verify_backup(backup_path):
                error = "Invalid backup file"
                logger.error(error)
                return False, error
            
            # Create pre-restore backup
            pre_restore_backup = self._create_pre_restore_backup()
            
            # Restore backup
            shutil.copy2(backup_path, self.db_path)
            
            # Verify restored database
            if not self._verify_backup(self.db_path):
                error = "Restored database verification failed"
                logger.error(error)
                # Restore pre-restore backup
                if pre_restore_backup:
                    shutil.copy2(pre_restore_backup, self.db_path)
                return False, error
            
            logger.info(f"Successfully restored backup from {backup_path}")
            return True, None
            
        except Exception as e:
            error = f"Failed to restore backup: {e}"
            logger.error(error, exc_info=True)
            return False, error
    
    def _create_pre_restore_backup(self) -> Optional[str]:
        """Create a backup before restoring."""
        if os.path.exists(self.db_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"pre_restore_{timestamp}.db"
            backup_path = os.path.join(self.backups_dir, backup_filename)
            try:
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"Created pre-restore backup: {backup_path}")
                return backup_path
            except Exception as e:
                logger.warning(f"Could not create pre-restore backup: {e}")
        return None
    
    def _cleanup_old_backups(self):
        """Remove old backups based on retention policy."""
        try:
            retention_days = get_config('backup.backup_retention_days', 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            backups = self.list_backups()
            removed_count = 0
            
            for backup_path, backup_info in backups:
                backup_date = backup_info.get('date')
                if backup_date and backup_date < cutoff_date:
                    try:
                        os.remove(backup_path)
                        removed_count += 1
                        logger.debug(f"Removed old backup: {backup_path}")
                    except Exception as e:
                        logger.warning(f"Could not remove old backup {backup_path}: {e}")
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old backup(s)")
                
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}", exc_info=True)
    
    def list_backups(self) -> List[Tuple[str, Dict]]:
        """
        List all available backups.
        
        Returns:
            List of tuples (backup_path, backup_info_dict)
        """
        backups = []
        
        if not os.path.exists(self.backups_dir):
            return backups
        
        try:
            for filename in os.listdir(self.backups_dir):
                if filename.endswith('.db') and 'backup' in filename.lower():
                    backup_path = os.path.join(self.backups_dir, filename)
                    
                    try:
                        stat = os.stat(backup_path)
                        backup_info = {
                            'filename': filename,
                            'path': backup_path,
                            'size': stat.st_size,
                            'date': datetime.fromtimestamp(stat.st_mtime),
                            'verified': self._verify_backup(backup_path)
                        }
                        backups.append((backup_path, backup_info))
                    except Exception as e:
                        logger.warning(f"Could not read backup info for {filename}: {e}")
            
            # Sort by date (newest first)
            backups.sort(key=lambda x: x[1]['date'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}", exc_info=True)
        
        return backups
    
    def start_auto_backup(self, interval: str = 'daily'):
        """
        Start automatic backup scheduling.
        
        Args:
            interval: Backup interval ('daily', 'weekly', 'monthly')
        """
        interval_mapping = {
            'daily': 24 * 60 * 60 * 1000,  # 24 hours in milliseconds
            'weekly': 7 * 24 * 60 * 60 * 1000,  # 7 days
            'monthly': 30 * 24 * 60 * 60 * 1000  # 30 days
        }
        
        interval_ms = interval_mapping.get(interval, interval_mapping['daily'])
        self.auto_backup_timer.start(interval_ms)
        logger.info(f"Started automatic backups (interval: {interval})")
    
    def stop_auto_backup(self):
        """Stop automatic backup scheduling."""
        self.auto_backup_timer.stop()
        logger.info("Stopped automatic backups")
    
    def perform_auto_backup(self):
        """Perform automatic backup."""
        logger.info("Performing automatic backup...")
        success, result = self.create_backup()
        if success:
            logger.info(f"Automatic backup completed: {result}")
        else:
            logger.error(f"Automatic backup failed: {result}")


def get_backup_manager() -> BackupManager:
    """Get singleton instance of BackupManager."""
    global _backup_manager
    if '_backup_manager' not in globals():
        _backup_manager = BackupManager()
    return _backup_manager

