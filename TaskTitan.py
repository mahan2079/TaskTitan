#!/usr/bin/env python
"""
TaskTitan - A modern task management application
Main entry point for the application
"""

import sys
import os
import traceback
from datetime import datetime

# Add the TaskTitan folder to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set up logging directory
log_dir = os.path.join(current_dir, "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

def log_error(error_msg):
    """Log error messages to a file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(log_dir, f"tasktitan_error_{datetime.now().strftime('%Y%m%d')}.log")
    
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] ERROR: {error_msg}\n")
        f.write(f"{'='*80}\n")

def main():
    """Main application entry point with error handling"""
    try:
        print("Starting TaskTitan application...")
        
        # Verify dependencies
        try:
            import PyQt6
            print("✅ PyQt6 is installed")
            
            # Import and check SQLite
            import sqlite3
            print("✅ SQLite3 is available")
            
            # Check if database structure is set up
            from app.database.setup import DatabaseSetup
            print("✅ Database module found")
            
        except ImportError as e:
            print(f"❌ Missing dependency: {str(e)}")
            log_error(f"Missing dependency: {str(e)}\n{traceback.format_exc()}")
            sys.exit(1)
        
        # Initialize the application - use local app module
        import app.main
        
        # Run the application
        print("Launching TaskTitan UI...")
        return app.main.main()
        
    except Exception as e:
        error_msg = f"Unhandled exception: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ Application error: {str(e)}")
        log_error(error_msg)
        
        # If PyQt is available, show error dialog
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setWindowTitle("TaskTitan Error")
            error_box.setText("An error occurred while starting TaskTitan")
            error_box.setDetailedText(error_msg)
            error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            error_box.exec()
        except:
            # If PyQt dialog fails, just print to console
            print(f"Error details have been logged to: {log_dir}")
        
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
