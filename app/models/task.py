from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime, timedelta
import sqlite3

class Task(QObject):
    """Model class for tasks in the Task Titan application."""
    
    # Define signals
    dataChanged = pyqtSignal()
    
    def __init__(self, db_connection, task_id=None):
        """Initialize a Task object.
        
        Args:
            db_connection: SQLite database connection
            task_id: ID of an existing task to load (optional)
        """
        super().__init__()
        self.conn = db_connection
        self.cursor = self.conn.cursor()
        
        # Initialize attributes
        self.id = task_id
        self.title = ""
        self.description = ""
        self.due_date = None
        self.completed_date = None
        self.status = "not_started"  # not_started, in_progress, completed
        self.priority = "medium"  # low, medium, high
        self.user_id = None
        self.goal_id = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.estimated_time = None  # In minutes
        self.actual_time = None  # In minutes
        self.tags = []
        self.recurring = False
        self.recurrence_pattern = None  # daily, weekly, monthly, etc.
        self.recurrence_end_date = None
        self.reminder_time = None
        self.notes = ""
        
        # Load task data if ID is provided
        if task_id:
            self.load()
    
    def load(self):
        """Load task data from the database."""
        try:
            self.cursor.execute("""
                SELECT title, description, due_date, completed_date, status, priority,
                       user_id, goal_id, created_at, updated_at, estimated_time,
                       actual_time, tags, recurring, recurrence_pattern,
                       recurrence_end_date, reminder_time, notes
                FROM tasks WHERE id = ?
            """, (self.id,))
            
            row = self.cursor.fetchone()
            if row:
                self.title = row[0]
                self.description = row[1] or ""
                self.due_date = datetime.fromisoformat(row[2]) if row[2] else None
                self.completed_date = datetime.fromisoformat(row[3]) if row[3] else None
                self.status = row[4]
                self.priority = row[5]
                self.user_id = row[6]
                self.goal_id = row[7]
                self.created_at = datetime.fromisoformat(row[8])
                self.updated_at = datetime.fromisoformat(row[9])
                self.estimated_time = row[10]
                self.actual_time = row[11]
                self.tags = row[12].split(",") if row[12] else []
                self.recurring = bool(row[13])
                self.recurrence_pattern = row[14]
                self.recurrence_end_date = datetime.fromisoformat(row[15]) if row[15] else None
                self.reminder_time = datetime.fromisoformat(row[16]) if row[16] else None
                self.notes = row[17] or ""
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        return False
    
    def save(self):
        """Save task data to the database."""
        self.updated_at = datetime.now()
        
        # Convert tags list to comma-separated string
        tags_str = ",".join(self.tags) if self.tags else ""
        
        try:
            if self.id:  # Update existing task
                self.cursor.execute("""
                    UPDATE tasks
                    SET title = ?, description = ?, due_date = ?, completed_date = ?,
                        status = ?, priority = ?, user_id = ?, goal_id = ?,
                        updated_at = ?, estimated_time = ?, actual_time = ?,
                        tags = ?, recurring = ?, recurrence_pattern = ?,
                        recurrence_end_date = ?, reminder_time = ?, notes = ?
                    WHERE id = ?
                """, (
                    self.title, self.description,
                    self.due_date.isoformat() if self.due_date else None,
                    self.completed_date.isoformat() if self.completed_date else None,
                    self.status, self.priority, self.user_id, self.goal_id,
                    self.updated_at.isoformat(), self.estimated_time, self.actual_time,
                    tags_str, 1 if self.recurring else 0, self.recurrence_pattern,
                    self.recurrence_end_date.isoformat() if self.recurrence_end_date else None,
                    self.reminder_time.isoformat() if self.reminder_time else None,
                    self.notes, self.id
                ))
            else:  # Insert new task
                self.cursor.execute("""
                    INSERT INTO tasks
                    (title, description, due_date, completed_date, status, priority,
                     user_id, goal_id, created_at, updated_at, estimated_time,
                     actual_time, tags, recurring, recurrence_pattern,
                     recurrence_end_date, reminder_time, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.title, self.description,
                    self.due_date.isoformat() if self.due_date else None,
                    self.completed_date.isoformat() if self.completed_date else None,
                    self.status, self.priority, self.user_id, self.goal_id,
                    self.created_at.isoformat(), self.updated_at.isoformat(),
                    self.estimated_time, self.actual_time,
                    tags_str, 1 if self.recurring else 0, self.recurrence_pattern,
                    self.recurrence_end_date.isoformat() if self.recurrence_end_date else None,
                    self.reminder_time.isoformat() if self.reminder_time else None,
                    self.notes
                ))
                self.id = self.cursor.lastrowid
            
            self.conn.commit()
            
            # If this task is part of a goal, update the goal's progress
            if self.goal_id:
                from app.models.goal import Goal
                goal = Goal(self.conn, self.goal_id)
                if goal.id:
                    # This will calculate progress based on completed tasks
                    goal.save()
            
            self.dataChanged.emit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
    
    def delete(self):
        """Delete task from the database."""
        if not self.id:
            return False
            
        try:
            # Store goal_id before deleting for progress update
            stored_goal_id = self.goal_id
            
            self.cursor.execute("DELETE FROM tasks WHERE id = ?", (self.id,))
            self.conn.commit()
            
            self.id = None
            
            # If this task was part of a goal, update the goal's progress
            if stored_goal_id:
                from app.models.goal import Goal
                goal = Goal(self.conn, stored_goal_id)
                if goal.id:
                    # This will calculate progress based on remaining tasks
                    goal.save()
            
            self.dataChanged.emit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
    
    def mark_completed(self):
        """Mark the task as completed."""
        self.status = "completed"
        self.completed_date = datetime.now()
        return self.save()
    
    def mark_in_progress(self):
        """Mark the task as in progress."""
        self.status = "in_progress"
        self.completed_date = None
        return self.save()
    
    def mark_not_started(self):
        """Mark the task as not started."""
        self.status = "not_started"
        self.completed_date = None
        return self.save()
    
    def is_overdue(self):
        """Check if the task is overdue.
        
        Returns:
            True if task is overdue, False otherwise
        """
        if self.due_date and self.status != "completed":
            return datetime.now() > self.due_date
        return False
    
    def get_days_left(self):
        """Get the number of days left until the due date.
        
        Returns:
            Number of days as integer, or None if no due date
        """
        if not self.due_date:
            return None
            
        delta = self.due_date - datetime.now()
        return max(0, delta.days)
    
    def set_tags(self, tags_list):
        """Set the tags for this task.
        
        Args:
            tags_list: List of tag strings
            
        Returns:
            True if saved successfully, False otherwise
        """
        self.tags = tags_list
        return self.save()
    
    def add_tag(self, tag):
        """Add a tag to this task.
        
        Args:
            tag: Tag string to add
            
        Returns:
            True if saved successfully, False otherwise
        """
        if tag not in self.tags:
            self.tags.append(tag)
            return self.save()
        return True
    
    def remove_tag(self, tag):
        """Remove a tag from this task.
        
        Args:
            tag: Tag string to remove
            
        Returns:
            True if saved successfully, False otherwise
        """
        if tag in self.tags:
            self.tags.remove(tag)
            return self.save()
        return True
    
    def set_recurring(self, recurring, pattern=None, end_date=None):
        """Set the task as recurring with a pattern.
        
        Args:
            recurring: Boolean indicating if task is recurring
            pattern: Recurrence pattern (daily, weekly, monthly, etc.)
            end_date: Date when recurrence ends
            
        Returns:
            True if saved successfully, False otherwise
        """
        self.recurring = recurring
        if recurring:
            self.recurrence_pattern = pattern
            self.recurrence_end_date = end_date
        else:
            self.recurrence_pattern = None
            self.recurrence_end_date = None
        return self.save()
    
    def generate_next_occurrence(self):
        """Generate the next occurrence of this recurring task.
        
        Returns:
            New Task object for the next occurrence or None if not recurring
        """
        if not self.recurring or not self.recurrence_pattern or self.status != "completed":
            return None
            
        # Check if we've reached the end date
        if self.recurrence_end_date and datetime.now() > self.recurrence_end_date:
            return None
            
        # Create a new task as the next occurrence
        new_task = Task(self.conn)
        new_task.title = self.title
        new_task.description = self.description
        new_task.priority = self.priority
        new_task.user_id = self.user_id
        new_task.goal_id = self.goal_id
        new_task.estimated_time = self.estimated_time
        new_task.tags = self.tags.copy()
        new_task.recurring = self.recurring
        new_task.recurrence_pattern = self.recurrence_pattern
        new_task.recurrence_end_date = self.recurrence_end_date
        new_task.notes = self.notes
        
        # Calculate the next due date based on the pattern
        if self.due_date:
            if self.recurrence_pattern == "daily":
                new_task.due_date = self.due_date + timedelta(days=1)
            elif self.recurrence_pattern == "weekly":
                new_task.due_date = self.due_date + timedelta(days=7)
            elif self.recurrence_pattern == "monthly":
                # Approximate a month as 30 days
                new_task.due_date = self.due_date + timedelta(days=30)
            elif self.recurrence_pattern == "yearly":
                # Approximate a year as 365 days
                new_task.due_date = self.due_date + timedelta(days=365)
            
            # If reminder was set, keep same relative time before due date
            if self.reminder_time and self.due_date:
                time_before = self.due_date - self.reminder_time
                new_task.reminder_time = new_task.due_date - time_before
        
        new_task.save()
        return new_task
    
    def set_reminder(self, reminder_datetime):
        """Set a reminder for this task.
        
        Args:
            reminder_datetime: Datetime for the reminder
            
        Returns:
            True if saved successfully, False otherwise
        """
        self.reminder_time = reminder_datetime
        return self.save()
    
    def clear_reminder(self):
        """Clear the reminder for this task.
        
        Returns:
            True if saved successfully, False otherwise
        """
        self.reminder_time = None
        return self.save()
    
    @staticmethod
    def get_by_id(db_connection, task_id):
        """Get a task by ID.
        
        Args:
            db_connection: SQLite database connection
            task_id: Task ID to retrieve
            
        Returns:
            Task object or None if not found
        """
        task = Task(db_connection, task_id)
        if task.title:  # Check if the task was loaded successfully
            return task
        return None
    
    @staticmethod
    def get_all_for_user(db_connection, user_id):
        """Get all tasks for a specific user.
        
        Args:
            db_connection: SQLite database connection
            user_id: User ID to get tasks for
            
        Returns:
            List of Task objects
        """
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM tasks WHERE user_id = ? ORDER BY due_date ASC", (user_id,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(db_connection, row[0]))
        
        return tasks
    
    @staticmethod
    def get_by_goal(db_connection, goal_id):
        """Get all tasks for a specific goal.
        
        Args:
            db_connection: SQLite database connection
            goal_id: Goal ID to get tasks for
            
        Returns:
            List of Task objects
        """
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM tasks WHERE goal_id = ? ORDER BY due_date ASC", (goal_id,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(db_connection, row[0]))
        
        return tasks
    
    @staticmethod
    def get_pending_tasks(db_connection, user_id):
        """Get all pending (not completed) tasks for a user.
        
        Args:
            db_connection: SQLite database connection
            user_id: User ID to get tasks for
            
        Returns:
            List of pending Task objects
        """
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT id FROM tasks 
            WHERE user_id = ? AND status != 'completed'
            ORDER BY due_date ASC
        """, (user_id,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(db_connection, row[0]))
        
        return tasks
    
    @staticmethod
    def get_due_today(db_connection, user_id):
        """Get all tasks due today for a user.
        
        Args:
            db_connection: SQLite database connection
            user_id: User ID to get tasks for
            
        Returns:
            List of Task objects due today
        """
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time()).isoformat()
        today_end = datetime.combine(today, datetime.max.time()).isoformat()
        
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT id FROM tasks 
            WHERE user_id = ? AND status != 'completed'
            AND due_date BETWEEN ? AND ?
            ORDER BY priority DESC
        """, (user_id, today_start, today_end))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(db_connection, row[0]))
        
        return tasks
    
    @staticmethod
    def get_overdue(db_connection, user_id):
        """Get all overdue tasks for a user.
        
        Args:
            db_connection: SQLite database connection
            user_id: User ID to get tasks for
            
        Returns:
            List of overdue Task objects
        """
        now = datetime.now().isoformat()
        
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT id FROM tasks 
            WHERE user_id = ? AND status != 'completed'
            AND due_date < ?
            ORDER BY due_date ASC
        """, (user_id, now))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(db_connection, row[0]))
        
        return tasks
    
    @staticmethod
    def get_upcoming_reminders(db_connection, user_id, hours_ahead=24):
        """Get all tasks with upcoming reminders for a user.
        
        Args:
            db_connection: SQLite database connection
            user_id: User ID to get tasks for
            hours_ahead: Hours to look ahead for reminders
            
        Returns:
            List of Task objects with upcoming reminders
        """
        now = datetime.now()
        future = (now + timedelta(hours=hours_ahead)).isoformat()
        now = now.isoformat()
        
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT id FROM tasks 
            WHERE user_id = ? AND status != 'completed'
            AND reminder_time BETWEEN ? AND ?
            ORDER BY reminder_time ASC
        """, (user_id, now, future))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(db_connection, row[0]))
        
        return tasks 