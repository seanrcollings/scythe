from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Select, Static, Button, Label
from textual.message import Message


class NewTimerModal(Vertical):
    class Cancel(Message):
        ...

    class NewTimer(Message):
        def __init__(self, project: str, task: str, note: str):
            self.project = project
            self.task = task
            self.note = note

            super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="body"):
            yield Label("New Timer", id="title")
            yield Select([("Project 1", "Project 1")], prompt="Project", id="project")
            yield Select([("Task 1", "Task 1")], prompt="Task", id="task")
            yield Input(placeholder="Note", id="note")

            with Horizontal(id="actions"):
                yield Static(id="spacer")
                yield Button("Cancel", id="cancel")
                yield Button("Save", id="save", variant="primary")

    @on(Button.Pressed, "#cancel")
    async def on_cancel(self, event: Button.Pressed):
        self.post_message(self.Cancel())
        self.clear()

    @on(Button.Pressed, "#save")
    async def on_save(self, event: Button.Pressed):
        self.post_message(self.NewTimer(**self.data()))
        self.clear()

    def data(self):
        inputs = self.query(Input)

        data = {}

        for input in inputs:
            data[input.id] = input.value

        selects = self.query(Select)

        for select in selects:
            data[select.id] = select.value

        return data

    def clear(self):
        inputs = self.query(Input)

        for input in inputs:
            input.value = ""

        selects = self.query(Select)

        for select in selects:
            select.value = None
