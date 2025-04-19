from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTreeWidget, 
    QTreeWidgetItem, QHeaderView, QLabel, QLineEdit, QDateEdit, QTimeEdit, 
    QPushButton, QComboBox, QDialog, QDialogButtonBox, QPlainTextEdit, QMenu
)
from PyQt5.QtCore import Qt, QDate, QTime
from app.controllers.utils import validate_time

class WeeklyPlanner(QMainWindow):
    """Weekly planner window for managing tasks for a specific week."""
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

            edit_action = QMenu.addAction(menu, 'Edit')
            edit_action.triggered.connect(lambda: self.open_edit_task_dialog(task_id))
            menu.addAction(edit_action)

            delete_action = QMenu.addAction(menu, 'Delete')
            delete_action.triggered.connect(lambda: self.delete_task(task_id))
            menu.addAction(delete_action)

            menu.exec_(self.weekly_task_tree.viewport().mapToGlobal(position))

    def open_edit_task_dialog(self, task_id):
        self.cursor.execute("SELECT id, title, description, due_date, due_time, completed FROM weekly_tasks WHERE id = ?", (task_id,))
        task = self.cursor.fetchone()
        if not task:
            from PyQt5.QtWidgets import QMessageBox
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
            from PyQt5.QtWidgets import QMessageBox
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
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid title and time.")
            return

        self.cursor.execute("INSERT INTO weekly_tasks (parent_id, week_start_date, title, description, due_date, due_time, completed) VALUES (?, ?, ?, ?, ?, ?, 0)",
                            (parent_id, self.start_of_week.toString("yyyy-MM-dd"), title, description, due_date, due_time))
        self.conn.commit()
        self.populate_weekly_tasks() 