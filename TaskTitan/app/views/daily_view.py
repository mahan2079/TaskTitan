"""
Daily planning view for TaskTitan.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QScrollArea, QFrame, QSplitter, QTabWidget, QListWidget, 
                           QListWidgetItem, QDialog, QLineEdit, QTimeEdit, QDateEdit,
                           QTextEdit, QCheckBox, QComboBox, QDialogButtonBox, QMessageBox, QMenu)
from PyQt6.QtCore import Qt, QDate, QTime, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QColor
from datetime import datetime, timedelta
import sqlite3

from app.resources import get_icon

class DailyTaskItem(QFrame):
    """Widget representing a task or event in the daily view."""
    
    statusChanged = pyqtSignal(int, bool)
    
    def __init__(self, item_id, time_str, description, is_completed=False, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.time_str = time_str
        self.description = description
        self.is_completed = is_completed
        
        self.setupUI()
    
    def setupUI(self):
        """Set up the UI for this task item."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Checkbox for completion status
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.is_completed)
        self.checkbox.toggled.connect(self.onStatusChanged)
        layout.addWidget(self.checkbox)
        
        # Time label
        time_label = QLabel(self.time_str)
        time_label.setStyleSheet("font-weight: bold; min-width: 60px;")
        layout.addWidget(time_label)
        
        # Description label
        desc_label = QLabel(self.description)
        if self.is_completed:
            desc_label.setStyleSheet("text-decoration: line-through; color: #9CA3AF;")
        layout.addWidget(desc_label, 1)  # Stretch to take available space
        
        # Set frame style
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border-radius: 6px;
                border: 1px solid #E5E7EB;
            }
            QFrame:hover {
                background-color: #F3F4F6;
            }
        """)
    
    def onStatusChanged(self, checked):
        """Handle checkbox toggle."""
        self.is_completed = checked
        
        # Update the style of the description label
        desc_label = self.findChild(QLabel, "", options=Qt.FindChildOption.FindChildrenRecursively)[1]  # Second label is description
        if self.is_completed:
            desc_label.setStyleSheet("text-decoration: line-through; color: #9CA3AF;")
        else:
            desc_label.setStyleSheet("")
        
        # Emit signal
        self.statusChanged.emit(self.item_id, checked)

class DailyView(QWidget):
    """Widget for daily planning."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store parent to access database
        
        # Initialize database connection if needed
        if parent and hasattr(parent, 'conn') and parent.conn:
            self.conn = parent.conn
            self.cursor = parent.cursor
        else:
            # Create our own connection if parent doesn't have one
            self.conn = sqlite3.connect('tasktitan.db')
            self.cursor = self.conn.cursor()
            self.ensure_tables_exist()
        
        self.current_date = QDate.currentDate()
        self.setupUI()
        
    def ensure_tables_exist(self):
        """Ensure required tables exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                time TEXT NOT NULL,
                description TEXT NOT NULL,
                type TEXT DEFAULT 'event',
                completed INTEGER DEFAULT 0
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_notes (
                date DATE PRIMARY KEY,
                note TEXT
            )
        """)
        
        self.conn.commit()
    
    def setupUI(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        
        # Header with date navigation
        header_layout = QHBoxLayout()
        
        # Previous day button
        prev_btn = QPushButton()
        prev_btn.setIcon(get_icon("arrow-left"))
        prev_btn.setFixedSize(36, 36)
        prev_btn.clicked.connect(self.previousDay)
        header_layout.addWidget(prev_btn)
        
        # Date display and today button
        date_layout = QVBoxLayout()
        date_layout.setSpacing(2)
        
        self.date_label = QLabel(self.current_date.toString('dddd, MMMM d, yyyy'))
        self.date_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_layout.addWidget(self.date_label)
        
        today_btn = QPushButton("Today")
        today_btn.setFixedWidth(100)
        today_btn.clicked.connect(self.goToToday)
        today_btn.setStyleSheet("font-size: 12px;")
        
        today_layout = QHBoxLayout()
        today_layout.addStretch()
        today_layout.addWidget(today_btn)
        today_layout.addStretch()
        date_layout.addLayout(today_layout)
        
        header_layout.addLayout(date_layout, 1)  # Stretch in middle
        
        # Next day button
        next_btn = QPushButton()
        next_btn.setIcon(get_icon("arrow-right"))
        next_btn.setFixedSize(36, 36)
        next_btn.clicked.connect(self.nextDay)
        header_layout.addWidget(next_btn)
        
        main_layout.addLayout(header_layout)
        
        # Tabs for different views
        self.tab_widget = QTabWidget()
        
        # Schedule tab (events and tasks)
        self.schedule_widget = QWidget()
        self.setupScheduleTab()
        self.tab_widget.addTab(self.schedule_widget, "Schedule")
        
        # Notes tab
        self.notes_widget = QWidget()
        self.setupNotesTab()
        self.tab_widget.addTab(self.notes_widget, "Notes")
        
        main_layout.addWidget(self.tab_widget)
    
    def setupScheduleTab(self):
        """Set up the schedule tab."""
        layout = QVBoxLayout(self.schedule_widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Add event button
        add_layout = QHBoxLayout()
        add_layout.addStretch()
        
        add_btn = QPushButton("Add Event")
        add_btn.setIcon(get_icon("add"))
        add_btn.clicked.connect(self.showAddEventDialog)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        # Create scrollable area for events
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.events_layout = QVBoxLayout(scroll_content)
        self.events_layout.setSpacing(10)
        self.events_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add stretcher at the end
        self.events_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # Load events for current date
        self.loadEvents()
    
    def setupNotesTab(self):
        """Set up the notes tab."""
        layout = QVBoxLayout(self.notes_widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Text editor for notes
        self.notes_editor = QTextEdit()
        self.notes_editor.setPlaceholderText("Enter your notes for this day...")
        layout.addWidget(self.notes_editor)
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        save_btn = QPushButton("Save Notes")
        save_btn.setIcon(get_icon("save"))
        save_btn.clicked.connect(self.saveNotes)
        save_layout.addWidget(save_btn)
        
        layout.addLayout(save_layout)
        
        # Load notes for current date
        self.loadNotes()
    
    def loadEvents(self):
        """Load events for the current date."""
        # Clear existing events
        while self.events_layout.count() > 1:  # Keep the last stretch item
            item = self.events_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            # Get events from database
            self.cursor.execute("""
                SELECT id, time, description, completed, type
                FROM events
                WHERE date = ?
                ORDER BY time
            """, (self.current_date.toString("yyyy-MM-dd"),))
            
            events = self.cursor.fetchall()
            
            if not events:
                # No events
                empty_label = QLabel("No events scheduled for this day.")
                empty_label.setStyleSheet("color: #6B7280; padding: 20px;")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.events_layout.insertWidget(0, empty_label)
                return
            
            # Add events to layout
            for event in events:
                event_id, time_str, description, completed, event_type = event
                event_item = DailyTaskItem(event_id, time_str, description, bool(completed))
                event_item.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                event_item.customContextMenuRequested.connect(lambda pos, eid=event_id: self.showEventContextMenu(pos, eid))
                event_item.statusChanged.connect(self.toggleEventStatus)
                
                self.events_layout.insertWidget(self.events_layout.count() - 1, event_item)
        
        except sqlite3.Error as e:
            print(f"Error loading events: {e}")
            # Show error message in the view
            error_label = QLabel(f"Error loading events: {e}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.events_layout.insertWidget(0, error_label)
    
    def loadNotes(self):
        """Load notes for the current date."""
        try:
            self.cursor.execute("""
                SELECT note FROM daily_notes WHERE date = ?
            """, (self.current_date.toString("yyyy-MM-dd"),))
            
            result = self.cursor.fetchone()
            if result:
                self.notes_editor.setPlainText(result[0])
            else:
                self.notes_editor.clear()
        
        except sqlite3.Error as e:
            print(f"Error loading notes: {e}")
            self.notes_editor.setPlainText(f"Error loading notes: {e}")
    
    def saveNotes(self):
        """Save the current notes to the database."""
        note_text = self.notes_editor.toPlainText()
        date_str = self.current_date.toString("yyyy-MM-dd")
        
        try:
            # Check if a note already exists for this date
            self.cursor.execute("SELECT 1 FROM daily_notes WHERE date = ?", (date_str,))
            exists = self.cursor.fetchone()
            
            if exists:
                # Update existing note
                self.cursor.execute("""
                    UPDATE daily_notes SET note = ? WHERE date = ?
                """, (note_text, date_str))
            else:
                # Insert new note
                self.cursor.execute("""
                    INSERT INTO daily_notes (date, note) VALUES (?, ?)
                """, (date_str, note_text))
            
            self.conn.commit()
            
            # Show small confirmation
            QMessageBox.information(self, "Notes Saved", "Your notes have been saved.")
        
        except sqlite3.Error as e:
            print(f"Error saving notes: {e}")
            QMessageBox.warning(self, "Error", f"Error saving notes: {e}")
    
    def showAddEventDialog(self):
        """Show dialog to add a new event."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Event")
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        
        # Time field
        time_layout = QHBoxLayout()
        time_label = QLabel("Time:")
        time_layout.addWidget(time_label)
        
        time_input = QTimeEdit()
        time_input.setTime(QTime.currentTime())
        time_layout.addWidget(time_input)
        
        layout.addLayout(time_layout)
        
        # Description field
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_layout.addWidget(desc_label)
        
        desc_input = QLineEdit()
        desc_layout.addWidget(desc_input)
        
        layout.addLayout(desc_layout)
        
        # Event type field
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        type_layout.addWidget(type_label)
        
        type_combo = QComboBox()
        type_combo.addItems(["event", "task", "appointment", "reminder"])
        type_layout.addWidget(type_combo)
        
        layout.addLayout(type_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            time_str = time_input.time().toString("HH:mm")
            description = desc_input.text()
            event_type = type_combo.currentText()
            
            if not description:
                QMessageBox.warning(self, "Error", "Description cannot be empty.")
                return
            
            self.addEvent(time_str, description, event_type)
    
    def addEvent(self, time_str, description, event_type="event"):
        """Add a new event to the database."""
        date_str = self.current_date.toString("yyyy-MM-dd")
        
        try:
            self.cursor.execute("""
                INSERT INTO events (date, time, description, type, completed)
                VALUES (?, ?, ?, ?, 0)
            """, (date_str, time_str, description, event_type))
            
            self.conn.commit()
            
            # Reload events
            self.loadEvents()
        
        except sqlite3.Error as e:
            print(f"Error adding event: {e}")
            QMessageBox.warning(self, "Error", f"Error adding event: {e}")
    
    def toggleEventStatus(self, event_id, is_completed):
        """Toggle the completion status of an event."""
        try:
            self.cursor.execute("""
                UPDATE events SET completed = ? WHERE id = ?
            """, (1 if is_completed else 0, event_id))
            
            self.conn.commit()
        
        except sqlite3.Error as e:
            print(f"Error updating event status: {e}")
            QMessageBox.warning(self, "Error", f"Error updating event status: {e}")
    
    def showEventContextMenu(self, position, event_id):
        """Show context menu for an event."""
        menu = QMenu(self)
        
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self.showEditEventDialog(event_id))
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.deleteEvent(event_id))
        
        # Get the sender widget
        sender = self.sender()
        menu.exec(sender.mapToGlobal(position))
    
    def showEditEventDialog(self, event_id):
        """Show dialog to edit an existing event."""
        try:
            # Get the event data
            self.cursor.execute("""
                SELECT time, description, type FROM events WHERE id = ?
            """, (event_id,))
            
            result = self.cursor.fetchone()
            if not result:
                QMessageBox.warning(self, "Error", "Event not found.")
                return
            
            time_str, description, event_type = result
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Edit Event")
            dialog.setMinimumWidth(350)
            
            layout = QVBoxLayout(dialog)
            
            # Time field
            time_layout = QHBoxLayout()
            time_label = QLabel("Time:")
            time_layout.addWidget(time_label)
            
            time_input = QTimeEdit()
            time_input.setTime(QTime.fromString(time_str, "HH:mm"))
            time_layout.addWidget(time_input)
            
            layout.addLayout(time_layout)
            
            # Description field
            desc_layout = QHBoxLayout()
            desc_label = QLabel("Description:")
            desc_layout.addWidget(desc_label)
            
            desc_input = QLineEdit(description)
            desc_layout.addWidget(desc_input)
            
            layout.addLayout(desc_layout)
            
            # Event type field
            type_layout = QHBoxLayout()
            type_label = QLabel("Type:")
            type_layout.addWidget(type_label)
            
            type_combo = QComboBox()
            type_combo.addItems(["event", "task", "appointment", "reminder"])
            type_combo.setCurrentText(event_type)
            type_layout.addWidget(type_combo)
            
            layout.addLayout(type_layout)
            
            # Dialog buttons
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_time = time_input.time().toString("HH:mm")
                new_desc = desc_input.text()
                new_type = type_combo.currentText()
                
                if not new_desc:
                    QMessageBox.warning(self, "Error", "Description cannot be empty.")
                    return
                
                self.updateEvent(event_id, new_time, new_desc, new_type)
        
        except sqlite3.Error as e:
            print(f"Error editing event: {e}")
            QMessageBox.warning(self, "Error", f"Error editing event: {e}")
    
    def updateEvent(self, event_id, time_str, description, event_type):
        """Update an existing event in the database."""
        try:
            self.cursor.execute("""
                UPDATE events 
                SET time = ?, description = ?, type = ?
                WHERE id = ?
            """, (time_str, description, event_type, event_id))
            
            self.conn.commit()
            
            # Reload events
            self.loadEvents()
        
        except sqlite3.Error as e:
            print(f"Error updating event: {e}")
            QMessageBox.warning(self, "Error", f"Error updating event: {e}")
    
    def deleteEvent(self, event_id):
        """Delete an event from the database."""
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion",
            "Are you sure you want to delete this event?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        try:
            self.cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            self.conn.commit()
            
            # Reload events
            self.loadEvents()
        
        except sqlite3.Error as e:
            print(f"Error deleting event: {e}")
            QMessageBox.warning(self, "Error", f"Error deleting event: {e}")
    
    def setDate(self, date):
        """Set the current date for the view.
        
        Args:
            date (QDate or datetime.date): The date to display
        """
        if hasattr(date, 'toPyDate'):
            # It's a QDate
            self.current_date = date
        else:
            # It's a datetime.date
            self.current_date = QDate(date.year, date.month, date.day)
        
        # Update the date label
        self.date_label.setText(self.current_date.toString('dddd, MMMM d, yyyy'))
        
        # Reload data for the new date
        self.loadEvents()
        self.loadNotes()
    
    def previousDay(self):
        """Go to the previous day."""
        self.setDate(self.current_date.addDays(-1))
    
    def nextDay(self):
        """Go to the next day."""
        self.setDate(self.current_date.addDays(1))
    
    def goToToday(self):
        """Go to today's date."""
        self.setDate(QDate.currentDate()) 