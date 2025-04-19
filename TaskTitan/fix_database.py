import sqlite3
import os

def fix_database_schema():
    """Fix the database schema by adding missing tables and columns."""
    print("Initializing database schema...")
    
    # Create a new connection to the database
    db_path = "tasktitan.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fix weekly_tasks table
    print("Fixing weekly_tasks table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            category TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            parent_id INTEGER,
            description TEXT,
            due_date DATE,
            due_time TIME
        )
    """)
    
    # Fix goals table to include priority column
    print("Fixing goals table...")
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
    
    # Fix habits table to include created_at column
    print("Fixing habits table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time TEXT NOT NULL,
            days_of_week TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_DATE
        )
    """)
    
    # Create habit_completions table
    print("Creating habit_completions table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completion_date DATE NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
        )
    """)
    
    # Create pomodoro_sessions table
    print("Creating pomodoro_sessions table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            duration INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            completed INTEGER DEFAULT 0
        )
    """)
    
    # Update schema for existing tables (safe to run even if columns already exist)
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
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database schema has been fixed. Path: {os.path.abspath(db_path)}")
    
if __name__ == "__main__":
    fix_database_schema() 