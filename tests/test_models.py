"""
Unit tests for model classes.
"""

import pytest
from datetime import datetime
from app.models.database_manager import DatabaseManager, get_manager
from app.models.activities_manager import ActivitiesManager


class TestDatabaseManagerSingleton:
    """Test singleton pattern for DatabaseManager."""
    
    def test_get_manager_singleton(self):
        """Test that get_manager returns a singleton."""
        manager1 = get_manager()
        manager2 = get_manager()
        
        # They should be the same instance
        assert manager1 is manager2


class TestActivitiesManagerMethods:
    """Test ActivitiesManager methods."""
    
    def test_set_connection(self, temp_db):
        """Test setting database connection."""
        conn, cursor = temp_db
        manager = ActivitiesManager()
        
        manager.set_connection(conn, cursor)
        
        assert manager.conn == conn
        assert manager.cursor == cursor
    
    def test_mark_activity_complete(self, temp_db, sample_activity_data):
        """Test marking an activity as complete."""
        from PyQt6.QtCore import QDate
        
        conn, cursor = temp_db
        manager = ActivitiesManager(conn, cursor)
        manager.create_tables()
        
        # Add activity
        activity_id = manager.add_activity(
            title=sample_activity_data['title'],
            date=sample_activity_data['date'],
            start_time=sample_activity_data['start_time'],
            end_time=sample_activity_data['end_time'],
            activity_type=sample_activity_data['type']
        )
        
        # Mark as complete
        completion_date = QDate.fromString(sample_activity_data['date'], 'yyyy-MM-dd')
        success = manager.mark_activity_complete(activity_id, completion_date)
        
        assert success is True
        
        # Verify completion
        activities = manager.get_activities_for_date(completion_date)
        completed = [a for a in activities if a[0] == activity_id]
        assert len(completed) > 0
        assert completed[0][6] == 1  # completed flag
    
    def test_delete_activity(self, temp_db, sample_activity_data):
        """Test deleting an activity."""
        conn, cursor = temp_db
        manager = ActivitiesManager(conn, cursor)
        manager.create_tables()
        
        # Add activity
        activity_id = manager.add_activity(
            title=sample_activity_data['title'],
            date=sample_activity_data['date'],
            start_time=sample_activity_data['start_time'],
            end_time=sample_activity_data['end_time'],
            activity_type=sample_activity_data['type']
        )
        
        # Delete activity
        success = manager.delete_activity(activity_id)
        assert success is True
        
        # Verify deletion
        cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
        result = cursor.fetchone()
        assert result is None

