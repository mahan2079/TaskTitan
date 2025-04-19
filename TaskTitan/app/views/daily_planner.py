from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QHeaderView, QLabel, QLineEdit, QTimeEdit, QPushButton, QCheckBox, QDialog,
    QDialogButtonBox, QTextEdit, QMenu, QAbstractItemView, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QTime
from app.controllers.utils import validate_time
from app.views.charts import DailyChartWindow, DailyPieChartWindow

class DailyPlanner(QMainWindow):
    """Daily planner window allowing management of daily tasks and events."""
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

            edit_action = QMenu.addAction(menu, 'Edit')
            edit_action.triggered.connect(lambda: self.open_edit_event_dialog(event_id))
            menu.addAction(edit_action)

            delete_action = QMenu.addAction(menu, 'Delete')
            delete_action.triggered.connect(lambda: self.delete_event(event_id))
            menu.addAction(delete_action)

            menu.exec_(self.event_list.viewport().mapToGlobal(position))

    def open_timeboxed_context_menu(self, position):
        item = self.timeboxed_list.itemAt(position)
        if item:
            row = item.row()
            event_id = self.timeboxed_list.item(row, 0).data(Qt.UserRole)
            menu = QMenu()

            edit_action = QMenu.addAction(menu, 'Edit')
            edit_action.triggered.connect(lambda: self.open_edit_timeboxed_dialog(event_id))
            menu.addAction(edit_action)

            delete_action = QMenu.addAction(menu, 'Delete')
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
            from PyQt5.QtWidgets import QMessageBox
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
            from PyQt5.QtWidgets import QMessageBox
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
            from PyQt5.QtWidgets import QMessageBox
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
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid description and time.")
            return

        self.cursor.execute("UPDATE events SET time = ?, description = ? WHERE id = ?", (time_str, description, event_id))
        self.conn.commit()
        self.populate_events()

    def open_edit_timeboxed_dialog(self, event_id):
        self.cursor.execute("SELECT id, time, description, completed FROM events WHERE id = ?", (event_id,))
        event = self.cursor.fetchone()
        if not event:
            from PyQt5.QtWidgets import QMessageBox
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
            from PyQt5.QtWidgets import QMessageBox
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