#!/usr/bin/env python3
"""
Database creation script for TaskTitan application.
"""

import os
import sqlite3

def create_database():
    """Create a fresh database with the correct schema."""
    print("TaskTitan Database Creation Tool")
    print("-------------------------------")
    
    # Create database in the current directory
    db_path = "tasktitan.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    print("Creating tables...")
    
    # Create weekly_tasks table
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
    
    # Create goals table
    cursor.execute("""
    CREATE TABLE goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER,
        title TEXT NOT NULL,
        due_date DATE,
        due_time TIME,
        completed INTEGER DEFAULT 0,
        priority INTEGER DEFAULT 1
    )
    """)
    
    # Create tasks table
    cursor.execute("""
    CREATE TABLE tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_id INTEGER,
        description TEXT NOT NULL,
        duration_minutes INTEGER,
        completed INTEGER DEFAULT 0
    )
    """)
    
    # Create habits table
    cursor.execute("""
    CREATE TABLE habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        time TEXT NOT NULL,
        days_of_week TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_DATE
    )
    """)
    
    # Create habit_completions table
    cursor.execute("""
    CREATE TABLE habit_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER NOT NULL,
        completion_date DATE NOT NULL
    )
    """)
    
    # Create events table
    cursor.execute("""
    CREATE TABLE events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        time TEXT NOT NULL,
        description TEXT NOT NULL,
        type TEXT DEFAULT 'event',
        completed INTEGER DEFAULT 0
    )
    """)
    
    # Create daily_notes table
    cursor.execute("""
    CREATE TABLE daily_notes (
        date DATE PRIMARY KEY,
        note TEXT
    )
    """)
    
    # Create productivity_sessions table
    cursor.execute("""
    CREATE TABLE productivity_sessions (
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
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database created successfully at: {os.path.abspath(db_path)}")
    print("You can now run the TaskTitan application.")

if __name__ == "__main__":
    create_database() 