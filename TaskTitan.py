# Include necessary imports
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCalendarWidget, 
    QTreeWidget, QTreeWidgetItem, QHeaderView, QLabel, QLineEdit, QComboBox, 
    QDateEdit, QTimeEdit, QMessageBox, QCheckBox, QDialog, QDialogButtonBox, 
    QTabWidget, QScrollArea, QTableWidget, QAbstractItemView, QFileDialog, 
    QInputDialog, QTableWidgetItem, QProgressBar, QPushButton, QTextEdit, QAction, 
    QMenu, QFormLayout, QListWidget, QListWidgetItem, QSizePolicy, QSplitter, QColorDialog,QPlainTextEdit , QGridLayout,QInputDialog
)
from PyQt5.QtCore import QDate, Qt, QTimer, QTime, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QColor, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import winsound
import os
import darkdetect


def initialize_db():
    conn = sqlite3.connect("planner.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
                   
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER,
            title TEXT NOT NULL,
            due_date DATE,
            due_time TIME,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER,
            description TEXT NOT NULL,
            duration_minutes INTEGER,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER,
            week_start_date DATE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            due_date DATE,
            due_time TIME,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (parent_id) REFERENCES weekly_tasks(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time TEXT NOT NULL,
            days_of_week TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            time TEXT NOT NULL,
            description TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'event',
            completed INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_notes (
            date DATE PRIMARY KEY,
            note TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productivity_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_title TEXT NOT NULL,
            date DATE,
            start_time TIME,
            end_time TIME,
            duration_minutes INTEGER,
            distractions INTEGER DEFAULT 0,
            tag TEXT
        )
    """)
    
    # Update the schema for weekly_tasks
    update_database_schema(cursor)
    
    conn.commit()
    return conn, cursor

def update_database_schema(cursor):
    try:
        cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN parent_id INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN title TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN description TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN due_date DATE")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE weekly_tasks ADD COLUMN due_time TIME")
    except sqlite3.OperationalError:
        pass  # Column already exists

def calculate_weeks_since_birth(birth_date):
    birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
    today = datetime.today()
    delta = today - birth_date
    weeks_since_birth = delta.days // 7
    return weeks_since_birth

def validate_time(time_str):
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def load_colors(self):
    try:
        with open("colors_config.json", "r") as file:
            colors = json.load(file)
            self.calendar.setStyleSheet(f"background-color: {colors['calendar_color']};")
            self.past_week_color = colors.get("past_week_color", "#E0E0E0")
            self.current_week_color = colors.get("current_week_color", "#FFEBCC")
            self.future_week_color = colors.get("future_week_color", "#FFFFFF")
    except FileNotFoundError:
        pass  # File not found, use default colors

class CustomCalendarWidget(QCalendarWidget):
    weekNumberClicked = pyqtSignal(int, QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFirstDayOfWeek(Qt.Monday)  # Set the first day of the week to Monday

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.mapFromGlobal(event.globalPos())
            if pos.x() < 40:  # Assuming the week number column is within the first 40 pixels
                date = self.dateAt(pos)
                week_number = self.calculate_week_number(date)
                self.weekNumberClicked.emit(week_number, date)
            else:
                super().mousePressEvent(event)

    def calculate_week_number(self, date):
        year_start = QDate(date.year(), 1, 1)
        while year_start.dayOfWeek() != Qt.Monday:
            year_start = year_start.addDays(-1)
        days_since_year_start = year_start.daysTo(date)
        week_number = (days_since_year_start // 7) + 1
        return week_number

    def dateAt(self, pos):
        col = pos.x() // self.cellWidth()
        row = pos.y() // self.cellHeight()
        return self.dateForCell(row, col)

    def cellWidth(self):
        return self.width() // 7

    def cellHeight(self):
        return self.height() // 6

    def dateForCell(self, row, col):
        first_date = QDate(self.yearShown(), self.monthShown(), 1)
        while first_date.dayOfWeek() != Qt.Monday:
            first_date = first_date.addDays(-1)
        return first_date.addDays(row * 7 + col)



class SmartScheduler(QMainWindow):
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
        """
        Applies a sophisticated, modern, and user-friendly dark theme with elegant purple and warm orange accents.
        Enhances UI interactions with refined color choices for a vibrant and visually appealing interface.
        """
        dark_stylesheet = """
        /* General Window and Dialog Background */
        QMainWindow, QDialog {
            background-color: #121212;  /* Deep charcoal for a sleek backdrop */
            color: #E0E0E0;             /* Soft white for high readability */
            font-family: 'Segoe UI', sans-serif;  /* Modern and clean font */
            font-size: 14px;
        }

        /* All Widgets */
        QWidget {
            background-color: #1E1E1E;  /* Slightly lighter than main window for contrast */
            color: #E0E0E0;
            border: none;
            padding: 0px;
            margin: 0px;
        }

        /* Input Fields */
        QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox {
            background-color: #2C2C2C;  /* Dark grey for input backgrounds */
            color: #FFFFFF;
            padding: 8px;
            border-radius: 6px;
            border: 1px solid #555555;
        }
        QLineEdit:hover, QPlainTextEdit:hover, QTextEdit:hover, QComboBox:hover, QDateEdit:hover, QTimeEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {
            background-color: #383838;  /* Slightly lighter on hover */
            border-color: #BB86FC;      /* Elegant purple accent on hover */
        }

        /* Tables and Tree Widgets */
        QTreeWidget, QTableWidget, QTreeView {
            background-color: #252525;  /* Darker background for table elements */
            color: #E0E0E0;
            alternate-background-color: #303030;  /* Alternating row colors for readability */
            border-radius: 8px;
            padding: 4px;
        }
        QHeaderView::section {
            background-color: #3C3C3C;  /* Header background with purple tint */
            color: #FFFFFF;
            padding: 8px;
            border: none;
            font-weight: bold;
        }

        /* Buttons */
        QPushButton {
            background-color: #BB86FC;  /* Elegant purple */
            color: #000000;
            padding: 10px 20px;
            border-radius: 8px;
            border: none;
            transition: background-color 0.3s ease, transform 0.2s ease;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #9A67EA;  /* Slightly darker purple on hover */
            transform: scale(1.05);     /* Subtle grow effect */
        }
        QPushButton:pressed {
            background-color: #7B4AED;  /* Even darker purple when pressed */
        }

        /* Labels */
        QLabel {
            color: #E0E0E0;
            font-weight: 500;
        }

        /* Tabs */
        QTabWidget::pane {
            background-color: #1E1E1E;
            border: none;
        }
        QTabBar::tab {
            background-color: #2C2C2C;
            color: #E0E0E0;
            padding: 10px 20px;
            border-radius: 6px;
            margin: 2px;
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        QTabBar::tab:selected {
            background-color: #BB86FC;  /* Purple highlight for selected tab */
            color: #000000;
        }
        QTabBar::tab:hover {
            background-color: #3C3C3C;
        }

        /* Menu Bar */
        QMenuBar {
            background-color: #1E1E1E;
            color: #E0E0E0;
            border: none;
        }
        QMenuBar::item:selected {
            background-color: #3C3C3C;
        }
        QMenu {
            background-color: #2C2C2C;
            color: #E0E0E0;
            border-radius: 6px;
        }
        QMenu::item:selected {
            background-color: #BB86FC;
            color: #000000;
        }

        /* Progress Bar */
        QProgressBar {
            background-color: #2C2C2C;
            color: #BB86FC;
            border: none;
            border-radius: 6px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #BB86FC;  /* Purple chunks */
            border-radius: 6px;
        }

        /* Checkboxes */
        QCheckBox {
            color: #E0E0E0;
        }

        /* Scroll Areas */
        QScrollArea {
            background-color: #1E1E1E;
            border: none;
        }

        /* List Widgets and Scroll Bars */
        QListWidget, QScrollBar {
            background-color: #2C2C2C;
            color: #E0E0E0;
            border-radius: 6px;
        }
        QScrollBar:horizontal, QScrollBar:vertical {
            background-color: #1E1E1E;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
            background-color: #BB86FC;  /* Purple handles */
            border-radius: 4px;
        }
        QScrollBar::add-line, QScrollBar::sub-line {
            background-color: #BB86FC;
            border-radius: 4px;
        }
        QScrollBar::add-page, QScrollBar::sub-page {
            background-color: #1E1E1E;
        }

        /* Calendar Widget */
    QCalendarWidget {
        background-color: #1E1E1E; /* Deep dark background for the calendar */
        color: #000000;           /* Default text color for calendar elements set to black */
        border: none;
        font-size: 14px;
    }
    QCalendarWidget QAbstractItemView {
        background-color: #2C2C2C;               /* Slightly lighter background for dates */
        selection-background-color: #FF7043;    /* Vibrant orange for selected dates */
        color: #000000;                         /* Black text for default and selected dates */
        selection-color: #000000;               /* Ensure selected date text is also black */
        gridline-color: #FFA726;                /* Subtle orange for gridlines */
    }
    QCalendarWidget QAbstractItemView::item {
        color: #000000;                         /* Default text color for dates */
        padding: 4px;                           /* Add spacing for readability */
    }

    /* Weekday Column Backgrounds (Monday to Sunday) */
    QCalendarWidget QTableView {
        alternate-background-color: #2E2E2E;   /* Alternating row colors */
        gridline-color: #FFA726;                /* Subtle orange for gridlines */
    }
    QCalendarWidget QTableView::item:enabled {
        background-color: #E0F7FA;             /* Light bluish background for enabled weekdays */
        color: #000000;                        /* Black text for visibility */
    }
    QCalendarWidget QTableView::item:enabled:alternate {
        background-color: #B2EBF2;             /* Slightly darker bluish background for alternating rows */
    }

    /* Navigation Buttons */
    QCalendarWidget QToolButton {
        background-color: #FF7043;             /* Warm orange for navigation buttons */
        color: #000000;                        /* Black text for contrast */
        border-radius: 6px;                    /* Rounded buttons for modern design */
        padding: 4px;                          /* Comfortable padding */
        font-weight: bold;                     /* Bold text for visibility */
    }
    QCalendarWidget QToolButton:hover {
        background-color: #FF5722;             /* Darker orange on hover for interactivity */
    }

    /* Spin Box in Calendar */
    QCalendarWidget QSpinBox {
        background-color: #2C2C2C;             /* Dark grey for spin box */
        color: #000000;                        /* Black text for readability */
        border-radius: 6px;                    /* Rounded corners */
        padding: 4px;                          /* Padding for better spacing */
    }

    /* Header (Day Names) */
    QCalendarWidget QHeaderView {
        background-color: #4DD0E1;             /* Bright bluish header background */
        color: #000000;                        /* Black text for contrast */
        border: none;                          /* Clean header look without borders */
    }


        """
        # Apply the dark theme stylesheet to the entire application
        self.setStyleSheet(dark_stylesheet)

    def load_colors(self):
        try:
            with open("colors_config.json", "r") as file:
                colors = json.load(file)
                self.calendar.setStyleSheet(f"background-color: {colors['calendar_color']};")
                self.past_week_color = colors.get("past_week_color", "#E0E0E0")
                self.current_week_color = colors.get("current_week_color", "#FFEBCC")
                self.future_week_color = colors.get("future_week_color", "#FFFFFF")
                self.weekly_planner_color = colors.get("weekly_planner_color", "#FFFFFF")
        except FileNotFoundError:
            pass  # File not found, use default colors

    def save_colors(self):
        colors = {
            "calendar_color": self.calendar.palette().color(self.calendar.backgroundRole()).name(),
            "past_week_color": self.past_week_color,
            "current_week_color": self.current_week_color,
            "future_week_color": self.future_week_color,
            "weekly_planner_color": self.weekly_planner_color
        }
        with open("colors_config.json", "w") as file:
            json.dump(colors, file)


            
    def initUI(self):
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
        birth_date = self.birth_date_edit.date().toString("yyyy-MM-dd")
        with open("birth_date.txt", "w") as file:
            file.write(birth_date)
        QMessageBox.information(self, "Saved", "Birth date saved successfully.")
        self.update_week_list(self.calendar.yearShown(), self.calendar.monthShown())

    def create_menu_bar(self):
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
        color = QColorDialog.getColor()
        if color.isValid():
            self.calendar.setStyleSheet(f"background-color: {color.name()};")
            self.save_colors()

    def choose_week_color(self, week_type):
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
        self.save_birth_date()
        dialog.accept()

    def add_goals_tab(self):
        goals_frame = QWidget()
        layout = QVBoxLayout()
        goals_frame.setLayout(layout)

        form_layout = QHBoxLayout()
        layout.addLayout(form_layout)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Goal Title")
        form_layout.addWidget(self.title_edit)

        self.parent_combobox = QComboBox()
        self.parent_combobox.setPlaceholderText("Select Parent Goal")
        form_layout.addWidget(self.parent_combobox)

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        form_layout.addWidget(self.due_date_edit)

        self.due_time_edit = QTimeEdit()
        form_layout.addWidget(self.due_time_edit)

        add_button = QPushButton('Add Goal')
        add_button.clicked.connect(self.add_goal)
        form_layout.addWidget(add_button)

        self.goals_tree = QTreeWidget()
        self.goals_tree.setColumnCount(6)
        self.goals_tree.setHeaderLabels(['ID', 'Title', 'Due Date', 'Due Time', 'Days Left', 'Completed'])
        self.goals_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.goals_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.goals_tree.customContextMenuRequested.connect(self.open_goal_context_menu)
        layout.addWidget(self.goals_tree)

        self.populate_goals()

        self.tab_widget.addTab(goals_frame, "Goals")

    def populate_goals(self):
        self.goals_tree.clear()
        self.parent_combobox.clear()
        self.cursor.execute("SELECT id, parent_id, title, due_date, due_time, completed FROM goals ORDER BY parent_id, id")
        goals = self.cursor.fetchall()
        goals_dict = {goal[0]: goal for goal in goals}
        root_goals = [goal for goal in goals if goal[1] is None]

        self.parent_combobox.addItem("No Parent", None)
        for goal in goals:
            self.parent_combobox.addItem(goal[2], goal[0])

        def add_goal_to_tree(goal, parent_item=None):
            goal_id, parent_id, title, due_date, due_time, completed = goal
            days_left = (datetime.strptime(due_date, "%Y-%m-%d").date() - datetime.now().date()).days
            goal_item = QTreeWidgetItem([str(goal_id), title, due_date, due_time or '', str(days_left), ''])
            goal_item.setFlags(goal_item.flags() | Qt.ItemIsUserCheckable)  # Make the item checkable
            goal_item.setCheckState(5, Qt.Checked if completed else Qt.Unchecked)  # Set the initial state of the checkbox
            goal_item.setData(5, Qt.UserRole, completed)  # Store completed state in user data

            if parent_item:
                parent_item.addChild(goal_item)
            else:
                self.goals_tree.addTopLevelItem(goal_item)

            child_goals = [g for g in goals if g[1] == goal_id]
            for child in child_goals:
                add_goal_to_tree(child, goal_item)

        for root_goal in root_goals:
            add_goal_to_tree(root_goal)

        # Connect the itemChanged signal to save the state when a checkbox is clicked
        self.goals_tree.itemChanged.connect(self.update_goal_completion)

    def update_goal_completion(self, item, column):
        if column == 5:  # If the "Completed" column is changed
            goal_id = int(item.text(0))
            completed = item.checkState(5) == Qt.Checked
            self.cursor.execute("UPDATE goals SET completed = ? WHERE id = ?", (completed, goal_id))
            self.conn.commit()

    def open_move_goal_dialog(self, goal_id):
        days, ok = QInputDialog.getInt(self, "Move Goal", "Enter number of days to move:", 0, -365, 365)
        if ok:
            self.move_goal_dates(goal_id, days)

    def move_goal_dates(self, goal_id, days):
        self.cursor.execute("SELECT id, due_date FROM goals WHERE id = ?", (goal_id,))
        goal = self.cursor.fetchone()
        if goal:
            goal_id, due_date = goal
            new_due_date = datetime.strptime(due_date, "%Y-%m-%d") + timedelta(days=days)
            self.cursor.execute("UPDATE goals SET due_date = ? WHERE id = ?", (new_due_date.strftime("%Y-%m-%d"), goal_id))
            self.conn.commit()
            self.move_child_goals_dates(goal_id, days)
            self.populate_goals()
            self.populate_daily_planner_with_goals()

    def move_child_goals_dates(self, parent_id, days):
        self.cursor.execute("SELECT id, due_date FROM goals WHERE parent_id = ?", (parent_id,))
        child_goals = self.cursor.fetchall()
        for child_goal in child_goals:
            child_goal_id, child_due_date = child_goal
            new_due_date = datetime.strptime(child_due_date, "%Y-%m-%d") + timedelta(days=days)
            self.cursor.execute("UPDATE goals SET due_date = ? WHERE id = ?", (new_due_date.strftime("%Y-%m-%d"), child_goal_id))
            self.conn.commit()
            self.move_child_goals_dates(child_goal_id, days)  # Recursively move child goals



    def open_goal_context_menu(self, position):
        item = self.goals_tree.itemAt(position)
        if item:
            goal_id = int(item.text(0))
            menu = QMenu()

            edit_action = QAction('Edit', self)
            edit_action.triggered.connect(lambda: self.open_edit_goal_dialog(goal_id))
            menu.addAction(edit_action)

            delete_action = QAction('Delete', self)
            delete_action.triggered.connect(lambda: self.delete_goal(goal_id))
            menu.addAction(delete_action)

            # Add the move action
            move_action = QAction('Move Goal', self)
            move_action.triggered.connect(lambda: self.open_move_goal_dialog(goal_id))
            menu.addAction(move_action)

            menu.exec_(self.goals_tree.viewport().mapToGlobal(position))

    def open_move_goal_dialog(self, goal_id):
        days, ok = QInputDialog.getInt(self, "Move Goal", "Enter number of days to move:", 0, -365, 365)
        if ok:
            self.move_goal_dates(goal_id, days)

    def move_goal_dates(self, goal_id, days):
        self.cursor.execute("SELECT id, due_date FROM goals WHERE id = ?", (goal_id,))
        goal = self.cursor.fetchone()
        if goal:
            goal_id, due_date = goal
            new_due_date = datetime.strptime(due_date, "%Y-%m-%d") + timedelta(days=days)
            self.cursor.execute("UPDATE goals SET due_date = ? WHERE id = ?", (new_due_date.strftime("%Y-%m-%d"), goal_id))
            self.conn.commit()
            self.move_child_goals_dates(goal_id, days)
            self.populate_goals()
            self.populate_daily_planner_with_goals()

    def move_child_goals_dates(self, parent_id, days):
        self.cursor.execute("SELECT id, due_date FROM goals WHERE parent_id = ?", (parent_id,))
        child_goals = self.cursor.fetchall()
        for child_goal in child_goals:
            child_goal_id, child_due_date = child_goal
            new_due_date = datetime.strptime(child_due_date, "%Y-%m-%d") + timedelta(days=days)
            self.cursor.execute("UPDATE goals SET due_date = ? WHERE id = ?", (new_due_date.strftime("%Y-%m-%d"), child_goal_id))
            self.conn.commit()
            self.move_child_goals_dates(child_goal_id, days)  # Recursively move child goals



    def add_goal(self):
        title = self.title_edit.text().strip()
        due_date = self.due_date_edit.date().toString("yyyy-MM-dd")
        due_time = self.due_time_edit.time().toString("HH:mm")
        if not title or not validate_time(due_time):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid title and time.")
            return

        parent_id = self.parent_combobox.currentData()
        self.cursor.execute("INSERT INTO goals (parent_id, title, due_date, due_time, completed) VALUES (?, ?, ?, ?, 0)",
                            (parent_id, title, due_date, due_time))
        self.conn.commit()
        self.populate_goals()
        self.populate_daily_planner_with_goals()

    def open_edit_goal_dialog(self, goal_id):
        self.cursor.execute("SELECT id, parent_id, title, due_date, due_time, completed FROM goals WHERE id = ?", (goal_id,))
        goal = self.cursor.fetchone()
        if not goal:
            QMessageBox.warning(self, "Invalid Goal", "Goal not found.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Goal")
        layout = QVBoxLayout(dialog)

        title_edit = QLineEdit(dialog)
        title_edit.setText(goal[2])
        layout.addWidget(title_edit)

        parent_combobox = QComboBox(dialog)
        parent_combobox.addItem("No Parent", None)
        self.cursor.execute("SELECT id, title FROM goals WHERE id != ?", (goal_id,))
        other_goals = self.cursor.fetchall()
        for other_goal in other_goals:
            parent_combobox.addItem(other_goal[1], other_goal[0])
        parent_combobox.setCurrentIndex(parent_combobox.findData(goal[1]))
        layout.addWidget(parent_combobox)

        due_date_edit = QDateEdit(dialog)
        due_date_edit.setDate(QDate.fromString(goal[3], "yyyy-MM-dd"))
        layout.addWidget(due_date_edit)

        due_time_edit = QTimeEdit(dialog)
        due_time_edit.setTime(QTime.fromString(goal[4], "HH:mm"))
        layout.addWidget(due_time_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        button_box.accepted.connect(lambda: self.edit_goal(goal_id, title_edit.text(), parent_combobox.currentData(), due_date_edit.date(), due_time_edit.time()))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def edit_goal(self, goal_id, title, parent_id, due_date, due_time):
        due_date_str = due_date.toString("yyyy-MM-dd")
        due_time_str = due_time.toString("HH:mm")
        if not title or not validate_time(due_time_str):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid title and time.")
            return

        self.cursor.execute("UPDATE goals SET parent_id = ?, title = ?, due_date = ?, due_time = ? WHERE id = ?",
                            (parent_id, title, due_date_str, due_time_str, goal_id))
        self.conn.commit()
        self.populate_goals()
        self.populate_daily_planner_with_goals()

    def delete_goal(self, goal_id):
        self.cursor.execute("SELECT title FROM goals WHERE id = ?", (goal_id,))
        goal = self.cursor.fetchone()
        if goal:
            title = goal[0]
            self.delete_goal_recursive(goal_id)
            self.conn.commit()
            self.populate_goals()
            self.populate_daily_planner_with_goals()

    def delete_goal_recursive(self, goal_id):
        self.cursor.execute("SELECT id FROM goals WHERE parent_id = ?", (goal_id,))
        sub_goals = self.cursor.fetchall()
        for sub_goal in sub_goals:
            self.delete_goal_recursive(sub_goal[0])

        self.cursor.execute("SELECT title FROM goals WHERE id = ?", (goal_id,))
        goal = self.cursor.fetchone()
        if goal:
            title = goal[0]
            self.cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
            self.cursor.execute("DELETE FROM events WHERE description = ? AND type = 'goal'", (title,))

    def open_move_dates_dialog(self):
        days, ok = QInputDialog.getInt(self, "Move All Goal Dates", "Enter number of days to move:", 0, -365, 365)
        if ok:
            self.move_all_goal_dates(days)

    def move_all_goal_dates(self, days):
        self.cursor.execute("SELECT id, due_date FROM goals")
        goals = self.cursor.fetchall()

        for goal in goals:
            goal_id, due_date = goal
            new_due_date = datetime.strptime(due_date, "%Y-%m-%d") + timedelta(days=days)
            self.cursor.execute("UPDATE goals SET due_date = ? WHERE id = ?", (new_due_date.strftime("%Y-%m-%d"), goal_id))

        self.conn.commit()
        self.populate_goals()
        self.populate_daily_planner_with_goals()

    def add_habits_tab(self):
        habits_frame = QWidget()
        layout = QVBoxLayout()
        habits_frame.setLayout(layout)

        form_layout = QHBoxLayout()
        layout.addLayout(form_layout)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Habit Name")
        form_layout.addWidget(self.name_edit)

        self.time_edit = QTimeEdit()
        form_layout.addWidget(self.time_edit)

        self.days_list = QHBoxLayout()
        self.days_checkboxes = []
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days:
            checkbox = QCheckBox(day)
            self.days_list.addWidget(checkbox)
            self.days_checkboxes.append(checkbox)
        form_layout.addLayout(self.days_list)

        add_button = QPushButton('Add Habit')
        add_button.clicked.connect(self.add_habit)
        form_layout.addWidget(add_button)

        self.habit_list = QTableWidget()
        self.habit_list.setColumnCount(5)
        self.habit_list.setHorizontalHeaderLabels(['ID', 'Name', 'Time', 'Days', ''])
        self.habit_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.habit_list)

        self.populate_habits()

        self.tab_widget.addTab(habits_frame, "Habits")

    def populate_habits(self):
        self.habit_list.clearContents()
        self.cursor.execute("SELECT id, name, time, days_of_week FROM habits")
        habits = self.cursor.fetchall()
        self.habit_list.setRowCount(len(habits))
        for i, habit in enumerate(habits):
            for j, val in enumerate(habit):
                self.habit_list.setItem(i, j, QTableWidgetItem(str(val)))
            delete_button = QPushButton('Delete')
            delete_button.clicked.connect(lambda _, id=habit[0]: self.delete_habit(id))
            self.habit_list.setCellWidget(i, 4, delete_button)
        self.populate_daily_planner_with_habits()

    def add_habit(self):
        name = self.name_edit.text().strip()
        time = self.time_edit.time().toString("HH:mm")
        selected_days = [checkbox.text() for checkbox in self.days_checkboxes if checkbox.isChecked()]
        days_str = ','.join(selected_days)
        if not name or not validate_time(time):
            QMessageBox.warning(self, "Invalid Input", "Please enter valid name and time.")
            return
        self.cursor.execute("INSERT INTO habits (name, time, days_of_week) VALUES (?, ?, ?)", (name, time, days_str))
        self.conn.commit()
        self.populate_habits()
        self.populate_daily_planner_with_habits()

    def delete_habit(self, habit_id):
        self.cursor.execute("SELECT name FROM habits WHERE id = ?", (habit_id,))
        habit = self.cursor.fetchone()
        if habit:
            name = habit[0]
            self.cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
            self.conn.commit()
            self.cursor.execute("DELETE FROM events WHERE description = ? AND type = 'habit'", (name,))
            self.conn.commit()
            self.populate_habits()

    def populate_daily_planner_with_habits(self):
        self.cursor.execute("DELETE FROM events WHERE type = 'habit'")
        self.cursor.execute("SELECT id, name, time, days_of_week FROM habits")
        habits = self.cursor.fetchall()
        today = datetime.now().date()
        for habit in habits:
            habit_id, name, time, days_of_week = habit
            days = days_of_week.split(',')
            for day in days:
                day_index = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(day)
                habit_date = today + timedelta((day_index - today.weekday()) % 7)
                self.cursor.execute("""
                    INSERT OR IGNORE INTO events (date, time, description, type, completed)
                    VALUES (?, ?, ?, 'habit', 0)
                """, (habit_date.isoformat(), time, name))
        self.conn.commit()

    def populate_daily_planner_with_goals(self):
        self.cursor.execute("DELETE FROM events WHERE type = 'goal'")
        self.cursor.execute("SELECT id, title, due_date, due_time FROM goals WHERE completed = 0")
        goals = self.cursor.fetchall()
        for goal in goals:
            goal_id, title, due_date, due_time = goal
            self.cursor.execute("INSERT OR IGNORE INTO events (date, time, description, type, completed) VALUES (?, ?, ?, 'goal', 0)",
                                (due_date, due_time, title))
        self.conn.commit()

    def open_daily_planner(self):
        selected_date = self.calendar.selectedDate().toPyDate()
        self.daily_planner = DailyPlanner(self, selected_date)
        self.daily_planner.show()

    def import_plan(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Plan", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            with open(file_path, 'r') as file:
                plan_data = json.load(file)
                self.process_imported_plan(plan_data)

    def process_imported_plan(self, plan_data):
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

    def add_imported_goal(self, goal, parent_id=None):
        title = goal['title']
        due_date = goal['due_date']
        due_time = goal.get('due_time', None)
        self.cursor.execute("INSERT INTO goals (parent_id, title, due_date, due_time, completed) VALUES (?, ?, ?, ?, 0)",
                            (parent_id, title, due_date, due_time))
        goal_id = self.cursor.lastrowid
        for sub_goal in goal.get('sub_goals', []):
            self.add_imported_goal(sub_goal, goal_id)
        for task in goal.get('tasks', []):
            self.cursor.execute("INSERT INTO tasks (goal_id, description, duration_minutes, completed) VALUES (?, ?, ?, 0)",
                                (goal_id, task['task'], task.get('duration_minutes', 0)))
        self.conn.commit()
        self.populate_goals()
        self.populate_daily_planner_with_goals()

    def add_imported_habit(self, habit):
        name = habit['name']
        time = habit['time']
        days = habit['days_of_week']
        self.cursor.execute("INSERT INTO habits (name, time, days_of_week) VALUES (?, ?, ?)", (name, time, days))
        self.conn.commit()
        self.populate_habits()
        self.populate_daily_planner_with_habits()

    def add_imported_daily_note(self, note):
        date = note['date']
        content = note['note']
        self.cursor.execute("REPLACE INTO daily_notes (date, note) VALUES (?, ?)", (date, content))
        self.conn.commit()

    def add_imported_weekly_task(self, task, parent_id=None, week_start_date=None):
        if week_start_date is None:
            week_start_date = task.get('week_start_date', '')

        title = task.get('title', '')
        description = task.get('description', '')
        due_date = task.get('due_date', None)
        due_time = task.get('due_time', None)
        
        self.cursor.execute("INSERT INTO weekly_tasks (parent_id, week_start_date, title, description, due_date, due_time, completed) VALUES (?, ?, ?, ?, ?, ?, 0)", 
                            (parent_id, week_start_date, title, description, due_date, due_time))
        task_id = self.cursor.lastrowid
        
        for sub_task in task.get('sub_tasks', []):
            self.add_imported_weekly_task(sub_task, task_id, week_start_date)
        
        self.conn.commit()

    def add_productivity_tab(self):
        productivity_frame = QWidget()
        layout = QVBoxLayout()
        productivity_frame.setLayout(layout)

        self.activity_title_input = QLineEdit()
        self.activity_title_input.setPlaceholderText("Enter Activity Title")
        layout.addWidget(self.activity_title_input)

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Enter Tags (comma-separated)")
        layout.addWidget(self.tag_input)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        layout.addWidget(self.date_edit)

        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        layout.addWidget(self.start_time_edit)

        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        layout.addWidget(self.end_time_edit)

        self.duration_edit = QLineEdit()
        self.duration_edit.setPlaceholderText("Enter Duration (minutes)")
        self.duration_edit.setReadOnly(True)
        layout.addWidget(self.duration_edit)

        self.start_time_edit.timeChanged.connect(self.update_duration)
        self.end_time_edit.timeChanged.connect(self.update_duration)

        save_activity_button = QPushButton("Save Activity")
        save_activity_button.clicked.connect(self.save_activity)
        layout.addWidget(save_activity_button)

        self.productivity_list = QTableWidget()
        self.productivity_list.setColumnCount(7)
        self.productivity_list.setHorizontalHeaderLabels(['ID', 'Activity Title', 'Tags', 'Date', 'Start Time', 'End Time', 'Duration (minutes)'])
        self.productivity_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.productivity_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.productivity_list.customContextMenuRequested.connect(self.open_productivity_context_menu)
        layout.addWidget(self.productivity_list)

        filter_layout = QHBoxLayout()
        self.filter_tag_input = QLineEdit()
        self.filter_tag_input.setPlaceholderText("Enter Tag to Filter")
        filter_layout.addWidget(self.filter_tag_input)
        
        self.filter_start_date_edit = QDateEdit(QDate.currentDate())
        self.filter_start_date_edit.setCalendarPopup(True)
        filter_layout.addWidget(self.filter_start_date_edit)
        
        self.filter_end_date_edit = QDateEdit(QDate.currentDate())
        self.filter_end_date_edit.setCalendarPopup(True)
        filter_layout.addWidget(self.filter_end_date_edit)

        filter_button = QPushButton("Filter")
        filter_button.clicked.connect(self.filter_activities)
        filter_layout.addWidget(filter_button)

        layout.addLayout(filter_layout)

        self.tab_widget.addTab(productivity_frame, "Productivity")

        self.populate_productivity_sessions()

    def update_duration(self):
        start_time = self.start_time_edit.time()
        end_time = self.end_time_edit.time()
        duration = start_time.secsTo(end_time) // 60
        self.duration_edit.setText(str(duration))

    def save_activity(self):
        activity_title = self.activity_title_input.text().strip()
        tags = self.tag_input.text().strip()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        start_time = self.start_time_edit.time().toString("HH:mm")
        end_time = self.end_time_edit.time().toString("HH:mm")
        duration = self.duration_edit.text().strip()

        if not activity_title or not tags or not validate_time(start_time) or not validate_time(end_time) or not duration:
            QMessageBox.warning(self, "Invalid Input", "Please enter all fields correctly.")
            return

        self.cursor.execute("INSERT INTO productivity_sessions (activity_title, date, start_time, end_time, duration_minutes, distractions, tag) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (activity_title, date, start_time, end_time, int(duration), 0, tags))
        self.conn.commit()
        self.populate_productivity_sessions()

    def populate_productivity_sessions(self):
        self.cursor.execute("SELECT id, activity_title, tag, date, start_time, end_time, duration_minutes FROM productivity_sessions ORDER BY date DESC, start_time DESC")
        sessions = self.cursor.fetchall()
        self.productivity_list.setRowCount(len(sessions))
        for i, session in enumerate(sessions):
            id_item = QTableWidgetItem(str(session[0]))
            id_item.setData(Qt.UserRole, session[0])
            self.productivity_list.setItem(i, 0, id_item)
            self.productivity_list.setItem(i, 1, QTableWidgetItem(session[1]))
            self.productivity_list.setItem(i, 2, QTableWidgetItem(session[2]))
            self.productivity_list.setItem(i, 3, QTableWidgetItem(session[3]))
            self.productivity_list.setItem(i, 4, QTableWidgetItem(session[4]))
            self.productivity_list.setItem(i, 5, QTableWidgetItem(session[5]))
            self.productivity_list.setItem(i, 6, QTableWidgetItem(str(session[6])))

    def open_productivity_context_menu(self, position):
        item = self.productivity_list.itemAt(position)
        if item:
            row = item.row()
            session_id = self.productivity_list.item(row, 0).data(Qt.UserRole)
            menu = QMenu()

            edit_action = QAction('Edit', self)
            edit_action.triggered.connect(lambda: self.open_edit_productivity_dialog(session_id))
            menu.addAction(edit_action)

            delete_action = QAction('Delete', self)
            delete_action.triggered.connect(lambda: self.delete_productivity_session(session_id))
            menu.addAction(delete_action)

            menu.exec_(self.productivity_list.viewport().mapToGlobal(position))

    def filter_activities(self):
        tag = self.filter_tag_input.text().strip()
        start_date = self.filter_start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.filter_end_date_edit.date().toString("yyyy-MM-dd")
        query = "SELECT id, activity_title, tag, date, start_time, end_time, duration_minutes FROM productivity_sessions WHERE date BETWEEN ? AND ?"
        params = [start_date, end_date]
        if tag:
            query += " AND tag LIKE ?"
            params.append('%' + tag + '%')
        query += " ORDER BY date DESC, start_time DESC"
        self.cursor.execute(query, params)
        sessions = self.cursor.fetchall()
        self.productivity_list.setRowCount(len(sessions))
        for i, session in enumerate(sessions):
            for j, val in enumerate(session):
                self.productivity_list.setItem(i, j, QTableWidgetItem(str(val)))

    def open_edit_productivity_dialog(self, session_id):
        self.cursor.execute("SELECT activity_title, date, start_time, end_time, duration_minutes, tag FROM productivity_sessions WHERE id = ?", (session_id,))
        session = self.cursor.fetchone()
        if session:
            activity_title, date, start_time, end_time, duration, tag = session

            dialog = QDialog(self)
            dialog.setWindowTitle("Edit Activity")
            layout = QVBoxLayout(dialog)

            activity_title_input = QLineEdit(dialog)
            activity_title_input.setText(activity_title)
            layout.addWidget(activity_title_input)

            tag_input = QLineEdit(dialog)
            tag_input.setText(tag)
            layout.addWidget(tag_input)

            date_edit = QDateEdit(QDate.fromString(date, "yyyy-MM-dd"), dialog)
            date_edit.setCalendarPopup(True)
            layout.addWidget(date_edit)

            start_time_edit = QTimeEdit(QTime.fromString(start_time, "HH:mm"), dialog)
            layout.addWidget(start_time_edit)

            end_time_edit = QTimeEdit(QTime.fromString(end_time, "HH:mm"), dialog)
            layout.addWidget(end_time_edit)

            duration_edit = QLineEdit(dialog)
            duration_edit.setText(str(duration))
            layout.addWidget(duration_edit)

            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
            button_box.accepted.connect(lambda: self.edit_productivity_session(session_id, activity_title_input.text(), tag_input.text(), date_edit.date(), start_time_edit.time(), end_time_edit.time(), duration_edit.text()))
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            dialog.exec_()

    def edit_productivity_session(self, session_id, activity_title, tag, date, start_time, end_time, duration):
        date_str = date.toString("yyyy-MM-dd")
        start_time_str = start_time.toString("HH:mm")
        end_time_str = end_time.toString("HH:mm")
        duration = int(duration)

        if not activity_title or not tag or not validate_time(start_time_str) or not validate_time(end_time_str):
            QMessageBox.warning(self, "Invalid Input", "Please enter all fields correctly.")
            return

        self.cursor.execute("UPDATE productivity_sessions SET activity_title = ?, date = ?, start_time = ?, end_time = ?, duration_minutes = ?, tag = ? WHERE id = ?",
                            (activity_title, date_str, start_time_str, end_time_str, duration, tag, session_id))
        self.conn.commit()
        self.populate_productivity_sessions()

    def delete_productivity_session(self, session_id):
        self.cursor.execute("DELETE FROM productivity_sessions WHERE id = ?", (session_id,))
        self.conn.commit()
        self.populate_productivity_sessions()

    def add_pomodoro_tab(self):
        pomodoro_frame = QWidget()
        layout = QVBoxLayout()
        pomodoro_frame.setLayout(layout)

        self.pomodoro_label = QLabel("Pomodoro Timer")
        self.pomodoro_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pomodoro_label)

        custom_layout = QFormLayout()
        self.session_duration_input = QLineEdit("25")
        self.break_duration_input = QLineEdit("5")
        self.number_of_sessions_input = QLineEdit("4")

        custom_layout.addRow("Session Duration (minutes):", self.session_duration_input)
        custom_layout.addRow("Break Duration (minutes):", self.break_duration_input)
        custom_layout.addRow("Number of Sessions:", self.number_of_sessions_input)
        layout.addLayout(custom_layout)

        self.sound_notifications_checkbox = QCheckBox("Enable Sound Notifications")
        layout.addWidget(self.sound_notifications_checkbox)

        self.pomodoro_timer_display = QLabel("25:00")
        self.pomodoro_timer_display.setFont(QFont('Arial', 40))
        self.pomodoro_timer_display.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pomodoro_timer_display)

        pomodoro_buttons_layout = QHBoxLayout()
        self.start_pomodoro_button = QPushButton("Start")
        self.start_pomodoro_button.clicked.connect(self.start_pomodoro)
        self.pause_pomodoro_button = QPushButton("Pause")
        self.pause_pomodoro_button.clicked.connect(self.pause_pomodoro)
        self.reset_pomodoro_button = QPushButton("Reset")
        self.reset_pomodoro_button.clicked.connect(self.reset_pomodoro)
        pomodoro_buttons_layout.addWidget(self.start_pomodoro_button)
        pomodoro_buttons_layout.addWidget(self.pause_pomodoro_button)
        pomodoro_buttons_layout.addWidget(self.reset_pomodoro_button)
        layout.addLayout(pomodoro_buttons_layout)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.tab_widget.addTab(pomodoro_frame, "Pomodoro")

        self.pomodoro_timer = QTimer()
        self.pomodoro_timer.timeout.connect(self.update_pomodoro)
        self.is_break = False
        self.is_paused = False
        self.current_session = 0

    def start_pomodoro(self):
        if not self.is_paused:
            self.pomodoro_session_duration = int(self.session_duration_input.text()) * 60
            self.break_duration = int(self.break_duration_input.text()) * 60
            self.number_of_sessions = int(self.number_of_sessions_input.text())
            self.pomodoro_time_left = self.pomodoro_session_duration
            self.current_session = 0
        self.is_paused = False
        self.pomodoro_timer.start(1000)

    def pause_pomodoro(self):
        self.is_paused = True
        self.pomodoro_timer.stop()

    def reset_pomodoro(self):
        self.pomodoro_timer.stop()
        self.is_break = False
        self.is_paused = False
        self.pomodoro_time_left = int(self.session_duration_input.text()) * 60
        self.pomodoro_timer_display.setText(f"{int(self.session_duration_input.text()):02d}:00")
        self.progress_bar.setValue(0)
        self.current_session = 0

    def update_pomodoro(self):
        if self.pomodoro_time_left > 0:
            self.pomodoro_time_left -= 1
            minutes, seconds = divmod(self.pomodoro_time_left, 60)
            self.pomodoro_timer_display.setText(f"{minutes:02d}:{seconds:02d}")
            progress = ((self.pomodoro_session_duration - self.pomodoro_time_left) / self.pomodoro_session_duration) * 100
            self.progress_bar.setValue(int(progress))
        else:
            self.pomodoro_timer.stop()
            if not self.is_break:
                self.current_session += 1
                if self.sound_notifications_checkbox.isChecked():
                    self.play_sound_notification()
                if self.current_session < self.number_of_sessions:
                    QMessageBox.information(self, "Pomodoro Timer", "Time's up! Take a break.")
                    self.is_break = True
                    self.pomodoro_time_left = self.break_duration
                    self.pomodoro_timer_display.setText(f"{int(self.break_duration / 60):02d}:00")
                    self.pomodoro_timer.start(1000)
                else:
                    QMessageBox.information(self, "Pomodoro Timer", "All sessions completed! Good job!")
                    self.reset_pomodoro()
            else:
                if self.sound_notifications_checkbox.isChecked():
                    self.play_sound_notification()
                QMessageBox.information(self, "Break Timer", "Break is over! Time to start a new session.")
                self.is_break = False
                self.pomodoro_time_left = self.pomodoro_session_duration
                self.pomodoro_timer_display.setText(f"{int(self.pomodoro_session_duration / 60):02d}:00")
                self.pomodoro_timer.start(1000)

    def play_sound_notification(self):
        if os.name == 'nt':
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)  # Windows default notification sound
        else:
            os.system('play -nq -t alsa synth 1 sine 440')  # Adjust this line according to your environment

    def add_visualization_tab(self):
        visualization_frame = QWidget()
        layout = QVBoxLayout()
        visualization_frame.setLayout(layout)

        self.date_filter_layout = QHBoxLayout()
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.date_filter_layout.addWidget(self.start_date_edit)

        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.date_filter_layout.addWidget(self.end_date_edit)

        filter_button = QPushButton("Filter")
        filter_button.clicked.connect(self.update_visualization)
        self.date_filter_layout.addWidget(filter_button)

        layout.addLayout(self.date_filter_layout)

        self.visualization_figure = plt.figure()
        self.visualization_canvas = FigureCanvas(self.visualization_figure)
        layout.addWidget(self.visualization_canvas)

        self.tab_widget.addTab(visualization_frame, "Visualization")

    def update_visualization(self):
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        self.visualization_figure.clear()

        query = """
            SELECT tag, SUM(duration_minutes) 
            FROM productivity_sessions 
            WHERE date BETWEEN ? AND ? 
            GROUP BY tag
        """
        self.cursor.execute(query, (start_date, end_date))
        sessions = self.cursor.fetchall()

        tags = []
        durations = []
        for session in sessions:
            tags.append(session[0])
            durations.append(session[1])

        ax = self.visualization_figure.add_subplot(111)
        ax.pie(durations, labels=tags, autopct='%1.1f%%', startangle=140)
        ax.set_title(f'Time Distribution by Tags ({start_date} to {end_date})')

        self.visualization_canvas.draw()

    def add_goal_list_tab(self):
        goal_list_frame = QWidget()
        layout = QVBoxLayout()
        goal_list_frame.setLayout(layout)

        self.goal_list_table = QTableWidget()
        self.goal_list_table.setColumnCount(4)
        self.goal_list_table.setHorizontalHeaderLabels(['ID', 'Title', 'Due Date', 'Days Left'])
        self.goal_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.goal_list_table)

        self.tab_widget.addTab(goal_list_frame, "Goal List")

        self.populate_goal_list()

    def populate_goal_list(self):
        self.goal_list_table.clearContents()
        self.cursor.execute("SELECT id, title, due_date FROM goals WHERE completed = 0 ORDER BY due_date")
        goals = self.cursor.fetchall()
        self.goal_list_table.setRowCount(len(goals))
        for i, goal in enumerate(goals):
            goal_id, title, due_date = goal
            days_left = (datetime.strptime(due_date, "%Y-%m-%d").date() - datetime.now().date()).days
            self.goal_list_table.setItem(i, 0, QTableWidgetItem(str(goal_id)))
            self.goal_list_table.setItem(i, 1, QTableWidgetItem(title))
            self.goal_list_table.setItem(i, 2, QTableWidgetItem(due_date))
            self.goal_list_table.setItem(i, 3, QTableWidgetItem(str(days_left)))

    def update_week_list(self, year, month):
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
        row = self.week_table_widget.currentRow()
        start_date = self.week_table_widget.item(row, 0).data(Qt.UserRole)
        self.open_weekly_planner(start_date)

    def calculate_weeks(self, year):
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

    def open_weekly_planner(self, start_of_week):
        self.weekly_planner = WeeklyPlanner(self, start_of_week)
        self.weekly_planner.show()

class DailyPlanner(QMainWindow):
    def __init__(self, parent, date):
        super().__init__(parent)
        self.conn = parent.conn
        self.cursor = parent.cursor
        self.date = date
        self.note_text = ""
        self.initUI()
        self.load_note()
        self.populate_events()

    def initUI(self):
        self.setWindowTitle(f"Daily Planner - {self.date.strftime('%B %d, %Y')}")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.event_list = QTableWidget()
        self.event_list.setColumnCount(4)
        self.event_list.setHorizontalHeaderLabels(['Time', 'Description', 'Completed', ''])
        self.event_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.event_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.event_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.event_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.event_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.event_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.event_list.customContextMenuRequested.connect(self.open_event_context_menu)

        event_list_widget = QWidget()
        event_list_layout = QVBoxLayout(event_list_widget)
        event_list_layout.addWidget(self.event_list)

        form_layout = QHBoxLayout()
        event_list_layout.addLayout(form_layout)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        form_layout.addWidget(self.time_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Event Description")
        form_layout.addWidget(self.description_edit)

        add_button = QPushButton('Add Event')
        add_button.clicked.connect(self.add_event)
        form_layout.addWidget(add_button)

        note_button = QPushButton('Add/View Note')
        note_button.clicked.connect(self.show_note_dialog)
        event_list_layout.addWidget(note_button)

        chart_button = QPushButton('Show Daily Chart')
        chart_button.clicked.connect(self.show_daily_chart_window)
        event_list_layout.addWidget(chart_button)

        pie_chart_button = QPushButton('Show Daily Pie Chart')
        pie_chart_button.clicked.connect(self.show_daily_pie_chart_window)
        event_list_layout.addWidget(pie_chart_button)

        self.tab_widget.addTab(event_list_widget, "Events")

        self.add_timeboxed_tab()

    def add_timeboxed_tab(self):
        timeboxed_frame = QWidget()
        layout = QVBoxLayout()
        timeboxed_frame.setLayout(layout)

        self.timeboxed_list = QTableWidget()
        self.timeboxed_list.setColumnCount(4)
        self.timeboxed_list.setHorizontalHeaderLabels(['Time', 'Habit', 'Completed', ''])
        self.timeboxed_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.timeboxed_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.timeboxed_list.customContextMenuRequested.connect(self.open_timeboxed_context_menu)
        layout.addWidget(self.timeboxed_list)

        form_layout = QHBoxLayout()
        layout.addLayout(form_layout)

        self.habit_time_edit = QTimeEdit()
        form_layout.addWidget(self.habit_time_edit)

        self.habit_description_edit = QLineEdit()
        form_layout.addWidget(self.habit_description_edit)

        add_button = QPushButton('Add Habit')
        add_button.clicked.connect(self.add_habit_event)
        form_layout.addWidget(add_button)

        self.tab_widget.addTab(timeboxed_frame, "Time-Boxed View")

    def open_event_context_menu(self, position):
        item = self.event_list.itemAt(position)
        if item:
            row = item.row()
            event_id = self.event_list.item(row, 0).data(Qt.UserRole)
            menu = QMenu()

            edit_action = QAction('Edit', self)
            edit_action.triggered.connect(lambda: self.open_edit_event_dialog(event_id))
            menu.addAction(edit_action)

            delete_action = QAction('Delete', self)
            delete_action.triggered.connect(lambda: self.delete_event(event_id))
            menu.addAction(delete_action)

            menu.exec_(self.event_list.viewport().mapToGlobal(position))

    def open_timeboxed_context_menu(self, position):
        item = self.timeboxed_list.itemAt(position)
        if item:
            row = item.row()
            event_id = self.timeboxed_list.item(row, 0).data(Qt.UserRole)
            menu = QMenu()

            edit_action = QAction('Edit', self)
            edit_action.triggered.connect(lambda: self.open_edit_timeboxed_dialog(event_id))
            menu.addAction(edit_action)

            delete_action = QAction('Delete', self)
            delete_action.triggered.connect(lambda: self.delete_habit_event(event_id))
            menu.addAction(delete_action)

            menu.exec_(self.timeboxed_list.viewport().mapToGlobal(position))

    def populate_events(self):
        self.cursor.execute("SELECT id, time, description, completed FROM events WHERE date = ? AND type = 'goal' ORDER BY time", (self.date.isoformat(),))
        events = self.cursor.fetchall()
        self.event_list.setRowCount(len(events))
        for i, event in enumerate(events):
            id_item = QTableWidgetItem(event[1])
            id_item.setData(Qt.UserRole, event[0])
            self.event_list.setItem(i, 0, id_item)
            self.event_list.setItem(i, 1, QTableWidgetItem(event[2]))
            completed_checkbox = QCheckBox()
            completed_checkbox.setChecked(event[3])
            completed_checkbox.stateChanged.connect(lambda state, e=event[0]: self.toggle_event_completion(e, state))
            self.event_list.setCellWidget(i, 2, completed_checkbox)
            delete_button = QPushButton('Delete')
            delete_button.clicked.connect(lambda _, e=event[0]: self.delete_event(e))
            self.event_list.setCellWidget(i, 3, delete_button)

        self.cursor.execute("SELECT id, time, description, completed FROM events WHERE date = ? AND type = 'habit' ORDER BY time", (self.date.isoformat(),))
        habits = self.cursor.fetchall()
        self.timeboxed_list.setRowCount(len(habits))
        for i, habit in enumerate(habits):
            id_item = QTableWidgetItem(habit[1])
            id_item.setData(Qt.UserRole, habit[0])
            self.timeboxed_list.setItem(i, 0, id_item)
            self.timeboxed_list.setItem(i, 1, QTableWidgetItem(habit[2]))
            completed_checkbox = QCheckBox()
            completed_checkbox.setChecked(habit[3])
            completed_checkbox.stateChanged.connect(lambda state, h=habit[0]: self.toggle_habit_completion(h, state))
            self.timeboxed_list.setCellWidget(i, 2, completed_checkbox)
            delete_button = QPushButton('Delete')
            delete_button.clicked.connect(lambda _, h=habit[0]: self.delete_habit_event(h))
            self.timeboxed_list.setCellWidget(i, 3, delete_button)

    def add_event(self):
        time = self.time_edit.time().toString("HH:mm")
        description = self.description_edit.text().strip()
        if not description or not validate_time(time):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid description and time.")
            return

        self.cursor.execute("INSERT INTO events (date, time, description, type, completed) VALUES (?, ?, ?, 'goal', 0)", (self.date.isoformat(), time, description))
        self.conn.commit()
        self.populate_events()

    def toggle_event_completion(self, event_id, state):
        self.cursor.execute("UPDATE events SET completed = ? WHERE id = ?", (state, event_id))
        self.conn.commit()

    def toggle_habit_completion(self, habit_id, state):
        self.cursor.execute("UPDATE events SET completed = ? WHERE id = ?", (state, habit_id))
        self.conn.commit()

    def delete_event(self, event_id):
        self.cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        self.conn.commit()
        self.populate_events()

    def add_habit_event(self):
        time = self.habit_time_edit.time().toString("HH:mm")
        description = self.habit_description_edit.text().strip()
        if not description or not validate_time(time):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid description and time.")
            return

        self.cursor.execute("INSERT INTO events (date, time, description, type, completed) VALUES (?, ?, ?, 'habit', 0)", (self.date.isoformat(), time, description))
        self.conn.commit()
        self.populate_events()

    def delete_habit_event(self, event_id):
        self.cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        self.conn.commit()
        self.populate_events()

    def open_edit_event_dialog(self, event_id):
        self.cursor.execute("SELECT id, time, description, completed FROM events WHERE id = ?", (event_id,))
        event = self.cursor.fetchone()
        if not event:
            QMessageBox.warning(self, "Invalid Event", "Event not found.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Event")
        layout = QVBoxLayout(dialog)

        time_edit = QTimeEdit(dialog)
        time_edit.setTime(QTime.fromString(event[1], "HH:mm"))
        layout.addWidget(time_edit)

        description_edit = QLineEdit(dialog)
        description_edit.setText(event[2])
        layout.addWidget(description_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        button_box.accepted.connect(lambda: self.edit_event(event_id, time_edit.time(), description_edit.text()))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def edit_event(self, event_id, time, description):
        time_str = time.toString("HH:mm")
        if not description or not validate_time(time_str):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid description and time.")
            return

        self.cursor.execute("UPDATE events SET time = ?, description = ? WHERE id = ?", (time_str, description, event_id))
        self.conn.commit()
        self.populate_events()

    def open_edit_timeboxed_dialog(self, event_id):
        self.cursor.execute("SELECT id, time, description, completed FROM events WHERE id = ?", (event_id,))
        event = self.cursor.fetchone()
        if not event:
            QMessageBox.warning(self, "Invalid Event", "Event not found.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Habit")
        layout = QVBoxLayout(dialog)

        time_edit = QTimeEdit(dialog)
        time_edit.setTime(QTime.fromString(event[1], "HH:mm"))
        layout.addWidget(time_edit)

        description_edit = QLineEdit(dialog)
        description_edit.setText(event[2])
        layout.addWidget(description_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        button_box.accepted.connect(lambda: self.edit_habit_event(event_id, time_edit.time(), description_edit.text()))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def edit_habit_event(self, event_id, time, description):
        time_str = time.toString("HH:mm")
        if not description or not validate_time(time_str):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid description and time.")
            return

        self.cursor.execute("UPDATE events SET time = ?, description = ? WHERE id = ?", (time_str, description, event_id))
        self.conn.commit()
        self.populate_events()

    def load_note(self):
        self.cursor.execute("SELECT note FROM daily_notes WHERE date = ?", (self.date.isoformat(),))
        result = self.cursor.fetchone()
        self.note_text = result[0] if result else ""

    def save_note_dialog(self, dialog):
        self.save_note()
        dialog.accept()

    def save_note(self):
        note = self.note_edit.toPlainText()
        self.cursor.execute("REPLACE INTO daily_notes (date, note) VALUES (?, ?)", (self.date.isoformat(), note))
        self.conn.commit()

    def show_note_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Daily Note")
        layout = QVBoxLayout(dialog)

        self.note_edit = QTextEdit(dialog)
        self.note_edit.setPlainText(self.note_text)
        layout.addWidget(self.note_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        button_box.accepted.connect(lambda: self.save_note_dialog(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def show_daily_chart_window(self):
        chart_window = DailyChartWindow(self, self.date)
        chart_window.show()

    def show_daily_pie_chart_window(self):
        pie_chart_window = DailyPieChartWindow(self, self.date)
        pie_chart_window.show()

class DailyChartWindow(QMainWindow):
    def __init__(self, parent, date):
        super().__init__(parent)
        self.conn = parent.conn
        self.cursor = parent.cursor
        self.date = date
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"Daily Chart - {self.date.strftime('%A, %B %d, %Y')}")
        self.setGeometry(200, 200, 800, 600)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)
        layout.addWidget(self.canvas)
        self.setCentralWidget(central_widget)

        self.plot_daily_data()

    def plot_daily_data(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        self.cursor.execute("SELECT start_time, end_time, duration_minutes, tag FROM productivity_sessions WHERE date = ? ORDER BY start_time", (self.date.isoformat(),))
        sessions = self.cursor.fetchall()

        times = []
        tags = []
        for session in sessions:
            start_time = datetime.strptime(session[0], "%H:%M").time()
            end_time = datetime.strptime(session[1], "%H:%M").time()
            tag = session[3]
            start_time_hours = start_time.hour + start_time.minute / 60.0
            end_time_hours = end_time.hour + end_time.minute / 60.0
            times.append((start_time_hours, end_time_hours))
            tags.append(tag)

        for i, (start_time, end_time) in enumerate(times):
            ax.plot([start_time, end_time], [i, i], marker='o', linestyle='-', color='skyblue')

        ax.set_xlabel('Time (hours since midnight)')
        ax.set_title('Daily Productivity Timeline')
        ax.set_yticks(range(len(tags)))
        ax.set_yticklabels(tags)

        self.canvas.draw()

class DailyPieChartWindow(QMainWindow):
    def __init__(self, parent, date):
        super().__init__(parent)
        self.conn = parent.conn
        self.cursor = parent.cursor
        self.date = date
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"Daily Pie Chart - {self.date.strftime('%A, %B %d, %Y')}")
        self.setGeometry(200, 200, 800, 600)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)
        layout.addWidget(self.canvas)
        self.setCentralWidget(central_widget)

        self.plot_daily_pie_chart()

    def plot_daily_pie_chart(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        self.cursor.execute("SELECT tag, SUM(duration_minutes) FROM productivity_sessions WHERE date = ? GROUP BY tag", (self.date.isoformat(),))
        sessions = self.cursor.fetchall()

        tags = []
        durations = []
        for session in sessions:
            tags.append(session[0])
            durations.append(session[1])

        ax.pie(durations, labels=tags, autopct='%1.1f%%', startangle=140)
        ax.set_title('Daily Time Distribution by Tags')

        self.canvas.draw()


class WeeklyPlanner(QMainWindow):
    def __init__(self, parent, start_of_week):
        super().__init__(parent)
        self.conn = parent.conn
        self.cursor = parent.cursor
        self.start_of_week = start_of_week
        self.end_of_week = start_of_week.addDays(6)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"Weekly Planner - {self.start_of_week.toString('MMM d')} - {self.end_of_week.toString('MMM d')}")
        self.setGeometry(100, 100, 1000, 600)  # Adjusted width for more space

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        central_widget.setLayout(main_layout)

        # Tree widget for weekly tasks
        self.weekly_task_tree = QTreeWidget()
        self.weekly_task_tree.setColumnCount(5)
        self.weekly_task_tree.setHeaderLabels(['Task', 'Description', 'Due Date', 'Due Time', 'Completed'])
        self.weekly_task_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.weekly_task_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.weekly_task_tree.customContextMenuRequested.connect(self.open_task_context_menu)
        self.weekly_task_tree.itemChanged.connect(self.update_task_completion)
        main_layout.addWidget(self.weekly_task_tree)

        # Form layout for adding new tasks
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(10)

        title_label = QLabel("Title:")
        form_layout.addWidget(title_label, 0, 0)
        self.task_title_edit = QLineEdit()
        self.task_title_edit.setPlaceholderText("Task Title")
        form_layout.addWidget(self.task_title_edit, 0, 1, 1, 3)  # Span across 3 columns

        description_label = QLabel("Description:")
        form_layout.addWidget(description_label, 1, 0)
        self.task_description_edit = QPlainTextEdit()
        self.task_description_edit.setPlaceholderText("Task Description")
        self.task_description_edit.setMaximumHeight(100)  # Set maximum height for the description field
        form_layout.addWidget(self.task_description_edit, 1, 1, 1, 3)  # Span across 3 columns

        due_date_label = QLabel("Due Date:")
        form_layout.addWidget(due_date_label, 2, 0)
        self.task_due_date_edit = QDateEdit()
        self.task_due_date_edit.setCalendarPopup(True)
        form_layout.addWidget(self.task_due_date_edit, 2, 1)

        due_time_label = QLabel("Due Time:")
        form_layout.addWidget(due_time_label, 2, 2)
        self.task_due_time_edit = QTimeEdit()
        form_layout.addWidget(self.task_due_time_edit, 2, 3)

        parent_task_label = QLabel("Parent Task:")
        form_layout.addWidget(parent_task_label, 3, 0)
        self.parent_task_combo = QComboBox()
        self.parent_task_combo.addItem("None", None)  # No parent option
        form_layout.addWidget(self.parent_task_combo, 3, 1, 1, 3)  # Span across 3 columns

        add_task_button = QPushButton('Add Task')
        form_layout.addWidget(add_task_button, 4, 0, 1, 4)  # Span across all columns
        add_task_button.clicked.connect(self.add_task)

        main_layout.addLayout(form_layout)

        self.populate_weekly_tasks()

    def populate_weekly_tasks(self):
        self.weekly_task_tree.clear()
        self.parent_task_combo.clear()
        self.parent_task_combo.addItem("None", None)  # Reset and add No parent option

        self.cursor.execute("""
            SELECT id, parent_id, title, description, due_date, due_time, completed
            FROM weekly_tasks
            WHERE week_start_date = ?
            ORDER BY parent_id, id
        """, (self.start_of_week.toString("yyyy-MM-dd"),))
        tasks = self.cursor.fetchall()
        tasks_dict = {task[0]: task for task in tasks}
        root_tasks = [task for task in tasks if task[1] is None]

        for task_id, parent_id, title, description, due_date, due_time, completed in tasks:
            self.parent_task_combo.addItem(title, task_id)

        def add_task_to_tree(task, parent_item=None):
            task_id, parent_id, title, description, due_date, due_time, completed = task
            task_item = QTreeWidgetItem([title, description, due_date or '', due_time or '', ''])
            task_item.setFlags(task_item.flags() | Qt.ItemIsUserCheckable)
            task_item.setCheckState(4, Qt.Checked if completed else Qt.Unchecked)
            task_item.setData(0, Qt.UserRole, task_id)  # Store task_id in the item

            if parent_item:
                parent_item.addChild(task_item)
            else:
                self.weekly_task_tree.addTopLevelItem(task_item)

            child_tasks = [t for t in tasks if t[1] == task_id]
            for child in child_tasks:
                add_task_to_tree(child, task_item)

        for root_task in root_tasks:
            add_task_to_tree(root_task)

    def update_task_completion(self, item, column):
        if column == 4:  # If the "Completed" column is changed
            task_id = item.data(0, Qt.UserRole)
            completed = item.checkState(4) == Qt.Checked
            self.cursor.execute("UPDATE weekly_tasks SET completed = ? WHERE id = ?", (completed, task_id))
            self.conn.commit()

    def open_task_context_menu(self, position):
        item = self.weekly_task_tree.itemAt(position)
        if item:
            task_id = item.data(0, Qt.UserRole)
            menu = QMenu()

            edit_action = QAction('Edit', self)
            edit_action.triggered.connect(lambda: self.open_edit_task_dialog(task_id))
            menu.addAction(edit_action)

            delete_action = QAction('Delete', self)
            delete_action.triggered.connect(lambda: self.delete_task(task_id))
            menu.addAction(delete_action)

            menu.exec_(self.weekly_task_tree.viewport().mapToGlobal(position))

    def open_edit_task_dialog(self, task_id):
        self.cursor.execute("SELECT id, title, description, due_date, due_time, completed FROM weekly_tasks WHERE id = ?", (task_id,))
        task = self.cursor.fetchone()
        if not task:
            QMessageBox.warning(self, "Invalid Task", "Task not found.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Task")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Title:"))
        title_edit = QLineEdit(dialog)
        title_edit.setText(task[1])
        layout.addWidget(title_edit)

        layout.addWidget(QLabel("Description:"))
        description_edit = QPlainTextEdit(dialog)
        description_edit.setPlainText(task[2])
        description_edit.setMaximumHeight(100)
        layout.addWidget(description_edit)

        layout.addWidget(QLabel("Due Date:"))
        due_date_edit = QDateEdit(QDate.fromString(task[3], "yyyy-MM-dd"), dialog)
        due_date_edit.setCalendarPopup(True)
        layout.addWidget(due_date_edit)

        layout.addWidget(QLabel("Due Time:"))
        due_time_edit = QTimeEdit(QTime.fromString(task[4], "HH:mm"), dialog)
        layout.addWidget(due_time_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        button_box.accepted.connect(lambda: self.edit_task(task_id, title_edit.text(), description_edit.toPlainText(), due_date_edit.date(), due_time_edit.time()))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def edit_task(self, task_id, title, description, due_date, due_time):
        due_date_str = due_date.toString("yyyy-MM-dd")
        due_time_str = due_time.toString("HH:mm")
        if not title or not validate_time(due_time_str):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid title and time.")
            return

        self.cursor.execute("UPDATE weekly_tasks SET title = ?, description = ?, due_date = ?, due_time = ? WHERE id = ?",
                            (title, description, due_date_str, due_time_str, task_id))
        self.conn.commit()
        self.populate_weekly_tasks()

    def delete_task(self, task_id):
        self.cursor.execute("DELETE FROM weekly_tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        self.populate_weekly_tasks()

    def add_task(self):
        title = self.task_title_edit.text().strip()
        description = self.task_description_edit.toPlainText().strip()
        due_date = self.task_due_date_edit.date().toString("yyyy-MM-dd")
        due_time = self.task_due_time_edit.time().toString("HH:mm")
        parent_id = self.parent_task_combo.currentData()

        if not title or not validate_time(due_time):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid title and time.")
            return

        self.cursor.execute("INSERT INTO weekly_tasks (parent_id, week_start_date, title, description, due_date, due_time, completed) VALUES (?, ?, ?, ?, ?, ?, 0)",
                            (parent_id, self.start_of_week.toString("yyyy-MM-dd"), title, description, due_date, due_time))
        self.conn.commit()
        self.populate_weekly_tasks()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    scheduler = SmartScheduler()
    scheduler.show()
    sys.exit(app.exec_())
