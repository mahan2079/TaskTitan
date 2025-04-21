import sqlite3
from datetime import datetime, timedelta
from app.models.database_schema import CREATE_TABLES_SQL

def initialize_db():
    """Initialize the database with the required tables."""
    conn = sqlite3.connect("tasktitan.db")
    cursor = conn.cursor()
    
    # Create activities table (unified system for tasks, events, habits)
    cursor.execute(CREATE_TABLES_SQL["activities"])
    
    # Create goals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER,
            title TEXT NOT NULL,
            due_date DATE,
            due_time TIME,
            completed INTEGER DEFAULT 0,
            priority INTEGER DEFAULT 1
        )
    """)
    
    # Drop weekly_tasks table if it exists (to resolve schema issues)
    cursor.execute("DROP TABLE IF EXISTS weekly_tasks")
    
    # Create weekly_tasks table with correct schema
    cursor.execute("""
        CREATE TABLE weekly_tasks (
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
    
    # Create pomodoro_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            duration INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            completed INTEGER DEFAULT 0,
            date DATE DEFAULT CURRENT_DATE
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
    
    try:
        cursor.execute("ALTER TABLE habits ADD COLUMN created_at TEXT DEFAULT CURRENT_DATE")
    except sqlite3.OperationalError:
        pass  # Column already exists 