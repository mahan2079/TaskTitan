class Event:
    def __init__(self, id=None, title="", description="", date=None, 
                 start_time=None, end_time=None, category=None):
        self.id = id
        self.title = title
        self.description = description
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.category = category 