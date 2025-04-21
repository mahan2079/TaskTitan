import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    """Manager class for database operations."""
    
    _instance = None
    
    def __init__(self, db_path="tasktitan.db"):
        """Initialize database manager with connection to the database."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
    
    def connect(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            self.conn.commit()
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed")
    
    def commit(self):
        """Commit changes to the database."""
        if self.conn:
            self.conn.commit()
    
    def execute(self, sql, params=None):
        """Execute SQL query with optional parameters."""
        try:
            if params:
                return self.cursor.execute(sql, params)
            else:
                return self.cursor.execute(sql)
        except sqlite3.Error as e:
            print(f"SQL execution error: {e}")
            print(f"Query: {sql}")
            print(f"Params: {params}")
            raise
    
    def fetchone(self):
        """Fetch one result from the cursor."""
        return self.cursor.fetchone()
    
    def fetchall(self):
        """Fetch all results from the cursor."""
        return self.cursor.fetchall()
    
    def initialize_db(self):
        """Initialize the database if needed."""
        # This method would recreate tables if needed
        from app.models.database import initialize_db
        self.conn, self.cursor = initialize_db()
    
    def count_items(self, table, completed=None):
        """Count items in a table, optionally filtered by completion status."""
        query = f"SELECT COUNT(*) FROM {table}"
        if completed is not None:
            query += f" WHERE completed = {1 if completed else 0}"
            
        self.execute(query)
        return self.fetchone()[0]
            
# Singleton instance
_manager = None

def get_manager():
    """Get the singleton instance of DatabaseManager."""
    global _manager
    if _manager is None:
        _manager = DatabaseManager()
    return _manager

def close_connection():
    """Close the database connection."""
    global _manager
    if _manager:
        _manager.close()
        _manager = None 