from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button
from textual.message import Message
from textual.reactive import reactive
from time import monotonic


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


class Timer(Static):
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
        project: str,
        task: str,
        note: str,
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        self.project = project
        self.task_name = task
        self.note = note

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
            with Vertical():
                yield Static(self.project, id="project")
                yield Static(self.task_name, id="task")
                yield Static(self.note, id="description")

            yield TimeDisplay()

            with Horizontal(id="actions"):
                yield Button("Start", id="start")
                yield Button("Stop", id="stop")

    @on(Button.Pressed, "#start")
    def on_start(self, event):
        self.post_message(self.Started(self))
        self.add_class("running")

    @on(Button.Pressed, "#stop")
    def on_stop(self, event):
        self.post_message(self.Stopped(self))
        self.remove_class("running")
