"""
Input validation utilities for TaskTitan.

This module provides validation functions for user input,
ensuring data integrity and preventing security issues.
"""

import os
import re
from typing import Optional, Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Validation constants
MAX_TITLE_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 5000
MAX_CATEGORY_LENGTH = 100
MAX_TAG_LENGTH = 50
MAX_NOTES_LENGTH = 10000

# Allowed file extensions for attachments
ALLOWED_FILE_EXTENSIONS = {
    # Documents
    '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
    # Archives
    '.zip', '.rar', '.7z', '.tar', '.gz',
    # Spreadsheets
    '.xls', '.xlsx', '.csv', '.ods',
    # Presentations
    '.ppt', '.pptx', '.odp',
    # Audio
    '.mp3', '.wav', '.ogg', '.flac',
    # Video
    '.mp4', '.avi', '.mov', '.mkv', '.webm',
    # Other
    '.json', '.xml', '.html', '.md'
}

# Maximum file size (50MB default)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes


def validate_text(text: str, field_name: str = "text", max_length: int = MAX_TITLE_LENGTH, 
                 allow_empty: bool = False, strip: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate text input.
    
    Args:
        text: Text to validate
        field_name: Name of the field for error messages
        max_length: Maximum allowed length
        allow_empty: Whether empty strings are allowed
        strip: Whether to strip whitespace
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(text, str):
        return False, f"{field_name} must be a string"
    
    if strip:
        text = text.strip()
    
    if not allow_empty and not text:
        return False, f"{field_name} cannot be empty"
    
    if len(text) > max_length:
        return False, f"{field_name} cannot exceed {max_length} characters"
    
    # Check for potentially dangerous characters
    if re.search(r'[<>"\']', text):
        logger.warning(f"Potentially dangerous characters detected in {field_name}")
        # Allow but log - these might be needed for formatting
    
    return True, None


def validate_title(title: str, allow_empty: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate a title."""
    return validate_text(title, "Title", MAX_TITLE_LENGTH, allow_empty)


def validate_description(description: str, allow_empty: bool = True) -> Tuple[bool, Optional[str]]:
    """Validate a description."""
    return validate_text(description, "Description", MAX_DESCRIPTION_LENGTH, allow_empty)


def validate_category(category: str, allow_empty: bool = True) -> Tuple[bool, Optional[str]]:
    """Validate a category name."""
    if allow_empty and not category:
        return True, None
    
    result = validate_text(category, "Category", MAX_CATEGORY_LENGTH, allow_empty=False)
    if not result[0]:
        return result
    
    # Category should not contain path separators
    if '/' in category or '\\' in category:
        return False, "Category cannot contain path separators"
    
    return True, None


def validate_tag(tag: str) -> Tuple[bool, Optional[str]]:
    """Validate a tag."""
    if not tag:
        return False, "Tag cannot be empty"
    
    result = validate_text(tag, "Tag", MAX_TAG_LENGTH, allow_empty=False)
    if not result[0]:
        return result
    
    # Tags should not contain commas or spaces (for CSV parsing)
    if ',' in tag or ' ' in tag:
        return False, "Tag cannot contain commas or spaces"
    
    return True, None


def validate_priority(priority: int) -> Tuple[bool, Optional[str]]:
    """Validate a priority value."""
    if not isinstance(priority, int):
        return False, "Priority must be an integer"
    
    if priority < 0 or priority > 3:
        return False, "Priority must be between 0 and 3"
    
    return True, None


def validate_date_string(date_str: str) -> Tuple[bool, Optional[str]]:
    """Validate a date string in YYYY-MM-DD format."""
    if not isinstance(date_str, str):
        return False, "Date must be a string"
    
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False, "Date must be in YYYY-MM-DD format"
    
    try:
        from datetime import datetime
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return False, "Invalid date"
    
    return True, None


def validate_time_string(time_str: str) -> Tuple[bool, Optional[str]]:
    """Validate a time string in HH:MM or HH:MM:SS format."""
    if not isinstance(time_str, str):
        return False, "Time must be a string"
    
    if not re.match(r'^\d{2}:\d{2}(:\d{2})?$', time_str):
        return False, "Time must be in HH:MM or HH:MM:SS format"
    
    parts = time_str.split(':')
    hour = int(parts[0])
    minute = int(parts[1])
    
    if hour < 0 or hour > 23:
        return False, "Hour must be between 0 and 23"
    
    if minute < 0 or minute > 59:
        return False, "Minute must be between 0 and 59"
    
    if len(parts) == 3:
        second = int(parts[2])
        if second < 0 or second > 59:
            return False, "Second must be between 0 and 59"
    
    return True, None


def validate_file_path(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a file path for security.
    
    Args:
        file_path: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(file_path, str):
        return False, "File path must be a string"
    
    if not file_path:
        return False, "File path cannot be empty"
    
    # Check for path traversal attempts
    if '..' in file_path or file_path.startswith('/') or ':' in file_path:
        logger.warning(f"Potentially dangerous path detected: {file_path}")
        return False, "Invalid file path"
    
    # Check for null bytes
    if '\x00' in file_path:
        return False, "File path contains invalid characters"
    
    return True, None


def validate_file_extension(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file extension against allowed list.
    
    Args:
        filename: Name of the file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "Filename cannot be empty"
    
    # Get extension
    ext = os.path.splitext(filename)[1].lower()
    
    if not ext:
        return False, "File must have an extension"
    
    if ext not in ALLOWED_FILE_EXTENSIONS:
        return False, f"File type '{ext}' is not allowed. Allowed types: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}"
    
    return True, None


def validate_file_size(file_path: str, max_size: int = MAX_FILE_SIZE) -> Tuple[bool, Optional[str]]:
    """
    Validate file size.
    
    Args:
        file_path: Path to the file
        max_size: Maximum allowed size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    import os
    
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    try:
        size = os.path.getsize(file_path)
        if size > max_size:
            size_mb = size / (1024 * 1024)
            max_mb = max_size / (1024 * 1024)
            return False, f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({max_mb:.2f}MB)"
        
        return True, None
    except OSError as e:
        logger.error(f"Error checking file size: {e}", exc_info=True)
        return False, f"Could not check file size: {e}"


def validate_goal_data(goal_data: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate goal data structure.
    
    Args:
        goal_data: Dictionary containing goal data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if 'title' not in goal_data:
        return False, "Goal title is required"
    
    # Validate title
    valid, error = validate_title(goal_data['title'])
    if not valid:
        return False, error
    
    # Validate parent_id if provided
    if 'parent_id' in goal_data and goal_data['parent_id'] is not None:
        if not isinstance(goal_data['parent_id'], int) or goal_data['parent_id'] < 1:
            return False, "Parent ID must be a positive integer"
    
    # Validate priority if provided
    if 'priority' in goal_data:
        valid, error = validate_priority(goal_data['priority'])
        if not valid:
            return False, error
    
    # Validate dates if provided
    if 'due_date' in goal_data and goal_data['due_date']:
        valid, error = validate_date_string(goal_data['due_date'])
        if not valid:
            return False, error
    
    if 'due_time' in goal_data and goal_data['due_time']:
        valid, error = validate_time_string(goal_data['due_time'])
        if not valid:
            return False, error
    
    # Validate color if provided (hex color code)
    if 'color' in goal_data and goal_data['color']:
        if not re.match(r'^#[0-9A-Fa-f]{6}$', goal_data['color']):
            return False, "Color must be a valid hex color code (e.g., #FF0000)"
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and other security issues.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Remove other dangerous characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


def sanitize_category(category: str) -> str:
    """
    Sanitize a category name.
    
    Args:
        category: Category name to sanitize
        
    Returns:
        Sanitized category name
    """
    # Remove path separators
    category = category.replace('/', '_').replace('\\', '_')
    
    # Remove null bytes
    category = category.replace('\x00', '')
    
    # Limit length
    if len(category) > MAX_CATEGORY_LENGTH:
        category = category[:MAX_CATEGORY_LENGTH]
    
    return category.strip()

