#!/usr/bin/env python3
"""
Database repair script for TaskTitan application.
Run this script to fix database schema issues.
"""

import os
import sys
import sqlite3
from pathlib import Path

def repair_database():
    """Fix database schema issues by creating missing tables and columns."""
    print("TaskTitan Database Repair Tool")
    print("------------------------------")
    
    # Check for existing database
    db_path = "tasktitan.db"
    if os.path.exists(db_path):
        print(f"Found existing database at: {os.path.abspath(db_path)}")
        print("Deleting existing database and creating a new one.")
        os.remove(db_path)
    else:
        print(f"No existing database found. Creating new database at: {os.path.abspath(db_path)}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nRepairing database schema...")
    
    # Fix weekly_tasks table
    print("- Fixing weekly_tasks table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT '',
            date DATE NOT NULL DEFAULT CURRENT_DATE,
            start_time TIME NOT NULL DEFAULT '09:00',
            end_time TIME NOT NULL DEFAULT '10:00',
            category TEXT NOT NULL DEFAULT 'Other',
            completed INTEGER DEFAULT 0,
            parent_id INTEGER,
            description TEXT,
            due_date DATE,
            due_time TIME,
            week_start_date DATE DEFAULT CURRENT_DATE
        )
    """)
    
    # Fix goals table
    print("- Fixing goals table")
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
    
    # Fix habits table
    print("- Fixing habits table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time TEXT NOT NULL,
            days_of_week TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_DATE
        )
    """)
    
    # Fix habit_completions table
    print("- Fixing habit_completions table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completion_date DATE NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
        )
    """)
    
    # Fix pomodoro_sessions table
    print("- Fixing pomodoro_sessions table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            duration INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            completed INTEGER DEFAULT 0,
            date DATE
        )
    """)
    
    # Add missing columns (safe to run even if columns already exist)
    try_add_column(cursor, "weekly_tasks", "category", "TEXT", "'Other'")
    try_add_column(cursor, "weekly_tasks", "date", "DATE", "CURRENT_DATE")
    try_add_column(cursor, "weekly_tasks", "start_time", "TIME", "'09:00'")
    try_add_column(cursor, "weekly_tasks", "end_time", "TIME", "'10:00'")
    try_add_column(cursor, "weekly_tasks", "week_start_date", "DATE", "CURRENT_DATE")
    
    try_add_column(cursor, "goals", "priority", "INTEGER", "1")
    try_add_column(cursor, "habits", "created_at", "TEXT", "CURRENT_DATE")
    try_add_column(cursor, "pomodoro_sessions", "date", "DATE", "CURRENT_DATE")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\nDatabase repair completed successfully!")
    print(f"Database location: {os.path.abspath(db_path)}")
    print("\nYou can now run the TaskTitan application.")

def try_add_column(cursor, table, column, data_type, default_value):
    """Try to add a column to a table, ignoring errors if it already exists."""
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {data_type} DEFAULT {default_value}")
        print(f"  - Added column '{column}' to table '{table}'")
    except sqlite3.OperationalError:
        # Column already exists
        pass

if __name__ == "__main__":
    repair_database() 