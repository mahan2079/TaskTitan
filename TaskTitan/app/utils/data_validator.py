"""
Data integrity validation and recovery for TaskTitan.

This module provides functions to check database integrity,
validate data consistency, and recover from corrupted data.
"""

import sqlite3
import os
from typing import List, Tuple, Dict, Optional
from datetime import datetime
from app.utils.logger import get_logger
from app.models.database import get_db_path
from app.utils.backup_manager import BackupManager

logger = get_logger(__name__)


class DataValidator:
    """Validates data integrity and consistency."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize data validator."""
        self.db_path = db_path or get_db_path()
        self.backup_manager = BackupManager()
    
    def check_database_integrity(self) -> Tuple[bool, List[str]]:
        """
        Check database integrity using SQLite integrity check.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            if not os.path.exists(self.db_path):
                errors.append("Database file does not exist")
                return False, errors
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            if result and result[0] != 'ok':
                errors.append(f"Integrity check failed: {result[0]}")
                conn.close()
                return False, errors
            
            # Check foreign key constraints
            cursor.execute("PRAGMA foreign_key_check")
            fk_errors = cursor.fetchall()
            
            if fk_errors:
                errors.append(f"Foreign key violations found: {len(fk_errors)}")
                for error in fk_errors[:10]:  # Limit to first 10
                    errors.append(f"  Table: {error[0]}, Row: {error[1]}, Referenced: {error[2]}")
            
            conn.close()
            
            return len(errors) == 0, errors
            
        except Exception as e:
            error_msg = f"Error checking database integrity: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            return False, errors
    
    def check_data_consistency(self) -> Tuple[bool, List[str]]:
        """
        Check data consistency across tables.
        
        Returns:
            Tuple of (is_consistent, list_of_issues)
        """
        issues = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for orphaned records
            # Activities referencing non-existent goals
            cursor.execute("""
                SELECT COUNT(*) FROM activities a
                LEFT JOIN goals g ON a.goal_id = g.id
                WHERE a.goal_id IS NOT NULL AND g.id IS NULL
            """)
            orphaned_activities = cursor.fetchone()[0]
            if orphaned_activities > 0:
                issues.append(f"Found {orphaned_activities} activities referencing non-existent goals")
            
            # Activity completions referencing non-existent activities
            cursor.execute("""
                SELECT COUNT(*) FROM activity_completions ac
                LEFT JOIN activities a ON ac.activity_id = a.id
                WHERE a.id IS NULL
            """)
            orphaned_completions = cursor.fetchone()[0]
            if orphaned_completions > 0:
                issues.append(f"Found {orphaned_completions} completions referencing non-existent activities")
            
            # Goals referencing non-existent parent goals
            cursor.execute("""
                SELECT COUNT(*) FROM goals g1
                LEFT JOIN goals g2 ON g1.parent_id = g2.id
                WHERE g1.parent_id IS NOT NULL AND g2.id IS NULL
            """)
            orphaned_goals = cursor.fetchone()[0]
            if orphaned_goals > 0:
                issues.append(f"Found {orphaned_goals} goals referencing non-existent parent goals")
            
            # Check for invalid dates
            cursor.execute("""
                SELECT COUNT(*) FROM activities
                WHERE date NOT LIKE '____-__-__' OR date < '1900-01-01' OR date > '2100-12-31'
            """)
            invalid_dates = cursor.fetchone()[0]
            if invalid_dates > 0:
                issues.append(f"Found {invalid_dates} activities with invalid dates")
            
            # Check for invalid times
            cursor.execute("""
                SELECT COUNT(*) FROM activities
                WHERE start_time NOT LIKE '__:__:__' AND start_time NOT LIKE '__:__'
                OR end_time NOT LIKE '__:__:__' AND end_time NOT LIKE '__:__'
            """)
            invalid_times = cursor.fetchone()[0]
            if invalid_times > 0:
                issues.append(f"Found {invalid_times} activities with invalid times")
            
            conn.close()
            
            return len(issues) == 0, issues
            
        except Exception as e:
            error_msg = f"Error checking data consistency: {e}"
            logger.error(error_msg, exc_info=True)
            issues.append(error_msg)
            return False, issues
    
    def repair_database(self) -> Tuple[bool, List[str]]:
        """
        Attempt to repair database issues.
        
        Returns:
            Tuple of (success, list_of_actions_taken)
        """
        actions = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Remove orphaned activity completions
            cursor.execute("""
                DELETE FROM activity_completions
                WHERE activity_id NOT IN (SELECT id FROM activities)
            """)
            deleted_completions = cursor.rowcount
            if deleted_completions > 0:
                actions.append(f"Removed {deleted_completions} orphaned activity completions")
            
            # Remove orphaned activities (activities referencing non-existent goals)
            cursor.execute("""
                UPDATE activities
                SET goal_id = NULL
                WHERE goal_id IS NOT NULL
                AND goal_id NOT IN (SELECT id FROM goals)
            """)
            fixed_activities = cursor.rowcount
            if fixed_activities > 0:
                actions.append(f"Fixed {fixed_activities} activities with invalid goal references")
            
            # Remove orphaned goals (goals referencing non-existent parents)
            cursor.execute("""
                UPDATE goals
                SET parent_id = NULL
                WHERE parent_id IS NOT NULL
                AND parent_id NOT IN (SELECT id FROM goals)
            """)
            fixed_goals = cursor.rowcount
            if fixed_goals > 0:
                actions.append(f"Fixed {fixed_goals} goals with invalid parent references")
            
            conn.commit()
            conn.close()
            
            logger.info(f"Database repair completed. Actions: {actions}")
            return True, actions
            
        except Exception as e:
            error_msg = f"Error repairing database: {e}"
            logger.error(error_msg, exc_info=True)
            return False, [error_msg]
    
    def recover_from_corruption(self, backup_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Recover database from corruption using backup.
        
        Args:
            backup_path: Optional path to specific backup. If None, uses most recent.
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # If no backup specified, find most recent backup
            if not backup_path:
                backups = self.backup_manager.list_backups()
                if not backups:
                    error = "No backups available for recovery"
                    logger.error(error)
                    return False, error
                
                # Find first verified backup
                backup_path = None
                for path, info in backups:
                    if info.get('verified', False):
                        backup_path = path
                        break
                
                if not backup_path:
                    error = "No verified backups available for recovery"
                    logger.error(error)
                    return False, error
            
            # Restore backup
            logger.info(f"Attempting to recover from backup: {backup_path}")
            success, error = self.backup_manager.restore_backup(backup_path)
            
            if success:
                logger.info("Database recovery successful")
                return True, None
            else:
                return False, error
                
        except Exception as e:
            error_msg = f"Error during recovery: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def validate_export_data(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate exported data structure.
        
        Args:
            data: Exported data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check required top-level keys
        required_keys = ['version', 'export_date']
        for key in required_keys:
            if key not in data:
                issues.append(f"Missing required key: {key}")
        
        # Validate version
        if 'version' in data:
            try:
                version = float(data['version'])
                if version < 1.0 or version > 10.0:
                    issues.append(f"Invalid version number: {version}")
            except (ValueError, TypeError):
                issues.append("Invalid version format")
        
        # Validate export date
        if 'export_date' in data:
            try:
                datetime.fromisoformat(data['export_date'])
            except (ValueError, TypeError):
                issues.append("Invalid export_date format")
        
        # Check for data sections
        data_sections = ['goals', 'activities', 'settings']
        has_data = any(section in data for section in data_sections)
        if not has_data:
            issues.append("No data sections found in export")
        
        return len(issues) == 0, issues


def validate_database() -> Tuple[bool, List[str]]:
    """
    Validate database integrity and consistency (convenience function).
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    validator = DataValidator()
    
    # Check integrity
    integrity_ok, integrity_errors = validator.check_database_integrity()
    
    # Check consistency
    consistency_ok, consistency_issues = validator.check_data_consistency()
    
    all_issues = integrity_errors + consistency_issues
    is_valid = integrity_ok and consistency_ok
    
    return is_valid, all_issues

