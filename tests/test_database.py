"""
Unit tests for database operations.
"""

import pytest
import sqlite3
from datetime import datetime
from app.models.database_manager import DatabaseManager
from app.models.database import initialize_db
from app.models.activities_manager import ActivitiesManager


class TestDatabaseManager:
    """Test cases for DatabaseManager."""
    
    def test_database_connection(self, db_manager):
        """Test database connection."""
        assert db_manager.conn is not None
        assert db_manager.cursor is not None
    
    def test_execute_query(self, db_manager):
        """Test executing SQL queries."""
        db_manager.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")
        db_manager.commit()
        
        db_manager.execute("INSERT INTO test_table (name) VALUES (?)", ("test",))
        db_manager.commit()
        
        db_manager.execute("SELECT * FROM test_table WHERE name = ?", ("test",))
        result = db_manager.fetchone()
        
        assert result is not None
        assert result[1] == "test"
    
    def test_save_goal(self, db_manager, sample_goal_data):
        """Test saving a goal."""
        # Create goals table if it doesn't exist
        db_manager.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                title TEXT NOT NULL,
                due_date DATE,
                due_time TIME,
                completed INTEGER DEFAULT 0,
                priority INTEGER DEFAULT 1,
                color TEXT
            )
        """)
        db_manager.commit()
        
        goal_id = db_manager.save_goal(sample_goal_data)
        
        assert goal_id is not None
        assert isinstance(goal_id, int)
        
        # Verify goal was saved
        db_manager.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        result = db_manager.fetchone()
        
        assert result is not None
        assert result[2] == sample_goal_data['title']  # title is 3rd column
    
    def test_count_items(self, db_manager):
        """Test counting items in a table."""
        db_manager.execute("CREATE TABLE IF NOT EXISTS test_count (id INTEGER PRIMARY KEY, completed INTEGER DEFAULT 0)")
        db_manager.commit()
        
        db_manager.execute("INSERT INTO test_count (completed) VALUES (0)")
        db_manager.execute("INSERT INTO test_count (completed) VALUES (1)")
        db_manager.execute("INSERT INTO test_count (completed) VALUES (0)")
        db_manager.commit()
        
        total = db_manager.count_items("test_count")
        assert total == 3
        
        completed = db_manager.count_items("test_count", completed=True)
        assert completed == 1
        
        incomplete = db_manager.count_items("test_count", completed=False)
        assert incomplete == 2


class TestActivitiesManager:
    """Test cases for ActivitiesManager."""
    
    def test_create_tables(self, temp_db):
        """Test creating activity tables."""
        conn, cursor = temp_db
        manager = ActivitiesManager(conn, cursor)
        
        manager.create_tables()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
        result = cursor.fetchone()
        assert result is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activity_completions'")
        result = cursor.fetchone()
        assert result is not None
    
    def test_add_activity(self, temp_db, sample_activity_data):
        """Test adding an activity."""
        conn, cursor = temp_db
        manager = ActivitiesManager(conn, cursor)
        manager.create_tables()
        
        activity_id = manager.add_activity(
            title=sample_activity_data['title'],
            date=sample_activity_data['date'],
            start_time=sample_activity_data['start_time'],
            end_time=sample_activity_data['end_time'],
            activity_type=sample_activity_data['type'],
            priority=sample_activity_data['priority'],
            category=sample_activity_data['category']
        )
        
        assert activity_id is not None
        
        # Verify activity was added
        cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == sample_activity_data['title']  # title is 2nd column
    
    def test_get_activities_for_date(self, temp_db, sample_activity_data):
        """Test retrieving activities for a date."""
        from PyQt6.QtCore import QDate
        
        conn, cursor = temp_db
        manager = ActivitiesManager(conn, cursor)
        manager.create_tables()
        
        # Add an activity
        manager.add_activity(
            title=sample_activity_data['title'],
            date=sample_activity_data['date'],
            start_time=sample_activity_data['start_time'],
            end_time=sample_activity_data['end_time'],
            activity_type=sample_activity_data['type']
        )
        
        # Get activities for date
        test_date = QDate.fromString(sample_activity_data['date'], 'yyyy-MM-dd')
        activities = manager.get_activities_for_date(test_date)
        
        assert len(activities) > 0
        assert any(a[1] == sample_activity_data['title'] for a in activities)


class TestDatabaseInitialization:
    """Test cases for database initialization."""
    
    def test_initialize_db(self, temp_db):
        """Test database initialization."""
        conn, cursor = temp_db
        
        # Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'activities' in tables or 'goals' in tables
    
    def test_database_schema(self, temp_db):
        """Test database schema structure."""
        conn, cursor = temp_db
        
        # Check goals table structure
        cursor.execute("PRAGMA table_info(goals)")
        columns = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        assert 'title' in column_names
        assert 'due_date' in column_names

