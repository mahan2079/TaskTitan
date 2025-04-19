import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, 
                              QLabel, QHBoxLayout, QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont

# Adjust imports based on how the module is being run
if __name__ == "__main__" or not __package__:
    # Add the parent directory to the path for direct execution
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, parent_dir)
    
    from app.views.task_widget import TaskWidget
    from app.resources import get_icon
else:
    # Normal imports when imported as a module
    from app.views.task_widget import TaskWidget
    from app.resources import get_icon

class TaskListView(QWidget): 