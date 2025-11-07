"""
Code quality guide for TaskTitan developers.

This file explains code quality standards and how to use
the configured tools.
"""

# Code Quality Standards

## Formatting

We use **Black** for code formatting. Black enforces consistent code style.

### Usage:
```bash
# Format all files
black TaskTitan/

# Check without formatting
black --check TaskTitan/

# Format specific file
black path/to/file.py
```

## Linting

We use **Flake8** for code linting to catch potential errors and style issues.

### Usage:
```bash
# Lint all files
flake8 TaskTitan/

# Lint specific file
flake8 path/to/file.py
```

## Import Sorting

We use **isort** to organize imports consistently.

### Usage:
```bash
# Sort imports in all files
isort TaskTitan/

# Check without sorting
isort --check-only TaskTitan/

# Sort specific file
isort path/to/file.py
```

## Type Checking

We use **mypy** for static type checking.

### Usage:
```bash
# Type check all files
mypy TaskTitan/

# Type check specific file
mypy path/to/file.py
```

## Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before commits.

### Setup:
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Code Quality Checklist

Before committing code, ensure:

- [ ] Code is formatted with Black
- [ ] No Flake8 errors or warnings
- [ ] Imports are sorted with isort
- [ ] Type hints added where appropriate
- [ ] No mypy errors (warnings acceptable for external libraries)
- [ ] Code follows PEP 8 style guide
- [ ] Functions have docstrings
- [ ] No obvious code duplication

## Running All Checks

```bash
# Run all quality checks
black --check TaskTitan/ && \
flake8 TaskTitan/ && \
isort --check-only TaskTitan/ && \
mypy TaskTitan/
```

## CI/CD Integration

All code quality checks run automatically in CI/CD pipeline
on every push and pull request.

