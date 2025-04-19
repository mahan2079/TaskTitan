from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime

class DailyChartWindow(QMainWindow):
    """Window for displaying daily time chart."""
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
    """Window for displaying daily pie chart of time distribution."""
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