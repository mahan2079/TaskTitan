"""
User model for TaskTitan.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class User:
    """Represents a user in the system."""
    
    def __init__(self, user_id: int, username: str, created_at: Optional[datetime] = None,
                 last_login: Optional[datetime] = None, is_active: bool = True):
        """
        Initialize a User object.
        
        Args:
            user_id: User ID
            username: Username
            created_at: Account creation timestamp
            last_login: Last login timestamp
            is_active: Whether account is active
        """
        self.id = user_id
        self.username = username
        self.created_at = created_at
        self.last_login = last_login
        self.is_active = is_active
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from dictionary."""
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'])
            else:
                created_at = data['created_at']
        
        last_login = None
        if data.get('last_login'):
            if isinstance(data['last_login'], str):
                last_login = datetime.fromisoformat(data['last_login'])
            else:
                last_login = data['last_login']
        
        return cls(
            user_id=data['id'],
            username=data['username'],
            created_at=created_at,
            last_login=last_login,
            is_active=data.get('is_active', True)
        )

