import sys
import os
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication, QMessageBox
import traceback
import sqlite3

# Fix the import paths when running the script directly
if __name__ == "__main__":
    # Add the parent directory to the path so 'app' can be found
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from views.main_window import TaskTitanApp
    from resources import get_resource_path, APP_NAME, APP_VERSION
    from models.database_manager import get_manager
else:
    # Normal import when imported as a module
    from app.views.main_window import TaskTitanApp
    from app.resources import get_resource_path, APP_NAME, APP_VERSION
    from app.models.database_manager import get_manager

# Set up exception handling
def exception_hook(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions to show error dialog to user."""
    # Log the error
    print("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    
    # Show dialog with error info
    error_msg = QMessageBox()
    error_msg.setIcon(QMessageBox.Icon.Critical)
    error_msg.setWindowTitle("Application Error")
    error_msg.setText(f"An unexpected error occurred: {exc_value}")
    error_msg.setDetailedText("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    error_msg.exec()
    
    # Call the default handler to exit the application if needed
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

def ensure_database_exists():
    """Make sure the database exists and is properly initialized."""
    try:
        db_manager = get_manager()
        db_path = db_manager.db_path
        db_dir = os.path.dirname(db_path)
        
        # Ensure directory exists
        if not os.path.exists(db_dir):
            print(f"Creating database directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
        
        # Test direct database connection
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            print("Database file doesn't exist or is empty. Creating a new database.")
            
            # Create a direct connection to ensure the database file is created
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            
            # Create tasks table directly to ensure it exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id INTEGER,
                    description TEXT NOT NULL,
                    duration_minutes INTEGER,
                    completed INTEGER DEFAULT 0,
                    due_date DATE,
                    due_time TIME,
                    priority INTEGER DEFAULT 1
                )
            """)
            
            # Create a test task to verify writing works
            cursor.execute("""
                INSERT INTO tasks (description, completed)
                VALUES (?, ?)
            """, ("Test task - Please delete me", 0))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"Database created successfully at: {db_path}")
        else:
            print(f"Database already exists at: {db_path}")
            
        # Ensure proper initialization through the manager
        db_manager.initialize_db()
        
        return True
    except Exception as e:
        print(f"Error ensuring database exists: {e}")
        traceback.print_exc()
        return False

def main():
    """Main entry point for the modernized TaskTitan application."""
    # Set up global exception handling
    sys.excepthook = exception_hook
    
    # Initialize the database early
    db_initialized = ensure_database_exists()
    if not db_initialized:
        print("Warning: Database initialization failed. App may not work correctly.")
    
    # Create and configure the application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Using Fusion style for a more modern look
    
    # Set up a simple default stylesheet
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #F8FAFC;
            color: #0F172A;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 14px;
        }
        
        QPushButton {
            background-color: #6366F1;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 16px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #818CF8;
        }
    """)
    
    # Create and show the main application window
    window = TaskTitanApp()
    window.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
    window.show()
    
    # Set up async event loop for smoother UI and animations
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Run the application
    with loop:
        sys.exit(loop.run_forever())

if __name__ == '__main__':
    main() 