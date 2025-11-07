"""
Database operations utilities for TaskTitan.
Handles database export, import, merge, and validation operations.
"""

import os
import shutil
import sqlite3
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
from datetime import datetime
from app.utils.logger import get_logger
from app.models.database import get_db_path

logger = get_logger(__name__)


class DatabaseOperations:
    """Utility class for database operations."""
    
    @staticmethod
    def export_database(source_path: str, destination_path: str, 
                       encrypt: bool = False, password: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Export database to a file.
        
        Args:
            source_path: Path to source database
            destination_path: Path to save exported database
            encrypt: Whether to encrypt the exported database
            password: Password for encryption (if encrypt=True)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not os.path.exists(source_path):
                return False, "Source database not found"
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            # Copy database
            shutil.copy2(source_path, destination_path)
            
            if encrypt and password:
                from app.utils.database_encryption import get_encryption_manager
                enc_manager = get_encryption_manager()
                success, error = enc_manager.encrypt_database(destination_path, password)
                if not success:
                    return False, error
            
            logger.info(f"Exported database from {source_path} to {destination_path}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error exporting database: {e}", exc_info=True)
            return False, str(e)
    
    @staticmethod
    def import_database(source_path: str, destination_path: str,
                       is_encrypted: bool = False, password: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Import database from a file.
        
        Args:
            source_path: Path to source database file
            destination_path: Path to save imported database
            is_encrypted: Whether source database is encrypted
            password: Password for decryption (if is_encrypted=True)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not os.path.exists(source_path):
                return False, "Source database not found"
            
            # Validate source database
            if is_encrypted and password:
                from app.utils.database_encryption import get_encryption_manager
                enc_manager = get_encryption_manager()
                conn = enc_manager.connect_encrypted_database(source_path, password)
                if not conn:
                    return False, "Failed to decrypt database or incorrect password"
                conn.close()
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            # Copy database
            shutil.copy2(source_path, destination_path)
            
            logger.info(f"Imported database from {source_path} to {destination_path}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error importing database: {e}", exc_info=True)
            return False, str(e)
    
    @staticmethod
    def merge_databases(source_path: str, destination_path: str,
                       merge_conflict_strategy: str = 'skip') -> Tuple[bool, Optional[str], Dict[str, int]]:
        """
        Merge two databases.
        
        Args:
            source_path: Path to source database to merge from
            destination_path: Path to destination database to merge into
            merge_conflict_strategy: How to handle conflicts ('skip', 'replace', 'rename')
            
        Returns:
            Tuple of (success, error_message, merge_stats)
        """
        stats = {
            'activities_added': 0,
            'goals_added': 0,
            'activities_skipped': 0,
            'goals_skipped': 0
        }
        
        try:
            if not os.path.exists(source_path):
                return False, "Source database not found", stats
            
            if not os.path.exists(destination_path):
                return False, "Destination database not found", stats
            
            # Connect to both databases
            source_conn = sqlite3.connect(source_path)
            source_cursor = source_conn.cursor()
            
            dest_conn = sqlite3.connect(destination_path)
            dest_cursor = dest_conn.cursor()
            
            # Merge activities
            source_cursor.execute("SELECT * FROM activities")
            activities = source_cursor.fetchall()
            
            dest_cursor.execute("SELECT id FROM activities")
            existing_ids = {row[0] for row in dest_cursor.fetchall()}
            
            for activity in activities:
                activity_id = activity[0]
                if activity_id in existing_ids:
                    if merge_conflict_strategy == 'skip':
                        stats['activities_skipped'] += 1
                        continue
                    elif merge_conflict_strategy == 'replace':
                        # Delete existing and insert new
                        dest_cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
                
                # Insert activity
                dest_cursor.execute("""
                    INSERT INTO activities 
                    (title, date, start_time, end_time, completed, type, priority, category, 
                     days_of_week, goal_id, created_at, updated_at, color)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, activity[1:])
                stats['activities_added'] += 1
            
            # Merge goals
            source_cursor.execute("SELECT * FROM goals")
            goals = source_cursor.fetchall()
            
            dest_cursor.execute("SELECT id FROM goals")
            existing_goal_ids = {row[0] for row in dest_cursor.fetchall()}
            
            for goal in goals:
                goal_id = goal[0]
                if goal_id in existing_goal_ids:
                    if merge_conflict_strategy == 'skip':
                        stats['goals_skipped'] += 1
                        continue
                    elif merge_conflict_strategy == 'replace':
                        dest_cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
                
                # Insert goal
                dest_cursor.execute("""
                    INSERT INTO goals 
                    (parent_id, title, created_date, due_date, due_time, completed, priority, color)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, goal[1:])
                stats['goals_added'] += 1
            
            dest_conn.commit()
            source_conn.close()
            dest_conn.close()
            
            logger.info(f"Merged database: {stats}")
            return True, None, stats
            
        except Exception as e:
            logger.error(f"Error merging databases: {e}", exc_info=True)
            return False, str(e), stats
    
    @staticmethod
    def validate_database(db_path: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate database integrity.
        
        Args:
            db_path: Path to database file
            
        Returns:
            Tuple of (is_valid, error_message, warnings)
        """
        warnings = []
        
        try:
            if not os.path.exists(db_path):
                return False, "Database file not found", warnings
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check for required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['activities', 'goals', 'users']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                return False, f"Missing required tables: {', '.join(missing_tables)}", warnings
            
            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()
            
            if integrity_result and integrity_result[0] != 'ok':
                warnings.append(f"Integrity check issue: {integrity_result[0]}")
            
            # Check foreign key constraints
            cursor.execute("PRAGMA foreign_key_check")
            foreign_key_issues = cursor.fetchall()
            
            if foreign_key_issues:
                warnings.append(f"Found {len(foreign_key_issues)} foreign key constraint violations")
            
            conn.close()
            
            return True, None, warnings
            
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}", warnings
        except Exception as e:
            logger.error(f"Error validating database: {e}", exc_info=True)
            return False, str(e), warnings
    
    @staticmethod
    def get_database_stats(db_path: str) -> Dict[str, Any]:
        """
        Get statistics about a database.
        
        Args:
            db_path: Path to database file
            
        Returns:
            Dictionary with database statistics
        """
        stats = {
            'file_size': 0,
            'file_size_mb': 0,
            'last_modified': None,
            'tables': {},
            'total_records': 0
        }
        
        try:
            if not os.path.exists(db_path):
                return stats
            
            # File stats
            file_stat = os.stat(db_path)
            stats['file_size'] = file_stat.st_size
            stats['file_size_mb'] = file_stat.st_size / (1024 * 1024)
            stats['last_modified'] = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            # Database stats
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats['tables'][table] = count
                stats['total_records'] += count
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}", exc_info=True)
        
        return stats

