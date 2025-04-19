"""Database connector module for TaskTitan."""

import sqlite3
import os

class DatabaseConnector:
    """Simple database connector class for TaskTitan."""
    
    def __init__(self):
        """Initialize the database connector."""
        self.connection = None
        self.cursor = None
        self.initialized = False
        self.db_path = None
    
    def initialize(self):
        """Initialize the database connection."""
        # Get the database path
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_dir = os.path.join(app_dir, "database", "data")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self.db_path = os.path.join(db_dir, "tasktitan.db")
        
        # Create connection
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self.initialized = True
        
        return self.connection
    
    def get_connection(self):
        """Get the database connection."""
        if not self.initialized:
            return self.initialize()
        return self.connection
    
    def get_manager(self):
        """Get the database manager (cursor)."""
        if not self.initialized:
            self.initialize()
        return self.cursor
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
            self.initialized = False 