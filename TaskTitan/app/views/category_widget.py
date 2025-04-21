from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QColorDialog, QDialogButtonBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

class CategoryWidget(QWidget):
    """Widget for displaying categories in lists or views."""
    
    categoryEdited = pyqtSignal(int)  # id
    categoryDeleted = pyqtSignal(int)  # id
    
    def __init__(self, category_id=None, name="", color="#4F46E5", parent=None):
        super().__init__(parent)
        self.category_id = category_id
        self.name = name
        self.color = color
        
        self.setupUI()
    
    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Color indicator
        self.color_indicator = QLabel()
        self.color_indicator.setFixedSize(16, 16)
        self.color_indicator.setStyleSheet(f"background-color: {self.color}; border-radius: 8px;")
        layout.addWidget(self.color_indicator)
        
        # Category name
        self.name_label = QLabel(self.name)
        self.name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.name_label, 1)
        
        # Action buttons
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.onEditClicked)
        layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.onDeleteClicked)
        layout.addWidget(self.delete_btn)
    
    def onEditClicked(self):
        self.categoryEdited.emit(self.category_id)
    
    def onDeleteClicked(self):
        self.categoryDeleted.emit(self.category_id)

class CategoryDialog(QDialog):
    """Dialog for adding or editing categories."""
    
    def __init__(self, parent=None, category=None):
        super().__init__(parent)
        
        self.category = category
        self.edit_mode = category is not None
        
        self.setWindowTitle("Add Category" if not self.edit_mode else "Edit Category")
        self.setMinimumWidth(350)
        
        self.setupUI()
        
        # If in edit mode, populate fields
        if self.edit_mode:
            self.populateFields()
    
    def setupUI(self):
        layout = QVBoxLayout(self)
        
        # Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input, 1)
        layout.addLayout(name_layout)
        
        # Color
        color_layout = QHBoxLayout()
        color_label = QLabel("Color:")
        color_layout.addWidget(color_label)
        
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet("background-color: #4F46E5; border-radius: 4px;")
        color_layout.addWidget(self.color_preview)
        
        self.color_btn = QPushButton("Select Color")
        self.color_btn.clicked.connect(self.selectColor)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch(1)
        layout.addLayout(color_layout)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Store the current color
        self.current_color = QColor("#4F46E5")
    
    def selectColor(self):
        """Open color dialog to select a color."""
        color = QColorDialog.getColor(self.current_color, self, "Select Category Color")
        if color.isValid():
            self.current_color = color
            self.color_preview.setStyleSheet(f"background-color: {color.name()}; border-radius: 4px;")
    
    def populateFields(self):
        """Populate fields with existing category data."""
        if self.category:
            self.name_input.setText(self.category.name)
            
            if self.category.color:
                self.current_color = QColor(self.category.color)
                self.color_preview.setStyleSheet(f"background-color: {self.category.color}; border-radius: 4px;")
    
    def getCategoryData(self):
        """Get the category data from the dialog fields."""
        return {
            "name": self.name_input.text(),
            "color": self.current_color.name()
        } 