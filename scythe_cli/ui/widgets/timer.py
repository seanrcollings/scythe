from textual import on
from textual.events import Key
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, Label
from textual.message import Message
from textual.reactive import reactive
from time import monotonic

from scythe_cli.harvest import AsyncHarvest, TimeEntry


class TimeDisplay(Static):
    """A widget to display elapsed time."""

    start_time: reactive[float] = reactive(monotonic)
    time = reactive(0.0)
    total = reactive(0.0)

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        """Method to update time to current."""
        self.time = self.total + (monotonic() - self.start_time)

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:02.0f}")

    def start(self) -> None:
        """Method to start (or resume) time updating."""
        self.start_time = monotonic()
        self.update_timer.resume()

    def stop(self) -> None:
        """Method to stop the time display updating."""
        self.update_timer.pause()
        self.total += monotonic() - self.start_time
        self.time = self.total

    def reset(self) -> None:
        """Method to reset the time display to zero."""
        self.total = 0
        self.time = 0


class Timer(Static, can_focus=True):
    class Started(Message):
        def __init__(self, timer: "Timer") -> None:
            self.timer = timer
            super().__init__()

    class Stopped(Message):
        def __init__(self, timer: "Timer") -> None:
            self.timer = timer
            super().__init__()

    def __init__(
        self,
        entry: TimeEntry,
        harvest: AsyncHarvest,
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        self.entry = entry
        self.harvest = harvest

        super().__init__(
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="info"):
                yield Label(self.entry.project.name, id="project")
                yield Label(self.entry.task.name, id="task")
                yield Label(self.entry.notes, id="description")

            yield TimeDisplay()

            with Horizontal(id="actions"):
                yield Button("Start", id="start")
                yield Button("Stop", id="stop")

    def on_mount(self) -> None:
        if self.entry.is_running:
            self.start_timer()

        seconds = self.entry.seconds()
        display = self.query_one(TimeDisplay)
        display.time = seconds
        display.total = seconds

    @on(Button.Pressed, "#start")
    async def on_start(self, event):
        await self.harvest.start_timer(self.entry.id)
        self.start_timer()

    @on(Button.Pressed, "#stop")
    async def on_stop(self, event):
        await self.harvest.stop_timer(self.entry.id)
        self.stop_timer()

    def on_key(self, event: Key):
        if event.key == "enter":
            self.toggle_timer()

    def toggle_timer(self):
        if self.has_class("running"):
            self.stop_timer()
        else:
            self.start_timer()

    def start_timer(self):
        self.add_class("running")
        display = self.query_one(TimeDisplay)
        display.start()
        self.post_message(self.Started(self))

    def stop_timer(self):
        self.remove_class("running")
        display = self.query_one(TimeDisplay)
        display.stop()
        self.post_message(self.Stopped(self))
