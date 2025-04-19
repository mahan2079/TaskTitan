import sqlite3
from datetime import datetime, timedelta

def initialize_db():
    """Initialize the database with the required tables."""
    conn = sqlite3.connect("planner.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
                   
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER,
            title TEXT NOT NULL,
            due_date DATE,
            due_time TIME,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE CASCADE
        )
    """)
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER,
            week_start_date DATE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            due_date DATE,
            due_time TIME,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (parent_id) REFERENCES weekly_tasks(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time TEXT NOT NULL,
            days_of_week TEXT NOT NULL
        )
    """)
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_notes (
            date DATE PRIMARY KEY,
            note TEXT
        )
    """)
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
    
    # Update the schema for weekly_tasks
    update_database_schema(cursor)
    
    conn.commit()
    return conn, cursor

def update_database_schema(cursor):
    """Update database schema for existing tables."""
    try:
        cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN parent_id INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN title TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN description TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN due_date DATE")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN due_time TIME")
    except sqlite3.OperationalError:
        pass  # Column already exists 