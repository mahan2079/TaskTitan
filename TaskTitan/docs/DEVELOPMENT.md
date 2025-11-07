# TaskTitan Developer Guide

## Table of Contents

1. [Setup](#setup)
2. [Project Structure](#project-structure)
3. [Code Structure](#code-structure)
4. [Contributing](#contributing)
5. [Testing](#testing)
6. [Building](#building)

## Setup

### Prerequisites

- Python 3.8 or later
- pip
- git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/TaskTitan.git
cd TaskTitan
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install development dependencies:
```bash
pip install -r requirements.txt[dev]
```

### Running the Application

```bash
python TaskTitan/run.py
```

## Project Structure

```
TaskTitan/
├── app/                    # Main application code
│   ├── controllers/        # Business logic controllers
│   ├── core/              # Core functionality (config, settings)
│   ├── models/            # Data models and database
│   ├── resources/         # Resources (icons, constants, styles)
│   ├── themes/            # UI themes
│   ├── utils/             # Utility functions
│   └── views/             # UI components
├── tests/                 # Test suite
├── data/                  # Application data directory
├── docs/                  # Documentation
└── requirements.txt       # Python dependencies
```

## Code Structure

### Architecture

TaskTitan follows a Model-View-Controller (MVC) architecture:

- **Models** (`app/models/`): Data layer, database operations
- **Views** (`app/views/`): UI components, widgets
- **Controllers** (`app/controllers/`): Business logic, data processing

### Key Components

#### Database Layer

- `database.py`: Database initialization and schema
- `database_manager.py`: Database operations manager
- `database_schema.py`: Schema definitions
- `activities_manager.py`: Activities (tasks/events/habits) management

#### Configuration

- `core/config.py`: Centralized configuration manager
- `core/settings.py`: Settings persistence

#### Utilities

- `logger.py`: Logging system
- `error_handler.py`: Error handling and crash recovery
- `validators.py`: Input validation
- `security.py`: Security utilities
- `cache.py`: Caching system
- `backup_manager.py`: Backup management
- `data_validator.py`: Data integrity validation

### Coding Standards

1. **Type Hints**: Use type hints for function parameters and return values
2. **Docstrings**: All public functions/classes must have docstrings
3. **Formatting**: Code is formatted with Black
4. **Linting**: Code must pass Flake8 checks
5. **Testing**: New features require tests

See `CODE_QUALITY.md` for detailed code quality guidelines.

## Contributing

### Development Workflow

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Run tests:
```bash
pytest tests/
```

4. Run code quality checks:
```bash
black --check TaskTitan/
flake8 TaskTitan/
isort --check-only TaskTitan/
mypy TaskTitan/
```

5. Commit changes:
```bash
git add .
git commit -m "Description of changes"
```

6. Push and create pull request

### Commit Message Format

- Use present tense: "Add feature" not "Added feature"
- Be descriptive but concise
- Reference issue numbers if applicable

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_database.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_database.py::TestDatabaseManager::test_database_connection
```

### Writing Tests

- Tests go in `tests/` directory
- Use descriptive test names: `test_function_name_scenario`
- Use fixtures from `conftest.py`
- Mock external dependencies

Example:
```python
def test_save_goal(db_manager, sample_goal_data):
    """Test saving a goal."""
    goal_id = db_manager.save_goal(sample_goal_data)
    assert goal_id is not None
```

## Building

### Creating Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller tasktitan.spec

# Executable will be in dist/
```

See `BUILD.md` for detailed build instructions.

## Debugging

### Logging

Logs are stored in `data/logs/tasktitan.log`. Log levels:
- DEBUG: Detailed information
- INFO: General information
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

### Database Debugging

Database file is located at `data/tasktitan.db`. You can use SQLite browser tools to inspect it.

## Resources

- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Python Documentation](https://docs.python.org/3/)
- [Pytest Documentation](https://docs.pytest.org/)

