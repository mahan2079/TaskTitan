import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox

from app.views.main_window import TaskTitanApp
from app.resources import get_resource_path, APP_NAME, APP_VERSION

def main():
    """Main entry point for the modernized TaskTitan application."""
    try:
        print("Creating QApplication...")
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Using Fusion style for a more modern look
        
        # Set up a simple default stylesheet
        print("Setting stylesheet...")
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
        print("Creating main window...")
        try:
            window = TaskTitanApp()
            print("Main window created successfully")
            window.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
            print("Showing main window...")
            window.show()
            print("Window shown successfully")
        except Exception as e:
            print(f"Error creating or showing main window: {e}")
            print(traceback.format_exc())
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setText("Application Error")
            error_msg.setInformativeText(f"Failed to create main window: {str(e)}")
            error_msg.setDetailedText(traceback.format_exc())
            error_msg.exec()
            return 1
        
        # Run the application using the standard Qt event loop (not qasync)
        print("Starting standard Qt event loop...")
        try:
            print("Entering application event loop...")
            exit_code = app.exec()
            print(f"Application exited with code: {exit_code}")
            return exit_code
        except Exception as e:
            print(f"Error in event loop: {e}")
            print(traceback.format_exc())
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setText("Application Error")
            error_msg.setInformativeText(f"Failed in event loop: {str(e)}")
            error_msg.setDetailedText(traceback.format_exc())
            error_msg.exec()
            return 1
            
    except Exception as e:
        print(f"Unexpected error in main function: {e}")
        print(traceback.format_exc())
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setText("Application Error")
        error_msg.setInformativeText(f"An unexpected error occurred: {str(e)}")
        error_msg.setDetailedText(traceback.format_exc())
        error_msg.exec()
        return 1

if __name__ == '__main__':
    sys.exit(main()) 