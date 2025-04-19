# TaskTitan

A comprehensive productivity and task management application built with PyQt5.

## Features

- **Goal Management**: Create, organize, and track hierarchical goals
- **Habit Tracking**: Monitor daily habits and routines
- **Weekly Planning**: Plan your weeks with a structured task system
- **Daily Planning**: Organize your day with events and tasks
- **Productivity Tracking**: Track and visualize your productivity sessions
- **Pomodoro Timer**: Focus on tasks with a built-in Pomodoro timer
- **Data Visualization**: View insights into your productivity and time usage

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/TaskTitan.git
cd TaskTitan
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
```
python -m app.main
```

## Project Structure

```
TaskTitan/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   └── database.py          # Database initialization
│   ├── controllers/             # Logic and utilities
│   │   ├── __init__.py
│   │   └── utils.py             # Utility functions
│   ├── views/                   # UI components
│   │   ├── __init__.py
│   │   ├── smart_scheduler.py   # Main application window
│   │   ├── daily_planner.py     # Daily planner view
│   │   ├── weekly_planner.py    # Weekly planner view
│   │   ├── calendar_widget.py   # Custom calendar widget
│   │   └── charts.py            # Data visualization
│   └── themes/                  # UI styling
│       ├── __init__.py
│       └── dark_theme.py        # Dark theme styling
└── requirements.txt             # Dependencies
```

## Usage

The application includes several views for managing different aspects of your productivity:

- **Calendar View**: Click on a date to open the daily planner
- **Weekly View**: Click on a week to open the weekly planner
- **Goals**: Create and manage hierarchical goals with due dates
- **Habits**: Track daily routines and habits
- **Productivity**: Log and track productivity sessions
- **Pomodoro**: Use the Pomodoro timer for focused work sessions
- **Visualizations**: View charts of your productivity data

## License

This project is licensed under the MIT License - see the LICENSE file for details. 