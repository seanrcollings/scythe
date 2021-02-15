"""Helper Classes to abstract away some of the complexity of the returned objects"""


class DictWrapper:
    def __init__(self, data: dict):
        self.data = data

    def __str__(self):
        return "\n".join(f"{key}: {value}" for key, value in self.data.items())

    def __getattr__(self, attr):
        return self.data[attr]

    @classmethod
    def from_list(cls, items):
        return list(cls(item) for item in items)


class Project(DictWrapper):
    id: int
    is_active: bool
    name: str

    def __init__(self, project: dict):
        self.tasks = Task.from_list(project["task_assignments"])
        ext: dict = project["project"]
        super().__init__(project | ext)


class Task(DictWrapper):
    def __init__(self, task: dict):
        ext: dict = task["task"]
        super().__init__(task | ext)


class TimeEntry(DictWrapper):
    ...


# def __init__(self, entry: dict):
