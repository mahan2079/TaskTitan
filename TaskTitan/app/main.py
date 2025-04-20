import sys
import os
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication

from app.views.main_window import TaskTitanApp
from app.resources import get_resource_path, APP_NAME, APP_VERSION

def main():
    """Main entry point for the modernized TaskTitan application."""
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