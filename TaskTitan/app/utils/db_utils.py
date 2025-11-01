import os
import sys
import sqlite3
import shutil
from datetime import datetime
import re
from app.utils.logger import get_logger
from app.utils.security import (
    validate_attachment_file,
    secure_file_copy,
    sanitize_filename,
    sanitize_category as sanitize_category_name
)
from app.utils.validators import MAX_FILE_SIZE
from app.models.database import get_db_path

logger = get_logger(__name__)

def get_attachments_dir(category=None, date_str=None):
    """
    Get the path to the attachments directory.
    
    Args:
        category: Optional category name to organize attachments
        date_str: Optional date string in 'yyyy-MM-dd' format
    
    Returns:
        Path to the appropriate attachments directory
    """
    # Handle PyInstaller frozen state
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable - use directory next to executable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    attachments_dir = os.path.join(base_dir, 'data', 'attachments')
    
    # Create main attachments directory if it doesn't exist
    if not os.path.exists(attachments_dir):
        os.makedirs(attachments_dir)
    
    # Create two completely separate directory structures:
    # 1. Date-based: /data/attachments/by_date/YYYY/MM/DD
    # 2. Category-based: /data/attachments/by_category/CategoryName
    
    # If date is provided, create a date-based directory structure
    if date_str:
        try:
            # Create dedicated date structure
            date_base_dir = os.path.join(attachments_dir, 'by_date')
            if not os.path.exists(date_base_dir):
                os.makedirs(date_base_dir)
                
            # Create a directory structure like YYYY/MM/DD
            year, month, day = date_str.split('-')
            year_dir = os.path.join(date_base_dir, year)
            month_dir = os.path.join(year_dir, month)
            day_dir = os.path.join(month_dir, day)
            
            # Create directory structure if needed
            for directory in [year_dir, month_dir, day_dir]:
                if not os.path.exists(directory):
                    os.makedirs(directory)
            
            # Return the day directory for date-based storage
            return day_dir
            
        except ValueError:
            # If date_str is not in expected format, use the main attachments dir
            logger.warning(f"Invalid date format {date_str}")
    
    # If category is provided, use a category-based directory structure
    if category:
        # Sanitize category name for file system use
        category = sanitize_category_name(category)
        
        # Create dedicated category structure
        category_base_dir = os.path.join(attachments_dir, 'by_category')
        if not os.path.exists(category_base_dir):
            os.makedirs(category_base_dir)
            
        category_dir = os.path.join(category_base_dir, category)
        
        # Create category directory if needed
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
        
        # Return the category directory
        return category_dir
    
    # If neither date nor category is provided, return the main attachments directory
    return attachments_dir

def get_exports_dir():
    """Get the path to the exports directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    exports_dir = os.path.join(base_dir, 'data', 'exports')
    
    # Create directory if it doesn't exist
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)
        
    return exports_dir

def get_backups_dir():
    """Get the path to the backups directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    backups_dir = os.path.join(base_dir, 'data', 'backups')
    
    # Create directory if it doesn't exist
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)
        
    return backups_dir

def save_attachment(file_path, date_str=None, category=None, filename=None):
    """
    Save an attachment file to the date-based directory structure and optionally
    create a shortcut in the category folder.
    
    Args:
        file_path: Path to the file to be saved
        date_str: Date string in 'yyyy-MM-dd' format for date-based organization
        category: Optional category name for shortcut creation
        filename: Optional custom filename (without path)
        
    Returns:
        A tuple of (original_path, category_shortcut_path) where category_shortcut_path may be None
    """
    # Generate unique filename if not provided
    if not filename:
        # Use original name but add timestamp to avoid overwriting
        original_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{original_name}"
    
    # First, save in date directory (main storage)
    date_dir = get_attachments_dir(date_str=date_str)
    
    # Create date directory if it doesn't exist
    if not os.path.exists(date_dir):
        os.makedirs(date_dir, exist_ok=True)
    
    # Path in the date directory
    date_path = os.path.join(date_dir, filename)
    
    # Copy the file to date directory
    try:
        shutil.copy2(file_path, date_path)
        logger.info(f"Copied file to date directory: {date_path}")
    except Exception as e:
        logger.error(f"Error copying file to date directory: {e}", exc_info=True)
        return (None, None)
    
    # If category provided and it's not just a year, create a shortcut in category directory
    category_path = None
    if category and not re.match(r'^\d{4}$', category):
        category_path = create_category_shortcut(date_path, category, filename)
    
    return (date_path, category_path)

