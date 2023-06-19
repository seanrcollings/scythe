from datetime import datetime
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Select, Button, Label
from textual.message import Message
from textual.reactive import reactive
from scythe_cli import utils

from scythe_cli.harvest import AsyncHarvest, TimeEntry
from scythe_cli.utils import display_time


class TimerModal(Vertical):
    class Cancel(Message):
        ...

    class NewTimer(Message):
        def __init__(self, entry: TimeEntry):
            self.entry = entry

            super().__init__()

    class UpdateTimer(Message):
        def __init__(self, entry: TimeEntry):
            self.entry = entry

            super().__init__()

    class DeleteTimer(Message):
        def __init__(self, entry: TimeEntry):
            self.entry = entry

            super().__init__()

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    timer = reactive[TimeEntry | None](None)

    def __init__(self, harvest: AsyncHarvest, **kwargs):
        super().__init__(**kwargs)
        self.harvest = harvest

    def compose(self) -> ComposeResult:
        with Vertical(id="body"):
            yield Label("New Timer", id="title")
            yield Select([], prompt="Project", id="project")
            yield Select([], prompt="Task", id="task", disabled=True)
            yield Input(placeholder="Note", id="note")
            with Horizontal(id="hours-container"):
                yield Input(placeholder="0:00", id="hours")

            with Horizontal(id="actions"):
                with Horizontal(id="action-buttons"):
                    yield Button("Cancel", id="cancel")
                    yield Button("Delete", id="delete", variant="error")
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

    def watch_timer(self, timer: TimeEntry | None) -> None:
        if not timer:
            return

        projects_select = self.query_one("#project", Select)
        projects_select.value = timer.project.id

        self.on_select_changed(Select.Changed(projects_select, timer.project.id))

        tasks_select = self.query_one("#task", Select)
        tasks_select.value = timer.task.id

        notes_input = self.query_one("#note", Input)
        notes_input.value = timer.notes or ""

        hours_input = self.query_one("#hours", Input)
        hours_input.value = display_time(timer.seconds(), "minutes")

        self.add_class("edit")

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
        tasks_select.set_options(
            [(t.task.name, t.task.id) for t in project.task_assignments]
        )

    def action_cancel(self):
        self.post_message(self.Cancel())
        self.clear()

    @on(Button.Pressed, "#cancel")
    async def on_cancel(self, event: Button.Pressed):
        self.post_message(self.Cancel())
        self.clear()
        self.timer = None

    @on(Button.Pressed, "#save")
    async def on_save(self, event: Button.Pressed) -> None:
        if self.timer:
            timer = await self.update_timer()
            self.timer = None
            self.remove_class("edit")
            self.post_message(self.UpdateTimer(timer))
        else:
            timer = await self.create_timer()
            self.post_message(self.NewTimer(timer))

        self.clear()

    @on(Button.Pressed, "#delete")
    async def on_delete(self, event: Button.Pressed) -> None:
        if self.timer:
            await self.harvest.delete_timer(self.timer.id)
            self.remove_class("edit")
            self.post_message(self.DeleteTimer(self.timer))
            self.timer = None
            self.clear()

    async def create_timer(self) -> TimeEntry:
        data = self.data()
        timer = await self.harvest.create_timer(
            {
                "project_id": data["project"],
                "task_id": data["task"],
                "notes": data["note"],
                "spent_date": self.app.current_day.strftime("%Y-%m-%d"),  # type: ignore
            }
        )
        return timer

    async def update_timer(self) -> TimeEntry:
        assert self.timer
        data = self.data()
        timer = await self.harvest.update_timer(
            self.timer.id,
            {
                "project_id": data["project"],
                "task_id": data["task"],
                "notes": data["note"],
                "hours": utils.convert_time(data["hours"]),
            },
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
