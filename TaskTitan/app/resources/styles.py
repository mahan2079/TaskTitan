"""
Style resources for TaskTitan.

This module provides functions to access and apply custom styles for different parts of the application.
"""

import os

# The resources directory
RESOURCES_DIR = os.path.dirname(os.path.abspath(__file__))

# Custom component styles
DASHBOARD_CARD_STYLE = """
    QFrame[class="card"] {
        background-color: white;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        padding: 16px;
    }
    
    QLabel[class="dashboard-widget-header"] {
        font-size: 18px;
        font-weight: bold;
        color: #1E293B;
        padding-bottom: 8px;
    }
"""

TASK_ITEM_STYLE = """
    QFrame[class="task-item"] {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        margin: 4px;
        padding: 12px;
    }
    
    QFrame[class="task-item"]:hover {
        border: 1px solid #CBD5E1;
        background-color: #F8FAFC;
    }
    
    QFrame[class="task-item-completed"] {
        background-color: #F0FDF4;
        border-radius: 8px;
        border: 1px solid #D1FAE5;
        margin: 4px;
        padding: 12px;
    }
    
    QLabel[class="task-title"] {
        font-size: 16px;
        font-weight: bold;
        color: #1E293B;
    }
    
    QLabel[class="task-title-completed"] {
        font-size: 16px;
        font-weight: bold;
        color: #047857;
        text-decoration: line-through;
    }
    
    QLabel[class="task-date"] {
        color: #64748B;
        font-size: 13px;
    }
"""

POMODORO_STYLE = """
    QFrame[class="pomodoro-active"] {
        background-color: #FEE2E2;
        border: 2px solid #EF4444;
        border-radius: 16px;
        padding: 24px;
    }
    
    QFrame[class="pomodoro-break"] {
        background-color: #DBEAFE;
        border: 2px solid #3B82F6;
        border-radius: 16px;
        padding: 24px;
    }
    
    QLabel[class="pomodoro-time"] {
        font-size: 72px;
        font-weight: bold;
        color: #1E293B;
    }
    
    QLabel[class="pomodoro-status"] {
        font-size: 18px;
        font-weight: bold;
        color: #1E293B;
    }
"""

CALENDAR_STYLE = """
    QLabel[class="date-cell"] {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 8px;
        font-size: 16px;
        font-weight: bold;
    }
    
    QLabel[class="date-cell-current"] {
        background-color: #EFF6FF;
        border: 2px solid #3B82F6;
        border-radius: 6px;
        padding: 8px;
        font-size: 16px;
        font-weight: bold;
        color: #1E293B;
    }
    
    QLabel[class="date-cell-has-events"] {
        background-color: #F0FDF4;
        border: 1px solid #D1FAE5;
        border-radius: 6px;
        padding: 8px;
        font-size: 16px;
        font-weight: bold;
    }
"""

def get_component_style(component_name):
    """
    Get a specific component style.
    
    Args:
        component_name (str): Name of the component style to retrieve
        
    Returns:
        str: The stylesheet for the component
    """
    styles = {
        "dashboard_card": DASHBOARD_CARD_STYLE,
        "task_item": TASK_ITEM_STYLE,
        "pomodoro": POMODORO_STYLE,
        "calendar": CALENDAR_STYLE
    }
    
    return styles.get(component_name, "") 