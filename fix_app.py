#!/usr/bin/env python3
"""
Fix TaskTitan database schema
"""

import sys
import os
import sqlite3

def fix_database():
    """Fix the database schema by recreating the problematic tables."""
    print("TaskTitan Database Fix Tool")
    print("---------------------------")
    
    db_path = "tasktitan.db"
    
    if not os.path.exists(db_path):
        print(f"No database found at {db_path}. Creating new database.")
    else:
        print(f"Fixing existing database at {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Delete the problematic tables
    print("Dropping problematic tables...")
    tables_to_drop = ["weekly_tasks", "pomodoro_sessions"]
    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"- Dropped table {table}")
        except sqlite3.Error as e:
            print(f"Error dropping {table}: {e}")
    
    # Create weekly_tasks table with correct schema
    print("Creating weekly_tasks table...")
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
    
    # Create pomodoro_sessions table
    print("Creating pomodoro_sessions table...")
    cursor.execute("""
        CREATE TABLE pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            duration INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            completed INTEGER DEFAULT 0,
            date DATE DEFAULT CURRENT_DATE
        )
    """)
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("Database fix completed successfully!")
    print(f"Database location: {os.path.abspath(db_path)}")
    print("\nYou can now run the TaskTitan application.")

if __name__ == "__main__":
    fix_database() 