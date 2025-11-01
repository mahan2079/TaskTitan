"""
Database encryption utilities for TaskTitan.
Handles database encryption/decryption using SQLCipher or SQLite encryption.
"""

import os
import sqlite3
from typing import Optional, Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseEncryption:
    """Manages database encryption and decryption."""
    
    def __init__(self):
        """Initialize database encryption manager."""
        self.use_sqlcipher = self._check_sqlcipher_available()
        logger.info(f"Database encryption: {'SQLCipher' if self.use_sqlcipher else 'SQLite built-in'} available")
    
    def _check_sqlcipher_available(self) -> bool:
        """
        Check if SQLCipher is available.
        
        Returns:
            True if SQLCipher is available, False otherwise
        """
        try:
            # Try to import pysqlcipher3
            import pysqlcipher3.dbapi2 as sqlcipher
            return True
        except ImportError:
            try:
                # Try alternative import
                from pysqlcipher import dbapi2 as sqlcipher
                return True
            except ImportError:
                logger.warning("SQLCipher not available. Database encryption will use SQLite's built-in encryption (if available)")
                return False
    
    def derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive encryption key from password.
        
        Args:
            password: User password
            salt: Optional salt bytes (if None, generates new salt)
            
        Returns:
            Encryption key bytes
        """
        import hashlib
        import secrets
        
        if salt is None:
            salt = secrets.token_bytes(16)
        
        # Use PBKDF2-like key derivation
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return key
    
    def encrypt_database(self, db_path: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Encrypt an existing database.
        
        Args:
            db_path: Path to database file
            password: Encryption password
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not os.path.exists(db_path):
                return False, "Database file not found"
            
            if self.use_sqlcipher:
                return self._encrypt_with_sqlcipher(db_path, password)
            else:
                # Fallback to SQLite encryption if available
                logger.warning("SQLCipher not available. Database encryption requires SQLCipher.")
                return False, "SQLCipher not available. Please install pysqlcipher3 for database encryption."
                
        except Exception as e:
            logger.error(f"Error encrypting database: {e}", exc_info=True)
            return False, str(e)
    
    def _encrypt_with_sqlcipher(self, db_path: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Encrypt database using SQLCipher.
        
        Args:
            db_path: Path to database file
            password: Encryption password
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            import pysqlcipher3.dbapi2 as sqlcipher
            
            # Create temporary encrypted database
            temp_path = db_path + ".encrypted"
            
            # Connect to source database
            source_conn = sqlite3.connect(db_path)
            
            # Create encrypted database
            encrypted_conn = sqlcipher.connect(temp_path)
            encrypted_conn.execute(f"PRAGMA key='{password}'")
            
            # Copy schema and data
            source_conn.backup(encrypted_conn)
            
            # Close connections
            source_conn.close()
            encrypted_conn.close()
            
            # Replace original with encrypted
            os.replace(temp_path, db_path)
            
            logger.info(f"Database encrypted successfully: {db_path}")
            return True, None
            
        except ImportError:
            return False, "SQLCipher (pysqlcipher3) not installed"
        except Exception as e:
            logger.error(f"Error encrypting with SQLCipher: {e}", exc_info=True)
            return False, str(e)
    
    def connect_encrypted_database(self, db_path: str, password: str) -> Optional[sqlite3.Connection]:
        """
        Connect to an encrypted database.
        
        Args:
            db_path: Path to encrypted database
            password: Decryption password
            
        Returns:
            Database connection or None if failed
        """
        try:
            if self.use_sqlcipher:
                return self._connect_with_sqlcipher(db_path, password)
            else:
                logger.warning("SQLCipher not available. Cannot connect to encrypted database.")
                return None
                
        except Exception as e:
            logger.error(f"Error connecting to encrypted database: {e}", exc_info=True)
            return None
    
    def _connect_with_sqlcipher(self, db_path: str, password: str) -> Optional[sqlite3.Connection]:
        """
        Connect to encrypted database using SQLCipher.
        
        Args:
            db_path: Path to encrypted database
            password: Decryption password
            
        Returns:
            Database connection or None if failed
        """
        try:
            import pysqlcipher3.dbapi2 as sqlcipher
            
            conn = sqlcipher.connect(db_path)
            conn.execute(f"PRAGMA key='{password}'")
            
            # Test connection
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            logger.info(f"Successfully connected to encrypted database: {db_path}")
            return conn
            
        except ImportError:
            logger.error("SQLCipher (pysqlcipher3) not installed")
            return None
        except Exception as e:
            logger.error(f"Error connecting to encrypted database: {e}", exc_info=True)
            return None
    
    def is_database_encrypted(self, db_path: str) -> bool:
        """
        Check if a database is encrypted.
        
        Args:
            db_path: Path to database file
            
        Returns:
            True if database appears to be encrypted, False otherwise
        """
        try:
            if not os.path.exists(db_path):
                return False
            
            # Try to open as regular SQLite database
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                conn.close()
                return False  # Successfully opened as regular SQLite
            except sqlite3.DatabaseError:
                # Database might be encrypted
                return True
                
        except Exception as e:
            logger.warning(f"Error checking database encryption status: {e}")
            return False


def get_encryption_manager() -> DatabaseEncryption:
    """Get singleton instance of DatabaseEncryption."""
    global _encryption_manager
    if '_encryption_manager' not in globals():
        _encryption_manager = DatabaseEncryption()
    return _encryption_manager

