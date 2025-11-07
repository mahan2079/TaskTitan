# TaskTitan Project Overview

This document provides a comprehensive overview of the TaskTitan project, intended to be used as a context for AI-powered development assistance.

## Project Overview

TaskTitan is a feature-rich, desktop-based task management application built with Python and the PyQt6 framework. It provides a modern and intuitive interface for users to manage goals, tasks, habits, and productivity sessions. The application uses SQLite for its database and features a modular architecture that separates concerns into presentation (views), business logic (controllers), data (models), and utility layers.

### Key Technologies

*   **Backend:** Python 3.8+
*   **GUI:** PyQt6
*   **Database:** SQLite
*   **Charting:** Matplotlib, pyqtgraph
*   **Code Quality:** black, flake8, isort, mypy
*   **Testing:** pytest, pytest-qt
*   **Packaging:** PyInstaller

## Building and Running

### Running the Application

To run the application from the source code:

1.  **Set up a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r TaskTitan/requirements.txt
    ```

3.  **Run the application:**
    ```bash
    python TaskTitan/run.py
    ```

### Building the Executable

The project uses PyInstaller to create a standalone executable.

*   **Build command:**
    ```bash
    pyinstaller TaskTitan/tasktitan.spec
    ```
*   The output executable will be located in the `TaskTitan/dist` directory.

### Running Tests

The project uses `pytest` for testing.

*   **Run all tests:**
    ```bash
    pytest tests/
    ```
*   **Run tests with coverage:**
    ```bash
    pytest --cov=app --cov-report=html
    ```

## Development Conventions

### Code Style

The project enforces a strict code style using the following tools:

*   **Formatting:** `black`
*   **Linting:** `flake8`
*   **Import Sorting:** `isort`
*   **Type Checking:** `mypy`

These checks are enforced using pre-commit hooks, configured in `.pre-commit-config.yaml`.

### Project Structure

The project follows a layered architecture:

*   `app/views/`: Contains all UI components (PyQt6 widgets).
*   `app/controllers/`: Handles business logic and acts as an intermediary between views and models.
*   `app/models/`: Manages data, including database interactions and data structures.
*   `app/utils/`: Provides common utility functions for logging, error handling, security, etc.
*   `app/core/`: Contains core application functionality, such as configuration management.
*   `app/resources/`: Stores static assets like icons and themes.
*   `tests/`: Contains all unit and integration tests.

### Database

*   The database schema is defined in `app/models/database_schema.py` and initialized in `app.models.database.py`.
*   The application uses a single SQLite database file (`tasktitan.db`), located in the root directory of the executable or the project's root when run from the source.
*   Database migrations are handled in `app/utils/migrate_db.py`.

### Documentation

The `docs` directory contains detailed documentation on the project's architecture, API, and development guidelines.
