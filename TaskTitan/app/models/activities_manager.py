"""
Activities Manager for TaskTitan.

This module provides functions to work with the unified activities system,
which combines tasks, events, and habits into a single data structure.
"""

import sqlite3
from datetime import datetime, timedelta
from PyQt6.QtCore import QDate, QTime
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
        except Exception:
            logger.debug("Adding color column to activities table")
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
            # We'll just log a message indicating this
            logger.debug("Migration of default activities has been disabled")
            
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
    
    def check_for_overlaps(self, date, start_time, end_time, exclude_activity_id=None):
        """Check if a time slot overlaps with existing activities.
        
        Args:
            date: QDate or date string for the date to check
            start_time: QTime or time string for start time
            end_time: QTime or time string for end time
            exclude_activity_id: Activity ID to exclude from check (when editing)
            
        Returns:
            List of conflicting activities with their details
        """
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
        
        # Convert QDate to string
        if isinstance(date, QDate):
            date_str = date.toString("yyyy-MM-dd")
            day_name = date.toString("dddd")
        else:
            date_str = date
            # Try to get day name from date string
            try:
                year, month, day = map(int, date_str.split('-'))
                qdate = QDate(year, month, day)
                day_name = qdate.toString("dddd")
            except:
                day_name = ""
        
        # Convert QTime to string
        if isinstance(start_time, QTime):
            start_str = start_time.toString("HH:mm")
        else:
            start_str = start_time
        
        if isinstance(end_time, QTime):
            end_str = end_time.toString("HH:mm")
        else:
            end_str = end_time
        
        # Build query to check for overlaps
        # Get activities for this specific date
        if exclude_activity_id:
            self.cursor.execute("""
                SELECT id, title, date, start_time, end_time, type, priority
                FROM activities
                WHERE date = ? AND id != ?
                ORDER BY start_time
            """, (date_str, exclude_activity_id))
        else:
            self.cursor.execute("""
                SELECT id, title, date, start_time, end_time, type, priority
                FROM activities
                WHERE date = ?
                ORDER BY start_time
            """, (date_str,))
        
        date_activities = self.cursor.fetchall()
        
        # Get repeating habits for this day of the week
        if day_name:
            self.cursor.execute("""
                SELECT id, title, date, start_time, end_time, type, priority
                FROM activities
                WHERE type = 'habit' AND days_of_week IS NOT NULL AND days_of_week LIKE ?
                ORDER BY start_time
            """, (f'%{day_name[:3]}%',))
            habit_activities = self.cursor.fetchall()
        else:
            habit_activities = []
        
        # Check for overlaps
        conflicts = []
        
        def check_time_overlap(start1, end1, start2, end2):
            """Check if two time ranges overlap."""
            # Convert to minutes for easy comparison
            def time_to_minutes(t):
                if isinstance(t, QTime):
                    return t.hour() * 60 + t.minute()
                elif isinstance(t, str):
                    try:
                        h, m = map(int, t.split(':'))
                        return h * 60 + m
                    except:
                        return 0
                else:
                    return 0
            
            start1_min = time_to_minutes(start1)
            end1_min = time_to_minutes(end1)
            start2_min = time_to_minutes(start2)
            end2_min = time_to_minutes(end2)
            
            # Check overlap: start1 < end2 AND start2 < end1
            return start1_min < end2_min and start2_min < end1_min
        
        # Check date-specific activities
        for row in date_activities:
            act_id, title, _, act_start, act_end, act_type, priority = row
            
            # Skip excluded activity
            if exclude_activity_id and act_id == exclude_activity_id:
                continue
            
            # Check for overlap
            if check_time_overlap(start_time, end_time, act_start, act_end):
                conflicts.append({
                    'id': act_id,
                    'title': title,
                    'start_time': act_start,
                    'end_time': act_end,
                    'type': act_type,
                    'priority': priority
                })
        
        # Check habits that occur on this day
        for row in habit_activities:
            act_id, title, _, act_start, act_end, act_type, priority = row
            
            # Skip excluded activity
            if exclude_activity_id and act_id == exclude_activity_id:
                continue
            
            # Check for overlap
            if check_time_overlap(start_time, end_time, act_start, act_end):
                # Convert time strings to QTime if needed for display
                conflict = {
                    'id': act_id,
                    'title': title,
                    'start_time': act_start,
                    'end_time': act_end,
                    'type': act_type,
                    'priority': priority
                }
                # Only add if not already in conflicts
                if not any(c['id'] == act_id for c in conflicts):
                    conflicts.append(conflict)
        
        return conflicts
    
    def suggest_alternative_slots(self, date, duration_minutes, preferred_start_hour=9, preferred_end_hour=17):
        """Suggest alternative time slots for an activity.
        
        Args:
            date: QDate or date string for the date
            duration_minutes: Duration of the activity in minutes
            preferred_start_hour: Preferred start hour (default 9 AM)
            preferred_end_hour: Preferred end hour (default 5 PM)
            
        Returns:
            List of suggested time slots as tuples (start_time, end_time)
        """
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
        
        # Get all activities for this date
        if isinstance(date, QDate):
            date_str = date.toString("yyyy-MM-dd")
            day_name = date.toString("dddd")
        else:
            date_str = date
            try:
                year, month, day = map(int, date_str.split('-'))
                qdate = QDate(year, month, day)
                day_name = qdate.toString("dddd")
            except:
                day_name = ""
        
        # Get date-specific activities
        self.cursor.execute("""
            SELECT start_time, end_time
            FROM activities
            WHERE date = ?
            ORDER BY start_time
        """, (date_str,))
        date_activities = self.cursor.fetchall()
        
        # Get habits for this day
        if day_name:
            self.cursor.execute("""
                SELECT start_time, end_time
                FROM activities
                WHERE type = 'habit' AND days_of_week IS NOT NULL AND days_of_week LIKE ?
                ORDER BY start_time
            """, (f'%{day_name[:3]}%',))
            habit_activities = self.cursor.fetchall()
        else:
            habit_activities = []
        
        # Combine and sort all activities
        all_activities = []
        
        def time_to_minutes(t):
            """Convert time to minutes."""
            if isinstance(t, QTime):
                return t.hour() * 60 + t.minute()
            elif isinstance(t, str):
                try:
                    h, m = map(int, t.split(':'))
                    return h * 60 + m
                except:
                    return 0
            return 0
        
        for row in date_activities:
            start_min = time_to_minutes(row[0])
            end_min = time_to_minutes(row[1])
            all_activities.append((start_min, end_min))
        
        for row in habit_activities:
            start_min = time_to_minutes(row[0])
            end_min = time_to_minutes(row[1])
            if (start_min, end_min) not in all_activities:
                all_activities.append((start_min, end_min))
        
        all_activities.sort(key=lambda x: x[0])
        
        # Find available slots
        suggestions = []
        search_start_hour = preferred_start_hour
        search_end_hour = preferred_end_hour
        
        def minutes_to_qtime(minutes):
            """Convert minutes to QTime."""
            hours = minutes // 60
            mins = minutes % 60
            return QTime(hours, mins)
        
        # Check each 30-minute slot
        for hour in range(search_start_hour, search_end_hour):
            for minute in [0, 30]:
                slot_start_min = hour * 60 + minute
                slot_end_min = slot_start_min + duration_minutes
                
                # Check if this slot overlaps with any existing activity
                overlaps = False
                for act_start, act_end in all_activities:
                    if slot_start_min < act_end and act_end > act_start:
                        overlaps = True
                        break
                
                if not overlaps and slot_end_min <= 24 * 60:  # Ensure it doesn't go past midnight
                    slot_start = minutes_to_qtime(slot_start_min)
                    slot_end = minutes_to_qtime(slot_end_min)
                    suggestions.append((slot_start, slot_end))
                    
                    if len(suggestions) >= 5:  # Limit to 5 suggestions
                        return suggestions
        
        return suggestions
    
    def find_empty_slots(self, date, start_hour=0, end_hour=24, min_duration_minutes=30):
        """Find empty time slots (gaps) in the schedule.
        
        Args:
            date: QDate or date string for the date
            start_hour: Start hour to search from (default 0)
            end_hour: End hour to search to (default 24)
            min_duration_minutes: Minimum duration for a slot to be considered
            
        Returns:
            List of empty slots as dicts with 'start_time', 'end_time', 'duration_minutes'
        """
        if not self.conn or not self.cursor:
            raise ValueError("Database connection not set")
        
        # Get all activities for this date
        activities = self.get_activities_for_date(date if isinstance(date, QDate) else QDate.fromString(date, "yyyy-MM-dd"))
        
        # Convert activities to time ranges in minutes
        def time_to_minutes(t):
            if isinstance(t, QTime):
                return t.hour() * 60 + t.minute()
            elif isinstance(t, str):
                try:
                    h, m = map(int, t.split(':'))
                    return h * 60 + m
                except:
                    return 0
            return 0
        
        occupied_ranges = []
        for act in activities:
            start_min = time_to_minutes(act['start_time'])
            end_min = time_to_minutes(act['end_time'])
            occupied_ranges.append((start_min, end_min))
        
        occupied_ranges.sort()
        
        # Find gaps
        empty_slots = []
        
        # Check gap from start_hour to first activity
        if occupied_ranges:
            first_start = occupied_ranges[0][0]
            start_min = start_hour * 60
            if first_start > start_min + min_duration_minutes:
                duration = first_start - start_min
                empty_slots.append({
                    'start_time': QTime(start_min // 60, start_min % 60),
                    'end_time': QTime(first_start // 60, first_start % 60),
                    'duration_minutes': duration
                })
        else:
            # No activities, entire day is empty
            total_minutes = (end_hour - start_hour) * 60
            if total_minutes >= min_duration_minutes:
                empty_slots.append({
                    'start_time': QTime(start_hour, 0),
                    'end_time': QTime(end_hour, 0),
                    'duration_minutes': total_minutes
                })
                return empty_slots
        
        # Check gaps between activities
        for i in range(len(occupied_ranges) - 1):
            _, current_end = occupied_ranges[i]
            next_start, _ = occupied_ranges[i + 1]
            
            gap_duration = next_start - current_end
            if gap_duration >= min_duration_minutes:
                empty_slots.append({
                    'start_time': QTime(current_end // 60, current_end % 60),
                    'end_time': QTime(next_start // 60, next_start % 60),
                    'duration_minutes': gap_duration
                })
        
        # Check gap from last activity to end_hour
        if occupied_ranges:
            last_end = occupied_ranges[-1][1]
            end_min = end_hour * 60
            if end_min > last_end + min_duration_minutes:
                duration = end_min - last_end
                empty_slots.append({
                    'start_time': QTime(last_end // 60, last_end % 60),
                    'end_time': QTime(end_hour, 0),
                    'duration_minutes': duration
                })
        
        return empty_slots 