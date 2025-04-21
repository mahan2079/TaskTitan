class Habit:
    def __init__(self, id=None, title="", description="", days_of_week=None, 
                 start_time=None, end_time=None, category=None, completed=False):
        self.id = id
        self.title = title
        self.description = description
        self.days_of_week = days_of_week or []  # List of weekdays (0-6)
        self.start_time = start_time
        self.end_time = end_time
        self.category = category
        self.completed = completed 