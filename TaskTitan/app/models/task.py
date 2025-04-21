from enum import Enum

class TaskStatus(Enum):
    TODO = 0
    IN_PROGRESS = 1
    COMPLETED = 2

class Task:
    def __init__(self, id=None, title="", description="", due_date=None, 
                 priority=0, category=None, status=TaskStatus.TODO, completed=False):
        self.id = id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.category = category
        self.status = status
        self.completed = completed 