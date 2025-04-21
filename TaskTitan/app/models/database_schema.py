"""
Database schema definitions for TaskTitan.

This module contains the SQL statements for creating and updating the database schema.
"""

# Table creation statements
CREATE_TABLES_SQL = {
    "activities": """
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            completed INTEGER DEFAULT 0,
            type TEXT NOT NULL,  -- 'task', 'event', or 'habit'
            priority INTEGER DEFAULT 1,  -- For tasks: 0=Low, 1=Medium, 2=High
            category TEXT,  -- For categorization: Work, Personal, Health, etc.
            days_of_week TEXT,  -- For habits: comma-separated list of days
            goal_id INTEGER,  -- For tasks associated with a goal
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL
        )
    """,
    
    "goals": """
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            due_date DATE,
            completed INTEGER DEFAULT 0,
            priority INTEGER DEFAULT 1,
            progress_type TEXT DEFAULT 'manual',  -- 'manual', 'tasks', 'time'
            target_value REAL,
            current_value REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE CASCADE
        )
    """,
    
    "activity_tags": """
        CREATE TABLE IF NOT EXISTS activity_tags (
            activity_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            PRIMARY KEY (activity_id, tag),
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
        )
    """,
    
    "productivity_sessions": """
        CREATE TABLE IF NOT EXISTS productivity_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER,
            date DATE,
            start_time TIME,
            end_time TIME,
            duration_minutes INTEGER,
            distractions INTEGER DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE SET NULL
        )
    """,
    
    "pomodoro_sessions": """
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER,
            duration INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            completed INTEGER DEFAULT 0,
            date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE SET NULL
        )
    """,
    
    "daily_notes": """
        CREATE TABLE IF NOT EXISTS daily_notes (
            date DATE PRIMARY KEY,
            note TEXT
        )
    """
}

# Migration scripts to update schema
MIGRATION_SCRIPTS = [
    # Migration 1: Convert existing tables to unified schema
    """
    -- Create the activities table if it doesn't exist
    {CREATE_TABLES_SQL[activities]}
    
    -- Migrate tasks to activities
    INSERT INTO activities (
        title, date, start_time, end_time, completed, type, 
        priority, category, goal_id, created_at
    )
    SELECT 
        description, due_date, due_time, 
        CASE WHEN due_time IS NULL THEN '00:00' ELSE due_time END,
        CASE WHEN due_time IS NULL THEN '01:00' ELSE time(due_time, '+1 hour') END,
        completed, 'task', priority, 'Other', goal_id, CURRENT_TIMESTAMP
    FROM tasks;
    
    -- Migrate events to activities
    INSERT INTO activities (
        title, date, start_time, end_time, completed, type,
        category, created_at
    )
    SELECT 
        description, date, time, 
        CASE WHEN time IS NULL THEN '00:00' ELSE time END,
        CASE WHEN time IS NULL THEN '01:00' ELSE time(time, '+1 hour') END,
        completed, 'event', 'Other', CURRENT_TIMESTAMP
    FROM events;
    
    -- Migrate habits to activities
    INSERT INTO activities (
        title, date, start_time, end_time, completed, type,
        days_of_week, category, created_at
    )
    SELECT 
        name, created_at, time, 
        CASE WHEN time IS NULL THEN '00:00' ELSE time END,
        CASE WHEN time IS NULL THEN '01:00' ELSE time(time, '+30 minutes') END,
        0, 'habit', days_of_week, 'Other', created_at
    FROM habits;
    """
]

# Schema version tracking
SCHEMA_VERSION = 1 