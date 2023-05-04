from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Static, Button
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

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical():
                yield Static("Project", id="project")
                yield Static("Task", id="task")
                yield Static("Description", id="description")

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


class ScytheApp(App):
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    CSS_PATH = "scythe.css"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()

        with Horizontal(id="header"):
            # yield Static("Test")
            yield Button("New", id="new")

        with VerticalScroll(id="timers"):
            yield Timer(id="timer1")
            yield Timer(id="timer2")
            yield Timer(id="timer3")
            yield Timer(id="timer4")
            yield Timer(id="timer5")
            yield Timer(id="timer6")
            yield Timer(id="timer7")
            yield Timer(id="timer8")

    @on(Timer.Started)
    def on_timer_started(self, event: Timer.Started):
        timers = self.query(Timer)
        for timer in timers:
            if timer.id != event.timer.id:
                if timer.has_class("running"):
                    timer.remove_class("running")
                    display = timer.query_one(TimeDisplay)
                    display.stop()
            else:
                timer.add_class("running")
                display = timer.query_one(TimeDisplay)
                display.start()

    @on(Timer.Stopped)
    def on_timer_stopped(self, event: Timer.Stopped):
        event.timer.remove_class("running")
        display = event.timer.query_one(TimeDisplay)
        display.stop()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    app = ScytheApp()
    app.run()
