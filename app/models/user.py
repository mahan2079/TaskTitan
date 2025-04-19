from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime
import sqlite3
import hashlib
import json

class User(QObject):
    """Model class for users in the Task Titan application."""
    
    # Define signals
    dataChanged = pyqtSignal()
    
    def __init__(self, db_connection, user_id=None):
        """Initialize a User object.
        
        Args:
            db_connection: SQLite database connection
            user_id: ID of an existing user to load (optional)
        """
        super().__init__()
        self.conn = db_connection
        self.cursor = self.conn.cursor()
        
        # Initialize attributes
        self.id = user_id
        self.username = ""
        self.email = ""
        self.password_hash = ""
        self.first_name = ""
        self.last_name = ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.last_login = None
        self.preferences = {}
        self.profile_image = None
        self.is_active = True
        
        # Load user data if ID is provided
        if user_id:
            self.load()
    
    def load(self):
        """Load user data from the database."""
        try:
            self.cursor.execute("""
                SELECT username, email, password_hash, first_name, last_name,
                       created_at, updated_at, last_login, preferences, profile_image, is_active
                FROM users WHERE id = ?
            """, (self.id,))
            
            row = self.cursor.fetchone()
            if row:
                self.username = row[0]
                self.email = row[1]
                self.password_hash = row[2]
                self.first_name = row[3] or ""
                self.last_name = row[4] or ""
                self.created_at = datetime.fromisoformat(row[5])
                self.updated_at = datetime.fromisoformat(row[6])
                self.last_login = datetime.fromisoformat(row[7]) if row[7] else None
                self.preferences = json.loads(row[8]) if row[8] else {}
                self.profile_image = row[9]
                self.is_active = bool(row[10])
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        return False
    
    def save(self):
        """Save user data to the database."""
        self.updated_at = datetime.now()
        
        try:
            if self.id:  # Update existing user
                self.cursor.execute("""
                    UPDATE users
                    SET username = ?, email = ?, password_hash = ?, first_name = ?,
                        last_name = ?, updated_at = ?, last_login = ?, 
                        preferences = ?, profile_image = ?, is_active = ?
                    WHERE id = ?
                """, (
                    self.username, self.email, self.password_hash, 
                    self.first_name, self.last_name, self.updated_at.isoformat(),
                    self.last_login.isoformat() if self.last_login else None,
                    json.dumps(self.preferences), self.profile_image, self.is_active,
                    self.id
                ))
            else:  # Insert new user
                self.cursor.execute("""
                    INSERT INTO users
                    (username, email, password_hash, first_name, last_name,
                     created_at, updated_at, last_login, preferences, profile_image, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.username, self.email, self.password_hash, 
                    self.first_name, self.last_name, 
                    self.created_at.isoformat(), self.updated_at.isoformat(),
                    self.last_login.isoformat() if self.last_login else None,
                    json.dumps(self.preferences), self.profile_image, self.is_active
                ))
                self.id = self.cursor.lastrowid
            
            self.conn.commit()
            self.dataChanged.emit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
    
    def delete(self):
        """Delete user from the database."""
        if not self.id:
            return False
            
        try:
            self.cursor.execute("DELETE FROM users WHERE id = ?", (self.id,))
            self.conn.commit()
            
            self.id = None
            self.dataChanged.emit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
    
    def set_password(self, password):
        """Set the password hash from a plain text password."""
        salt = "tasktitan"  # In production, use a secure random salt per user
        password_with_salt = password + salt
        self.password_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
    
    def check_password(self, password):
        """Check if a plain text password matches the stored hash."""
        salt = "tasktitan"  # Use the same salt as in set_password
        password_with_salt = password + salt
        return self.password_hash == hashlib.sha256(password_with_salt.encode()).hexdigest()
    
    def record_login(self):
        """Record the current date/time as the last login time."""
        self.last_login = datetime.now()
        return self.save()
    
    def update_preference(self, key, value):
        """Update a user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        self.preferences[key] = value
        return self.save()
    
    def get_preference(self, key, default=None):
        """Get a user preference.
        
        Args:
            key: Preference key
            default: Default value if preference doesn't exist
            
        Returns:
            Preference value or default
        """
        return self.preferences.get(key, default)
    
    @staticmethod
    def get_by_id(db_connection, user_id):
        """Get a user by their ID.
        
        Args:
            db_connection: SQLite database connection
            user_id: User ID to retrieve
        
        Returns:
            User object or None if not found
        """
        user = User(db_connection, user_id)
        if user.username:  # Check if the user was loaded successfully
            return user
        return None
    
    @staticmethod
    def get_by_username(db_connection, username):
        """Get a user by their username.
        
        Args:
            db_connection: SQLite database connection
            username: Username to search for
        
        Returns:
            User object or None if not found
        """
        cursor = db_connection.cursor()
        
        try:
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            
            if row:
                return User(db_connection, row[0])
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            
        return None
    
    @staticmethod
    def get_by_email(db_connection, email):
        """Get a user by their email address.
        
        Args:
            db_connection: SQLite database connection
            email: Email address to search for
        
        Returns:
            User object or None if not found
        """
        cursor = db_connection.cursor()
        
        try:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            
            if row:
                return User(db_connection, row[0])
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            
        return None
    
    @staticmethod
    def authenticate(db_connection, username, password):
        """Authenticate a user with username and password.
        
        Args:
            db_connection: SQLite database connection
            username: Username to authenticate
            password: Password to check
        
        Returns:
            User object if authentication successful, None otherwise
        """
        user = User.get_by_username(db_connection, username)
        
        if user and user.check_password(password):
            user.record_login()
            return user
            
        return None
    
    def get_full_name(self):
        """Get the user's full name.
        
        Returns:
            User's full name or username if no name is set
        """
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username
    
    def get_tasks(self):
        """Get all tasks created by this user.
        
        Returns:
            List of Task objects
        """
        from app.models.task import Task
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM tasks WHERE user_id = ?", (self.id,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(self.conn, row[0]))
        
        return tasks
    
    def get_goals(self):
        """Get all goals created by this user.
        
        Returns:
            List of Goal objects
        """
        from app.models.goal import Goal
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM goals WHERE user_id = ?", (self.id,))
        
        goals = []
        for row in cursor.fetchall():
            goals.append(Goal(self.conn, row[0]))
        
        return goals 