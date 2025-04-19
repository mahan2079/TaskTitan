import json
import darkdetect
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableWidget, 
    QTreeWidget, QTreeWidgetItem, QHeaderView, QLabel, QLineEdit, QComboBox, 
    QDateEdit, QTimeEdit, QMessageBox, QCheckBox, QDialog, QDialogButtonBox,
    QTabWidget, QTableWidgetItem, QProgressBar, QPushButton, QColorDialog,
    QFileDialog, QFormLayout, QAction, QMenu, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate, QTimer, QTime, pyqtSignal
from PyQt5.QtGui import QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import winsound
import os

from app.models.database import initialize_db
from app.controllers.utils import calculate_weeks_since_birth, validate_time, load_colors, save_colors
from app.views.calendar_widget import CustomCalendarWidget
from app.views.daily_planner import DailyPlanner
from app.views.weekly_planner import WeeklyPlanner
from app.themes.dark_theme import get_dark_stylesheet

class SmartScheduler(QMainWindow):
    """Main application window for the TaskTitan Smart Scheduler."""
    def __init__(self):
        super().__init__()
        self.conn, self.cursor = initialize_db()

        # Default colors for dark mode with more distinct, elegant variations
        self.past_week_color = "#2A2E45"  # Muted slate blue for past weeks
        self.current_week_color = "#4F46E5"  # Bright royal blue to signify the current week
        self.future_week_color = "#264653"  # Teal blue for future weeks

        self.initUI()  # Initialize the UI
        self.load_colors()  # Load saved colors (if any)

        # Apply dark theme if system is using dark mode
        if darkdetect.isDark():
            self.apply_dark_theme()

        self.current_tags = []

    def apply_dark_theme(self):
        """Apply dark theme to the application."""
        dark_stylesheet = get_dark_stylesheet()
        self.setStyleSheet(dark_stylesheet)

    def load_colors(self):
        """Load color configuration from settings file."""
        try:
            colors = load_colors()
            self.calendar.setStyleSheet(f"background-color: {colors['calendar_color']};")
            self.past_week_color = colors.get("past_week_color", "#E0E0E0")
            self.current_week_color = colors.get("current_week_color", "#FFEBCC")
            self.future_week_color = colors.get("future_week_color", "#FFFFFF")
            self.weekly_planner_color = colors.get("weekly_planner_color", "#FFFFFF")
        except Exception as e:
            print(f"Error loading colors: {e}")
            # Use default colors

    def save_colors(self):
        """Save color configuration to settings file."""
        colors = {
            "calendar_color": self.calendar.palette().color(self.calendar.backgroundRole()).name(),
            "past_week_color": self.past_week_color,
            "current_week_color": self.current_week_color,
            "future_week_color": self.future_week_color,
            "weekly_planner_color": self.weekly_planner_color
        }
        save_colors(colors)

    def initUI(self):
        """Initialize the user interface components."""
        self.setWindowTitle('Smart Scheduler')
        self.setGeometry(100, 100, 1200, 800)  # Set a reasonable default size for the main window

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create a main splitter for the calendar/week table and the tabs
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(5)

        # Create a splitter for the calendar and week table
        calendar_week_splitter = QSplitter(Qt.Vertical)
        calendar_week_splitter.setHandleWidth(5)  # Set handle width for better aesthetics

        self.calendar = CustomCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setFirstDayOfWeek(Qt.Monday)  # Ensure the calendar starts the week on Monday
        self.calendar.clicked.connect(self.open_daily_planner)
        self.calendar.currentPageChanged.connect(self.update_week_list)  # Update weeks list when month/year changes
        self.calendar.setStyleSheet("background-color: #E6E6FA;")  # Set background color

        self.week_table_widget = QTableWidget()
        self.week_table_widget.setColumnCount(3)
        self.week_table_widget.setHorizontalHeaderLabels(["Week Number", "Week Range", "Weeks Since Birth"])
        self.week_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.week_table_widget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.week_table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.week_table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.week_table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.week_table_widget.itemClicked.connect(self.on_week_selected)
        self.week_table_widget.setStyleSheet("background-color: #C1E1C1;")  # Set background color

        calendar_week_splitter.addWidget(self.calendar)
        calendar_week_splitter.addWidget(self.week_table_widget)
        calendar_week_splitter.setSizes([300, 300])  # Set initial sizes to be square

        main_splitter.addWidget(calendar_week_splitter)
        self.tab_widget = QTabWidget()
        main_splitter.addWidget(self.tab_widget)
        
        # Set initial sizes proportionally
        main_splitter.setStretchFactor(0, 3)  # Calendar and week table take 30% of the space
        main_splitter.setStretchFactor(1, 7)  # Tab widget takes 70% of the space

        main_layout.addWidget(main_splitter)

        self.add_goals_tab()
        self.add_habits_tab()
        self.add_productivity_tab()
        self.add_pomodoro_tab()
        self.add_visualization_tab()
        self.add_goal_list_tab()

        self.create_menu_bar()

        # Populate weeks list for the current year and month
        self.update_week_list(self.calendar.yearShown(), self.calendar.monthShown())

    def save_birth_date(self):
        """Save the user's birth date to a file."""
        birth_date = self.birth_date_edit.date().toString("yyyy-MM-dd")
        with open("birth_date.txt", "w") as file:
            file.write(birth_date)
        QMessageBox.information(self, "Saved", "Birth date saved successfully.")
        self.update_week_list(self.calendar.yearShown(), self.calendar.monthShown())

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')

        import_action = QAction('Import Plan', self)
        import_action.triggered.connect(self.import_plan)
        file_menu.addAction(import_action)

        move_dates_action = QAction('Move All Goal Dates', self)
        move_dates_action.triggered.connect(self.open_move_dates_dialog)
        file_menu.addAction(move_dates_action)

        birth_date_action = QAction('Set Birth Date', self)
        birth_date_action.triggered.connect(self.show_birth_date_dialog)
        file_menu.addAction(birth_date_action)

        color_menu = QMenu('Set Colors', self)

        calendar_color_action = QAction('Calendar Color', self)
        calendar_color_action.triggered.connect(self.choose_calendar_color)
        color_menu.addAction(calendar_color_action)

        past_week_color_action = QAction('Past Week Color', self)
        past_week_color_action.triggered.connect(lambda: self.choose_week_color('past'))
        color_menu.addAction(past_week_color_action)

        current_week_color_action = QAction('Current Week Color', self)
        current_week_color_action.triggered.connect(lambda: self.choose_week_color('current'))
        color_menu.addAction(current_week_color_action)

        future_week_color_action = QAction('Future Week Color', self)
        future_week_color_action.triggered.connect(lambda: self.choose_week_color('future'))
        color_menu.addAction(future_week_color_action)

        weekly_planner_color_action = QAction('Weekly Planner Color', self)
        weekly_planner_color_action.triggered.connect(lambda: self.choose_week_color('weekly_planner'))
        color_menu.addAction(weekly_planner_color_action)

        file_menu.addMenu(color_menu)

    def choose_calendar_color(self):
        """Allow user to choose calendar background color."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.calendar.setStyleSheet(f"background-color: {color.name()};")
            self.save_colors()

    def choose_week_color(self, week_type):
        """Allow user to choose colors for different week types."""
        color = QColorDialog.getColor()
        if color.isValid():
            if week_type == 'past':
                self.past_week_color = color.name()
            elif week_type == 'current':
                self.current_week_color = color.name()
            elif week_type == 'future':
                self.future_week_color = color.name()
            elif week_type == 'weekly_planner':
                self.weekly_planner_color = color.name()
            self.update_week_list(self.calendar.yearShown(), self.calendar.monthShown())
            self.save_colors()

    def show_birth_date_dialog(self):
        """Show dialog to set birth date."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Birth Date")
        layout = QVBoxLayout(dialog)

        birth_date_layout = QHBoxLayout()
        birth_date_label = QLabel("Enter your birth date:")
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDisplayFormat("yyyy-MM-dd")
        birth_date_layout.addWidget(birth_date_label)
        birth_date_layout.addWidget(self.birth_date_edit)

        save_birth_date_button = QPushButton("Save Birth Date")
        save_birth_date_button.clicked.connect(lambda: self.save_birth_date_dialog(dialog))
        birth_date_layout.addWidget(save_birth_date_button)

        layout.addLayout(birth_date_layout)

        dialog.exec_()

    def save_birth_date_dialog(self, dialog):
        """Save birth date and close dialog."""
        self.save_birth_date()
        dialog.accept()

    def update_week_list(self, year, month):
        """Update the weeks list for the given year."""
        self.week_table_widget.clearContents()
        self.week_table_widget.setRowCount(0)
        weeks = self.calculate_weeks(year)

        try:
            with open("birth_date.txt", "r") as file:
                birth_date = file.read().strip()
        except FileNotFoundError:
            birth_date = "1990-01-01"  # Default date if the file is not found

        weeks_since_birth = calculate_weeks_since_birth(birth_date)

        today = QDate.currentDate()

        for i, (start_date, end_date) in enumerate(weeks):
            weeks_since_birth_for_week = weeks_since_birth + i
            week_number_item = QTableWidgetItem(f"Week {i + 1}")
            week_range_item = QTableWidgetItem(f"{start_date.toString('MMM d')} - {end_date.toString('MMM d')}")
            weeks_since_birth_item = QTableWidgetItem(str(weeks_since_birth_for_week))

            if start_date <= today <= end_date:
                # Highlight the current week
                color = QColor(self.current_week_color)  # Light peach background for current week
            elif end_date < today:
                # Color past weeks
                color = QColor(self.past_week_color)
            else:
                # Future weeks stay default
                color = QColor(self.future_week_color)

            week_number_item.setBackground(color)
            week_range_item.setBackground(color)
            weeks_since_birth_item.setBackground(color)

            row_position = self.week_table_widget.rowCount()
            self.week_table_widget.insertRow(row_position)
            self.week_table_widget.setItem(row_position, 0, week_number_item)
            self.week_table_widget.setItem(row_position, 1, week_range_item)
            self.week_table_widget.setItem(row_position, 2, weeks_since_birth_item)
            self.week_table_widget.item(row_position, 0).setData(Qt.UserRole, start_date)

    def on_week_selected(self, item):
        """Handle week selection in the week table."""
        row = self.week_table_widget.currentRow()
        start_date = self.week_table_widget.item(row, 0).data(Qt.UserRole)
        self.open_weekly_planner(start_date)

    def calculate_weeks(self, year):
        """Calculate the weeks for a given year."""
        # Start from the first day of the year
        first_day = QDate(year, 1, 1)
        # Adjust the first day to the start of the first week
        if first_day.dayOfWeek() != Qt.Monday:
            first_day = first_day.addDays(-(first_day.dayOfWeek() - Qt.Monday))

        weeks = []
        current_day = first_day
        while current_day.year() == year or (current_day.addDays(6).year() == year):
            end_day = current_day.addDays(6)
            weeks.append((current_day, end_day))
            current_day = end_day.addDays(1)

        return weeks

    def open_daily_planner(self):
        """Open the daily planner for the selected date."""
        selected_date = self.calendar.selectedDate().toPyDate()
        self.daily_planner = DailyPlanner(self, selected_date)
        self.daily_planner.show()

    def open_weekly_planner(self, start_of_week):
        """Open the weekly planner for the selected week."""
        self.weekly_planner = WeeklyPlanner(self, start_of_week)
        self.weekly_planner.show()

    def import_plan(self):
        """Import a plan from a JSON file."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Plan", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            with open(file_path, 'r') as file:
                plan_data = json.load(file)
                self.process_imported_plan(plan_data)

    def process_imported_plan(self, plan_data):
        """Process imported plan data."""
        for goal in plan_data.get("goals", []):
            self.add_imported_goal(goal)
        for habit in plan_data.get("habits", []):
            self.add_imported_habit(habit)
        for note in plan_data.get("daily_notes", []):
            self.add_imported_daily_note(note)
        for week_task in plan_data.get("weekly_tasks", []):
            self.add_imported_weekly_task(week_task)
        self.populate_daily_planner_with_habits()
        self.populate_daily_planner_with_goals()

    # The remainder of the SmartScheduler methods would be implemented here,
    # following the same patterns shown above. 