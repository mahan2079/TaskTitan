from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime
import sqlite3

class Goal(QObject):
    """Model class for goals in the Task Titan application."""
    
    # Define signals
    dataChanged = pyqtSignal()
    
    def __init__(self, db_connection, goal_id=None):
        """Initialize a Goal object.
        
        Args:
            db_connection: SQLite database connection
            goal_id: ID of an existing goal to load (optional)
        """
        super().__init__()
        self.conn = db_connection
        self.cursor = self.conn.cursor()
        
        # Initialize attributes
        self.id = goal_id
        self.title = ""
        self.description = ""
        self.start_date = None
        self.end_date = None
        self.status = "not_started"  # not_started, in_progress, completed, abandoned
        self.user_id = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.completed_at = None
        self.category = ""
        self.priority = "medium"  # low, medium, high
        self.target_value = None  # For quantifiable goals
        self.current_value = None  # Current progress towards target
        self.color = "#4287f5"  # Default color
        
        # Load goal data if ID is provided
        if goal_id:
            self.load()
    
    def load(self):
        """Load goal data from the database."""
        try:
            self.cursor.execute("""
                SELECT title, description, start_date, end_date, status, user_id,
                       created_at, updated_at, completed_at, category, priority,
                       target_value, current_value, color
                FROM goals WHERE id = ?
            """, (self.id,))
            
            row = self.cursor.fetchone()
            if row:
                self.title = row[0]
                self.description = row[1] or ""
                self.start_date = datetime.fromisoformat(row[2]) if row[2] else None
                self.end_date = datetime.fromisoformat(row[3]) if row[3] else None
                self.status = row[4]
                self.user_id = row[5]
                self.created_at = datetime.fromisoformat(row[6])
                self.updated_at = datetime.fromisoformat(row[7])
                self.completed_at = datetime.fromisoformat(row[8]) if row[8] else None
                self.category = row[9] or ""
                self.priority = row[10]
                self.target_value = row[11]
                self.current_value = row[12]
                self.color = row[13] or "#4287f5"
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        return False
    
    def save(self):
        """Save goal data to the database."""
        self.updated_at = datetime.now()
        
        try:
            if self.id:  # Update existing goal
                self.cursor.execute("""
                    UPDATE goals
                    SET title = ?, description = ?, start_date = ?, end_date = ?, 
                        status = ?, user_id = ?, updated_at = ?, completed_at = ?,
                        category = ?, priority = ?, target_value = ?, current_value = ?, color = ?
                    WHERE id = ?
                """, (
                    self.title, self.description, 
                    self.start_date.isoformat() if self.start_date else None,
                    self.end_date.isoformat() if self.end_date else None,
                    self.status, self.user_id, self.updated_at.isoformat(),
                    self.completed_at.isoformat() if self.completed_at else None,
                    self.category, self.priority, self.target_value, self.current_value, self.color,
                    self.id
                ))
            else:  # Insert new goal
                self.cursor.execute("""
                    INSERT INTO goals
                    (title, description, start_date, end_date, status, user_id,
                     created_at, updated_at, completed_at, category, priority,
                     target_value, current_value, color)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.title, self.description, 
                    self.start_date.isoformat() if self.start_date else None,
                    self.end_date.isoformat() if self.end_date else None,
                    self.status, self.user_id, self.created_at.isoformat(), self.updated_at.isoformat(),
                    self.completed_at.isoformat() if self.completed_at else None,
                    self.category, self.priority, self.target_value, self.current_value, self.color
                ))
                self.id = self.cursor.lastrowid
            
            self.conn.commit()
            self.dataChanged.emit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
    
    def delete(self):
        """Delete goal from the database."""
        if not self.id:
            return False
            
        try:
            # Delete associated tasks first
            self.cursor.execute("DELETE FROM tasks WHERE goal_id = ?", (self.id,))
            
            # Now delete the goal
            self.cursor.execute("DELETE FROM goals WHERE id = ?", (self.id,))
            self.conn.commit()
            
            self.id = None
            self.dataChanged.emit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
    
    def mark_completed(self):
        """Mark the goal as completed."""
        self.status = "completed"
        self.completed_at = datetime.now()
        return self.save()
    
    def mark_in_progress(self):
        """Mark the goal as in progress."""
        self.status = "in_progress"
        self.completed_at = None
        return self.save()
    
    def mark_not_started(self):
        """Mark the goal as not started."""
        self.status = "not_started"
        self.completed_at = None
        return self.save()
    
    def mark_abandoned(self):
        """Mark the goal as abandoned."""
        self.status = "abandoned"
        return self.save()
    
    def update_progress(self, new_value):
        """Update the current progress value towards the target.
        
        Args:
            new_value: The new progress value
            
        Returns:
            True if saved successfully, False otherwise
        """
        self.current_value = new_value
        
        # Automatically update status based on progress
        if self.target_value is not None and self.current_value is not None:
            if self.current_value >= self.target_value:
                self.status = "completed"
                self.completed_at = datetime.now()
            elif self.current_value > 0:
                self.status = "in_progress"
        
        return self.save()
    
    def get_progress_percentage(self):
        """Get the progress percentage towards the target.
        
        Returns:
            Progress percentage (0-100) or None if not applicable
        """
        if self.target_value is not None and self.current_value is not None and self.target_value > 0:
            return min(100, (self.current_value / self.target_value) * 100)
        return None
    
    def get_tasks(self):
        """Get all tasks associated with this goal.
        
        Returns:
            List of Task objects
        """
        from app.models.task import Task
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM tasks WHERE goal_id = ?", (self.id,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(self.conn, row[0]))
        
        return tasks
    
    def get_completed_tasks_count(self):
        """Get the count of completed tasks associated with this goal.
        
        Returns:
            Number of completed tasks
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM tasks 
            WHERE goal_id = ? AND status = 'completed'
        """, (self.id,))
        
        return cursor.fetchone()[0]
    
    def get_total_tasks_count(self):
        """Get the total count of tasks associated with this goal.
        
        Returns:
            Total number of tasks
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE goal_id = ?", (self.id,))
        
        return cursor.fetchone()[0]
    
    def get_task_completion_percentage(self):
        """Calculate the percentage of tasks completed for this goal.
        
        Returns:
            Percentage of completed tasks (0-100) or 0 if no tasks
        """
        total_tasks = self.get_total_tasks_count()
        if total_tasks == 0:
            return 0
        
        completed_tasks = self.get_completed_tasks_count()
        return (completed_tasks / total_tasks) * 100
    
    def is_overdue(self):
        """Check if the goal is overdue.
        
        Returns:
            True if goal is overdue, False otherwise
        """
        if self.end_date and self.status not in ["completed", "abandoned"]:
            return datetime.now() > self.end_date
        return False
    
    @staticmethod
    def get_by_id(db_connection, goal_id):
        """Get a goal by ID.
        
        Args:
            db_connection: SQLite database connection
            goal_id: Goal ID to retrieve
            
        Returns:
            Goal object or None if not found
        """
        goal = Goal(db_connection, goal_id)
        if goal.title:  # Check if the goal was loaded successfully
            return goal
        return None
    
    @staticmethod
    def get_all_for_user(db_connection, user_id):
        """Get all goals for a specific user.
        
        Args:
            db_connection: SQLite database connection
            user_id: User ID to get goals for
            
        Returns:
            List of Goal objects
        """
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM goals WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        
        goals = []
        for row in cursor.fetchall():
            goals.append(Goal(db_connection, row[0]))
        
        return goals
    
    @staticmethod
    def get_active_goals(db_connection, user_id):
        """Get all active (not completed or abandoned) goals for a user.
        
        Args:
            db_connection: SQLite database connection
            user_id: User ID to get goals for
            
        Returns:
            List of active Goal objects
        """
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT id FROM goals 
            WHERE user_id = ? AND status NOT IN ('completed', 'abandoned')
            ORDER BY end_date ASC
        """, (user_id,))
        
        goals = []
        for row in cursor.fetchall():
            goals.append(Goal(db_connection, row[0]))
        
        return goals
    
    @staticmethod
    def get_completed_goals(db_connection, user_id):
        """Get all completed goals for a user.
        
        Args:
            db_connection: SQLite database connection
            user_id: User ID to get goals for
            
        Returns:
            List of completed Goal objects
        """
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT id FROM goals 
            WHERE user_id = ? AND status = 'completed'
            ORDER BY completed_at DESC
        """, (user_id,))
        
        goals = []
        for row in cursor.fetchall():
            goals.append(Goal(db_connection, row[0]))
        
        return goals 