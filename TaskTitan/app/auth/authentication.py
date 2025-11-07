"""
Authentication management for TaskTitan.
Handles user login, logout, session management, and authentication state.
"""

import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from app.auth.password_manager import PasswordManager
from app.utils.logger import get_logger
from app.models.database import get_db_path

logger = get_logger(__name__)


class AuthenticationManager:
    """Manages user authentication and sessions."""
    
    _instance: Optional['AuthenticationManager'] = None
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize authentication manager."""
        if AuthenticationManager._instance is not None:
            raise RuntimeError("AuthenticationManager is a singleton. Use get_auth_manager() instead.")
        
        self.db_path = db_path or get_db_path()
        self.password_manager = PasswordManager()
        self.current_user: Optional[Dict[str, Any]] = None
        self.session_token: Optional[str] = None
        self.session_expiry: Optional[datetime] = None
        self._ensure_users_table()
    
    def _ensure_users_table(self):
        """Ensure users table exists in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            conn.commit()
            conn.close()
            logger.debug("Users table ensured")
        except Exception as e:
            logger.error(f"Error ensuring users table: {e}", exc_info=True)
    
    def create_user(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Create a new user account.
        
        Args:
            username: Username for the account
            password: Plain text password
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate username
            if not username or len(username.strip()) < 3:
                return False, "Username must be at least 3 characters long"
            
            username = username.strip().lower()
            
            # Validate password strength
            is_valid, error_msg = self.password_manager.validate_password_strength(password)
            if not is_valid:
                return False, error_msg
            
            # Check if user already exists
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return False, "Username already exists"
            
            # Hash password and create user
            password_hash = self.password_manager.hash_password(password)
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, created_at, is_active)
                VALUES (?, ?, CURRENT_TIMESTAMP, 1)
            """, (username, password_hash))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created user account: {username}")
            return True, None
            
        except sqlite3.Error as e:
            logger.error(f"Database error creating user: {e}", exc_info=True)
            return False, "Database error occurred"
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            return False, str(e)
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            username = username.strip().lower()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, password_hash, is_active
                FROM users
                WHERE username = ?
            """, (username,))
            
            user_data = cursor.fetchone()
            conn.close()
            
            if not user_data:
                logger.warning(f"Authentication failed: user not found - {username}")
                return False, "Invalid username or password"
            
            user_id, db_username, password_hash, is_active = user_data
            
            if not is_active:
                return False, "Account is disabled"
            
            # Verify password
            if not self.password_manager.verify_password(password, password_hash):
                logger.warning(f"Authentication failed: wrong password - {username}")
                return False, "Invalid username or password"
            
            # Update last login
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user_id,))
            conn.commit()
            conn.close()
            
            # Create session
            self.current_user = {
                'id': user_id,
                'username': db_username,
                'is_active': bool(is_active)
            }
            
            self.session_token = secrets.token_urlsafe(32)
            self.session_expiry = datetime.now() + timedelta(hours=24)
            
            logger.info(f"User authenticated: {username}")
            return True, None
            
        except sqlite3.Error as e:
            logger.error(f"Database error during authentication: {e}", exc_info=True)
            return False, "Database error occurred"
        except Exception as e:
            logger.error(f"Error during authentication: {e}", exc_info=True)
            return False, str(e)
    
    def logout(self):
        """Logout current user and clear session."""
        if self.current_user:
            logger.info(f"User logged out: {self.current_user.get('username')}")
        
        self.current_user = None
        self.session_token = None
        self.session_expiry = None
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        if not self.current_user or not self.session_token:
            return False
        
        # Check session expiry
        if self.session_expiry and datetime.now() > self.session_expiry:
            logger.info("Session expired")
            self.logout()
            return False
        
        return True
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user."""
        if not self.is_authenticated():
            return None
        return self.current_user.copy()
    
    def change_password(self, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Change password for current user.
        
        Args:
            old_password: Current password
            new_password: New password
            
        Returns:
            Tuple of (success, error_message)
        """
        if not self.is_authenticated():
            return False, "Not authenticated"
        
        try:
            username = self.current_user['username']
            
            # Verify old password
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (self.current_user['id'],))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False, "User not found"
            
            old_password_hash = result[0]
            
            if not self.password_manager.verify_password(old_password, old_password_hash):
                conn.close()
                return False, "Current password is incorrect"
            
            # Validate new password strength
            is_valid, error_msg = self.password_manager.validate_password_strength(new_password)
            if not is_valid:
                conn.close()
                return False, error_msg
            
            # Update password
            new_password_hash = self.password_manager.hash_password(new_password)
            cursor.execute("""
                UPDATE users SET password_hash = ?
                WHERE id = ?
            """, (new_password_hash, self.current_user['id']))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Password changed for user: {username}")
            return True, None
            
        except sqlite3.Error as e:
            logger.error(f"Database error changing password: {e}", exc_info=True)
            return False, "Database error occurred"
        except Exception as e:
            logger.error(f"Error changing password: {e}", exc_info=True)
            return False, str(e)
    
    def reset_password(self, username: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Reset password for a user (admin function).
        
        Args:
            username: Username
            new_password: New password
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate new password strength
            is_valid, error_msg = self.password_manager.validate_password_strength(new_password)
            if not is_valid:
                return False, error_msg
            
            username = username.strip().lower()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not cursor.fetchone():
                conn.close()
                return False, "User not found"
            
            # Update password
            new_password_hash = self.password_manager.hash_password(new_password)
            cursor.execute("""
                UPDATE users SET password_hash = ?
                WHERE username = ?
            """, (new_password_hash, username))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Password reset for user: {username}")
            return True, None
            
        except sqlite3.Error as e:
            logger.error(f"Database error resetting password: {e}", exc_info=True)
            return False, "Database error occurred"
        except Exception as e:
            logger.error(f"Error resetting password: {e}", exc_info=True)
            return False, str(e)


def get_auth_manager(db_path: Optional[str] = None) -> AuthenticationManager:
    """Get singleton instance of AuthenticationManager."""
    if AuthenticationManager._instance is None:
        AuthenticationManager._instance = AuthenticationManager(db_path)
    return AuthenticationManager._instance

