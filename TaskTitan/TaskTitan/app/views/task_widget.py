import os
import sys
from PyQt6.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, 
                              QCheckBox, QPushButton, QSizePolicy, QFrame,
                              QGraphicsDropShadowEffect, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QIcon, QCursor, QPainter, QBrush, QPen, QPalette, QFont

# Adjust imports based on how the module is being run
if __name__ == "__main__" or not __package__:
    # Add the parent directory to the path for direct execution
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, parent_dir)
    
    from app.resources import get_icon
else:
    # Normal imports when imported as a module
    from app.resources import get_icon

class TaskWidget(QWidget): 