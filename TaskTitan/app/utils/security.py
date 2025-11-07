"""
Security utilities for TaskTitan.

This module provides security-related functions for file handling,
path sanitization, and security checks.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from app.utils.logger import get_logger
from app.utils.validators import (
    validate_file_path,
    validate_file_extension,
    validate_file_size,
    sanitize_filename,
    sanitize_category,
    MAX_FILE_SIZE,
    ALLOWED_FILE_EXTENSIONS
)

logger = get_logger(__name__)


def sanitize_path(file_path: str, base_dir: Optional[str] = None) -> Optional[str]:
    """
    Sanitize a file path to prevent path traversal attacks.
    
    Args:
        file_path: Path to sanitize
        base_dir: Base directory to ensure path stays within
        
    Returns:
        Sanitized path or None if invalid
    """
    try:
        # Normalize the path
        normalized = os.path.normpath(file_path)
        
        # Check for path traversal attempts
        if '..' in normalized or normalized.startswith('/'):
            logger.warning(f"Path traversal attempt detected: {file_path}")
            return None
        
        # If base_dir is provided, ensure path is within it
        if base_dir:
            base_path = os.path.normpath(base_dir)
            full_path = os.path.abspath(os.path.join(base_path, normalized))
            if not full_path.startswith(os.path.abspath(base_path)):
                logger.warning(f"Path outside base directory: {file_path}")
                return None
        
        return normalized
    except Exception as e:
        logger.error(f"Error sanitizing path: {e}", exc_info=True)
        return None


def check_file_security(file_path: str, check_size: bool = True, 
                       check_extension: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Perform comprehensive security checks on a file.
    
    Args:
        file_path: Path to the file to check
        check_size: Whether to check file size
        check_extension: Whether to check file extension
        
    Returns:
        Tuple of (is_safe, error_message)
    """
    # Validate path
    valid, error = validate_file_path(file_path)
    if not valid:
        return False, error
    
    # Check file exists
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    # Check file extension
    if check_extension:
        filename = os.path.basename(file_path)
        valid, error = validate_file_extension(filename)
        if not valid:
            return False, error
    
    # Check file size
    if check_size:
        valid, error = validate_file_size(file_path)
        if not valid:
            return False, error
    
    return True, None


def get_file_hash(file_path: str, algorithm: str = 'sha256') -> Optional[str]:
    """
    Calculate hash of a file for integrity checking.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use ('md5', 'sha1', 'sha256')
        
    Returns:
        Hex digest of the hash or None on error
    """
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}", exc_info=True)
        return None


def secure_file_copy(source: str, destination: str, 
                    validate_source: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Securely copy a file with validation.
    
    Args:
        source: Source file path
        destination: Destination file path
        validate_source: Whether to validate source file
        
    Returns:
        Tuple of (success, error_message)
    """
    import shutil
    
    # Validate source file
    if validate_source:
        safe, error = check_file_security(source)
        if not safe:
            return False, error
    
    # Sanitize destination path
    dest_dir = os.path.dirname(destination)
    sanitized_dest = sanitize_path(destination, dest_dir)
    if not sanitized_dest:
        return False, "Invalid destination path"
    
    try:
        # Ensure destination directory exists
        os.makedirs(dest_dir, exist_ok=True)
        
        # Copy file
        shutil.copy2(source, sanitized_dest)
        logger.info(f"Securely copied file from {source} to {sanitized_dest}")
        return True, None
    except Exception as e:
        logger.error(f"Error securely copying file: {e}", exc_info=True)
        return False, str(e)


def is_safe_path(path: str, base_path: str) -> bool:
    """
    Check if a path is safe (within base path).
    
    Args:
        path: Path to check
        base_path: Base path that path must be within
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        real_path = os.path.realpath(path)
        real_base = os.path.realpath(base_path)
        return real_path.startswith(real_base)
    except Exception:
        return False


def prevent_sql_injection(text: str) -> str:
    """
    Basic SQL injection prevention (though we use parameterized queries).
    This is a secondary check.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    # Remove common SQL injection patterns
    dangerous_patterns = [
        r"(\bOR\b|\bAND\b)\s*\d+\s*=\s*\d+",
        r"(\bOR\b|\bAND\b)\s*['\"]\s*['\"]",
        r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b|\bDROP\b)",
        r"--",
        r"/\*",
        r"\*/",
        r";\s*--",
    ]
    
    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def validate_attachment_file(file_path: str, max_size: int = MAX_FILE_SIZE) -> Tuple[bool, Optional[str]]:
    """
    Validate an attachment file comprehensively.
    
    Args:
        file_path: Path to the file
        max_size: Maximum file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file exists
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    # Check file security
    safe, error = check_file_security(file_path, check_size=True, check_extension=True)
    if not safe:
        return False, error
    
    # Check file size with custom limit
    if max_size != MAX_FILE_SIZE:
        size = os.path.getsize(file_path)
        if size > max_size:
            size_mb = size / (1024 * 1024)
            max_mb = max_size / (1024 * 1024)
            return False, f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({max_mb:.2f}MB)"
    
    return True, None

