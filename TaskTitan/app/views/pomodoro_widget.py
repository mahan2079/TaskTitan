"""
Pomodoro timer widget for TaskTitan.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QProgressBar, QSlider, QGroupBox, 
                           QSpinBox, QComboBox, QFormLayout, QDialog,
                           QDialogButtonBox, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
from datetime import datetime, timedelta
import random

from app.resources import get_icon

class PomodoroWidget(QWidget):
    """Widget for using the Pomodoro Technique to manage work sessions."""
    
    # Signals for session events
    sessionStarted = pyqtSignal(dict)
    sessionPaused = pyqtSignal()
    sessionResumed = pyqtSignal()
    sessionCompleted = pyqtSignal(dict)
    sessionCancelled = pyqtSignal()
    
    # Timer states
    IDLE = 0
    WORKING = 1
    BREAK = 2
    PAUSED = 3
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store parent to access database
        
        # Pomodoro settings
        self.work_duration = 25  # minutes
        self.short_break_duration = 5  # minutes
        self.long_break_duration = 15  # minutes
        self.pomodoros_until_long_break = 4
        self.auto_start_breaks = True
        self.auto_start_work = False
        self.selected_task = None
        
        # Pomodoro state
        self.state = self.IDLE
        self.time_left = 0  # seconds
        self.pomodoro_count = 0
        self.current_session = None
        
        # Setup timer
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # 1 second
        self.timer.timeout.connect(self.updateTimer)
        
        # Session history
        self.session_history = []
        
        # Setup UI
        self.setupUI()
    
    def setupUI(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("pomodoroHeader")
        header.setMinimumHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Title
        title = QLabel("Pomodoro Timer")
        title.setObjectName("pomodoroTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        header_layout.addWidget(title)
        
        # Settings button
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("pomodoroSettingsButton")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self.showSettingsDialog)
        
        # Add icon to button
        settings_icon = get_icon("settings")
        if not settings_icon.isNull():
            settings_btn.setIcon(settings_icon)
        
        header_layout.addWidget(settings_btn)
        
        main_layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("pomodoroSeparator")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Main content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Timer display
        timer_group = QGroupBox("Timer")
        timer_layout = QVBoxLayout(timer_group)
        timer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # State label
        self.state_label = QLabel("Ready to start")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setObjectName("pomodoroStateLabel")
        timer_layout.addWidget(self.state_label)
        
        # Time display
        self.time_display = QLabel("25:00")
        self.time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_display.setObjectName("pomodoroTimeDisplay")
        timer_layout.addWidget(self.time_display)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.work_duration * 60)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setFormat("%v seconds")
        self.progress_bar.setTextVisible(True)
        timer_layout.addWidget(self.progress_bar)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Start/Resume button
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.startTimer)
        controls_layout.addWidget(self.start_btn)
        
        # Pause button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pauseTimer)
        self.pause_btn.setEnabled(False)
        controls_layout.addWidget(self.pause_btn)
        
        # Skip button
        self.skip_btn = QPushButton("Skip")
        self.skip_btn.clicked.connect(self.skipTimer)
        self.skip_btn.setEnabled(False)
        controls_layout.addWidget(self.skip_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.resetTimer)
        self.reset_btn.setEnabled(False)
        controls_layout.addWidget(self.reset_btn)
        
        timer_layout.addLayout(controls_layout)
        
        content_layout.addWidget(timer_group)
        
        # Session information
        session_group = QGroupBox("Current Session")
        session_layout = QFormLayout(session_group)
        
        self.session_type_label = QLabel("None")
        session_layout.addRow("Session Type:", self.session_type_label)
        
        self.session_count_label = QLabel("0/4")
        session_layout.addRow("Pomodoros Completed:", self.session_count_label)
        
        self.session_task_label = QLabel("None")
        session_layout.addRow("Current Task:", self.session_task_label)
        
        # Task selection
        task_layout = QHBoxLayout()
        
        self.task_combo = QComboBox()
        self.task_combo.addItem("None", None)
        # In a real app, we'd load tasks from the database
        self.task_combo.addItem("Sample Task 1", 1001)
        self.task_combo.addItem("Sample Task 2", 1002)
        self.task_combo.addItem("Sample Task 3", 1003)
        self.task_combo.currentIndexChanged.connect(self.onTaskSelected)
        task_layout.addWidget(self.task_combo)
        
        session_layout.addRow("Select Task:", task_layout)
        
        content_layout.addWidget(session_group)
        
        # Statistics group
        stats_group = QGroupBox("Today's Statistics")
        stats_layout = QFormLayout(stats_group)
        
        self.completed_pomodoros_label = QLabel("0")
        stats_layout.addRow("Completed Pomodoros:", self.completed_pomodoros_label)
        
        self.focus_time_label = QLabel("0 minutes")
        stats_layout.addRow("Total Focus Time:", self.focus_time_label)
        
        content_layout.addWidget(stats_group)
        
        main_layout.addWidget(content)
        
        # Remove hardcoded styles - theme system handles styling via object names
        # Object names are already set: pomodoroHeader, pomodoroTitle, pomodoroSettingsButton,
        # pomodoroSeparator, pomodoroStateLabel, pomodoroTimeDisplay
        
        # Load statistics
        self.loadStatistics()
    
    def showSettingsDialog(self):
        """Show dialog to configure Pomodoro settings."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Pomodoro Settings")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Work duration
        work_layout = QHBoxLayout()
        work_label = QLabel("Work Duration (minutes):")
        work_layout.addWidget(work_label)
        self.work_duration_input = QSpinBox()
        self.work_duration_input.setRange(1, 60)
        self.work_duration_input.setValue(self.work_duration)
        work_layout.addWidget(self.work_duration_input)
        layout.addLayout(work_layout)
        
        # Short break duration
        short_break_layout = QHBoxLayout()
        short_break_label = QLabel("Short Break Duration (minutes):")
        short_break_layout.addWidget(short_break_label)
        self.short_break_duration_input = QSpinBox()
        self.short_break_duration_input.setRange(1, 30)
        self.short_break_duration_input.setValue(self.short_break_duration)
        short_break_layout.addWidget(self.short_break_duration_input)
        layout.addLayout(short_break_layout)
        
        # Long break duration
        long_break_layout = QHBoxLayout()
        long_break_label = QLabel("Long Break Duration (minutes):")
        long_break_layout.addWidget(long_break_label)
        self.long_break_duration_input = QSpinBox()
        self.long_break_duration_input.setRange(1, 60)
        self.long_break_duration_input.setValue(self.long_break_duration)
        long_break_layout.addWidget(self.long_break_duration_input)
        layout.addLayout(long_break_layout)
        
        # Pomodoros until long break
        pomodoros_layout = QHBoxLayout()
        pomodoros_label = QLabel("Pomodoros Until Long Break:")
        pomodoros_layout.addWidget(pomodoros_label)
        self.pomodoros_input = QSpinBox()
        self.pomodoros_input.setRange(1, 10)
        self.pomodoros_input.setValue(self.pomodoros_until_long_break)
        pomodoros_layout.addWidget(self.pomodoros_input)
        layout.addLayout(pomodoros_layout)
        
        # Auto start options
        auto_start_breaks_layout = QHBoxLayout()
        auto_start_breaks_label = QLabel("Auto-start Breaks:")
        auto_start_breaks_layout.addWidget(auto_start_breaks_label)
        self.auto_start_breaks_input = QComboBox()
        self.auto_start_breaks_input.addItems(["Yes", "No"])
        self.auto_start_breaks_input.setCurrentIndex(0 if self.auto_start_breaks else 1)
        auto_start_breaks_layout.addWidget(self.auto_start_breaks_input)
        layout.addLayout(auto_start_breaks_layout)
        
        auto_start_work_layout = QHBoxLayout()
        auto_start_work_label = QLabel("Auto-start Work:")
        auto_start_work_layout.addWidget(auto_start_work_label)
        self.auto_start_work_input = QComboBox()
        self.auto_start_work_input.addItems(["Yes", "No"])
        self.auto_start_work_input.setCurrentIndex(0 if self.auto_start_work else 1)
        auto_start_work_layout.addWidget(self.auto_start_work_input)
        layout.addLayout(auto_start_work_layout)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.saveSettings(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def saveSettings(self, dialog):
        """Save Pomodoro settings."""
        # Get values from inputs
        self.work_duration = self.work_duration_input.value()
        self.short_break_duration = self.short_break_duration_input.value()
        self.long_break_duration = self.long_break_duration_input.value()
        self.pomodoros_until_long_break = self.pomodoros_input.value()
        self.auto_start_breaks = self.auto_start_breaks_input.currentIndex() == 0
        self.auto_start_work = self.auto_start_work_input.currentIndex() == 0
        
        # Update UI
        if self.state == self.IDLE:
            # Update progress bar range
            self.progress_bar.setRange(0, self.work_duration * 60)
            self.progress_bar.setValue(0)
            
            # Update time display
            self.time_display.setText(f"{self.work_duration:02d}:00")
        
        # Update session count label
        self.session_count_label.setText(f"{self.pomodoro_count}/{self.pomodoros_until_long_break}")
        
        # Close dialog
        dialog.accept()
    
    def startTimer(self):
        """Start or resume the Pomodoro timer."""
        if self.state == self.IDLE:
            # Start a new work session
            self.state = self.WORKING
            self.time_left = self.work_duration * 60
            self.progress_bar.setRange(0, self.time_left)
            self.progress_bar.setValue(0)
            self.state_label.setText("Working")
            self.state_label.setStyleSheet("color: #EF4444;")  # Red for work
            
            # Create a new session
            self.current_session = {
                'id': random.randint(1000, 9999),
                'type': 'work',
                'start_time': datetime.now(),
                'end_time': None,
                'duration': self.work_duration * 60,
                'completed': False,
                'task_id': self.selected_task
            }
            
            # Update session info
            self.session_type_label.setText("Work")
            
            # Emit signal
            self.sessionStarted.emit(self.current_session)
        elif self.state == self.PAUSED:
            # Resume the current session
            if self.current_session['type'] == 'work':
                self.state = self.WORKING
                self.state_label.setText("Working")
                self.state_label.setStyleSheet("color: #EF4444;")  # Red for work
            else:
                self.state = self.BREAK
                self.state_label.setText("Break")
                self.state_label.setStyleSheet("color: #10B981;")  # Green for break
            
            # Emit signal
            self.sessionResumed.emit()
        
        # Start the timer
        self.timer.start()
        
        # Update buttons
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)
    
    def pauseTimer(self):
        """Pause the Pomodoro timer."""
        if self.state == self.WORKING or self.state == self.BREAK:
            self.state = self.PAUSED
            self.timer.stop()
            
            # Update label
            self.state_label.setText("Paused")
            self.state_label.setStyleSheet("color: #F59E0B;")  # Amber for paused
            
            # Update buttons
            self.start_btn.setEnabled(True)
            self.start_btn.setText("Resume")
            self.pause_btn.setEnabled(False)
            
            # Emit signal
            self.sessionPaused.emit()
    
    def skipTimer(self):
        """Skip the current Pomodoro interval."""
        if self.state == self.WORKING:
            # Complete the work session
            self.completeWorkSession()
        elif self.state == self.BREAK:
            # Complete the break
            self.completeBreakSession()
        elif self.state == self.PAUSED:
            # If we're paused, complete the appropriate session
            if self.current_session['type'] == 'work':
                self.completeWorkSession()
            else:
                self.completeBreakSession()
    
    def resetTimer(self):
        """Reset the Pomodoro timer."""
        # Stop the timer
        self.timer.stop()
        
        # Reset state
        self.state = self.IDLE
        self.time_left = 0
        
        # Reset UI
        self.state_label.setText("Ready to start")
        self.state_label.setStyleSheet("color: #6B7280;")
        self.time_display.setText(f"{self.work_duration:02d}:00")
        self.progress_bar.setRange(0, self.work_duration * 60)
        self.progress_bar.setValue(0)
        
        # Reset buttons
        self.start_btn.setEnabled(True)
        self.start_btn.setText("Start")
        self.pause_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        
        # Cancel the current session
        if self.current_session:
            self.current_session['end_time'] = datetime.now()
            self.current_session['completed'] = False
            self.session_history.append(self.current_session)
            self.current_session = None
            
            # Emit signal
            self.sessionCancelled.emit()
    
    def updateTimer(self):
        """Update the timer every second."""
        if self.time_left > 0:
            self.time_left -= 1
            minutes = self.time_left // 60
            seconds = self.time_left % 60
            
            # Update time display
            self.time_display.setText(f"{minutes:02d}:{seconds:02d}")
            
            # Update progress bar
            if self.state == self.WORKING:
                self.progress_bar.setValue(self.progress_bar.maximum() - self.time_left)
            else:
                self.progress_bar.setValue(self.time_left)
        else:
            # Time's up
            if self.state == self.WORKING:
                self.completeWorkSession()
            elif self.state == self.BREAK:
                self.completeBreakSession()
    
    def completeWorkSession(self):
        """Complete a work session."""
        # Stop the timer
        self.timer.stop()
        
        # Update the current session
        if self.current_session:
            self.current_session['end_time'] = datetime.now()
            self.current_session['completed'] = True
            self.session_history.append(self.current_session)
            
            # Emit signal
            self.sessionCompleted.emit(self.current_session)
        
        # Increment pomodoro count
        self.pomodoro_count += 1
        self.session_count_label.setText(f"{self.pomodoro_count}/{self.pomodoros_until_long_break}")
        
        # Update statistics
        self.completed_pomodoros_label.setText(str(int(self.completed_pomodoros_label.text()) + 1))
        self.focus_time_label.setText(f"{int(self.focus_time_label.text().split()[0]) + self.work_duration} minutes")
        
        # Determine the type of break
        if self.pomodoro_count >= self.pomodoros_until_long_break:
            # Long break
            self.startBreak(long=True)
        else:
            # Short break
            self.startBreak(long=False)
    
    def startBreak(self, long=False):
        """Start a break session."""
        # Reset state
        self.state = self.BREAK
        
        # Set break duration
        if long:
            self.time_left = self.long_break_duration * 60
            self.progress_bar.setRange(0, self.long_break_duration * 60)
            self.session_type_label.setText("Long Break")
            
            # Reset pomodoro count after long break
            self.pomodoro_count = 0
            self.session_count_label.setText(f"{self.pomodoro_count}/{self.pomodoros_until_long_break}")
        else:
            self.time_left = self.short_break_duration * 60
            self.progress_bar.setRange(0, self.short_break_duration * 60)
            self.session_type_label.setText("Short Break")
        
        # Update UI
        self.state_label.setText("Break")
        self.state_label.setStyleSheet("color: #10B981;")  # Green for break
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.time_display.setText(f"{minutes:02d}:{seconds:02d}")
        self.progress_bar.setValue(0)
        
        # Create a new session
        self.current_session = {
            'id': random.randint(1000, 9999),
            'type': 'long_break' if long else 'short_break',
            'start_time': datetime.now(),
            'end_time': None,
            'duration': self.time_left,
            'completed': False,
            'task_id': None
        }
        
        # Auto-start or wait for user
        if self.auto_start_breaks:
            self.timer.start()
            
            # Update buttons
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.skip_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
            
            # Emit signal
            self.sessionStarted.emit(self.current_session)
        else:
            # Reset buttons
            self.start_btn.setEnabled(True)
            self.start_btn.setText("Start Break")
            self.pause_btn.setEnabled(False)
            self.skip_btn.setEnabled(False)
            self.reset_btn.setEnabled(True)
    
    def completeBreakSession(self):
        """Complete a break session."""
        # Stop the timer
        self.timer.stop()
        
        # Update the current session
        if self.current_session:
            self.current_session['end_time'] = datetime.now()
            self.current_session['completed'] = True
            self.session_history.append(self.current_session)
            
            # Emit signal
            self.sessionCompleted.emit(self.current_session)
        
        # Reset for next work session
        self.state = self.IDLE
        self.time_left = self.work_duration * 60
        
        # Update UI
        self.state_label.setText("Ready to start")
        self.state_label.setStyleSheet("color: #6B7280;")
        self.time_display.setText(f"{self.work_duration:02d}:00")
        self.progress_bar.setRange(0, self.work_duration * 60)
        self.progress_bar.setValue(0)
        self.session_type_label.setText("None")
        
        # Reset buttons
        self.start_btn.setEnabled(True)
        self.start_btn.setText("Start")
        self.pause_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        
        # Auto-start next work session
        if self.auto_start_work:
            self.startTimer()
    
    def onTaskSelected(self, index):
        """Handle when a task is selected."""
        self.selected_task = self.task_combo.currentData()
        
        if self.selected_task:
            self.session_task_label.setText(self.task_combo.currentText())
        else:
            self.session_task_label.setText("None")
        
        # Update current session if we're in the middle of one
        if self.current_session and self.state == self.WORKING:
            self.current_session['task_id'] = self.selected_task
    
    def loadStatistics(self):
        """Load Pomodoro statistics from the database."""
        if hasattr(self.parent, 'cursor') and self.parent.cursor:
            try:
                # Get today's date
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Get completed pomodoros for today
                self.parent.cursor.execute("""
                    SELECT COUNT(*) 
                    FROM pomodoro_sessions 
                    WHERE date = ? AND type = 'work' AND completed = 1
                """, (today,))
                
                result = self.parent.cursor.fetchone()
                if result:
                    completed_pomodoros = result[0]
                    self.completed_pomodoros_label.setText(str(completed_pomodoros))
                
                # Get total focus time for today
                self.parent.cursor.execute("""
                    SELECT SUM(duration_minutes) 
                    FROM pomodoro_sessions 
                    WHERE date = ? AND type = 'work' AND completed = 1
                """, (today,))
                
                result = self.parent.cursor.fetchone()
                if result and result[0]:
                    focus_minutes = result[0]
                    self.focus_time_label.setText(f"{focus_minutes} minutes")
                
            except Exception as e:
                print(f"Error loading Pomodoro statistics: {e}")
    
    def saveSessionToDatabase(self, session):
        """Save a completed session to the database."""
        if hasattr(self.parent, 'cursor') and self.parent.cursor:
            try:
                # Calculate duration in minutes
                start_time = session['start_time']
                end_time = session['end_time']
                duration_minutes = (end_time - start_time).total_seconds() // 60
                
                # Insert into database
                self.parent.cursor.execute("""
                    INSERT INTO pomodoro_sessions 
                    (type, date, start_time, end_time, duration_minutes, completed, task_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session['type'],
                    start_time.strftime("%Y-%m-%d"),
                    start_time.strftime("%H:%M:%S"),
                    end_time.strftime("%H:%M:%S"),
                    duration_minutes,
                    1 if session['completed'] else 0,
                    session['task_id']
                ))
                
                self.parent.conn.commit()
                
            except Exception as e:
                print(f"Error saving Pomodoro session: {e}")
    
    def refresh(self):
        """Refresh the widget data."""
        self.loadStatistics()
        
        # Update task dropdown
        if hasattr(self.parent, 'cursor') and self.parent.cursor:
            try:
                # Clear the combo box
                self.task_combo.clear()
                self.task_combo.addItem("None", None)
                
                # Get tasks from database
                self.parent.cursor.execute("""
                    SELECT id, title 
                    FROM tasks 
                    WHERE completed = 0
                    ORDER BY due_date
                """)
                
                for task_id, title in self.parent.cursor.fetchall():
                    self.task_combo.addItem(title, task_id)
                
            except Exception as e:
                print(f"Error loading tasks for Pomodoro: {e}")
                # Add some sample tasks
                self.task_combo.addItem("Sample Task 1", 1001)
                self.task_combo.addItem("Sample Task 2", 1002)
                self.task_combo.addItem("Sample Task 3", 1003) 