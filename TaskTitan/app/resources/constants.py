"""
Constants for TaskTitan application.

This module defines application-wide constants.
"""

# Application information
APP_NAME = "TaskTitan"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "A comprehensive productivity and task management application"

# Default settings
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_SIDEBAR_WIDTH = 240
DEFAULT_FONT_FAMILY = "Segoe UI"
DEFAULT_FONT_SIZE = 10

# Time constants
POMODORO_WORK_MINUTES = 25
POMODORO_SHORT_BREAK_MINUTES = 5
POMODORO_LONG_BREAK_MINUTES = 15
POMODORO_LONG_BREAK_INTERVAL = 4  # After how many work sessions to take a long break

# Task priorities
PRIORITY_LOW = 0
PRIORITY_MEDIUM = 1
PRIORITY_HIGH = 2
PRIORITY_URGENT = 3

PRIORITY_NAMES = {
    PRIORITY_LOW: "Low",
    PRIORITY_MEDIUM: "Medium",
    PRIORITY_HIGH: "High",
    PRIORITY_URGENT: "Urgent"
}

# Status constants
STATUS_TODO = 0
STATUS_IN_PROGRESS = 1
STATUS_COMPLETED = 2
STATUS_CANCELLED = 3

STATUS_NAMES = {
    STATUS_TODO: "To Do",
    STATUS_IN_PROGRESS: "In Progress",
    STATUS_COMPLETED: "Completed",
    STATUS_CANCELLED: "Cancelled"
}

# Database constants
DB_NAME = "planner.db"

# View constants
DASHBOARD_VIEW = 0
ACTIVITIES_VIEW = 1
GOALS_VIEW = 2
PRODUCTIVITY_VIEW = 3
POMODORO_VIEW = 4
WEEKLY_PLAN_VIEW = 5
SETTINGS_VIEW = 6

VIEW_NAMES = {
    DASHBOARD_VIEW: "Dashboard",
    ACTIVITIES_VIEW: "Activities",
    GOALS_VIEW: "Goals",
    PRODUCTIVITY_VIEW: "Productivity",
    POMODORO_VIEW: "Pomodoro",
    WEEKLY_PLAN_VIEW: "Weekly Plan",
    SETTINGS_VIEW: "Settings"
} 