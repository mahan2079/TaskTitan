import sys
import os
import sqlite3

# Add the parent directory to sys.path to make imports work properly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Define app version and name directly
APP_NAME = "TaskTitan"
APP_VERSION = "1.0.0"

# Import necessary QtWidgets after path setup
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QMessageBox, QProgressBar
from PyQt6.QtCore import Qt, QTimer

# Import the database setup module
from app.database.setup import DatabaseSetup

def initialize_database():
    """Initialize the database if it doesn't exist"""
    # Get the database path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(current_dir, "database", "data")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    db_path = os.path.join(db_dir, "tasktitan.db")
    
    # Create the database if it doesn't exist
    if not os.path.exists(db_path):
        print("Creating new database...")
        setup = DatabaseSetup(db_path)
        setup.setup_database()
        setup.insert_default_data()
        setup.close()
        print("Database initialization complete.")
    else:
        print("Using existing database.")
    
    return db_path

class SplashScreen(QWidget):
    """Splash screen shown during application startup"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TaskTitan")
        self.setFixedSize(600, 300)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        
        layout = QVBoxLayout(self)
        
        # Add title
        title = QLabel("TaskTitan")
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #6366F1;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Add loading message
        self.message = QLabel("Starting application...")
        self.message.setStyleSheet("font-size: 14px;")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message)
        
        # Add progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #E2E8F0;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #6366F1;
                width: 10px;
                margin: 0.5px;
            }
        """)
        layout.addWidget(self.progress)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # Setup timer to simulate loading
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.current_progress = 0
        
    def start_progress(self):
        """Start the progress animation"""
        self.timer.start(30)
        
    def update_progress(self):
        """Update the progress bar"""
        self.current_progress += 1
        self.progress.setValue(self.current_progress)
        
        # Update message based on progress
        if self.current_progress < 30:
            self.message.setText("Initializing components...")
        elif self.current_progress < 60:
            self.message.setText("Loading database...")
        elif self.current_progress < 90:
            self.message.setText("Preparing interface...")
        else:
            self.message.setText("Ready to launch!")
        
        # When complete, stop the timer
        if self.current_progress >= 100:
            self.timer.stop()
            self.app.show_main_window()

class SimpleMainWindow(QMainWindow):
    """A simple main window as a placeholder until the full UI is implemented"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TaskTitan")
        self.setMinimumSize(800, 600)
        
        # Set up the central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add a welcome label
        welcome_label = QLabel("Welcome to TaskTitan!")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(welcome_label)
        
        # Add a description
        description = QLabel("The database has been set up successfully. "
                            "The full application UI is currently under development.")
        description.setStyleSheet("font-size: 16px; margin: 10px;")
        layout.addWidget(description)
        
        # Add a button to test database connection
        test_db_button = QPushButton("Test Database Connection")
        test_db_button.clicked.connect(self.test_database)
        layout.addWidget(test_db_button)
        
        # Add empty space
        layout.addStretch()

    def test_database(self):
        """Test the database connection and display some basic info"""
        try:
            # Get the database path
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                  "database", "data", "tasktitan.db")
            
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get some basic stats
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tasks")
            task_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM goals")
            goal_count = cursor.fetchone()[0]
            
            # Show the results
            QMessageBox.information(self, "Database Test", 
                                  f"Connection successful!\n\n"
                                  f"Users: {user_count}\n"
                                  f"Tasks: {task_count}\n"
                                  f"Goals: {goal_count}")
            
            # Close the connection
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error: {str(e)}")

class TaskTitanApp:
    """Main application coordinator"""
    
    def __init__(self):
        # Initialize the application
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        
        # Apply stylesheet
        self.apply_stylesheet()
        
        # Create splash screen
        self.splash = SplashScreen()
        # Store reference to app in splash screen
        self.splash.app = self
        
        # Initialize database
        self.db_path = None
        
        # Main window (created later)
        self.main_window = None
    
    def apply_stylesheet(self):
        """Apply application-wide stylesheet"""
        self.app.setStyleSheet("""
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
    
    def initialize(self):
        """Run initialization sequence"""
        # Show splash screen
        self.splash.show()
        self.splash.start_progress()
        
        # Initialize database in the background
        QTimer.singleShot(100, self.initialize_database)
        
        return self.app.exec()
    
    def initialize_database(self):
        """Initialize the database"""
        # This will be called by the timer
        self.db_path = initialize_database()
    
    def show_main_window(self):
        """Show the main application window"""
        # Close splash screen
        self.splash.close()
        
        # Create and show main window
        self.main_window = SimpleMainWindow()
        self.main_window.show()

def main():
    """Main entry point for the TaskTitan application."""
    # Create the application
    app = TaskTitanApp()
    
    # Initialize and run
    return app.initialize()

# Re-export main function to keep imports consistent
__all__ = ['main']

if __name__ == '__main__':
    sys.exit(main()) 