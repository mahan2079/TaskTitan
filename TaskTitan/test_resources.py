"""
Simple test script for the resources module.
"""
import sys
import os

# Add parent directory to path to make imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from app.resources import get_icon, get_pixmap, APP_NAME, APP_VERSION
from app.resources.icons import ICONS_DIR

def main():
    """Test the resources module."""
    print(f"Testing {APP_NAME} Resources v{APP_VERSION}")
    print(f"Icons directory: {ICONS_DIR}")
    print(f"Icons directory exists: {os.path.exists(ICONS_DIR)}")
    
    if os.path.exists(ICONS_DIR):
        print("Contents of icons directory:")
        for item in os.listdir(ICONS_DIR):
            print(f"  - {item}")
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle(f"Testing {APP_NAME} Resources v{APP_VERSION}")
    window.setGeometry(100, 100, 400, 300)
    
    # Create central widget
    central = QWidget()
    window.setCentralWidget(central)
    
    # Layout
    layout = QVBoxLayout(central)
    
    # Add a label
    label = QLabel(f"Testing {APP_NAME} Resources v{APP_VERSION}")
    layout.addWidget(label)
    
    # Display an icon if found
    icon = get_icon("dashboard")
    print(f"Icon is null: {icon.isNull()}")
    
    if not icon.isNull():
        window.setWindowIcon(icon)
        label.setText(f"Icon found for dashboard!")
    else:
        label.setText("Icon not found for dashboard.")
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 