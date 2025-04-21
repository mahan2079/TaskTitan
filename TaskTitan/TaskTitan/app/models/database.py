"""
Database initialization for TaskTitan.

This module handles connecting to the database and initializing it with
the required schema if necessary.
"""
import os
import sqlite3
from pathlib import Path

from app.models.database_updater import update_database

def initialize_db():
    """Initialize the database connection and schema."""
    # Create an application data directory in user's home folder
    app_data_dir = os.path.join(str(Path.home()), '.tasktitan')
    
    # Create directory if it doesn't exist
    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)
        
    # Set database path to an absolute path in the app data directory
    db_path = os.path.join(app_data_dir, 'tasktitan.db')
    print(f"Using database at: {db_path}")
    
    # Update the database schema if needed
    db_exists = os.path.exists(db_path)
    if db_exists:
        try:
            update_database(db_path)
        except Exception as e:
            print(f"Warning: Database schema update failed: {e}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Return connection and cursor
    return conn, cursor 