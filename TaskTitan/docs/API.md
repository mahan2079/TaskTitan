# TaskTitan API Documentation

## Overview

TaskTitan is a productivity and task management application built with PyQt6.

## Core Modules

### app.core.config

Configuration management system.

#### ConfigManager

Main configuration manager class.

**Methods:**
- `get(key_path: str, default: Any = None) -> Any`: Get configuration value
- `set(key_path: str, value: Any, save: bool = True)`: Set configuration value
- `get_section(section: str) -> Dict[str, Any]`: Get configuration section
- `update_section(section: str, values: Dict[str, Any], save: bool = True)`: Update section
- `reload()`: Reload configuration from file
- `reset_to_defaults()`: Reset to default values

**Example:**
```python
from app.core.config import ConfigManager

config = ConfigManager.get_instance()
width = config.get('window.width')
config.set('window.width', 1400)
```

### app.models.database_manager

Database operations manager.

#### DatabaseManager

Manages database connections and operations.

**Methods:**
- `connect()`: Connect to database
- `execute(sql: str, params: Optional[Tuple] = None)`: Execute SQL query
- `fetchone()`: Fetch one result
- `fetchall()`: Fetch all results
- `commit()`: Commit transaction
- `save_goal(goal_data: Dict) -> int`: Save goal to database
- `count_items(table: str, completed: Optional[bool] = None) -> int`: Count items

**Example:**
```python
from app.models.database_manager import DatabaseManager

db = DatabaseManager()
db.execute("SELECT * FROM goals WHERE completed = ?", (False,))
results = db.fetchall()
```

### app.models.activities_manager

Activities management.

#### ActivitiesManager

Manages tasks, events, and habits.

**Methods:**
- `create_tables()`: Create activity tables
- `add_activity(...) -> int`: Add new activity
- `get_activities_for_date(date: QDate) -> List`: Get activities for date
- `mark_activity_complete(activity_id: int, date: QDate) -> bool`: Mark complete
- `delete_activity(activity_id: int) -> bool`: Delete activity

**Example:**
```python
from app.models.activities_manager import ActivitiesManager
from PyQt6.QtCore import QDate

manager = ActivitiesManager(conn, cursor)
activity_id = manager.add_activity(
    title="Task",
    date="2024-01-01",
    start_time="09:00",
    end_time="10:00",
    activity_type="task"
)
```

### app.utils.logger

Logging system.

#### Functions

- `get_logger(name: Optional[str] = None) -> logging.Logger`: Get logger instance
- `setup_logging(level: int = logging.INFO)`: Setup logging

**Example:**
```python
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Application started")
logger.error("Error occurred", exc_info=True)
```

### app.utils.validators

Input validation utilities.

#### Functions

- `validate_text(text: str, ...) -> Tuple[bool, Optional[str]]`: Validate text
- `validate_title(title: str) -> Tuple[bool, Optional[str]]`: Validate title
- `validate_category(category: str) -> Tuple[bool, Optional[str]]`: Validate category
- `validate_file_path(file_path: str) -> Tuple[bool, Optional[str]]`: Validate file path
- `sanitize_filename(filename: str) -> str`: Sanitize filename

**Example:**
```python
from app.utils.validators import validate_title, sanitize_filename

valid, error = validate_title("My Task")
if not valid:
    print(f"Error: {error}")

safe_name = sanitize_filename("file<>name.txt")
```

### app.utils.security

Security utilities.

#### Functions

- `sanitize_path(file_path: str, base_dir: Optional[str] = None) -> Optional[str]`: Sanitize path
- `check_file_security(file_path: str, ...) -> Tuple[bool, Optional[str]]`: Check file security
- `validate_attachment_file(file_path: str, max_size: int = MAX_FILE_SIZE) -> Tuple[bool, Optional[str]]`: Validate attachment

**Example:**
```python
from app.utils.security import validate_attachment_file

safe, error = validate_attachment_file("document.pdf")
if safe:
    # Process file
    pass
```

### app.utils.cache

Caching system.

#### CacheManager

Centralized cache manager.

**Methods:**
- `get(key: str, default: Any = None) -> Any`: Get cached value
- `set(key: str, value: Any)`: Set cached value
- `invalidate(key: str)`: Invalidate cache entry
- `clear()`: Clear all caches

**Example:**
```python
from app.utils.cache import CacheManager

cache = CacheManager.get_instance()
cached_value = cache.get("my_key")
cache.set("my_key", my_value)
```

### app.utils.backup_manager

Backup management.

#### BackupManager

Manages automatic backups.

**Methods:**
- `create_backup(custom_name: Optional[str] = None) -> Tuple[bool, Optional[str]]`: Create backup
- `restore_backup(backup_path: str) -> Tuple[bool, Optional[str]]`: Restore backup
- `list_backups() -> List[Tuple[str, Dict]]`: List available backups
- `start_auto_backup(interval: str = 'daily')`: Start automatic backups

**Example:**
```python
from app.utils.backup_manager import BackupManager

backup_mgr = BackupManager()
success, backup_path = backup_mgr.create_backup()
if success:
    print(f"Backup created: {backup_path}")
```

### app.utils.data_validator

Data integrity validation.

#### DataValidator

Validates database integrity and consistency.

**Methods:**
- `check_database_integrity() -> Tuple[bool, List[str]]`: Check integrity
- `check_data_consistency() -> Tuple[bool, List[str]]`: Check consistency
- `repair_database() -> Tuple[bool, List[str]]`: Repair issues
- `recover_from_corruption(backup_path: Optional[str] = None) -> Tuple[bool, Optional[str]]`: Recover from corruption

**Example:**
```python
from app.utils.data_validator import DataValidator

validator = DataValidator()
is_valid, errors = validator.check_database_integrity()
if not is_valid:
    repair_success, actions = validator.repair_database()
```

## Configuration

Configuration is stored in JSON format at `data/config.json`.

### Configuration Sections

- `window`: Window size and position
- `display`: Theme and font settings
- `pomodoro`: Pomodoro timer settings
- `backup`: Backup settings
- `notifications`: Notification preferences
- `updates`: Update checking settings
- `database`: Database settings
- `performance`: Performance settings

## Database Schema

### Tables

- `activities`: Unified table for tasks, events, and habits
- `goals`: Goal hierarchy
- `activity_completions`: Daily activity completions
- `journal_entries`: Daily journal entries
- `time_entries`: Time tracking entries
- `pomodoro_sessions`: Pomodoro session records

See `app/models/database_schema.py` for complete schema definitions.

## Error Handling

All errors are logged to `data/logs/tasktitan.log`. Critical errors trigger the global exception handler which:
- Logs the error
- Shows user-friendly error dialog
- Saves crash state for recovery

## Security

- All user input is validated
- File paths are sanitized
- File attachments are validated for type and size
- SQL injection prevention via parameterized queries

## Performance

- Database connection pooling
- LRU cache for frequently accessed data
- Lazy loading for large datasets
- Optimized SQLite settings (WAL mode, cache size)

