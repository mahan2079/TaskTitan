from datetime import datetime, timedelta
import json

def calculate_weeks_since_birth(birth_date):
    """Calculate the number of weeks since a birth date."""
    birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
    today = datetime.today()
    delta = today - birth_date
    weeks_since_birth = delta.days // 7
    return weeks_since_birth

def validate_time(time_str):
    """Validate a time string in HH:MM format."""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def load_colors(config_path="colors_config.json"):
    """Load color configuration from a JSON file."""
    try:
        with open(config_path, "r") as file:
            colors = json.load(file)
            return colors
    except FileNotFoundError:
        # Default colors
        return {
            "calendar_color": "#E6E6FA",
            "past_week_color": "#E0E0E0",
            "current_week_color": "#FFEBCC",
            "future_week_color": "#FFFFFF",
            "weekly_planner_color": "#FFFFFF"
        }

def save_colors(colors, config_path="colors_config.json"):
    """Save color configuration to a JSON file."""
    with open(config_path, "w") as file:
        json.dump(colors, file) 