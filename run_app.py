#!/usr/bin/env python3
"""
TaskTitan Application Launcher with Database Initialization
"""

import os
import sys
import sqlite3
from pathlib import Path

def initialize_database():
    """Initialize the database with required tables."""
    print("Initializing database...")
    
    db_path = "tasktitan.db"
    if not os.path.exists(db_path):
        print(f"Creating new database at: {os.path.abspath(db_path)}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create weekly_tasks table
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
    
    # Create tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_id INTEGER,
        description TEXT NOT NULL,
        duration_minutes INTEGER,
        completed INTEGER DEFAULT 0
    )
    """)
    
    # Create habits table
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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habit_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER NOT NULL,
        completion_date DATE NOT NULL
    )
    """)
    
    # Create events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
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
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def run_app():
    """Run the TaskTitan application."""
    print("Starting TaskTitan application...")
    
    try:
        # Initialize the database first
        initialize_database()
        
        # Import the application code
        print("Creating QApplication...")
        import sys
        import asyncio
        import qasync
        from PyQt6.QtWidgets import QApplication
        from TaskTitan.app.views.main_window import TaskTitanApp
        from TaskTitan.app.resources import APP_NAME, APP_VERSION
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Set up stylesheet
        app.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #F8FAFC;
                color: #0F172A;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 14px;
            }
            
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #818CF8;
            }
        """)
        
        # Create and show main window
        print("Creating main window...")
        try:
            window = TaskTitanApp()
            window.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
            window.show()
            
            # Set up async event loop
            loop = qasync.QEventLoop(app)
            asyncio.set_event_loop(loop)
            
            # Run the application
            with loop:
                sys.exit(loop.run_forever())
        except Exception as e:
            print(f"Error creating or showing main window: {e}")
            raise
            
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_app()) 