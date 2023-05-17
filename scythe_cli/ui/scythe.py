from pathlib import Path
import webbrowser
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Button
from textual.containers import Vertical

from scythe_cli.ui.widgets import TimerContainer, Actions, NewTimerModal


class ScytheApp(App):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("o", "open_harvest", "Open Harvest"),
    ]
    CSS_PATH = list((Path(__file__).parent / "styles").glob("*.css"))
    _timer_id = 0

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()

        with Vertical(id="main"):
            yield Actions(id="header")
            yield TimerContainer(id="timers")

        yield NewTimerModal()

    @on(Button.Pressed, "#new")
    async def on_new(self, event: Button.Pressed):
        self.open_new_modal()

    @on(NewTimerModal.Cancel)
    async def on_cancel(self, event: NewTimerModal.Cancel):
        self.close_new_modal()

    @on(NewTimerModal.NewTimer)
    async def on_new_timer(self, event: NewTimerModal.NewTimer):
        self.close_new_modal()
        container = self.query_one(TimerContainer)

        container.add_timer(event.project, event.task, event.note)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_open_harvest(self) -> None:
        """An action to open Harvest."""
        webbrowser.open("https://atomicjolt.harvestapp.com")

    def open_new_modal(self):
        modal = self.query_one(NewTimerModal)
        modal.add_class("open")
        modal.children[0].focusable_children[0].focus()

        main = self.query_one("#main")
        main.disabled = True

    def close_new_modal(self):
        modal = self.query_one(NewTimerModal)
        modal.remove_class("open")

        main = self.query_one("#main")
        main.disabled = False


if __name__ == "__main__":
    app = ScytheApp()
    app.run()
