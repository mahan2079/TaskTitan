import sqlite3
from datetime import datetime, timedelta
from app.models.database_manager import get_manager, get_connection, get_cursor, close_connection

def initialize_db():
    """Initialize the database with the required tables.
    
    Returns:
        tuple: A tuple containing (connection, cursor)
    """
    # Use the database manager to ensure a properly initialized database
    manager = get_manager()
    
    # Get a connection and cursor
    conn = get_connection()
    cursor = get_cursor()
    
    return conn, cursor 