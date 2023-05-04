from time import monotonic
from textual import on
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Footer, Header, Static, Button
from textual.reactive import reactive


class TimeDisplay(Static):
    start_time: reactive[float] = reactive(monotonic)
    time: reactive[float] = reactive(0.0)
    total = reactive(0.0)

    def on_mount(self) -> None:
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        self.time = self.total + monotonic() - self.start_time

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")

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


class Stopwatch(Static):
    def compose(self) -> ComposeResult:
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")
        yield TimeDisplay("00:00:00.00")

    @on(Button.Pressed, "#start")
    def on_start(self, event: Button.Pressed) -> None:
        display = self.query_one(TimeDisplay)
        display.start()
        self.add_class("started")

    @on(Button.Pressed, "#stop")
    def on_stop(self, event: Button.Pressed) -> None:
        display = self.query_one(TimeDisplay)
        display.stop()
        self.remove_class("started")

    @on(Button.Pressed, "#reset")
    def on_reset(self, event: Button.Pressed) -> None:
        display = self.query_one(TimeDisplay)
        display.reset()


class ScytheApp(App):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "add_stopwatch", "Add "),
        ("r", "remove_stopwatch", "Remove"),
    ]

    CSS_PATH = "scythe.css"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield ScrollableContainer(Stopwatch(), Stopwatch(), Stopwatch(), id="timers")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_add_stopwatch(self) -> None:
        """An action to add a stopwatch."""
        stopwatch = Stopwatch()
        self.query_one("#timers").mount(stopwatch)
        stopwatch.scroll_visible()

    def action_remove_stopwatch(self) -> None:
        timers = self.query("Stopwatch")
        if timers:
            timers.last().remove()


if __name__ == "__main__":
    app = ScytheApp()
    app.run()
