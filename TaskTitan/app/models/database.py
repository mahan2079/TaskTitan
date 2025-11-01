import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import Optional
from app.models.database_schema import CREATE_TABLES_SQL
from app.utils.logger import get_logger
from app.core.config import get_config

logger = get_logger(__name__)

def get_db_path():
    """Get the path to the database file in the same directory as the executable."""
    # Check if a custom database path is set in config
    custom_path = get_config('database.current_path', None)
    if custom_path and os.path.exists(custom_path):
        return custom_path
    
    # For PyInstaller executables, get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Create database in the same directory as the executable
    db_path = os.path.join(base_dir, 'tasktitan.db')
    
    return db_path

def set_current_database(db_path: str):
    """
    Set the current database path.
    
    Args:
        db_path: Path to the database file
    """
    from app.core.config import set_config
    set_config('database.current_path', db_path)
    logger.info(f"Current database set to: {db_path}")

def get_current_database() -> str:
    """
    Get the current database path.
    
    Returns:
        Path to the current database file
    """
    return get_db_path()

def initialize_db(db_path: Optional[str] = None):
    """Initialize the database with the required tables.
    
    Args:
        db_path: Optional specific database path. If None, uses get_db_path().
    """
    if db_path is None:
        db_path = get_db_path()
    
    # Check database integrity on startup if configured
    integrity_check = get_config('database.integrity_check_on_startup', False)
    if integrity_check and os.path.exists(db_path):
        try:
            from app.utils.data_validator import DataValidator
            validator = DataValidator(db_path)
            is_valid, errors = validator.check_database_integrity()
            if not is_valid:
                logger.warning(f"Database integrity issues detected: {errors}")
                # Attempt repair
                repair_success, repair_actions = validator.repair_database()
                if repair_success:
                    logger.info(f"Database repair completed: {repair_actions}")
                else:
                    logger.error(f"Database repair failed: {repair_actions}")
        except Exception as e:
            logger.warning(f"Could not perform integrity check: {e}")
    
    # Create backup on startup if configured
    backup_on_startup = get_config('database.backup_on_startup', False)
    if backup_on_startup and os.path.exists(db_path):
        try:
            from app.utils.backup_manager import BackupManager
            backup_manager = BackupManager()
            backup_manager.create_backup()
        except Exception as e:
            logger.warning(f"Could not create startup backup: {e}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table for authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Create activities table (unified system for tasks, events, habits)
    cursor.execute(CREATE_TABLES_SQL["activities"])
    
    # Create goals table (includes created_date and color to match UI expectations)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER,
            title TEXT NOT NULL,
            created_date DATE,
            due_date DATE,
            due_time TIME,
            completed INTEGER DEFAULT 0,
            priority INTEGER DEFAULT 1,
            color TEXT,
            FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE CASCADE
        )
    """)
    
    # Create journal_entries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            id TEXT PRIMARY KEY,
            date TEXT UNIQUE,
            wins TEXT,
            challenges TEXT,
            learnings TEXT,
            tomorrow TEXT,
            gratitude TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create journal_attachments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            file_path TEXT NOT NULL
        )
    """)
    
    # Create time_entries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_entries (
            id TEXT PRIMARY KEY,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            category TEXT,
            description TEXT,
            energy_level INTEGER,
            mood_level INTEGER
        )
    """)
    
    # Create time_categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_categories (
            name TEXT PRIMARY KEY,
            color TEXT,
            description TEXT
        )
    """)
    
    # Create weekly_tasks table with correct schema (no destructive drop)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT '',
            date DATE DEFAULT CURRENT_DATE,
            start_time TIME DEFAULT '09:00',
            end_time TIME DEFAULT '10:00',
            category TEXT DEFAULT 'Other',
            completed INTEGER DEFAULT 0,
            parent_id INTEGER,
            description TEXT,
            due_date DATE,
            due_time TIME,
            week_start_date DATE DEFAULT CURRENT_DATE
        )
    """)
    
    # Create old tables for backward compatibility
    # Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER,
            description TEXT NOT NULL,
            duration_minutes INTEGER,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
        )
    """)
    
    # Habits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time TEXT NOT NULL,
            days_of_week TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_DATE
        )
    """)
    
    # Habit completions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completion_date DATE NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
        )
    """)
    
    # Events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            time TEXT NOT NULL,
            description TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'event',
            completed INTEGER DEFAULT 0
        )
    """)
    
    # Create daily_notes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_notes (
            date DATE PRIMARY KEY,
            note TEXT
        )
    """)
    
    # Create productivity_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productivity_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_title TEXT NOT NULL,
            date DATE,
            start_time TIME,
            end_time TIME,
            duration_minutes INTEGER,
            distractions INTEGER DEFAULT 0,
            tag TEXT
        )
    """)
    
    # Create pomodoro_sessions table (align with PomodoroWidget usage)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            date DATE,
            start_time TIME,
            end_time TIME,
            duration_minutes INTEGER,
            completed INTEGER DEFAULT 0,
            task_id INTEGER,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
        )
    """)

    # Create activity_completions table used by ActivitiesManager
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_completions (
            activity_id INTEGER NOT NULL,
            completion_date DATE NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (activity_id, completion_date),
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
        )
    """)
    
    # Create migration trigger to update timestamps
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_activity_timestamp 
        AFTER UPDATE ON activities
        BEGIN
            UPDATE activities SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = NEW.id;
        END;
    """)
    
    # Apply incremental schema updates for existing databases
    try:
        update_database_schema(cursor)
    except Exception as e:
        logger.warning(f"update_database_schema failed: {e}", exc_info=True)

    conn.commit()
    return conn, cursor

def update_database_schema(cursor):
    """Update database schema for existing tables."""
    try:
        cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN category TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE goals ADD COLUMN priority INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Ensure goals table has created_date, due_time and color columns
    try:
        cursor.execute("ALTER TABLE goals ADD COLUMN created_date DATE")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE goals ADD COLUMN due_time TIME")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE goals ADD COLUMN color TEXT")
    except sqlite3.OperationalError:
        pass

    # Ensure tasks table has expected columns used by views
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN due_date DATE")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN due_time TIME")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN title TEXT")
    except sqlite3.OperationalError:
        pass
    # Backfill title from description if empty or NULL
    try:
        cursor.execute("UPDATE tasks SET title = description WHERE (title IS NULL OR title = '') AND description IS NOT NULL")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE habits ADD COLUMN created_at TEXT DEFAULT CURRENT_DATE")
    except sqlite3.OperationalError:
        pass  # Column already exists 

    # Ensure pomodoro_sessions has modern columns; add if missing
    try:
        cursor.execute("ALTER TABLE pomodoro_sessions ADD COLUMN type TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE pomodoro_sessions ADD COLUMN duration_minutes INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE pomodoro_sessions ADD COLUMN task_id INTEGER")
    except sqlite3.OperationalError:
        pass