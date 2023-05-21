from datetime import datetime
from typing import Iterable
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Select, Static, Button, Label
from textual.message import Message

from scythe_cli.harvest import AsyncHarvest, TimeEntry


class NewTimerModal(Vertical):
    class Cancel(Message):
        ...

    class NewTimer(Message):
        def __init__(self, entry: TimeEntry):
            self.entry = entry

            super().__init__()

    def __init__(self, harvest: AsyncHarvest, user_id: str, **kwargs):
        super().__init__(**kwargs)
        self.harvest = harvest
        self.user_id = user_id

    def compose(self) -> ComposeResult:
        with Vertical(id="body"):
            yield Label("New Timer", id="title")
            yield Select([], prompt="Project", id="project")
            yield Select([], prompt="Task", id="task", disabled=True)
            yield Input(placeholder="Note", id="note")

            with Horizontal(id="actions"):
                yield Static(id="spacer")
                yield Button("Cancel", id="cancel")
                yield Button("Save", id="save", variant="primary")

    async def on_mount(self) -> None:
        self.get_projects()

    @work(exclusive=True)
    async def get_projects(self) -> None:
        self.projects = await self.harvest.get_user_projects()
        projects_select = self.query_one("#project", Select)
        projects_select.set_options(
            [(p.project.name, p.project.id) for p in self.projects if p.is_active]
        )

    def on_select_changed(self, event: Select.Changed):
        if not event.control:
            return

        if event.control.id == "project":
            self.on_project_changed(event)

    def on_project_changed(self, event: Select.Changed):
        if not event.value:
            return
        project = next((p for p in self.projects if p.project.id == event.value), None)

        if not project:
            return

        tasks_select = self.query_one("#task", Select)
        tasks_select.disabled = False
        # TODO: why does the fail on the second selection?
        tasks_select.set_options(
            [(t.task.name, t.task.id) for t in project.task_assignments]
        )

    @on(Button.Pressed, "#cancel")
    async def on_cancel(self, event: Button.Pressed):
        self.post_message(self.Cancel())
        self.clear()

    @on(Button.Pressed, "#save")
    async def on_save(self, event: Button.Pressed):
        timer = await self.create_timer()
        self.post_message(self.NewTimer(**self.data()))
        self.clear()

    async def create_timer(self):
        data = self.data()
        timer = await self.harvest.create_timer(
            {
                "project_id": data["project"],
                "task_id": data["task"],
                "notes": data["note"],
                "spent_date": datetime.now().strftime("%Y-%m-%d"),
            }
        )
        return timer

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
