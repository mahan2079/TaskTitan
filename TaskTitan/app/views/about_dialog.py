"""
About dialog for TaskTitan.

This dialog displays application information including version,
license, and credits.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from app.resources.constants import APP_NAME, APP_VERSION, APP_DESCRIPTION
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AboutDialog(QDialog):
    """About dialog showing application information."""
    
    def __init__(self, parent=None):
        """Initialize about dialog."""
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumSize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        
        # Application name and version
        title_label = QLabel(APP_NAME)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        # Description
        desc_label = QLabel(APP_DESCRIPTION)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        layout.addSpacing(20)
        
        # License information
        license_text = QTextEdit()
        license_text.setReadOnly(True)
        license_text.setPlainText(
            "TaskTitan is licensed under the Apache License 2.0.\n\n"
            "Copyright 2025 Mahan Dashti Gohari\n\n"
            "This software is provided 'as is', without warranty of any kind."
        )
        license_text.setMaximumHeight(150)
        layout.addWidget(license_text)
        
        # Credits
        credits_label = QLabel(
            "Built with PyQt6\n"
            "Icons from Material Design Icons"
        )
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_label.setStyleSheet("color: #666;")
        layout.addWidget(credits_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)


def show_about_dialog(parent=None):
    """Show about dialog (convenience function)."""
    dialog = AboutDialog(parent)
    dialog.exec()

