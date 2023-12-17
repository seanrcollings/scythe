from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Container
from textual.widgets import Button, Label
from textual.message import Message
from textual.reactive import reactive

from scythe_cli.harvest import AsyncHarvest, TimeEntry
from scythe_cli.ui.widgets.time_display import TimeDisplay


class Timer(Container, can_focus=True):
    class TimerMessage(Message):
        def __init__(self, timer: "Timer") -> None:
            self.timer = timer
            super().__init__()

    class Start(TimerMessage):
        ...

    class Stop(TimerMessage):
        ...

    class Edit(TimerMessage):
        ...

    class Delete(TimerMessage):
        ...

    BINDINGS = [
        ("e", "edit_timer", "Edit Timer"),
        ("d", "delete_timer", "Delete Timer"),
        ("enter", "toggle_timer", "Toggle Timer"),
    ]

    running: reactive[bool] = reactive(False)

    def __init__(
        self,
        entry: TimeEntry,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.entry = entry

    def compose(self) -> ComposeResult:
        with Horizontal(id="info"):
            yield Label(self.entry.project.name, id="project")
            yield Label(self.entry.task.name, id="task")
            yield Label(self.entry.notes or "", id="description")

        yield TimeDisplay()

        with Horizontal(id="actions"):
            yield Button.success("Start", id="start")
            yield Button.error("Stop", id="stop")
            yield Button("Edit", id="edit")

    def on_mount(self) -> None:
        if self.entry.is_running:
            self.running = True

        seconds = self.entry.seconds()
        display = self.query_one(TimeDisplay)
        display.time = seconds
        display.total = seconds

    def watch_running(self, running: bool) -> None:
        if running:
            self.add_class("running")
            display = self.query_one(TimeDisplay)
            display.start()
        else:
            self.remove_class("running")
            display = self.query_one(TimeDisplay)
            display.stop()

    @on(Button.Pressed, "#start")
    async def on_start(self, event):
        self.post_message(self.Start(self))

    @on(Button.Pressed, "#stop")
    async def on_stop(self, event):
        self.post_message(self.Stop(self))

    @on(Button.Pressed, "#edit")
    async def on_edit(self, event):
        self.post_message(self.Edit(self))

    def action_edit_timer(self):
        self.post_message(self.Edit(self))

    async def action_delete_timer(self):
        self.post_message(self.Delete(self))

    def action_toggle_timer(self):
        if self.running:
            self.post_message(self.Stop(self))
        else:
            self.post_message(self.Start(self))

    def update_entry(self, entry: TimeEntry) -> None:
        self.entry = entry
        project_label = self.query_one("#project", Label)
        project_label.update(entry.project.name)
        task_label = self.query_one("#task", Label)
        task_label.update(entry.task.name)
        description_label = self.query_one("#description", Label)
        description_label.update(entry.notes or "")

        seconds = entry.seconds()
        display = self.query_one(TimeDisplay)
        display.time = seconds
        display.total = seconds
