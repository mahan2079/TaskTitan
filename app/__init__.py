"""
TaskTitan application package
Main application modules
"""

import os

# Application metadata
__version__ = "1.0.0"
__app_name__ = "TaskTitan"

# Define version info at module level
__author__ = 'TaskTitan Team'

# Import database connector and initialize connection
from app.models.database_connector import DatabaseConnector
db_connector = DatabaseConnector()

def get_db_manager():
    """Get the application's database manager instance."""
    return db_connector.get_manager()

def get_db_connection():
    """Get a direct database connection."""
    return db_connector.get_connection()

def close_db():
    """Close the database connection."""
    db_connector.close() 