def create_category_shortcut(source_path, category, filename=None):
    """
    Create a shortcut or symlink in the category folder pointing to the source file.
    
    Args:
        source_path: Path to the original file
        category: Category name for the shortcut
        filename: Optional filename for the shortcut (defaults to source filename)
        
    Returns:
        Path to the created shortcut or None if creation failed
    """
    if not os.path.exists(source_path):
        logger.warning(f"Source file does not exist: {source_path}")
        return None
    
    # Use original filename if not provided
    if not filename:
        filename = os.path.basename(source_path)
    
    # Get category directory
    category_dir = get_attachments_dir(category=category)
    
    # Create category directory if it doesn't exist
    if not os.path.exists(category_dir):
        os.makedirs(category_dir, exist_ok=True)
    
    # Path for the shortcut
    shortcut_path = None
    
    try:
        # Determine platform and create appropriate link type
        if os.name == 'nt':  # Windows
            try:
                import pythoncom  # type: ignore
                # Defer win32com import to runtime; ignore if not present
                try:
                    from win32com.shell import shell  # type: ignore
                except Exception:
                    shell = None  # type: ignore

                shortcut_path = os.path.join(category_dir, f"{filename}.lnk")

                if shell is not None:
                    # Create shortcut via COM
                    shortcut = pythoncom.CoCreateInstance(  # type: ignore
                        shell.CLSID_ShellLink,  # type: ignore
                        None,
                        pythoncom.CLSCTX_INPROC_SERVER,  # type: ignore
                        shell.IID_IShellLink  # type: ignore
                    )
                    shortcut.SetPath(source_path)  # type: ignore
                    shortcut.SetDescription(f"Link to {filename}")  # type: ignore
                    persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)  # type: ignore
                    persist_file.Save(shortcut_path, 0)  # type: ignore
                    logger.debug(f"Created Windows shortcut: {shortcut_path}")
                else:
                    # Fall back to file copy if win32com not available
                    shortcut_path = os.path.join(category_dir, filename)
                    shutil.copy2(source_path, shortcut_path)
                    logger.debug(f"Created copy instead of shortcut: {shortcut_path}")

            except Exception as e:
                logger.error(f"Error creating Windows shortcut: {e}", exc_info=True)
                shortcut_path = None
                
        else:  # Unix/Linux/Mac
            shortcut_path = os.path.join(category_dir, filename)
            try:
                # Create symbolic link
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                os.symlink(source_path, shortcut_path)
                logger.debug(f"Created symbolic link: {shortcut_path}")
                
            except Exception as e:
                logger.error(f"Error creating symbolic link: {e}", exc_info=True)
                # Fall back to file copy if link creation fails
                try:
                    shutil.copy2(source_path, shortcut_path)
                    logger.debug(f"Created copy instead of symlink: {shortcut_path}")
                except Exception as copy_error:
                    logger.error(f"Error creating file copy: {copy_error}", exc_info=True)
                    shortcut_path = None
    
    except Exception as e:
        logger.error(f"Unexpected error in create_category_shortcut: {e}", exc_info=True)
        shortcut_path = None
    
    return shortcut_path

def remove_attachment(file_path, shortcut_path=None):
    """
    Remove an attachment file and its shortcut if present.
    
    Args:
        file_path: Path to the main file to be removed
        shortcut_path: Optional path to shortcut/link to be removed
        
    Returns:
        True if successfully removed, False otherwise
    """
    success = True
    try:
        # Remove main file first
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        else:
            success = False
        
        # Remove shortcut if provided
        if shortcut_path and os.path.exists(shortcut_path):
            os.remove(shortcut_path)
    except Exception as e:
        logger.error(f"Error removing attachment: {e}", exc_info=True)
        success = False
    
    return success

def list_attachment_categories():
    """
    List all existing attachment categories.
    
    Returns:
        List of category names (folder names)
    """
    attachments_dir = get_attachments_dir()
    
    if not os.path.exists(attachments_dir):
        return []
    
    # Get only directories in the attachments folder
    categories = []
    for name in os.listdir(attachments_dir):
        if os.path.isdir(os.path.join(attachments_dir, name)):
            # Skip directories that are just 4-digit numbers (years)
            if not re.match(r'^\d{4}$', name):
                categories.append(name)
    
    return categories

def update_attachment_category(file_id, old_category, new_category, connection=None):
    """
    Update the category for an attachment, moving it from one category folder to another.
    
    Args:
        file_id: Database ID for the attachment
        old_category: Previous category name
        new_category: New category name
        connection: Optional database connection
        
    Returns:
        Tuple of (success, new_shortcut_path)
    """
    # Connect to database if connection not provided
    close_conn = False
    if not connection:
        db_path = get_db_path()
        connection = sqlite3.connect(db_path)
        close_conn = True
    
    cursor = connection.cursor()
    
    try:
        # Get attachment information
        cursor.execute(
            "SELECT file_path, shortcut_path FROM journal_attachments WHERE id = ?",
            (file_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            logger.warning(f"Attachment not found with ID: {file_id}")
            return (False, None)
        
        file_path, old_shortcut_path = result
        
        # Remove old shortcut if it exists
        if old_shortcut_path and os.path.exists(old_shortcut_path):
            try:
                os.remove(old_shortcut_path)
                logger.debug(f"Removed old shortcut: {old_shortcut_path}")
            except Exception as e:
                logger.warning(f"Could not remove old shortcut: {e}", exc_info=True)
        
        # Create new shortcut
        new_shortcut_path = None
        if new_category:
            new_shortcut_path = create_category_shortcut(file_path, new_category)
        
        # Update database
        cursor.execute(
            "UPDATE journal_attachments SET category = ?, shortcut_path = ? WHERE id = ?",
            (new_category, new_shortcut_path, file_id)
        )
        connection.commit()
        
        return (True, new_shortcut_path)
        
    except Exception as e:
        logger.error(f"Error updating attachment category: {e}", exc_info=True)
        return (False, None)
        
    finally:
        if close_conn:
            connection.close() 