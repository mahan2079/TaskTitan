"""
Database schema updater for TaskTitan.

This module handles upgrading the database schema and migrating data
between versions to ensure compatibility with newer application versions.
"""
import sqlite3
import os
import logging
from datetime import datetime

from app.models.database_schema import CREATE_TABLES_SQL, MIGRATION_SCRIPTS, SCHEMA_VERSION

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("database_migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseUpdater:
    """Handles database schema updates and data migration."""
    
    def __init__(self, db_path):
        """Initialize the updater with a database path."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def get_schema_version(self):
        """Get the current schema version from the database."""
        try:
            # Check if the version table exists
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            if not self.cursor.fetchone():
                # Create the version table if it doesn't exist
                self.cursor.execute(
                    "CREATE TABLE schema_version (version INTEGER NOT NULL)"
                )
                self.cursor.execute("INSERT INTO schema_version (version) VALUES (0)")
                self.conn.commit()
                return 0
            
            # Get the current version
            self.cursor.execute("SELECT version FROM schema_version")
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                # Insert version 0 if no row exists
                self.cursor.execute("INSERT INTO schema_version (version) VALUES (0)")
                self.conn.commit()
                return 0
        except sqlite3.Error as e:
            logger.error(f"Failed to get schema version: {e}")
            return 0
    
    def update_schema_version(self, version):
        """Update the schema version in the database."""
        try:
            self.cursor.execute("UPDATE schema_version SET version = ?", (version,))
            self.conn.commit()
            logger.info(f"Updated schema version to {version}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to update schema version: {e}")
            return False
    
    def backup_database(self):
        """Create a backup of the database before schema changes."""
        try:
            backup_path = f"{self.db_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Created database backup at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return False
    
    def check_if_table_exists(self, table_name):
        """Check if a table exists in the database."""
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return bool(self.cursor.fetchone())
    
    def update_schema(self):
        """Update the database schema to the latest version."""
        try:
            # Connect to the database
            if not self.connect():
                return False
            
            # Get the current schema version
            current_version = self.get_schema_version()
            logger.info(f"Current schema version: {current_version}")
            
            # Check if we need to update
            if current_version >= SCHEMA_VERSION:
                logger.info("Database schema is up to date")
                return True
            
            # Create a backup before updating
            if not self.backup_database():
                logger.warning("Failed to create backup, but continuing with update")
            
            # Apply migrations sequentially
            for version in range(current_version + 1, SCHEMA_VERSION + 1):
                logger.info(f"Applying migration to version {version}")
                
                try:
                    # Apply the migration script
                    if version - 1 < len(MIGRATION_SCRIPTS):
                        # Format the SQL to include any required table creation scripts
                        migration_sql = MIGRATION_SCRIPTS[version - 1].format(**CREATE_TABLES_SQL)
                        
                        # Execute the migration script
                        self.cursor.executescript(migration_sql)
                        self.conn.commit()
                    
                    # Update the schema version
                    self.update_schema_version(version)
                    logger.info(f"Successfully migrated to version {version}")
                
                except sqlite3.Error as e:
                    logger.error(f"Migration to version {version} failed: {e}")
                    # Roll back the transaction
                    self.conn.rollback()
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Schema update failed: {e}")
            return False
        
        finally:
            # Close the connection
            self.close()
    
    def check_database_integrity(self):
        """Check the integrity of the database."""
        try:
            if not self.connect():
                return False
                
            self.cursor.execute("PRAGMA integrity_check")
            result = self.cursor.fetchone()
            
            if result and result[0] == 'ok':
                logger.info("Database integrity check passed")
                return True
            else:
                logger.error(f"Database integrity check failed: {result}")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Database integrity check failed: {e}")
            return False
            
        finally:
            self.close()


def update_database(db_path):
    """Update the database schema and migrate data."""
    logger.info(f"Starting database update for {db_path}")
    
    # Create the updater
    updater = DatabaseUpdater(db_path)
    
    # Check database integrity
    if not updater.check_database_integrity():
        logger.error("Database integrity check failed, aborting update")
        return False
    
    # Update the schema
    if not updater.update_schema():
        logger.error("Database schema update failed")
        return False
    
    logger.info("Database update completed successfully")
    return True 