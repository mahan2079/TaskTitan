"""
Fix TaskTitan database
"""

import os
import sqlite3

# Path to database
db_path = "tasktitan.db"

# Remove existing database if it exists
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Removed existing database: {db_path}")

# Create a new database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables
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

cursor.execute("""
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER,
    description TEXT NOT NULL,
    duration_minutes INTEGER,
    completed INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    time TEXT NOT NULL,
    days_of_week TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_DATE
)
""")

cursor.execute("""
CREATE TABLE habit_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    completion_date DATE NOT NULL
)
""")

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

cursor.execute("""
CREATE TABLE daily_notes (
    date DATE PRIMARY KEY,
    note TEXT
)
""")

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

# Commit changes and close
conn.commit()
conn.close()

print(f"Created new database at {os.path.abspath(db_path)}")
print("You can now run the TaskTitan application.") 