"""
Activities Manager for TaskTitan.

This module provides functions to work with the unified activities system,
which combines tasks, events, and habits into a single data structure.
"""

import sqlite3
from datetime import datetime, timedelta
from PyQt6.QtCore import QDate, QTime


class ActivitiesManager:
    """Manager class for working with unified activities."""
    
    def __init__(self, conn=None, cursor=None):
        """Initialize with an optional connection and cursor."""
        self.conn = conn
        self.cursor = cursor
    
    def set_connection(self, conn, cursor):
        """Set the database connection and cursor."""
        self.conn = conn
        self.cursor = cursor
    
    def create_tables(self):
        """Create the necessary tables if they don't exist."""
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
            
        # Create activities table
        self.cursor.execute("""
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
                color TEXT,  -- For color information (especially for events)
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL
            )
        """)
        
        # Create activity_completions table to track daily completions
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_completions (
                activity_id INTEGER NOT NULL,
                completion_date DATE NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (activity_id, completion_date),
                FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
            )
        """)
        
        # Make sure color column exists (for existing tables)
        try:
            self.cursor.execute("SELECT color FROM activities LIMIT 1")
        except:
            print("Adding color column to activities table")
            self.cursor.execute("ALTER TABLE activities ADD COLUMN color TEXT")
        
        # Create migration trigger to update timestamps
        self.cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_activity_timestamp 
            AFTER UPDATE ON activities
            BEGIN
                UPDATE activities SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END;
        """)
        
        self.conn.commit()
    
    def migrate_existing_data(self):
        """Migrate data from separate tables into the unified activities table."""
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
            
        # Check if the activities table is empty
        self.cursor.execute("SELECT COUNT(*) FROM activities")
        count = self.cursor.fetchone()[0]
        
        # Only proceed if activities table is empty
        if count == 0:
            # Migration has been disabled to prevent default activities
            # We'll just print a message indicating this
            print("Migration of default activities has been disabled")
            
            # If we need to create any system-required records (like categories) we could do that here
            # But we won't create any default user-facing activities
            
            # Original migration code has been removed to prevent any default
            # activities from being created
            pass
    
    def get_activities_for_date(self, date):
        """Get all activities for a specific date.
        
        Args:
            date: A QDate object representing the date to fetch activities for
            
        Returns:
            A list of activity dictionaries
        """
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
            
        date_str = date.toString("yyyy-MM-dd")
        day_name = date.toString("dddd")
        
        # Get activities specifically for this date
        self.cursor.execute("""
            SELECT 
                a.id, a.title, a.date, a.start_time, a.end_time, 
                CASE WHEN ac.activity_id IS NOT NULL THEN 1 ELSE 0 END as completed, 
                a.type, a.priority, a.category, a.days_of_week, a.goal_id, a.created_at, a.color
            FROM activities a
            LEFT JOIN activity_completions ac ON a.id = ac.activity_id AND ac.completion_date = ?
            WHERE a.date = ?
            ORDER BY a.start_time
        """, (date_str, date_str))
        
        date_activities = self.cursor.fetchall()
        
        # Get repeating habits for this day of the week
        self.cursor.execute("""
            SELECT 
                a.id, a.title, a.date, a.start_time, a.end_time, 
                CASE WHEN ac.activity_id IS NOT NULL THEN 1 ELSE 0 END as completed, 
                a.type, a.priority, a.category, a.days_of_week, a.goal_id, a.created_at, a.color
            FROM activities a
            LEFT JOIN activity_completions ac ON a.id = ac.activity_id AND ac.completion_date = ?
            WHERE 
                a.type = 'habit' AND 
                a.days_of_week IS NOT NULL AND
                a.days_of_week LIKE ?
            ORDER BY a.start_time
        """, (date_str, f'%{day_name[:3]}%'))  # Match day name abbreviation
        
        habit_activities = self.cursor.fetchall()
        
        # Combine results
        results = []
        
        # Process date-specific activities
        for row in date_activities:
            activity = self._row_to_activity(row)
            results.append(activity)
        
        # Process habits that repeat on this day
        for row in habit_activities:
            # Skip if already in date_activities
            if any(a['id'] == row[0] and a['type'] == 'habit' for a in results):
                continue
                
            activity = self._row_to_activity(row)
            results.append(activity)
        
        # Sort by start time
        results.sort(key=lambda x: x['start_time'].toString("HH:mm"))
        
        return results
    
    def get_all_activities(self):
        """Get all activities.
        
        Returns:
            A list of activity dictionaries
        """
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
            
        self.cursor.execute("""
            SELECT 
                id, title, date, start_time, end_time, completed, type,
                priority, category, days_of_week, goal_id, created_at, color
            FROM activities
            ORDER BY date, start_time
        """)
        
        results = []
        for row in self.cursor.fetchall():
            activity = self._row_to_activity(row)
            results.append(activity)
            
        return results
    
    def add_activity(self, activity_data):
        """Add a new activity.
        
        Args:
            activity_data: Dictionary containing activity data
            
        Returns:
            The ID of the newly added activity
        """
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
            
        # Extract data
        title = activity_data.get('title', '')
        date = activity_data.get('date')
        if isinstance(date, QDate):
            date = date.toString("yyyy-MM-dd")
            
        start_time = activity_data.get('start_time')
        if isinstance(start_time, QTime):
            start_time = start_time.toString("HH:mm")
            
        end_time = activity_data.get('end_time')
        if isinstance(end_time, QTime):
            end_time = end_time.toString("HH:mm")
            
        activity_type = activity_data.get('type', '')
        completed = 1 if activity_data.get('completed', False) else 0
        priority = activity_data.get('priority', 0)
        category = activity_data.get('category', '')
        days_of_week = activity_data.get('days_of_week', '')
        goal_id = activity_data.get('goal_id', None)
        color = activity_data.get('color', '')
        
        # Execute the SQL
        self.cursor.execute("""
            INSERT INTO activities (
                title, date, start_time, end_time, completed, type,
                priority, category, days_of_week, goal_id, color
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, date, start_time, end_time, completed, activity_type,
            priority, category, days_of_week, goal_id, color
        ))
        
        self.conn.commit()
        
        # Return the ID of the newly inserted row
        return self.cursor.lastrowid
    
    def update_activity(self, activity_id, activity_data):
        """Update an existing activity.
        
        Args:
            activity_id: The ID of the activity to update
            activity_data: Dictionary containing updated activity data
            
        Returns:
            True if the activity was updated, False otherwise
        """
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
            
        # Check if the activity exists
        self.cursor.execute("SELECT id FROM activities WHERE id = ?", (activity_id,))
        result = self.cursor.fetchone()
        if not result:
            return False
        
        # Build the SET clause and parameters dynamically
        set_clauses = []
        params = []
        
        fields_mapping = {
            'title': 'title',
            'date': 'date',
            'start_time': 'start_time',
            'end_time': 'end_time',
            'completed': 'completed',
            'type': 'type',
            'priority': 'priority',
            'category': 'category',
            'days_of_week': 'days_of_week',
            'goal_id': 'goal_id',
            'color': 'color'
        }
        
        for key, field in fields_mapping.items():
            if key in activity_data:
                value = activity_data[key]
                
                # Convert QDate/QTime objects to strings
                if isinstance(value, QDate):
                    value = value.toString("yyyy-MM-dd")
                elif isinstance(value, QTime):
                    value = value.toString("HH:mm")
                elif key == 'completed' and isinstance(value, bool):
                    value = 1 if value else 0
                
                set_clauses.append(f"{field} = ?")
                params.append(value)
        
        # If no fields to update, return False
        if not set_clauses:
            return False
        
        # Build the SQL and execute
        sql = f"UPDATE activities SET {', '.join(set_clauses)} WHERE id = ?"
        params.append(activity_id)
        
        self.cursor.execute(sql, params)
        self.conn.commit()
        
        return True
    
    def delete_activity(self, activity_id):
        """Delete an activity.
        
        Args:
            activity_id: The ID of the activity to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
            
        self.cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        self.conn.commit()
        
        # Check if any rows were affected
        return self.cursor.rowcount > 0
    
    def toggle_activity_completion(self, activity_id, completed, date=None):
        """Toggle the completion status of an activity for a specific date.
        
        Args:
            activity_id: The ID of the activity
            completed: Boolean indicating completion status
            date: Optional QDate or date string for the completion date (defaults to today)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
        
        # Default to today if no date provided
        if date is None:
            from PyQt6.QtCore import QDate
            date = QDate.currentDate()
            
        # Convert QDate to string if needed
        if hasattr(date, 'toString'):
            date_str = date.toString("yyyy-MM-dd")
        else:
            date_str = date
        
        try:
            if completed:
                # Add a record to activity_completions
                self.cursor.execute(
                    "INSERT OR REPLACE INTO activity_completions (activity_id, completion_date) VALUES (?, ?)",
                    (activity_id, date_str)
                )
            else:
                # Remove the record from activity_completions
                self.cursor.execute(
                    "DELETE FROM activity_completions WHERE activity_id = ? AND completion_date = ?",
                    (activity_id, date_str)
                )
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error toggling activity completion: {e}")
            return False
    
    def get_activities_by_type(self, activity_type):
        """Get all activities of a specific type.
        
        Args:
            activity_type: String type ('task', 'event', or 'habit')
            
        Returns:
            A list of activity dictionaries
        """
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
            
        self.cursor.execute("""
            SELECT 
                id, title, date, start_time, end_time, completed, type,
                priority, category, days_of_week, goal_id, created_at
            FROM activities
            WHERE type = ?
            ORDER BY date, start_time
        """, (activity_type,))
        
        results = []
        for row in self.cursor.fetchall():
            activity = self._row_to_activity(row)
            results.append(activity)
            
        return results
    
    def get_activity_by_id(self, activity_id):
        """Get a specific activity by ID.
        
        Args:
            activity_id: The ID of the activity
            
        Returns:
            An activity dictionary, or None if not found
        """
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
            
        self.cursor.execute("""
            SELECT 
                id, title, date, start_time, end_time, completed, type,
                priority, category, days_of_week, goal_id, created_at, color
            FROM activities
            WHERE id = ?
        """, (activity_id,))
        
        row = self.cursor.fetchone()
        if row:
            return self._row_to_activity(row)
        else:
            return None
    
    def _row_to_activity(self, row):
        """Convert a database row to an activity dictionary.
        
        Args:
            row: A database row containing activity data
            
        Returns:
            A dictionary containing the activity data with proper types
        """
        # Expand row columns:
        # id, title, date, start_time, end_time, completed, type,
        # priority, category, days_of_week, goal_id, created_at, color
        result = {
            'id': row[0],
            'title': row[1],
            'date': self._string_to_qdate(row[2]),
            'start_time': self._string_to_qtime(row[3]),
            'end_time': self._string_to_qtime(row[4]),
            'completed': bool(row[5]),
            'type': row[6],
            'priority': row[7] if row[7] is not None else 0,
            'category': row[8] if row[8] is not None else '',
            'days_of_week': row[9] if row[9] is not None else '',
            'goal_id': row[10]
        }
        
        # Get color data in index 12
        if len(row) > 12 and row[12] is not None and row[12] != '':
            result['color'] = row[12]
            print(f"Activity {row[0]} has color: {row[12]}")
        
        return result
    
    def _string_to_qdate(self, date_str):
        """Convert a date string to QDate.
        
        Args:
            date_str: Date string in format 'YYYY-MM-DD'
            
        Returns:
            QDate object
        """
        if not date_str:
            return QDate.currentDate()
            
        try:
            year, month, day = map(int, date_str.split('-'))
            return QDate(year, month, day)
        except:
            return QDate.currentDate()
    
    def _string_to_qtime(self, time_str):
        """Convert a time string to QTime.
        
        Args:
            time_str: Time string in format 'HH:MM'
            
        Returns:
            QTime object
        """
        if not time_str:
            return QTime(0, 0)
            
        try:
            if ':' in time_str:
                hour, minute = map(int, time_str.split(':'))
                return QTime(hour, minute)
            else:
                # Handle integer seconds
                return QTime(0, 0)
        except:
            return QTime(0, 0) 