"""
Settings dialog for TaskTitan.
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel


class SettingsDialog(QDialog):
    """Dialog for application settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()

    def setupUI(self):
        """Set up the UI components."""
        self.setWindowTitle("Settings")
        self.resize(500, 380)

        from PyQt6.QtWidgets import (
            QHBoxLayout,
            QPushButton,
            QCheckBox,
            QComboBox,
            QFormLayout,
        )
        from app.themes import ThemeManager

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Theme section
        theme_form = QFormLayout()
        self.follow_system_checkbox = QCheckBox("Follow system theme")
        # Load saved
        current_theme, follow = ThemeManager.get_saved_selection()
        self.follow_system_checkbox.setChecked(bool(follow))

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(ThemeManager.list_themes()))
        # Select saved
        try:
            idx = self.theme_combo.findText(current_theme)
            if idx < 0:
                # if following system, preselect pseudo-option
                idx = self.theme_combo.findText("System (Auto)")
            if idx >= 0:
                self.theme_combo.setCurrentIndex(idx)
        except Exception:
            pass

        # If a non-system theme is picked, ensure we don't force system follow
        def _on_theme_changed(txt: str):
            if txt != "System (Auto)":
                self.follow_system_checkbox.setChecked(False)
        self.theme_combo.currentTextChanged.connect(_on_theme_changed)

        theme_form.addRow("Theme:", self.theme_combo)
        theme_form.addRow(" ", self.follow_system_checkbox)
        layout.addLayout(theme_form)

        # Buttons
        btn_row = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.save_btn = QPushButton("Save")
        self.close_btn = QPushButton("Close")
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        # Wire up
        def apply_theme():
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if not app:
                return
            chosen = self.theme_combo.currentText()
            follow2 = self.follow_system_checkbox.isChecked()
            # If user picked System (Auto), force follow_system
            if chosen == "System (Auto)":
                follow2 = True
                chosen2 = "Light"  # placeholder, ThemeManager will override
            else:
                chosen2 = chosen
                # Non-system theme: ensure follow is disabled so the choice applies
                follow2 = False
            ThemeManager.apply_theme(app, chosen2, follow2)

        def save_theme():
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if not app:
                return
            chosen = self.theme_combo.currentText()
            follow2 = self.follow_system_checkbox.isChecked()
            if chosen == "System (Auto)":
                follow2 = True
                chosen2 = "Light"
            else:
                chosen2 = chosen
                follow2 = False
            ThemeManager.save_selection(chosen2, follow2)
            ThemeManager.apply_saved_theme(app)

        self.apply_btn.clicked.connect(apply_theme)
        self.save_btn.clicked.connect(save_theme)
        self.close_btn.clicked.connect(self.accept)