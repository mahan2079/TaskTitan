import sqlite3
import os
from datetime import datetime, timedelta

class DatabaseSetup:
    """Class to set up the TaskTitan database"""
    
    def __init__(self, db_path):
        """Initialize with the database path"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def setup_database(self):
        """Set up all database tables"""
        # Create users table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create goals table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            due_date DATE,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        # Create tasks table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            goal_id INTEGER,
            description TEXT NOT NULL,
            due_date DATE,
            completed INTEGER DEFAULT 0,
            priority INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (goal_id) REFERENCES goals(id)
        )
        """)
        
        # Create settings table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            theme TEXT DEFAULT 'light',
            notifications INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        # Create categories table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            color TEXT DEFAULT '#6366F1'
        )
        """)
        
        # Create task_categories table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_categories (
            task_id INTEGER,
            category_id INTEGER,
            PRIMARY KEY (task_id, category_id),
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
        """)
        
        # Commit the changes
        self.conn.commit()
    
    def insert_default_data(self):
        """Insert default data for testing"""
        # Insert default user
        self.cursor.execute("""
        INSERT OR IGNORE INTO users (username, email) 
        VALUES ('user', 'user@example.com')
        """)
        
        # Get user ID
        self.cursor.execute("SELECT id FROM users WHERE username = 'user'")
        user_id = self.cursor.fetchone()[0]
        
        # Insert default categories
        categories = [
            ('Work', '#EF4444'),  # Red
            ('Personal', '#3B82F6'),  # Blue
            ('Health', '#10B981'),  # Green
            ('Learning', '#8B5CF6'),  # Purple
            ('Finance', '#F59E0B')   # Amber
        ]
        
        for name, color in categories:
            self.cursor.execute("""
            INSERT OR IGNORE INTO categories (name, color) 
            VALUES (?, ?)
            """, (name, color))
        
        # Insert default goals
        goals = [
            (user_id, 'Learn Python', 'Master Python programming', '2023-12-31', 0),
            (user_id, 'Exercise Regularly', 'Workout 3 times per week', '2023-12-31', 0),
            (user_id, 'Read 12 Books', 'Read one book per month', '2023-12-31', 0)
        ]
        
        for user_id, title, description, due_date, completed in goals:
            self.cursor.execute("""
            INSERT OR IGNORE INTO goals (user_id, title, description, due_date, completed) 
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, title, description, due_date, completed))
        
        # Get goal IDs
        self.cursor.execute("SELECT id FROM goals WHERE title = 'Learn Python'")
        python_goal_id = self.cursor.fetchone()[0]
        
        # Insert default tasks
        tasks = [
            (user_id, python_goal_id, 'Complete Python course', '2023-11-30', 0, 2),
            (user_id, python_goal_id, 'Build a small project', '2023-12-15', 0, 1),
            (user_id, None, 'Buy groceries', '2023-10-15', 0, 0),
            (user_id, None, 'Pay bills', '2023-10-20', 0, 1),
            (user_id, None, 'Schedule doctor appointment', '2023-10-25', 0, 1)
        ]
        
        for user_id, goal_id, description, due_date, completed, priority in tasks:
            self.cursor.execute("""
            INSERT OR IGNORE INTO tasks (user_id, goal_id, description, due_date, completed, priority) 
            VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, goal_id, description, due_date, completed, priority))
        
        # Insert default settings
        self.cursor.execute("""
        INSERT OR IGNORE INTO settings (user_id, theme, notifications) 
        VALUES (?, 'light', 1)
        """, (user_id,))
        
        # Commit the changes
        self.conn.commit()
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()


# Example usage
if __name__ == "__main__":
    # Get the absolute path to the database file
    db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    db_path = os.path.join(db_dir, 'tasktitan.db')
    
    # Create and set up the database
    db_setup = DatabaseSetup(db_path)
    db_setup.setup_database()
    
    # Insert default data
    db_setup.insert_default_data()
    
    # Close the connection
    db_setup.close() 