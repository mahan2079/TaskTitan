import os
import shutil
import sqlite3
from pathlib import Path
import sys
from app.utils.logger import get_logger

logger = get_logger(__name__)

def fix_journal_entries_schema(db_path):
    """
    Fix schema issues with the journal_entries table.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if journal_entries table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_entries'")
        if not cursor.fetchone():
            # Create the table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id TEXT PRIMARY KEY,
                    date TEXT UNIQUE,
                    wins TEXT,
                    challenges TEXT,
                    learnings TEXT,
                    tomorrow TEXT,
                    gratitude TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info(f"Created journal_entries table in {db_path}")
            
        # Check if journal_attachments table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_attachments'")
        if not cursor.fetchone():
            # Create the table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    category TEXT
                )
            """)
            logger.info(f"Created journal_attachments table in {db_path}")
        else:
            # Check if the category column exists in journal_attachments
            cursor.execute("PRAGMA table_info(journal_attachments)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'category' not in columns:
                # Add category column if it doesn't exist
                cursor.execute("ALTER TABLE journal_attachments ADD COLUMN category TEXT")
                logger.info(f"Added category column to journal_attachments table in {db_path}")
        
        # Commit changes
        conn.commit()
        
        return True
    except Exception as e:
        logger.error(f"Error fixing journal_entries schema: {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()

def migrate_databases():
    """
    Migrate existing database files to the central data directory.
    This function searches for database files in various locations and copies them
    to the central data directory if they don't already exist there.
    """
    # Adjust import paths
    import os
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(current_dir)
    root_dir = os.path.dirname(app_dir)
    
    # Add root directory to sys.path for proper imports
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    
    # Now we can import app modules
    from app.models.database import get_db_path
    
    # Get the target path
    target_db_path = get_db_path()
    target_dir = os.path.dirname(target_db_path)
    
    # Create the target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        logger.info(f"Created data directory: {target_dir}")
    
    # Check if the target database already exists
    if os.path.exists(target_db_path):
        logger.info(f"Database already exists at {target_db_path}")
        # Ensure schema is up to date even if DB exists
        fix_journal_entries_schema(target_db_path)
        try:
            from app.models.database import initialize_db
            conn, cursor = initialize_db()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not apply database schema updates: {e}", exc_info=True)
        return
    
    # Possible database locations
    possible_locations = []
    
    # App data directory
    app_data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "TaskTitan")
    possible_locations.append(os.path.join(app_data_dir, "tasktitan.db"))
    
    # Current directory
    possible_locations.append("tasktitan.db")
    
    # Home directory
    possible_locations.append(os.path.join(os.path.expanduser("~"), "tasktitan.db"))
    
    # Check all possible locations
    for source_path in possible_locations:
        if os.path.exists(source_path):
            logger.info(f"Found database at {source_path}")
            try:
                # Copy the database
                shutil.copy2(source_path, target_db_path)
                logger.info(f"Migrated database to {target_db_path}")
                
                # Fix schema if needed
                fix_journal_entries_schema(target_db_path)
                
                return
            except Exception as e:
                logger.error(f"Error migrating database: {e}", exc_info=True)
    
    # If no existing database was found, create a new one
    logger.info("No existing database found. Creating a new one.")
    from app.models.database import initialize_db
    initialize_db()

if __name__ == "__main__":
    try:
        logger.info("Running database migration...")
        logger.debug(f"Current working directory: {os.getcwd()}")
        migrate_databases()
        logger.info("Database migration completed.")
    except Exception as e:
        logger.critical(f"Error during migration: {e}", exc_info=True) 