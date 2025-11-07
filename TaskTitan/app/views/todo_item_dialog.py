from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel
from PyQt6.QtCore import Qt

class TodoItemDialog(QDialog):
    def __init__(self, parent=None, text=""):
        super().__init__(parent)
        self.setWindowTitle("Todo Item")
        self.setMinimumWidth(400)
        self.setMinimumHeight(150)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title label
        title_label = QLabel("Enter todo item:")
        title_label.setObjectName("dialogTitle")
        layout.addWidget(title_label)

        # Text input
        self.text_edit = QLineEdit(text)
        self.text_edit.setPlaceholderText("What needs to be done?")
        self.text_edit.setMinimumHeight(35)
        self.text_edit.setObjectName("todoInput")
        if text:
            self.text_edit.selectAll()
        layout.addWidget(self.text_edit)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Set focus to text edit
        self.text_edit.setFocus()

    def get_text(self):
        return self.text_edit.text().strip()