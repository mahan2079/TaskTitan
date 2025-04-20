import sqlite3
import os
from datetime import datetime
import threading
from pathlib import Path

# Thread-local storage for database connections
local_storage = threading.local()

class DatabaseManager:
    """A singleton database manager to handle connections and transactions."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        """Initialize the database manager."""
        # Create an application data directory in user's home folder
        app_data_dir = os.path.join(str(Path.home()), '.tasktitan')
        
        # Create directory if it doesn't exist
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)
            
        # Set database path to an absolute path in the app data directory
        self.db_path = os.path.join(app_data_dir, 'tasktitan.db')
        print(f"Using database at: {self.db_path}")
        
        self.initialize_db()
    
    def get_connection(self):
        """Get a thread-local database connection."""
        if not hasattr(local_storage, "connection"):
            local_storage.connection = sqlite3.connect(self.db_path)
            # Enable foreign keys
            local_storage.connection.execute("PRAGMA foreign_keys = ON")
            # For better column access
            local_storage.connection.row_factory = sqlite3.Row
        
        return local_storage.connection
    
    def get_cursor(self):
        """Get a cursor from the thread-local connection."""
        conn = self.get_connection()
        if not hasattr(local_storage, "cursor"):
            local_storage.cursor = conn.cursor()
        return local_storage.cursor
    
    def close_connection(self):
        """Close the thread-local connection if it exists."""
        if hasattr(local_storage, "connection"):
            if hasattr(local_storage, "cursor"):
                local_storage.cursor.close()
                delattr(local_storage, "cursor")
                
            local_storage.connection.close()
            delattr(local_storage, "connection")
            
    def initialize_db(self):
        """Initialize the database with the required tables."""
        try:
            db_exists = os.path.exists(self.db_path)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create tables if they don't exist
            self._create_tables(cursor)
            
            # If the database already existed, check if we need to update the schema
            if db_exists:
                self._update_schema(cursor)
            
            conn.commit()
            conn.close()
            
            print("Database initialized successfully.")
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
            # Create a backup file if there was an error with the existing database
            if db_exists:
                self._backup_database()
                print("Created database backup due to error.")
    
    def _create_tables(self, cursor):
        """Create all required tables if they don't exist."""
        # Create goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                title TEXT NOT NULL,
                due_date DATE,
                due_time TIME,
                completed INTEGER DEFAULT 0,
                priority INTEGER DEFAULT 1,
                FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE CASCADE
            )
        """)
        
        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER,
                description TEXT NOT NULL,
                duration_minutes INTEGER,
                completed INTEGER DEFAULT 0,
                due_date DATE,
                due_time TIME,
                priority INTEGER DEFAULT 1,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
            )
        """)
        
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
                week_start_date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (parent_id) REFERENCES weekly_tasks(id) ON DELETE CASCADE
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
                completion_date DATE NOT NULL,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
            )
        """)
        
        # Create events table
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
    
    def _update_schema(self, cursor):
        """Update database schema if necessary."""
        try:
            # Check if any columns need to be added to existing tables
            
            # Check if priority column exists in tasks table
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'priority' not in columns:
                print("Adding priority column to tasks table")
                cursor.execute("ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 1")
            
            # Additional schema updates can be added here as needed
        except sqlite3.Error as e:
            print(f"Error updating schema: {e}")
    
    def _backup_database(self):
        """Create a backup of the database file."""
        if os.path.exists(self.db_path):
            backup_path = f"{self.db_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            try:
                import shutil
                shutil.copy2(self.db_path, backup_path)
                print(f"Database backup created at: {backup_path}")
            except Exception as e:
                print(f"Failed to create database backup: {e}")
    
    # Task operations
    def save_task(self, task_data):
        """Save a task to the database."""
        conn = self.get_connection()
        cursor = self.get_cursor()
        task_id = None
        
        try:
            # Check if this is an update or insert
            if 'id' in task_data and task_data['id']:
                # Update existing task
                cursor.execute("""
                    UPDATE tasks SET 
                        goal_id = ?,
                        description = ?,
                        duration_minutes = ?,
                        completed = ?,
                        due_date = ?,
                        due_time = ?,
                        priority = ?
                    WHERE id = ?
                """, (
                    task_data.get('goal_id'),
                    task_data['description'],
                    task_data.get('duration_minutes'),
                    1 if task_data.get('completed') else 0,
                    task_data.get('due_date'),
                    task_data.get('due_time'),
                    task_data.get('priority', 1),
                    task_data['id']
                ))
                task_id = task_data['id']
                
                # Verify the update worked
                if cursor.rowcount == 0:
                    print(f"Warning: Task update affected 0 rows, ID: {task_id}")
            else:
                # Insert new task
                cursor.execute("""
                    INSERT INTO tasks (
                        goal_id, description, duration_minutes, completed, due_date, due_time, priority
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_data.get('goal_id'),
                    task_data['description'],
                    task_data.get('duration_minutes'),
                    1 if task_data.get('completed') else 0,
                    task_data.get('due_date'),
                    task_data.get('due_time'),
                    task_data.get('priority', 1)
                ))
                task_id = cursor.lastrowid
                
                # Verify the insert worked
                if not task_id:
                    raise sqlite3.Error("Failed to get ID of inserted task")
            
            # Commit the changes
            conn.commit()
            
            # Double-check that the task exists in the database
            cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
            if not cursor.fetchone():
                raise sqlite3.Error(f"Task with ID {task_id} not found after save")
                
            print(f"Successfully saved task ID: {task_id}")
            return task_id
            
        except sqlite3.Error as e:
            # Roll back transaction on error
            conn.rollback()
            print(f"Error saving task: {e}")
            raise
    
    def get_tasks(self, goal_id=None, completed=None):
        """Get tasks from the database, optionally filtered."""
        cursor = self.get_cursor()
        
        query = "SELECT * FROM tasks"
        params = []
        
        # Build WHERE clause based on filters
        where_clauses = []
        
        if goal_id is not None:
            where_clauses.append("goal_id = ?")
            params.append(goal_id)
            
        if completed is not None:
            where_clauses.append("completed = ?")
            params.append(1 if completed else 0)
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY due_date, due_time"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_task(self, task_id):
        """Get a specific task by ID."""
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    def delete_task(self, task_id):
        """Delete a task by ID."""
        conn = self.get_connection()
        cursor = self.get_cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    def update_task_status(self, task_id, completed):
        """Update a task's completion status."""
        conn = self.get_connection()
        cursor = self.get_cursor()
        cursor.execute(
            "UPDATE tasks SET completed = ? WHERE id = ?", 
            (1 if completed else 0, task_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    
    # Goal operations
    def save_goal(self, goal_data):
        """Save a goal to the database."""
        conn = self.get_connection()
        cursor = self.get_cursor()
        goal_id = None
        
        try:
            # Check if this is an update or insert
            if 'id' in goal_data and goal_data['id']:
                # Update existing goal
                cursor.execute("""
                    UPDATE goals SET 
                        parent_id = ?,
                        title = ?,
                        due_date = ?,
                        due_time = ?,
                        completed = ?,
                        priority = ?
                    WHERE id = ?
                """, (
                    goal_data.get('parent_id'),
                    goal_data['title'],
                    goal_data.get('due_date'),
                    goal_data.get('due_time'),
                    1 if goal_data.get('completed') else 0,
                    goal_data.get('priority', 1),
                    goal_data['id']
                ))
                goal_id = goal_data['id']
                
                # Verify the update worked
                if cursor.rowcount == 0:
                    print(f"Warning: Goal update affected 0 rows, ID: {goal_id}")
            else:
                # Insert new goal
                cursor.execute("""
                    INSERT INTO goals (
                        parent_id, title, due_date, due_time, completed, priority
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    goal_data.get('parent_id'),
                    goal_data['title'],
                    goal_data.get('due_date'),
                    goal_data.get('due_time'),
                    1 if goal_data.get('completed') else 0,
                    goal_data.get('priority', 1)
                ))
                goal_id = cursor.lastrowid
                
                # Verify the insert worked
                if not goal_id:
                    raise sqlite3.Error("Failed to get ID of inserted goal")
            
            # Commit the changes
            conn.commit()
            
            # Double-check that the goal exists in the database
            cursor.execute("SELECT id FROM goals WHERE id = ?", (goal_id,))
            if not cursor.fetchone():
                raise sqlite3.Error(f"Goal with ID {goal_id} not found after save")
                
            print(f"Successfully saved goal ID: {goal_id}")
            return goal_id
            
        except sqlite3.Error as e:
            # Roll back transaction on error
            conn.rollback()
            print(f"Error saving goal: {e}")
            raise
    
    def get_goals(self, parent_id=None, completed=None):
        """Get goals from the database, optionally filtered."""
        cursor = self.get_cursor()
        
        query = "SELECT * FROM goals"
        params = []
        
        # Build WHERE clause based on filters
        where_clauses = []
        
        if parent_id is not None:
            where_clauses.append("parent_id IS NULL" if parent_id is None else "parent_id = ?")
            if parent_id is not None:
                params.append(parent_id)
            
        if completed is not None:
            where_clauses.append("completed = ?")
            params.append(1 if completed else 0)
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY due_date, due_time"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_goal(self, goal_id):
        """Get a specific goal by ID."""
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    def delete_goal(self, goal_id):
        """Delete a goal by ID (will cascade to subgoals due to foreign key)."""
        conn = self.get_connection()
        cursor = self.get_cursor()
        cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    def update_goal_status(self, goal_id, completed):
        """Update a goal's completion status."""
        conn = self.get_connection()
        cursor = self.get_cursor()
        cursor.execute(
            "UPDATE goals SET completed = ? WHERE id = ?", 
            (1 if completed else 0, goal_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    
    # Weekly task operations
    def save_weekly_task(self, task_data):
        """Save a weekly task to the database."""
        conn = self.get_connection()
        cursor = self.get_cursor()
        
        # Check if this is an update or insert
        if 'id' in task_data and task_data['id']:
            # Update existing task
            cursor.execute("""
                UPDATE weekly_tasks SET 
                    title = ?,
                    date = ?,
                    start_time = ?,
                    end_time = ?,
                    category = ?,
                    completed = ?,
                    parent_id = ?,
                    description = ?,
                    due_date = ?,
                    due_time = ?,
                    week_start_date = ?
                WHERE id = ?
            """, (
                task_data['title'],
                task_data.get('date'),
                task_data.get('start_time'),
                task_data.get('end_time'),
                task_data.get('category', 'Other'),
                1 if task_data.get('completed') else 0,
                task_data.get('parent_id'),
                task_data.get('description'),
                task_data.get('due_date'),
                task_data.get('due_time'),
                task_data.get('week_start_date'),
                task_data['id']
            ))
            task_id = task_data['id']
        else:
            # Insert new task
            cursor.execute("""
                INSERT INTO weekly_tasks (
                    title, date, start_time, end_time, category, completed, 
                    parent_id, description, due_date, due_time, week_start_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data['title'],
                task_data.get('date'),
                task_data.get('start_time'),
                task_data.get('end_time'),
                task_data.get('category', 'Other'),
                1 if task_data.get('completed') else 0,
                task_data.get('parent_id'),
                task_data.get('description'),
                task_data.get('due_date'),
                task_data.get('due_time'),
                task_data.get('week_start_date')
            ))
            task_id = cursor.lastrowid
        
        conn.commit()
        return task_id

    def get_weekly_tasks(self, week_start_date=None):
        """Get weekly tasks for a specific week."""
        cursor = self.get_cursor()
        
        if week_start_date:
            cursor.execute(
                "SELECT * FROM weekly_tasks WHERE week_start_date = ? ORDER BY date, start_time", 
                (week_start_date,)
            )
        else:
            cursor.execute("SELECT * FROM weekly_tasks ORDER BY date, start_time")
            
        return [dict(row) for row in cursor.fetchall()]
        
    # Helper methods for common queries
    def count_items(self, table, completed=None):
        """Count items in a table, optionally filtered by completion status."""
        cursor = self.get_cursor()
        
        query = f"SELECT COUNT(*) FROM {table}"
        params = []
        
        if completed is not None:
            query += " WHERE completed = ?"
            params.append(1 if completed else 0)
            
        cursor.execute(query, params)
        return cursor.fetchone()[0]
        
    def count_habits_completion(self, date):
        """Count completed habits for a specific date."""
        cursor = self.get_cursor()
        
        # Count total habits
        cursor.execute("SELECT COUNT(*) FROM habits")
        total = cursor.fetchone()[0]
        
        # Count completions for today
        cursor.execute(
            "SELECT COUNT(*) FROM habit_completions WHERE completion_date = ?", 
            (date,)
        )
        completed = cursor.fetchone()[0]
        
        return completed, total


# Create a singleton instance
db_manager = DatabaseManager()

# Convenience functions
def get_manager():
    """Get the database manager instance."""
    return db_manager

def get_connection():
    """Get a database connection."""
    return db_manager.get_connection()

def get_cursor():
    """Get a database cursor."""
    return db_manager.get_cursor()

def close_connection():
    """Close the current database connection."""
    db_manager.close_connection() 