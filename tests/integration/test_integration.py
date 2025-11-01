"""
Integration tests for TaskTitan.
"""

import pytest
from PyQt6.QtWidgets import QApplication
import sys
from app.models.database_manager import DatabaseManager
from app.models.activities_manager import ActivitiesManager
from app.core.config import ConfigManager


@pytest.fixture(scope="session")
def qt_app():
    """Create QApplication for Qt tests."""
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    yield app


class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    def test_full_goal_workflow(self, db_manager, sample_goal_data):
        """Test complete workflow for creating and managing goals."""
        # Create goals table
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
        
        # Create goal
        goal_id = db_manager.save_goal(sample_goal_data)
        assert goal_id is not None
        
        # Update goal
        sample_goal_data['id'] = goal_id
        sample_goal_data['completed'] = True
        updated_id = db_manager.save_goal(sample_goal_data)
        assert updated_id == goal_id
        
        # Verify update
        db_manager.execute("SELECT completed FROM goals WHERE id = ?", (goal_id,))
        result = db_manager.fetchone()
        assert result[0] == 1
    
    def test_activity_lifecycle(self, temp_db, sample_activity_data):
        """Test complete activity lifecycle."""
        from PyQt6.QtCore import QDate
        
        conn, cursor = temp_db
        manager = ActivitiesManager(conn, cursor)
        manager.create_tables()
        
        # Create activity
        activity_id = manager.add_activity(
            title=sample_activity_data['title'],
            date=sample_activity_data['date'],
            start_time=sample_activity_data['start_time'],
            end_time=sample_activity_data['end_time'],
            activity_type=sample_activity_data['type'],
            priority=sample_activity_data['priority'],
            category=sample_activity_data['category']
        )
        
        # Mark complete
        completion_date = QDate.fromString(sample_activity_data['date'], 'yyyy-MM-dd')
        manager.mark_activity_complete(activity_id, completion_date)
        
        # Verify completion
        activities = manager.get_activities_for_date(completion_date)
        completed = [a for a in activities if a[0] == activity_id and a[6] == 1]
        assert len(completed) > 0
        
        # Delete activity
        manager.delete_activity(activity_id)
        
        # Verify deletion
        activities = manager.get_activities_for_date(completion_date)
        found = [a for a in activities if a[0] == activity_id]
        assert len(found) == 0


class TestConfigIntegration:
    """Integration tests for configuration."""
    
    def test_config_persistence(self, temp_config):
        """Test that configuration persists."""
        manager = temp_config
        
        # Set values
        manager.set('window.width', 1500)
        manager.set('pomodoro.work_minutes', 30)
        
        # Reload config
        manager.reload()
        
        # Verify persistence
        assert manager.get('window.width') == 1500
        assert manager.get('pomodoro.work_minutes') == 30
    
    def test_config_defaults(self, temp_config):
        """Test that defaults are applied correctly."""
        manager = temp_config
        
        # Get default values
        width = manager.get('window.width')
        assert width == 1200
        
        # Reset to defaults
        manager.reset_to_defaults()
        
        # Verify defaults
        assert manager.get('window.width') == 1200

