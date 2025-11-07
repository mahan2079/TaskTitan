import sqlite3
import os
from datetime import datetime
from app.utils.logger import get_logger
from app.utils.cache import CacheManager

logger = get_logger(__name__)

class DatabaseManager:
    """Manager class for database operations."""
    
    _instance = None
    _connection_pool: dict = {}  # Connection pool
    
    def __init__(self, db_path=None):
        """Initialize database manager with connection to the database."""
        # Use the get_db_path function for consistent database location
        if db_path is None:
            from app.models.database import get_db_path
            self.db_path = get_db_path()
        else:
            self.db_path = db_path
            
        self.conn = None
        self.cursor = None
        self.cache = CacheManager.get_instance()
        self.connect()
    
    def connect(self):
        """Connect to the database."""
        try:
            # Check connection pool first
            if self.db_path in DatabaseManager._connection_pool:
                self.conn = DatabaseManager._connection_pool[self.db_path]
            else:
                self.conn = sqlite3.connect(self.db_path)
                # Store in connection pool
                DatabaseManager._connection_pool[self.db_path] = self.conn
            
            self.cursor = self.conn.cursor()
            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            # Optimize SQLite settings for performance
            self.cursor.execute("PRAGMA synchronous = NORMAL;")
            self.cursor.execute("PRAGMA journal_mode = WAL;")
            self.cursor.execute("PRAGMA cache_size = -64000;")  # 64MB cache
            self.cursor.execute("PRAGMA temp_store = MEMORY;")
            self.conn.commit()
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}", exc_info=True)
            raise
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
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
            logger.error(f"SQL execution error: {e}")
            logger.debug(f"Query: {sql}")
            logger.debug(f"Params: {params}")
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
        # Check cache first
        cache_key = f"count:{table}:{completed}"
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        query = f"SELECT COUNT(*) FROM {table}"
        if completed is not None:
            query += f" WHERE completed = {1 if completed else 0}"
            
        self.execute(query)
        result = self.fetchone()[0]
        
        # Cache result
        self.cache.set(cache_key, result)
        
        return result
            
    def save_goal(self, goal_data):
        """Save a goal to the database."""
        goal_id = None
        
        try:
            # Check if this is an update or insert
            if 'id' in goal_data and goal_data['id']:
                # Update existing goal
                self.cursor.execute("""
                    UPDATE goals SET 
                        parent_id = ?,
                        title = ?,
                        due_date = ?,
                        due_time = ?,
                        completed = ?,
                        priority = ?,
                        color = ?
                    WHERE id = ?
                """, (
                    goal_data.get('parent_id'),
                    goal_data['title'],
                    goal_data.get('due_date'),
                    goal_data.get('due_time'),
                    1 if goal_data.get('completed') else 0,
                    goal_data.get('priority', 1),
                    goal_data.get('color'),
                    goal_data['id']
                ))
                goal_id = goal_data['id']
                
                # Verify the update worked
                if self.cursor.rowcount == 0:
                    logger.warning(f"Goal update affected 0 rows, ID: {goal_id}")
            else:
                # Insert new goal
                self.cursor.execute("""
                    INSERT INTO goals (
                        parent_id, title, due_date, due_time, completed, priority, color
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    goal_data.get('parent_id'),
                    goal_data['title'],
                    goal_data.get('due_date'),
                    goal_data.get('due_time'),
                    1 if goal_data.get('completed') else 0,
                    goal_data.get('priority', 1),
                    goal_data.get('color')
                ))
                goal_id = self.cursor.lastrowid
                
                # Verify the insert worked
                if not goal_id:
                    raise sqlite3.Error("Failed to get ID of inserted goal")
            
            # Commit the changes
            self.conn.commit()
            
            # Double-check that the goal exists in the database
            self.cursor.execute("SELECT id FROM goals WHERE id = ?", (goal_id,))
            if not self.cursor.fetchone():
                raise sqlite3.Error(f"Goal with ID {goal_id} not found after save")
                
            logger.info(f"Successfully saved goal ID: {goal_id}")
            
            # Invalidate related caches
            if self.cache:
                self.cache.invalidate_pattern("count:goals")
                self.cache.invalidate_pattern(f"goal:{goal_id}")
            
            return goal_id
            
        except sqlite3.Error as e:
            # Roll back transaction on error
            self.conn.rollback()
            logger.error(f"Error saving goal: {e}", exc_info=True)
            raise

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