from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QCheckBox, QTimeEdit, QComboBox, QDialogButtonBox
from PyQt6.QtCore import Qt, pyqtSignal, QTime

class HabitWidget(QWidget):
    """Widget for displaying habit items in lists or views."""
    
    habitEdited = pyqtSignal(int)  # id
    habitDeleted = pyqtSignal(int)  # id
    habitCompleted = pyqtSignal(int, bool)  # id, completed
    
    def __init__(self, habit_id=None, title="", days_of_week=None, completed=False, parent=None):
        super().__init__(parent)
        self.habit_id = habit_id
        self.title = title
        self.days_of_week = days_of_week or []
        self.completed = completed
        
        self.setupUI()
    
    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Completion checkbox
        self.complete_checkbox = QCheckBox()
        self.complete_checkbox.setChecked(self.completed)
        self.complete_checkbox.stateChanged.connect(self.onCompletionChanged)
        layout.addWidget(self.complete_checkbox)
        
        # Basic display of habit information
        self.title_label = QLabel(self.title)
        layout.addWidget(self.title_label, 1)
        
        # Days of week display
        days_str = ", ".join(self.days_of_week) if self.days_of_week else "No days selected"
        self.days_label = QLabel(days_str)
        layout.addWidget(self.days_label)
        
        # Action buttons
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.onEditClicked)
        layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.onDeleteClicked)
        layout.addWidget(self.delete_btn)
    
    def onCompletionChanged(self, state):
        self.completed = (state == Qt.CheckState.Checked)
        self.habitCompleted.emit(self.habit_id, self.completed)
    
    def onEditClicked(self):
        self.habitEdited.emit(self.habit_id)
    
    def onDeleteClicked(self):
        self.habitDeleted.emit(self.habit_id)

class HabitDialog(QDialog):
    """Dialog for adding or editing habits."""
    
    def __init__(self, parent=None, habit=None):
        super().__init__(parent)
        
        self.habit = habit
        self.edit_mode = habit is not None
        
        self.setWindowTitle("Add Habit" if not self.edit_mode else "Edit Habit")
        self.setMinimumWidth(400)
        
        self.setupUI()
        
        # If in edit mode, populate fields
        if self.edit_mode:
            self.populateFields()
    
    def setupUI(self):
        layout = QVBoxLayout(self)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        title_layout.addWidget(self.title_input, 1)
        layout.addLayout(title_layout)
        
        # Days of week
        days_layout = QVBoxLayout()
        days_label = QLabel("Repeat on:")
        days_layout.addWidget(days_label)
        
        days_checkboxes_layout = QHBoxLayout()
        self.day_checkboxes = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day in days:
            checkbox = QCheckBox(day)
            days_checkboxes_layout.addWidget(checkbox)
            self.day_checkboxes[day] = checkbox
        
        days_layout.addLayout(days_checkboxes_layout)
        layout.addLayout(days_layout)
        
        # Time
        time_layout = QHBoxLayout()
        start_label = QLabel("Start:")
        time_layout.addWidget(start_label)
        
        self.start_time_input = QTimeEdit()
        self.start_time_input.setTime(QTime.currentTime())
        time_layout.addWidget(self.start_time_input)
        
        end_label = QLabel("End:")
        time_layout.addWidget(end_label)
        
        self.end_time_input = QTimeEdit()
        self.end_time_input.setTime(QTime.currentTime().addSecs(3600))
        time_layout.addWidget(self.end_time_input)
        layout.addLayout(time_layout)
        
        # Category
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_layout.addWidget(category_label)
        
        self.category_input = QComboBox()
        self.category_input.addItems(["Health", "Learning", "Productivity", "Other"])
        category_layout.addWidget(self.category_input, 1)
        layout.addLayout(category_layout)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def populateFields(self):
        """Populate fields with existing habit data."""
        if self.habit:
            self.title_input.setText(self.habit.title)
            
            # Set days of week checkboxes
            for day in self.habit.days_of_week:
                if day in self.day_checkboxes:
                    self.day_checkboxes[day].setChecked(True)
                    
            if self.habit.start_time:
                self.start_time_input.setTime(self.habit.start_time)
                
            if self.habit.end_time:
                self.end_time_input.setTime(self.habit.end_time)
                
            if self.habit.category:
                index = self.category_input.findText(self.habit.category)
                if index >= 0:
                    self.category_input.setCurrentIndex(index)
    
    def getHabitData(self):
        """Get the habit data from the dialog fields."""
        # Get selected days
        selected_days = []
        for day, checkbox in self.day_checkboxes.items():
            if checkbox.isChecked():
                selected_days.append(day)
                
        return {
            "title": self.title_input.text(),
            "days_of_week": selected_days,
            "start_time": self.start_time_input.time(),
            "end_time": self.end_time_input.time(),
            "category": self.category_input.currentText()
        } 