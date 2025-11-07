# TaskTitan Architecture Overview

## System Architecture

TaskTitan follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────┐
│           Presentation Layer         │
│         (Views, Widgets, UI)         │
└─────────────────────────────────────┘
                  │
┌─────────────────────────────────────┐
│          Controller Layer            │
│    (Business Logic, Processing)      │
└─────────────────────────────────────┘
                  │
┌─────────────────────────────────────┐
│            Model Layer               │
│    (Data Models, Database)           │
└─────────────────────────────────────┘
                  │
┌─────────────────────────────────────┐
│          Utility Layer               │
│  (Logging, Security, Caching, etc.)  │
└─────────────────────────────────────┘
```

## Component Overview

### Views Layer (`app/views/`)

UI components built with PyQt6:
- `main_window.py`: Main application window
- `unified_activities_widget.py`: Tasks/events/habits view
- `goal_widget.py`: Goals management
- `productivity_view.py`: Daily tracker
- `pomodoro_widget.py`: Pomodoro timer
- `calendar_widget.py`: Calendar view

### Controllers Layer (`app/controllers/`)

Business logic and processing:
- `search_manager.py`: Search functionality
- `utils.py`: Controller utilities

### Models Layer (`app/models/`)

Data management:
- `database.py`: Database initialization
- `database_manager.py`: Database operations
- `activities_manager.py`: Activities management
- `database_schema.py`: Schema definitions

### Core Layer (`app/core/`)

Core functionality:
- `config.py`: Configuration management
- `settings.py`: Settings persistence

### Utilities Layer (`app/utils/`)

Supporting utilities:
- `logger.py`: Logging system
- `error_handler.py`: Error handling
- `validators.py`: Input validation
- `security.py`: Security utilities
- `cache.py`: Caching system
- `backup_manager.py`: Backup management
- `data_validator.py`: Data validation

## Data Flow

### Creating an Activity

1. User enters data in view (`unified_activities_widget.py`)
2. View validates input using `validators.py`
3. View calls `ActivitiesManager.add_activity()`
4. ActivitiesManager validates and saves to database
5. DatabaseManager executes SQL with parameters
6. Cache is invalidated
7. View refreshes to show new activity

### Loading Data

1. View requests data from manager
2. Manager checks cache first
3. If cache miss, query database
4. Result cached and returned
5. View displays data

## Database Design

### Schema

- **Unified Activities**: Tasks, events, and habits in single table
- **Goals**: Hierarchical structure with parent-child relationships
- **Completions**: Separate table for tracking daily completions
- **Journal**: Daily journal entries
- **Time Tracking**: Time entries and categories

### Optimizations

- WAL mode for better concurrency
- Indexes on frequently queried columns
- Connection pooling
- Query caching

## Security Model

### Input Validation

- All user input validated before processing
- File paths sanitized
- File types and sizes checked
- SQL injection prevention via parameterized queries

### Data Protection

- Regular backups
- Integrity checks
- Recovery mechanisms
- Secure file handling

## Configuration System

### Configuration Storage

- JSON-based config file
- Environment variable support
- Runtime updates
- Default values from constants

### Settings Categories

- Window preferences
- Display settings
- Feature toggles
- Performance settings

## Error Handling

### Logging

- Structured logging with rotation
- Multiple log levels
- File and console output
- Context information

### Exception Handling

- Global exception handler
- User-friendly error messages
- Crash recovery
- Error reporting

## Performance Optimizations

### Caching

- LRU cache for frequently accessed data
- Time-based expiration
- Configurable cache size

### Database

- Connection pooling
- Query optimization
- Index usage
- Batch operations

### UI

- Lazy loading
- Virtual scrolling
- Debounced search
- Efficient updates

## Extension Points

### Adding New Features

1. Create model in `app/models/`
2. Create view in `app/views/`
3. Add controller logic if needed
4. Update database schema
5. Add tests
6. Update documentation

### Adding New Views

1. Create widget class inheriting from `QWidget`
2. Add to main window navigation
3. Implement data loading/refresh
4. Add keyboard shortcuts
5. Update settings if needed

## Testing Strategy

- Unit tests for models and utilities
- Integration tests for workflows
- UI tests for critical paths
- Coverage target: >70%

## Deployment

- PyInstaller for executables
- Platform-specific builds
- Automated release process
- Version management

