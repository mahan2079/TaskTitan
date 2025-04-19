import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path=None):
        """Initialize database connection"""
        if db_path is None:
            # Default to the same location as setup.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(current_dir, "data")
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            db_path = os.path.join(data_dir, "tasktitan.db")
        
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
    
    def commit(self):
        """Commit changes to the database"""
        self.conn.commit()
    
    # User operations
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = self.cursor.fetchone()
        return dict(user) if user else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = self.cursor.fetchone()
        return dict(user) if user else None
    
    def create_user(self, username: str, password_hash: str, email: str) -> int:
        """Create a new user"""
        self.cursor.execute(
            "INSERT INTO users (username, password_hash, email, created_at) VALUES (?, ?, ?, ?)",
            (username, password_hash, email, datetime.now())
        )
        self.commit()
        return self.cursor.lastrowid
    
    def update_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Update user information"""
        allowed_fields = ['username', 'email', 'password_hash']
        
        # Build SET clause and parameters
        set_clause = ", ".join([f"{field} = ?" for field in data.keys() if field in allowed_fields])
        params = [data[field] for field in data.keys() if field in allowed_fields]
        
        if not set_clause:
            return False
        
        # Add user_id to params
        params.append(user_id)
        
        # Execute update
        self.cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", params)
        self.commit()
        return self.cursor.rowcount > 0
    
    # Task operations
    def get_tasks(self, user_id: int, status: str = None, goal_id: int = None) -> List[Dict]:
        """Get tasks for a user with optional filters"""
        query = "SELECT * FROM tasks WHERE user_id = ?"
        params = [user_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if goal_id:
            query += " AND goal_id = ?"
            params.append(goal_id)
        
        query += " ORDER BY due_date ASC"
        
        self.cursor.execute(query, params)
        tasks = self.cursor.fetchall()
        return [dict(task) for task in tasks]
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """Get task by ID"""
        self.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = self.cursor.fetchone()
        return dict(task) if task else None
    
    def create_task(self, user_id: int, title: str, description: str = None, 
                   due_date: datetime = None, priority: str = "medium",
                   status: str = "pending", goal_id: int = None) -> int:
        """Create a new task"""
        self.cursor.execute(
            """
            INSERT INTO tasks 
            (user_id, title, description, due_date, priority, status, goal_id, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, due_date, priority, status, goal_id, datetime.now())
        )
        self.commit()
        return self.cursor.lastrowid
    
    def update_task(self, task_id: int, data: Dict[str, Any]) -> bool:
        """Update task information"""
        allowed_fields = ['title', 'description', 'due_date', 'priority', 'status', 'goal_id']
        
        # Build SET clause and parameters
        set_clause = ", ".join([f"{field} = ?" for field in data.keys() if field in allowed_fields])
        params = [data[field] for field in data.keys() if field in allowed_fields]
        
        if not set_clause:
            return False
        
        # Add updated_at timestamp
        set_clause += ", updated_at = ?"
        params.append(datetime.now())
        
        # Add task_id to params
        params.append(task_id)
        
        # Execute update
        self.cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", params)
        self.commit()
        return self.cursor.rowcount > 0
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.commit()
        return self.cursor.rowcount > 0
    
    # Goal operations
    def get_goals(self, user_id: int, status: str = None) -> List[Dict]:
        """Get goals for a user with optional status filter"""
        query = "SELECT * FROM goals WHERE user_id = ?"
        params = [user_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY due_date ASC"
        
        self.cursor.execute(query, params)
        goals = self.cursor.fetchall()
        return [dict(goal) for goal in goals]
    
    def get_goal(self, goal_id: int) -> Optional[Dict]:
        """Get goal by ID"""
        self.cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        goal = self.cursor.fetchone()
        return dict(goal) if goal else None
    
    def create_goal(self, user_id: int, title: str, description: str = None, 
                   due_date: datetime = None, status: str = "in_progress") -> int:
        """Create a new goal"""
        self.cursor.execute(
            """
            INSERT INTO goals 
            (user_id, title, description, due_date, status, created_at) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, due_date, status, datetime.now())
        )
        self.commit()
        return self.cursor.lastrowid
    
    def update_goal(self, goal_id: int, data: Dict[str, Any]) -> bool:
        """Update goal information"""
        allowed_fields = ['title', 'description', 'due_date', 'status']
        
        # Build SET clause and parameters
        set_clause = ", ".join([f"{field} = ?" for field in data.keys() if field in allowed_fields])
        params = [data[field] for field in data.keys() if field in allowed_fields]
        
        if not set_clause:
            return False
        
        # Add updated_at timestamp
        set_clause += ", updated_at = ?"
        params.append(datetime.now())
        
        # Add goal_id to params
        params.append(goal_id)
        
        # Execute update
        self.cursor.execute(f"UPDATE goals SET {set_clause} WHERE id = ?", params)
        self.commit()
        return self.cursor.rowcount > 0
    
    def delete_goal(self, goal_id: int) -> bool:
        """Delete a goal and its associated tasks"""
        # First, delete associated tasks
        self.cursor.execute("DELETE FROM tasks WHERE goal_id = ?", (goal_id,))
        
        # Then delete the goal
        self.cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        self.commit()
        return self.cursor.rowcount > 0
    
    # Category and tag operations
    def get_categories(self, user_id: int) -> List[Dict]:
        """Get categories for a user"""
        self.cursor.execute("SELECT * FROM categories WHERE user_id = ?", (user_id,))
        categories = self.cursor.fetchall()
        return [dict(category) for category in categories]
    
    def get_tags(self, user_id: int) -> List[Dict]:
        """Get tags for a user"""
        self.cursor.execute("SELECT * FROM tags WHERE user_id = ?", (user_id,))
        tags = self.cursor.fetchall()
        return [dict(tag) for tag in tags]
    
    def create_category(self, user_id: int, name: str, color: str = "#FFFFFF") -> int:
        """Create a new category"""
        self.cursor.execute(
            "INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)",
            (user_id, name, color)
        )
        self.commit()
        return self.cursor.lastrowid
    
    def create_tag(self, user_id: int, name: str, color: str = "#FFFFFF") -> int:
        """Create a new tag"""
        self.cursor.execute(
            "INSERT INTO tags (user_id, name, color) VALUES (?, ?, ?)",
            (user_id, name, color)
        )
        self.commit()
        return self.cursor.lastrowid
    
    # Statistics operations
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get statistics for a user"""
        stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "pending_tasks": 0,
            "overdue_tasks": 0,
            "total_goals": 0,
            "completed_goals": 0,
            "in_progress_goals": 0
        }
        
        # Task statistics
        self.cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
        stats["total_tasks"] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'completed'", (user_id,))
        stats["completed_tasks"] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'pending'", (user_id,))
        stats["pending_tasks"] = self.cursor.fetchone()[0]
        
        self.cursor.execute(
            "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND due_date < ? AND status != 'completed'", 
            (user_id, datetime.now())
        )
        stats["overdue_tasks"] = self.cursor.fetchone()[0]
        
        # Goal statistics
        self.cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ?", (user_id,))
        stats["total_goals"] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = 'completed'", (user_id,))
        stats["completed_goals"] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = 'in_progress'", (user_id,))
        stats["in_progress_goals"] = self.cursor.fetchone()[0]
        
        return stats
    
    # User settings operations
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get settings for a user"""
        self.cursor.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,))
        settings = self.cursor.fetchone()
        return dict(settings) if settings else {}
    
    def update_user_settings(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Update user settings"""
        allowed_fields = ['theme', 'notification_enabled', 'daily_goal', 'start_day_of_week']
        
        # Check if settings exist for the user
        self.cursor.execute("SELECT id FROM settings WHERE user_id = ?", (user_id,))
        settings = self.cursor.fetchone()
        
        if not settings:
            # Insert new settings
            fields = ["user_id"] + [field for field in data.keys() if field in allowed_fields]
            placeholders = "?, " + ", ".join(["?" for _ in range(len(fields) - 1)])
            values = [user_id] + [data[field] for field in data.keys() if field in allowed_fields]
            
            self.cursor.execute(
                f"INSERT INTO settings ({', '.join(fields)}) VALUES ({placeholders})",
                values
            )
        else:
            # Update existing settings
            set_clause = ", ".join([f"{field} = ?" for field in data.keys() if field in allowed_fields])
            params = [data[field] for field in data.keys() if field in allowed_fields]
            
            if not set_clause:
                return False
            
            # Add user_id to params
            params.append(user_id)
            
            # Execute update
            self.cursor.execute(f"UPDATE settings SET {set_clause} WHERE user_id = ?", params)
        
        self.commit()
        return True

# Example usage
if __name__ == "__main__":
    db = DatabaseManager()
    try:
        # Get current user
        user = db.get_user(1)
        print(f"Current user: {user['username']}")
        
        # Get user's tasks
        tasks = db.get_tasks(1)
        print(f"Total tasks: {len(tasks)}")
        
        # Get user statistics
        stats = db.get_user_statistics(1)
        print(f"User statistics: {stats}")
    finally:
        db.close() 