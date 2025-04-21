import os
import sqlite3
import shutil
from datetime import datetime

def get_db_path():
    """Get the path to the database file."""
    # Get app data directory
    app_data_dir = os.path.join(os.path.expanduser("~"), ".tasktitan")
    
    # Create directory if it doesn't exist
    os.makedirs(app_data_dir, exist_ok=True)
    
    # Return path to database file
    return os.path.join(app_data_dir, "tasktitan.db")

def create_tables(conn=None, cursor=None):
    """Create database tables if they don't exist."""
    # Connect to database if connection not provided
    if not conn or not cursor:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        close_after = True
    else:
        close_after = False
    
    try:
        # Create tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority INTEGER DEFAULT 0,
                category TEXT,
                status INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                created_at TEXT,
                modified_at TEXT
            )
        ''')
        
        # Create events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                date TEXT,
                start_time TEXT,
                end_time TEXT,
                category TEXT,
                created_at TEXT,
                modified_at TEXT
            )
        ''')
        
        # Create habits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                days_of_week TEXT,
                start_time TEXT,
                end_time TEXT,
                category TEXT,
                completed BOOLEAN DEFAULT 0,
                created_at TEXT,
                modified_at TEXT
            )
        ''')
        
        # Create categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT,
                created_at TEXT,
                modified_at TEXT
            )
        ''')
        
        # Create unified activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                date TEXT,
                start_time TEXT,
                end_time TEXT,
                completed BOOLEAN DEFAULT 0,
                type TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                category TEXT,
                days_of_week TEXT,
                goal_id INTEGER,
                created_at TEXT,
                modified_at TEXT
            )
        ''')
        
        # Commit changes
        conn.commit()
    finally:
        # Close connection if we opened it
        if close_after:
            conn.close()

def backup_database():
    """Create a backup of the database file."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return False
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    # Copy database file to backup
    shutil.copy2(db_path, backup_path)
    
    return backup_path

def restore_database(backup_path):
    """Restore database from a backup file."""
    db_path = get_db_path()
    
    # Check if backup file exists
    if not os.path.exists(backup_path):
        return False
    
    # Create a backup of current database before restoring
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore_backup = f"{db_path}.pre_restore_{timestamp}"
        shutil.copy2(db_path, pre_restore_backup)
    
    # Copy backup file to database path
    shutil.copy2(backup_path, db_path)
    
    return True 