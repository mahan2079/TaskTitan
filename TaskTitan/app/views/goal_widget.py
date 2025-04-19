"""
Goal widget for TaskTitan.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QScrollArea, QFrame, QTreeWidget, 
                           QTreeWidgetItem, QDialog, QLineEdit, QDateEdit, 
                           QTimeEdit, QComboBox, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
from datetime import datetime
import random

from app.resources import get_icon

class GoalWidget(QWidget):
    """Widget for managing goals and tracking progress."""
    
    # Signals
    goalAdded = pyqtSignal(dict)
    goalCompleted = pyqtSignal(int, bool)
    goalDeleted = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store parent to access database
        
        # Goals data
        self.goals = []
        
        # Setup UI
        self.setupUI()
        
        # Load initial data
        self.loadGoals()
    
    def setupUI(self):
        """Set up the user interface components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("goalHeader")
        header.setMinimumHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Title
        title = QLabel("My Goals")
        title.setObjectName("goalTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        header_layout.addWidget(title)
        
        # Add goal button
        self.add_btn = QPushButton("Add Goal")
        self.add_btn.setObjectName("addGoalButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setMinimumWidth(100)
        self.add_btn.clicked.connect(self.showAddGoalDialog)
        
        # Add icon to button
        add_icon = get_icon("add")
        if not add_icon.isNull():
            self.add_btn.setIcon(add_icon)
        
        header_layout.addWidget(self.add_btn)
        
        main_layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("goalSeparator")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Goal tree widget
        self.goal_tree = QTreeWidget()
        self.goal_tree.setObjectName("goalTree")
        self.goal_tree.setColumnCount(4)
        self.goal_tree.setHeaderLabels(["Goal", "Due Date", "Due Time", "Status"])
        self.goal_tree.setAlternatingRowColors(True)
        self.goal_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.goal_tree.setAnimated(True)
        self.goal_tree.setIndentation(20)
        self.goal_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.goal_tree.customContextMenuRequested.connect(self.showContextMenu)
        self.goal_tree.itemChanged.connect(self.handleItemStatusChanged)
        
        # Set column widths
        self.goal_tree.setColumnWidth(0, 400)  # Goal title
        self.goal_tree.setColumnWidth(1, 100)  # Due date
        self.goal_tree.setColumnWidth(2, 100)  # Due time
        self.goal_tree.setColumnWidth(3, 100)  # Status
        
        main_layout.addWidget(self.goal_tree)
        
        # Apply styles
        self.setStyleSheet("""
            #goalHeader {
                background-color: #FFFFFF;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            #goalTitle {
                color: #111827;
            }
            #addGoalButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            #addGoalButton:hover {
                background-color: #4338CA;
            }
            #addGoalButton:pressed {
                background-color: #3730A3;
            }
            #goalSeparator {
                background-color: #E5E7EB;
            }
            #goalTree {
                background-color: #F9FAFB;
                border: none;
            }
            QTreeWidget::item {
                padding: 6px 0;
            }
            QTreeWidget::item:selected {
                background-color: #EEF2FF;
            }
        """)
    
    def showAddGoalDialog(self):
        """Show the dialog to add a new goal."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Goal")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_layout.addWidget(title_label)
        self.title_input = QLineEdit()
        title_layout.addWidget(self.title_input)
        layout.addLayout(title_layout)
        
        # Parent goal (for sub-goals)
        parent_layout = QHBoxLayout()
        parent_label = QLabel("Parent Goal:")
        parent_layout.addWidget(parent_label)
        self.parent_input = QComboBox()
        self.parent_input.addItem("None", None)
        
        # Add existing goals as potential parents
        for goal in self.goals:
            self.parent_input.addItem(goal['title'], goal['id'])
        
        parent_layout.addWidget(self.parent_input)
        layout.addLayout(parent_layout)
        
        # Due date
        date_layout = QHBoxLayout()
        date_label = QLabel("Due Date:")
        date_layout.addWidget(date_label)
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate().addDays(7))  # Default to one week from now
        date_layout.addWidget(self.date_input)
        layout.addLayout(date_layout)
        
        # Due time
        time_layout = QHBoxLayout()
        time_label = QLabel("Due Time:")
        time_layout.addWidget(time_label)
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime(12, 0))  # Default to noon
        time_layout.addWidget(self.time_input)
        layout.addLayout(time_layout)
        
        # Priority
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Priority:")
        priority_layout.addWidget(priority_label)
        self.priority_input = QComboBox()
        self.priority_input.addItems(["Low", "Medium", "High"])
        priority_layout.addWidget(self.priority_input)
        layout.addLayout(priority_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.addGoal(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def addGoal(self, dialog):
        """Add a new goal from the dialog data."""
        title = self.title_input.text().strip()
        parent_id = self.parent_input.currentData()
        due_date = self.date_input.date().toString("yyyy-MM-dd")
        due_time = self.time_input.time().toString("HH:mm")
        priority = self.priority_input.currentIndex()
        
        if not title:
            QMessageBox.warning(dialog, "Error", "Goal title cannot be empty")
            return
        
        # In a real app, we'd save to database
        # For now, we'll use a random ID
        goal_id = random.randint(1000, 9999)
        
        # Create the goal dictionary
        goal = {
            'id': goal_id,
            'title': title,
            'parent_id': parent_id,
            'due_date': due_date,
            'due_time': due_time,
            'priority': priority,
            'completed': False
        }
        
        # Add to our list
        self.goals.append(goal)
        
        # Add to the tree
        self.addGoalToTree(goal)
        
        # Emit signal
        self.goalAdded.emit(goal)
        
        # Close the dialog
        dialog.accept()
    
    def addGoalToTree(self, goal, parent_item=None):
        """Add a goal to the tree widget."""
        # Create a new tree item
        item = QTreeWidgetItem()
        item.setText(0, goal['title'])
        item.setText(1, goal['due_date'])
        item.setText(2, goal['due_time'])
        item.setData(0, Qt.ItemDataRole.UserRole, goal['id'])
        
        # Set the status checkbox
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        status = Qt.CheckState.Checked if goal['completed'] else Qt.CheckState.Unchecked
        item.setCheckState(3, status)
        
        # Set priority color
        if goal['priority'] == 0:  # Low
            item.setBackground(0, Qt.GlobalColor.green)
        elif goal['priority'] == 1:  # Medium
            item.setBackground(0, Qt.GlobalColor.yellow)
        else:  # High
            item.setBackground(0, Qt.GlobalColor.red)
        
        # Add to parent or root
        if parent_item:
            parent_item.addChild(item)
        else:
            if goal['parent_id'] is None:
                # This is a root goal
                self.goal_tree.addTopLevelItem(item)
            else:
                # Find parent item
                for i in range(self.goal_tree.topLevelItemCount()):
                    top_item = self.goal_tree.topLevelItem(i)
                    if self.findParentItem(top_item, goal['parent_id']):
                        break
        
        # Expand the item
        item.setExpanded(True)
        
        return item
    
    def findParentItem(self, item, parent_id):
        """Find a parent item by ID and add the child to it."""
        if item.data(0, Qt.ItemDataRole.UserRole) == parent_id:
            return item
        
        # Search in children
        for i in range(item.childCount()):
            child = item.child(i)
            result = self.findParentItem(child, parent_id)
            if result:
                return result
        
        return None
    
    def handleItemStatusChanged(self, item, column):
        """Handle when a goal's status is changed."""
        if column == 3:  # Status column
            goal_id = item.data(0, Qt.ItemDataRole.UserRole)
            completed = item.checkState(3) == Qt.CheckState.Checked
            
            # Update our data
            for goal in self.goals:
                if goal['id'] == goal_id:
                    goal['completed'] = completed
                    break
            
            # Emit signal
            self.goalCompleted.emit(goal_id, completed)
            
            # If parent is completed, complete all children
            if completed:
                self.updateChildrenStatus(item, Qt.CheckState.Checked)
    
    def updateChildrenStatus(self, parent_item, status):
        """Update the status of all children when parent status changes."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child.setCheckState(3, status)
            
            # Update our data
            goal_id = child.data(0, Qt.ItemDataRole.UserRole)
            for goal in self.goals:
                if goal['id'] == goal_id:
                    goal['completed'] = (status == Qt.CheckState.Checked)
                    break
            
            # Emit signal
            self.goalCompleted.emit(goal_id, status == Qt.CheckState.Checked)
            
            # Recurse for sub-goals
            if child.childCount() > 0:
                self.updateChildrenStatus(child, status)
    
    def showContextMenu(self, position):
        """Show a context menu for the selected goal."""
        item = self.goal_tree.itemAt(position)
        if not item:
            return
            
        goal_id = item.data(0, Qt.ItemDataRole.UserRole)
        
        menu = QDialog.createPopupMenu()
        
        edit_action = menu.addAction("Edit Goal")
        edit_action.triggered.connect(lambda: self.showEditGoalDialog(goal_id))
        
        delete_action = menu.addAction("Delete Goal")
        delete_action.triggered.connect(lambda: self.deleteGoal(goal_id))
        
        add_subgoal_action = menu.addAction("Add Sub-Goal")
        add_subgoal_action.triggered.connect(lambda: self.showAddSubGoalDialog(goal_id))
        
        menu.exec(self.goal_tree.viewport().mapToGlobal(position))
    
    def showEditGoalDialog(self, goal_id):
        """Show dialog to edit an existing goal."""
        # Find the goal
        goal = None
        for g in self.goals:
            if g['id'] == goal_id:
                goal = g
                break
        
        if not goal:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Goal: {goal['title']}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_layout.addWidget(title_label)
        self.edit_title_input = QLineEdit(goal['title'])
        title_layout.addWidget(self.edit_title_input)
        layout.addLayout(title_layout)
        
        # Parent goal (for sub-goals)
        parent_layout = QHBoxLayout()
        parent_label = QLabel("Parent Goal:")
        parent_layout.addWidget(parent_label)
        self.edit_parent_input = QComboBox()
        self.edit_parent_input.addItem("None", None)
        
        # Add existing goals as potential parents (except self and descendants)
        for g in self.goals:
            if g['id'] != goal_id:
                self.edit_parent_input.addItem(g['title'], g['id'])
        
        # Set current parent
        index = self.edit_parent_input.findData(goal['parent_id'])
        if index >= 0:
            self.edit_parent_input.setCurrentIndex(index)
        
        parent_layout.addWidget(self.edit_parent_input)
        layout.addLayout(parent_layout)
        
        # Due date
        date_layout = QHBoxLayout()
        date_label = QLabel("Due Date:")
        date_layout.addWidget(date_label)
        self.edit_date_input = QDateEdit()
        self.edit_date_input.setCalendarPopup(True)
        self.edit_date_input.setDate(QDate.fromString(goal['due_date'], "yyyy-MM-dd"))
        date_layout.addWidget(self.edit_date_input)
        layout.addLayout(date_layout)
        
        # Due time
        time_layout = QHBoxLayout()
        time_label = QLabel("Due Time:")
        time_layout.addWidget(time_label)
        self.edit_time_input = QTimeEdit()
        self.edit_time_input.setTime(QTime.fromString(goal['due_time'], "HH:mm"))
        time_layout.addWidget(self.edit_time_input)
        layout.addLayout(time_layout)
        
        # Priority
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Priority:")
        priority_layout.addWidget(priority_label)
        self.edit_priority_input = QComboBox()
        self.edit_priority_input.addItems(["Low", "Medium", "High"])
        self.edit_priority_input.setCurrentIndex(goal['priority'])
        priority_layout.addWidget(self.edit_priority_input)
        layout.addLayout(priority_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.updateGoal(dialog, goal_id))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def updateGoal(self, dialog, goal_id):
        """Update an existing goal."""
        title = self.edit_title_input.text().strip()
        parent_id = self.edit_parent_input.currentData()
        due_date = self.edit_date_input.date().toString("yyyy-MM-dd")
        due_time = self.edit_time_input.time().toString("HH:mm")
        priority = self.edit_priority_input.currentIndex()
        
        if not title:
            QMessageBox.warning(dialog, "Error", "Goal title cannot be empty")
            return
        
        # Update the goal in our list
        for goal in self.goals:
            if goal['id'] == goal_id:
                goal['title'] = title
                goal['parent_id'] = parent_id
                goal['due_date'] = due_date
                goal['due_time'] = due_time
                goal['priority'] = priority
                break
        
        # Refresh the tree
        self.refreshGoalTree()
        
        # Close the dialog
        dialog.accept()
    
    def deleteGoal(self, goal_id):
        """Delete a goal and its sub-goals."""
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            "Are you sure you want to delete this goal and all its sub-goals?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Find all sub-goals
        sub_goal_ids = self.findSubGoalIds(goal_id)
        
        # Delete the goal and sub-goals
        self.goals = [g for g in self.goals if g['id'] != goal_id and g['id'] not in sub_goal_ids]
        
        # Refresh the tree
        self.refreshGoalTree()
        
        # Emit signal
        self.goalDeleted.emit(goal_id)
    
    def findSubGoalIds(self, parent_id):
        """Find all sub-goal IDs for a given parent ID."""
        sub_goal_ids = []
        
        for goal in self.goals:
            if goal['parent_id'] == parent_id:
                sub_goal_ids.append(goal['id'])
                # Recursively find sub-sub-goals
                sub_goal_ids.extend(self.findSubGoalIds(goal['id']))
        
        return sub_goal_ids
    
    def showAddSubGoalDialog(self, parent_id):
        """Show dialog to add a sub-goal."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Sub-Goal")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_layout.addWidget(title_label)
        self.subgoal_title_input = QLineEdit()
        title_layout.addWidget(self.subgoal_title_input)
        layout.addLayout(title_layout)
        
        # Due date
        date_layout = QHBoxLayout()
        date_label = QLabel("Due Date:")
        date_layout.addWidget(date_label)
        self.subgoal_date_input = QDateEdit()
        self.subgoal_date_input.setCalendarPopup(True)
        self.subgoal_date_input.setDate(QDate.currentDate().addDays(7))
        date_layout.addWidget(self.subgoal_date_input)
        layout.addLayout(date_layout)
        
        # Due time
        time_layout = QHBoxLayout()
        time_label = QLabel("Due Time:")
        time_layout.addWidget(time_label)
        self.subgoal_time_input = QTimeEdit()
        self.subgoal_time_input.setTime(QTime(12, 0))
        time_layout.addWidget(self.subgoal_time_input)
        layout.addLayout(time_layout)
        
        # Priority
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Priority:")
        priority_layout.addWidget(priority_label)
        self.subgoal_priority_input = QComboBox()
        self.subgoal_priority_input.addItems(["Low", "Medium", "High"])
        priority_layout.addWidget(self.subgoal_priority_input)
        layout.addLayout(priority_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.addSubGoal(dialog, parent_id))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def addSubGoal(self, dialog, parent_id):
        """Add a sub-goal."""
        title = self.subgoal_title_input.text().strip()
        due_date = self.subgoal_date_input.date().toString("yyyy-MM-dd")
        due_time = self.subgoal_time_input.time().toString("HH:mm")
        priority = self.subgoal_priority_input.currentIndex()
        
        if not title:
            QMessageBox.warning(dialog, "Error", "Goal title cannot be empty")
            return
        
        # In a real app, we'd save to database
        # For now, we'll use a random ID
        goal_id = random.randint(1000, 9999)
        
        # Create the goal dictionary
        goal = {
            'id': goal_id,
            'title': title,
            'parent_id': parent_id,
            'due_date': due_date,
            'due_time': due_time,
            'priority': priority,
            'completed': False
        }
        
        # Add to our list
        self.goals.append(goal)
        
        # Refresh the tree
        self.refreshGoalTree()
        
        # Emit signal
        self.goalAdded.emit(goal)
        
        # Close the dialog
        dialog.accept()
    
    def refreshGoalTree(self):
        """Refresh the entire goal tree."""
        self.goal_tree.clear()
        
        # First add all root goals
        for goal in [g for g in self.goals if g['parent_id'] is None]:
            item = self.addGoalToTree(goal)
            
            # Then add their sub-goals
            self.addSubGoalsToTree(goal['id'], item)
    
    def addSubGoalsToTree(self, parent_id, parent_item):
        """Add sub-goals to the tree recursively."""
        for goal in [g for g in self.goals if g['parent_id'] == parent_id]:
            item = self.addGoalToTree(goal, parent_item)
            
            # Recursively add sub-sub-goals
            self.addSubGoalsToTree(goal['id'], item)
    
    def loadGoals(self):
        """Load goals from the database."""
        if hasattr(self.parent, 'cursor') and self.parent.cursor:
            try:
                # Execute SQL to get all goals
                self.parent.cursor.execute("""
                    SELECT id, title, parent_id, due_date, due_time, priority, completed 
                    FROM goals
                    ORDER BY due_date
                """)
                
                # Process results
                results = self.parent.cursor.fetchall()
                
                # Clear existing goals
                self.goals = []
                
                # Process results
                for row in results:
                    goal = {
                        'id': row[0],
                        'title': row[1],
                        'parent_id': row[2],
                        'due_date': row[3],
                        'due_time': row[4],
                        'priority': row[5],
                        'completed': bool(row[6])
                    }
                    self.goals.append(goal)
                
                # Refresh the tree
                self.refreshGoalTree()
            except Exception as e:
                print(f"Error loading goals: {e}")
                # Add some sample goals for testing
                self.addSampleGoals()
        else:
            # Add some sample goals for testing
            self.addSampleGoals()
    
    def addSampleGoals(self):
        """Add sample goals for testing."""
        # Clear existing goals
        self.goals = []
        
        # Generate sample goals
        sample_goals = [
            {
                'id': 1001,
                'title': "Complete Project Proposal",
                'parent_id': None,
                'due_date': QDate.currentDate().addDays(7).toString("yyyy-MM-dd"),
                'due_time': "12:00",
                'priority': 2,  # High
                'completed': False
            },
            {
                'id': 1002,
                'title': "Research Project Requirements",
                'parent_id': 1001,
                'due_date': QDate.currentDate().addDays(2).toString("yyyy-MM-dd"),
                'due_time': "12:00",
                'priority': 1,  # Medium
                'completed': False
            },
            {
                'id': 1003,
                'title': "Create Presentation",
                'parent_id': 1001,
                'due_date': QDate.currentDate().addDays(5).toString("yyyy-MM-dd"),
                'due_time': "12:00",
                'priority': 1,  # Medium
                'completed': False
            },
            {
                'id': 1004,
                'title': "Learn Python",
                'parent_id': None,
                'due_date': QDate.currentDate().addDays(30).toString("yyyy-MM-dd"),
                'due_time': "12:00",
                'priority': 0,  # Low
                'completed': False
            },
            {
                'id': 1005,
                'title': "Complete Online Course",
                'parent_id': 1004,
                'due_date': QDate.currentDate().addDays(20).toString("yyyy-MM-dd"),
                'due_time': "12:00",
                'priority': 0,  # Low
                'completed': False
            }
        ]
        
        # Add sample goals
        self.goals.extend(sample_goals)
        
        # Refresh the tree
        self.refreshGoalTree()
    
    def refresh(self):
        """Refresh the widget's data."""
        self.loadGoals() 