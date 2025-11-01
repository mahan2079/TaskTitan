"""
Login dialog for TaskTitan authentication.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QCheckBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from app.auth.authentication import get_auth_manager
from app.auth.password_manager import PasswordManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LoginDialog(QDialog):
    """Dialog for user login and account creation."""
    
    authenticated = pyqtSignal(dict)  # Emits user dict when authenticated
    
    def __init__(self, parent=None, allow_creation=True):
        """
        Initialize login dialog.
        
        Args:
            parent: Parent widget
            allow_creation: Whether to allow account creation
        """
        super().__init__(parent)
        self.allow_creation = allow_creation
        self.auth_manager = get_auth_manager()
        self.password_manager = PasswordManager()
        self.setupUI()
    
    def setupUI(self):
        """Set up the UI components."""
        self.setWindowTitle("TaskTitan - Login")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Welcome to TaskTitan")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Username field
        self.username_field = QLineEdit()
        self.username_field.setPlaceholderText("Enter username")
        self.username_field.setMaxLength(50)
        form_layout.addRow("Username:", self.username_field)
        
        # Password field
        self.password_field = QLineEdit()
        self.password_field.setPlaceholderText("Enter password")
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setMaxLength(100)
        form_layout.addRow("Password:", self.password_field)
        
        # Show password checkbox
        self.show_password_checkbox = QCheckBox("Show password")
        self.show_password_checkbox.toggled.connect(self.toggle_password_visibility)
        form_layout.addRow("", self.show_password_checkbox)
        
        layout.addLayout(form_layout)
        
        # Password strength indicator (for new accounts)
        self.password_strength_label = QLabel()
        self.password_strength_label.setVisible(False)
        self.password_strength_label.setWordWrap(True)
        layout.addWidget(self.password_strength_label)
        
        # Error message label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        if self.allow_creation:
            self.create_account_btn = QPushButton("Create Account")
            self.create_account_btn.clicked.connect(self.show_create_account)
            button_layout.addWidget(self.create_account_btn)
        
        button_layout.addStretch()
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setDefault(True)
        self.login_btn.clicked.connect(self.handle_login)
        button_layout.addWidget(self.login_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Connect enter key
        self.password_field.returnPressed.connect(self.handle_login)
        
        # Set focus
        self.username_field.setFocus()
    
    def toggle_password_visibility(self, checked: bool):
        """Toggle password visibility."""
        if checked:
            self.password_field.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
    
    def show_create_account(self):
        """Show create account dialog."""
        username = self.username_field.text().strip()
        password = self.password_field.text()
        
        if not username:
            self.show_error("Please enter a username")
            return
        
        if not password:
            self.show_error("Please enter a password")
            return
        
        # Validate password strength
        is_valid, error_msg = self.password_manager.validate_password_strength(password)
        if not is_valid:
            self.show_error(error_msg)
            return
        
        # Create account
        success, error_msg = self.auth_manager.create_user(username, password)
        
        if success:
            QMessageBox.information(self, "Account Created", 
                                  "Account created successfully! Please login.")
            self.password_field.clear()
            self.error_label.setVisible(False)
        else:
            self.show_error(error_msg)
    
    def handle_login(self):
        """Handle login attempt."""
        username = self.username_field.text().strip()
        password = self.password_field.text()
        
        if not username:
            self.show_error("Please enter a username")
            return
        
        if not password:
            self.show_error("Please enter a password")
            return
        
        # Attempt authentication
        success, error_msg = self.auth_manager.authenticate(username, password)
        
        if success:
            user = self.auth_manager.get_current_user()
            if user:
                logger.info(f"User logged in: {user['username']}")
                self.authenticated.emit(user)
                self.accept()
            else:
                self.show_error("Authentication failed")
        else:
            self.show_error(error_msg)
    
    def show_error(self, message: str):
        """Show error message."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
    
    def clear_error(self):
        """Clear error message."""
        self.error_label.clear()
        self.error_label.setVisible(False)

