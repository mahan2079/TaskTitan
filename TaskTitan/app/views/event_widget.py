from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QDateEdit, QTimeEdit, QComboBox, QDialogButtonBox
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime

class EventWidget(QWidget):
    """Widget for displaying event items in lists or views."""
    
    eventEdited = pyqtSignal(int)  # id
    eventDeleted = pyqtSignal(int)  # id
    
    def __init__(self, event_id=None, title="", date=None, start_time=None, end_time=None, category=None, parent=None):
        super().__init__(parent)
        self.event_id = event_id
        self.title = title
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.category = category
        
        self.setupUI()
    
    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Basic display of event information
        self.title_label = QLabel(self.title)
        layout.addWidget(self.title_label, 1)
        
        date_str = self.date.toString("MM/dd/yyyy") if self.date else ""
        time_str = f"{self.start_time} - {self.end_time}" if self.start_time and self.end_time else ""
        self.time_label = QLabel(f"{date_str} {time_str}")
        layout.addWidget(self.time_label)
        
        # Action buttons
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.onEditClicked)
        layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.onDeleteClicked)
        layout.addWidget(self.delete_btn)
    
    def onEditClicked(self):
        self.eventEdited.emit(self.event_id)
    
    def onDeleteClicked(self):
        self.eventDeleted.emit(self.event_id)

class EventDialog(QDialog):
    """Dialog for adding or editing events."""
    
    def __init__(self, parent=None, event=None):
        super().__init__(parent)
        
        self.event = event
        self.edit_mode = event is not None
        
        self.setWindowTitle("Add Event" if not self.edit_mode else "Edit Event")
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
        
        # Date
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_layout.addWidget(date_label)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_input, 1)
        layout.addLayout(date_layout)
        
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
        self.category_input.addItems(["Work", "Personal", "Meeting", "Other"])
        category_layout.addWidget(self.category_input, 1)
        layout.addLayout(category_layout)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def populateFields(self):
        """Populate fields with existing event data."""
        if self.event:
            self.title_input.setText(self.event.title)
            
            if self.event.date:
                self.date_input.setDate(self.event.date)
                
            if self.event.start_time:
                self.start_time_input.setTime(self.event.start_time)
                
            if self.event.end_time:
                self.end_time_input.setTime(self.event.end_time)
                
            if self.event.category:
                index = self.category_input.findText(self.event.category)
                if index >= 0:
                    self.category_input.setCurrentIndex(index)
    
    def getEventData(self):
        """Get the event data from the dialog fields."""
        return {
            "title": self.title_input.text(),
            "date": self.date_input.date(),
            "start_time": self.start_time_input.time(),
            "end_time": self.end_time_input.time(),
            "category": self.category_input.currentText()
        } 