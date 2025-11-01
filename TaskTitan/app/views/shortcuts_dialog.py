"""
Keyboard shortcuts help dialog for TaskTitan.

This module provides a searchable dialog showing all available
keyboard shortcuts in the application.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ShortcutsDialog(QDialog):
    """Dialog displaying keyboard shortcuts."""
    
    SHORTCUTS = [
        # Navigation
        ("Navigation", "Ctrl+B", "Toggle Sidebar"),
        ("Navigation", "Ctrl+K", "Focus Search"),
        ("Navigation", "Esc", "Close Dialog/Cancel"),
        
        # File Operations
        ("File", "Ctrl+S", "Save"),
        ("File", "Ctrl+O", "Open"),
        ("File", "Ctrl+N", "New"),
        
        # Editing
        ("Edit", "Ctrl+Z", "Undo"),
        ("Edit", "Ctrl+Y", "Redo"),
        ("Edit", "Ctrl+C", "Copy"),
        ("Edit", "Ctrl+V", "Paste"),
        ("Edit", "Ctrl+X", "Cut"),
        ("Edit", "Delete", "Delete Selected"),
        
        # Views
        ("View", "Ctrl+1", "Dashboard"),
        ("View", "Ctrl+2", "Activities"),
        ("View", "Ctrl+3", "Goals"),
        ("View", "Ctrl+4", "Daily Tracker"),
        ("View", "Ctrl+5", "Pomodoro"),
        ("View", "Ctrl+6", "Weekly Plan"),
        ("View", "Ctrl+,", "Settings"),
        
        # Actions
        ("Actions", "Ctrl+A", "Select All"),
        ("Actions", "Ctrl+F", "Find"),
        ("Actions", "Ctrl+H", "Find & Replace"),
        ("Actions", "F5", "Refresh"),
        ("Actions", "Ctrl+R", "Refresh"),
        
        # Pomodoro
        ("Pomodoro", "Space", "Start/Pause Timer"),
        ("Pomodoro", "R", "Reset Timer"),
        ("Pomodoro", "S", "Skip Break"),
    ]
    
    def __init__(self, parent=None):
        """Initialize shortcuts dialog."""
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search shortcuts...")
        self.search_input.textChanged.connect(self.filter_shortcuts)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Category", "Shortcut", "Description"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Populate table
        self.populate_table()
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def populate_table(self, filter_text: str = ""):
        """Populate table with shortcuts."""
        filtered = self.SHORTCUTS
        if filter_text:
            filter_lower = filter_text.lower()
            filtered = [
                s for s in self.SHORTCUTS
                if filter_lower in s[0].lower() or
                   filter_lower in s[1].lower() or
                   filter_lower in s[2].lower()
            ]
        
        self.table.setRowCount(len(filtered))
        
        for row, (category, shortcut, description) in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(category))
            self.table.setItem(row, 1, QTableWidgetItem(shortcut))
            self.table.setItem(row, 2, QTableWidgetItem(description))
        
        self.table.resizeColumnsToContents()
    
    def filter_shortcuts(self, text: str):
        """Filter shortcuts based on search text."""
        self.populate_table(text)


def show_shortcuts_dialog(parent=None):
    """Show shortcuts dialog (convenience function)."""
    dialog = ShortcutsDialog(parent)
    dialog.exec()

