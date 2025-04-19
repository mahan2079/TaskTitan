import os
import sqlite3
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QTabWidget,
    QSplitter, QFrame, QSizePolicy, QLineEdit, 
    QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QFont

class TaskTitanApp(QMainWindow):
    """Main application window for TaskTitan."""
    
    def __init__(self):
        super().__init__()
        self.setupUI()
        
        # Initialize database connection
        self.init_database()
        
        # Load initial data
        self.loadData()
        
        # Set up refresh timer (every 60 seconds)
        self.refreshTimer = QTimer(self)
        self.refreshTimer.timeout.connect(self.refreshData)
        self.refreshTimer.start(60000)

    def init_database(self):
        """Initialize database connection"""
        try:
            # Get the database path
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "database", "data", "tasktitan.db")
            
            # Connect to the database
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            print("Database connection established successfully")
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            QMessageBox.critical(self, "Database Error", 
                               f"Could not connect to database: {str(e)}")
    
    def setupUI(self):
        """Set up the user interface"""
        self.setWindowTitle("TaskTitan")
        self.setMinimumSize(1000, 700)
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar
        self.setup_sidebar(main_layout)
        
        # Create main content area
        self.content_area = QFrame()
        self.content_area.setFrameShape(QFrame.Shape.StyledPanel)
        self.content_area.setStyleSheet("background-color: #F8FAFC;")
        main_layout.addWidget(self.content_area, 3)
        
        # Content area layout
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Welcome header
        header = QLabel("Welcome to TaskTitan")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        content_layout.addWidget(header)
        
        # Task management section
        task_section = QFrame()
        task_layout = QVBoxLayout(task_section)
        
        task_header = QLabel("Today's Tasks")
        task_header.setStyleSheet("font-size: 18px; font-weight: bold;")
        task_layout.addWidget(task_header)
        
        # Add new task input
        new_task_layout = QHBoxLayout()
        self.new_task_input = QLineEdit()
        self.new_task_input.setPlaceholderText("Add a new task...")
        self.new_task_input.returnPressed.connect(self.add_new_task)
        new_task_layout.addWidget(self.new_task_input)
        
        add_task_button = QPushButton("Add Task")
        add_task_button.clicked.connect(self.add_new_task)
        new_task_layout.addWidget(add_task_button)
        task_layout.addLayout(new_task_layout)
        
        # Task list
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #E2E8F0;
            }
            QListWidget::item:selected {
                background-color: #EFF6FF;
                color: #1E40AF;
            }
        """)
        task_layout.addWidget(self.task_list)
        
        # Add to main content
        content_layout.addWidget(task_section)
        
        # Stats section
        stats_section = QFrame()
        stats_layout = QHBoxLayout(stats_section)
        
        # Tasks completed
        tasks_completed = QFrame()
        tasks_completed.setStyleSheet("""
            background-color: #DBEAFE;
            border-radius: 8px;
            padding: 10px;
        """)
        tasks_completed_layout = QVBoxLayout(tasks_completed)
        tasks_label = QLabel("Tasks Completed")
        tasks_label.setStyleSheet("font-weight: bold;")
        tasks_completed_layout.addWidget(tasks_label)
        
        self.completed_count = QLabel("0")
        self.completed_count.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E40AF;")
        tasks_completed_layout.addWidget(self.completed_count)
        
        stats_layout.addWidget(tasks_completed)
        
        # Goals progress
        goals_progress = QFrame()
        goals_progress.setStyleSheet("""
            background-color: #ECFDF5;
            border-radius: 8px;
            padding: 10px;
        """)
        goals_layout = QVBoxLayout(goals_progress)
        goals_label = QLabel("Goals Progress")
        goals_label.setStyleSheet("font-weight: bold;")
        goals_layout.addWidget(goals_label)
        
        self.goals_count = QLabel("0/0")
        self.goals_count.setStyleSheet("font-size: 24px; font-weight: bold; color: #047857;")
        goals_layout.addWidget(self.goals_count)
        
        stats_layout.addWidget(goals_progress)
        
        # Add stats to main content
        content_layout.addWidget(stats_section)
        
        # Add spacer at the bottom
        content_layout.addStretch()

    def setup_sidebar(self, main_layout):
        """Create the application sidebar"""
        sidebar = QFrame()
        sidebar.setMaximumWidth(250)
        sidebar.setMinimumWidth(200)
        sidebar.setStyleSheet("""
            background-color: #1E293B;
            color: white;
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # App title
        title = QLabel("TaskTitan")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            padding: 20px;
            background-color: #0F172A;
        """)
        sidebar_layout.addWidget(title)
        
        # Navigation buttons
        menu_items = [
            ("Dashboard", self.show_dashboard),
            ("Tasks", self.show_tasks),
            ("Goals", self.show_goals),
            ("Analytics", self.show_analytics),
            ("Settings", self.show_settings)
        ]
        
        for item_text, item_func in menu_items:
            button = QPushButton(item_text)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 12px 15px;
                    border: none;
                    font-size: 16px;
                    font-weight: 500;
                    color: #CBD5E1;
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: #334155;
                }
                QPushButton:pressed {
                    background-color: #475569;
                }
            """)
            button.clicked.connect(item_func)
            sidebar_layout.addWidget(button)
        
        # Add spacer
        sidebar_layout.addStretch()
        
        # Add user info section
        user_section = QFrame()
        user_section.setStyleSheet("""
            background-color: #0F172A;
            padding: 15px;
        """)
        user_layout = QHBoxLayout(user_section)
        
        user_name = QLabel("User")
        user_name.setStyleSheet("color: #CBD5E1; font-weight: bold;")
        user_layout.addWidget(user_name)
        
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            background-color: transparent;
            color: #94A3B8;
            border: none;
        """)
        logout_btn.clicked.connect(self.logout)
        user_layout.addWidget(logout_btn)
        
        sidebar_layout.addWidget(user_section)
        
        # Add to main layout
        main_layout.addWidget(sidebar, 1)

    def loadData(self):
        """Load data from the database"""
        try:
            # Load tasks
            self.cursor.execute("SELECT id, description FROM tasks WHERE completed = 0 LIMIT 10")
            tasks = self.cursor.fetchall()
            
            self.task_list.clear()
            for task_id, description in tasks:
                self.task_list.addItem(description)
            
            # Load statistics
            self.cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 1")
            completed_count = self.cursor.fetchone()[0]
            self.completed_count.setText(str(completed_count))
            
            self.cursor.execute("SELECT COUNT(*), SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) FROM goals")
            result = self.cursor.fetchone()
            total_goals = result[0] or 0
            completed_goals = result[1] or 0
            self.goals_count.setText(f"{completed_goals}/{total_goals}")
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
    
    def refreshData(self):
        """Refresh data from the database"""
        self.loadData()
    
    def add_new_task(self):
        """Add a new task to the database"""
        task_text = self.new_task_input.text().strip()
        if not task_text:
            return
        
        try:
            # Insert new task
            self.cursor.execute(
                "INSERT INTO tasks (description, completed) VALUES (?, 0)",
                (task_text,)
            )
            self.conn.commit()
            
            # Clear input and refresh
            self.new_task_input.clear()
            self.loadData()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not add task: {str(e)}")
    
    # Navigation methods
    def show_dashboard(self):
        print("Showing dashboard")
        # Implement dashboard view
    
    def show_tasks(self):
        print("Showing tasks")
        # Implement tasks view
    
    def show_goals(self):
        print("Showing goals")
        # Implement goals view
    
    def show_analytics(self):
        print("Showing analytics")
        # Implement analytics view
    
    def show_settings(self):
        print("Showing settings")
        # Implement settings view
    
    def logout(self):
        """Log out the current user"""
        reply = QMessageBox.question(
            self, "Logout", "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Logout", "You have been logged out.")
            # Implement actual logout functionality 