"""
Database management dialog for TaskTitan.
Allows users to create, load, save, and switch between multiple databases.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QFileDialog,
    QMessageBox, QFormLayout, QGroupBox, QDialogButtonBox, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
import os
import shutil
import sqlite3
from datetime import datetime
from app.utils.logger import get_logger
from app.models.database import get_db_path, initialize_db
from app.models.database_manager import DatabaseManager

logger = get_logger(__name__)


class DatabaseManagerDialog(QDialog):
    """Dialog for managing multiple databases."""
    
    database_changed = pyqtSignal(str)  # Emits new database path when changed
    
    def __init__(self, parent=None):
        """Initialize database manager dialog."""
        super().__init__(parent)
        self.current_db_path = get_db_path()
        self.databases_config = self._load_databases_config()
        self.setupUI()
        self.load_databases_list()
    
    def setupUI(self):
        """Set up the UI components."""
        self.setWindowTitle("Database Manager")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Database Manager")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Current database info
        current_group = QGroupBox("Current Database")
        current_layout = QVBoxLayout()
        
        self.current_db_label = QLabel()
        self.current_db_label.setText(f"Path: {self.current_db_path}")
        self.current_db_label.setWordWrap(True)
        current_layout.addWidget(self.current_db_label)
        
        # Database info
        db_info = self._get_database_info(self.current_db_path)
        info_label = QLabel(db_info)
        info_label.setWordWrap(True)
        current_layout.addWidget(info_label)
        
        current_group.setLayout(current_layout)
        layout.addWidget(current_group)
        
        # Databases list
        list_group = QGroupBox("Saved Databases")
        list_layout = QVBoxLayout()
        
        self.databases_list = QListWidget()
        self.databases_list.itemDoubleClicked.connect(self.load_selected_database)
        list_layout.addWidget(self.databases_list)
        
        list_buttons = QHBoxLayout()
        
        self.switch_btn = QPushButton("Switch to Selected")
        self.switch_btn.clicked.connect(self.load_selected_database)
        self.switch_btn.setEnabled(False)
        
        self.remove_btn = QPushButton("Remove from List")
        self.remove_btn.clicked.connect(self.remove_selected_database)
        self.remove_btn.setEnabled(False)
        
        list_buttons.addWidget(self.switch_btn)
        list_buttons.addWidget(self.remove_btn)
        list_buttons.addStretch()
        
        list_layout.addLayout(list_buttons)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Connect list selection
        self.databases_list.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.new_db_name = QLineEdit()
        self.new_db_name.setPlaceholderText("Enter database name")
        form_layout.addRow("Create New Database:", self.new_db_name)
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_new_database)
        form_layout.addRow("", create_btn)
        
        actions_layout.addLayout(form_layout)
        
        # Load existing database
        load_btn = QPushButton("Load Database from File...")
        load_btn.clicked.connect(self.load_database_from_file)
        actions_layout.addWidget(load_btn)
        
        # Save current database
        save_btn = QPushButton("Save Current Database As...")
        save_btn.clicked.connect(self.save_current_database)
        actions_layout.addWidget(save_btn)
        
        # Export database
        export_btn = QPushButton("Export Database...")
        export_btn.clicked.connect(self.export_database)
        actions_layout.addWidget(export_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _load_databases_config(self) -> dict:
        """Load saved databases configuration."""
        from app.core.config import get_config
        return get_config('database.saved_databases', {})
    
    def _save_databases_config(self, config: dict):
        """Save databases configuration."""
        from app.core.config import set_config
        set_config('database.saved_databases', config)
    
    def _get_database_info(self, db_path: str) -> str:
        """Get information about a database."""
        if not os.path.exists(db_path):
            return "Database file does not exist"
        
        try:
            size = os.path.getsize(db_path)
            size_mb = size / (1024 * 1024)
            modified = datetime.fromtimestamp(os.path.getmtime(db_path))
            
            # Get database stats
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM activities")
            activity_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM goals")
            goal_count = cursor.fetchone()[0]
            
            conn.close()
            
            return (
                f"Size: {size_mb:.2f} MB\n"
                f"Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Activities: {activity_count}\n"
                f"Goals: {goal_count}"
            )
        except Exception as e:
            logger.error(f"Error getting database info: {e}", exc_info=True)
            return f"Error: {str(e)}"
    
    def load_databases_list(self):
        """Load saved databases into the list."""
        self.databases_list.clear()
        
        for name, db_info in self.databases_config.items():
            db_path = db_info.get('path', '')
            if os.path.exists(db_path):
                item = QListWidgetItem(f"{name} - {db_path}")
                item.setData(Qt.ItemDataRole.UserRole, db_path)
                self.databases_list.addItem(item)
    
    def on_selection_changed(self):
        """Handle selection change in databases list."""
        has_selection = len(self.databases_list.selectedItems()) > 0
        self.switch_btn.setEnabled(has_selection)
        self.remove_btn.setEnabled(has_selection)
    
    def create_new_database(self):
        """Create a new database."""
        name = self.new_db_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a database name")
            return
        
        # Validate name
        if not all(c.isalnum() or c in (' ', '_', '-') for c in name):
            QMessageBox.warning(self, "Invalid Name", "Database name can only contain letters, numbers, spaces, underscores, and hyphens")
            return
        
        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Create New Database",
            f"{name}.db",
            "Database Files (*.db);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Create new database
            if not file_path.endswith('.db'):
                file_path += '.db'
            
            # Initialize empty database
            conn, cursor = initialize_db()
            conn.close()
            
            # Copy to new location
            current_db = get_db_path()
            if os.path.exists(current_db):
                shutil.copy2(current_db, file_path)
            else:
                # Create from scratch
                import sqlite3
                conn = sqlite3.connect(file_path)
                cursor = conn.cursor()
                from app.models.database_schema import CREATE_TABLES_SQL
                cursor.execute(CREATE_TABLES_SQL["activities"])
                conn.commit()
                conn.close()
            
            # Add to saved databases
            self.databases_config[name] = {
                'path': file_path,
                'created': datetime.now().isoformat()
            }
            self._save_databases_config(self.databases_config)
            
            QMessageBox.information(self, "Success", f"Database '{name}' created successfully!")
            self.new_db_name.clear()
            self.load_databases_list()
            
        except Exception as e:
            logger.error(f"Error creating database: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to create database: {str(e)}")
    
    def load_selected_database(self):
        """Load the selected database."""
        selected_items = self.databases_list.selectedItems()
        if not selected_items:
            return
        
        db_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.switch_to_database(db_path)
    
    def load_database_from_file(self):
        """Load a database from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Database",
            "",
            "Database Files (*.db);;All Files (*)"
        )
        
        if not file_path or not os.path.exists(file_path):
            return
        
        # Validate database
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Invalid Database", f"The selected file is not a valid database: {str(e)}")
            return
        
        # Ask for name
        name, ok = QInputDialog.getText(self, "Database Name", "Enter a name for this database:")
        if not ok or not name.strip():
            return
        
        # Add to saved databases
        self.databases_config[name] = {
            'path': file_path,
            'loaded': datetime.now().isoformat()
        }
        self._save_databases_config(self.databases_config)
        self.load_databases_list()
        
        # Ask if user wants to switch to this database
        reply = QMessageBox.question(
            self,
            "Switch Database",
            f"Switch to database '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.switch_to_database(file_path)
    
    def save_current_database(self):
        """Save current database to a new location."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Database As",
            "tasktitan_backup.db",
            "Database Files (*.db);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            if not file_path.endswith('.db'):
                file_path += '.db'
            
            current_db = get_db_path()
            if os.path.exists(current_db):
                shutil.copy2(current_db, file_path)
                QMessageBox.information(self, "Success", f"Database saved to:\n{file_path}")
            else:
                QMessageBox.warning(self, "Error", "Current database file not found")
                
        except Exception as e:
            logger.error(f"Error saving database: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save database: {str(e)}")
    
    def export_database(self):
        """Export database to a chosen location."""
        self.save_current_database()
    
    def remove_selected_database(self):
        """Remove selected database from the list."""
        selected_items = self.databases_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        db_path = item.data(Qt.ItemDataRole.UserRole)
        
        # Find database name
        db_name = None
        for name, info in self.databases_config.items():
            if info.get('path') == db_path:
                db_name = name
                break
        
        if not db_name:
            return
        
        reply = QMessageBox.question(
            self,
            "Remove Database",
            f"Remove '{db_name}' from the list?\n\nNote: This does not delete the database file.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.databases_config[db_name]
            self._save_databases_config(self.databases_config)
            self.load_databases_list()
    
    def switch_to_database(self, db_path: str):
        """Switch to a different database."""
        if not os.path.exists(db_path):
            QMessageBox.critical(self, "Error", "Database file not found")
            return
        
        reply = QMessageBox.question(
            self,
            "Switch Database",
            "Switching databases will close the current session.\n\n"
            "Make sure you have saved all your work.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.database_changed.emit(db_path)
            self.accept()

