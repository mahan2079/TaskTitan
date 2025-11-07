"""
Password management utilities for TaskTitan.
Handles password hashing, validation, and strength checking.
"""

import re
import bcrypt
from typing import Tuple, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PasswordManager:
    """Manages password operations including hashing and validation."""
    
    # Minimum password requirements
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        try:
            # Generate salt and hash password
            salt = bcrypt.gensalt(rounds=12)
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
            return password_hash.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {e}", exc_info=True)
            raise
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Stored password hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error verifying password: {e}", exc_info=True)
            return False
    
    @classmethod
    def validate_password_strength(cls, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength against requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password cannot be empty"
        
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters long"
        
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if cls.REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if cls.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, None
    
    @staticmethod
    def calculate_password_strength(password: str) -> int:
        """
        Calculate password strength score (0-100).
        
        Args:
            password: Password to evaluate
            
        Returns:
            Strength score from 0 to 100
        """
        score = 0
        
        # Length score (max 40 points)
        length_bonus = min(len(password) * 2, 40)
        score += length_bonus
        
        # Character variety (max 30 points)
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        variety_count = sum([has_upper, has_lower, has_digit, has_special])
        score += variety_count * 7.5
        
        # Complexity bonus (max 30 points)
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        if re.search(r'(.)\1{2,}', password):  # Repeated characters
            score -= 10
        
        return min(max(score, 0), 100)

