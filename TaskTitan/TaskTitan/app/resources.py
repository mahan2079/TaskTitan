"""
Resource management for TaskTitan.

This module provides helper functions to access application resources like icons
and contains application-wide constants.
"""
import os
import sys
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap

# View indices for the stacked widget
DASHBOARD_VIEW = 0
ACTIVITIES_VIEW = 1  # Combined view for tasks, events, habits
GOALS_VIEW = 2
PRODUCTIVITY_VIEW = 3
POMODORO_VIEW = 4
SETTINGS_VIEW = 5

# View names
VIEW_NAMES = {
    DASHBOARD_VIEW: "Dashboard",
    ACTIVITIES_VIEW: "Activities",
    GOALS_VIEW: "Goals",
    PRODUCTIVITY_VIEW: "Productivity",
    POMODORO_VIEW: "Pomodoro",
    SETTINGS_VIEW: "Settings"
}

# Application metadata
APP_NAME = "TaskTitan"
APP_VERSION = "1.0.0" 