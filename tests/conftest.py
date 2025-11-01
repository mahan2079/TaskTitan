"""
Pytest configuration and fixtures for TaskTitan tests.
"""

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.database import initialize_db, get_db_path
from app.models.database_manager import DatabaseManager
from app.core.config import ConfigManager


@pytest.fixture(scope="function")
def temp_db():
    """Create a temporary database for testing."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test_tasktitan.db')
    
    # Initialize database
    conn, cursor = initialize_db()
    original_path = get_db_path()
    
    # Override database path temporarily
    import app.models.database as db_module
    original_get_path = db_module.get_db_path
    db_module.get_db_path = lambda: db_path
    
    # Create tables
    conn, cursor = initialize_db()
    
    yield conn, cursor
    
    # Cleanup
    conn.close()
    db_module.get_db_path = original_get_path
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def db_manager(temp_db):
    """Create a DatabaseManager instance with temporary database."""
    conn, cursor = temp_db
    manager = DatabaseManager()
    manager.conn = conn
    manager.cursor = cursor
    manager.db_path = get_db_path()
    
    yield manager
    
    manager.close()


@pytest.fixture(scope="function")
def temp_config():
    """Create a temporary configuration file."""
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, 'test_config.json')
    
    # Create config manager with temp path
    manager = ConfigManager()
    original_path = manager.config_file
    manager.config_file = Path(config_path)
    manager.config = manager._get_default_config()
    manager._save_config()
    
    yield manager
    
    # Cleanup
    if os.path.exists(config_path):
        os.remove(config_path)
    os.rmdir(temp_dir)
    manager.config_file = original_path


@pytest.fixture(scope="function")
def sample_goal_data():
    """Sample goal data for testing."""
    return {
        'title': 'Test Goal',
        'parent_id': None,
        'due_date': '2024-12-31',
        'due_time': None,
        'completed': False,
        'priority': 1,
        'color': None
    }


@pytest.fixture(scope="function")
def sample_activity_data():
    """Sample activity data for testing."""
    return {
        'title': 'Test Activity',
        'date': '2024-01-01',
        'start_time': '09:00',
        'end_time': '10:00',
        'type': 'task',
        'priority': 1,
        'category': 'Work',
        'completed': False
    }


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for tests."""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    yield
    # Cleanup logging if needed


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for file operations."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

