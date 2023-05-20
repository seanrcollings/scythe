from pathlib import Path
from typing import Type
import webbrowser
from textual import on
from textual.app import App, CSSPathType, ComposeResult
from textual.driver import Driver
from textual.widgets import Footer, Header, Button
from textual.containers import Vertical
from scythe_cli import constants
from scythe_cli.config import Config
from scythe_cli.harvest import AsyncHarvest

from scythe_cli.ui.widgets import TimerContainer, Actions, NewTimerModal


class ScytheApp(App):
    TITLE = "Scythe"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
        ("o", "open_harvest", "Open Harvest"),
        ("o", "open_harvest", "Open Harvest"),
        ("n", "open_new_modal", "New Timer"),
    ]
    CSS_PATH = list((Path(__file__).parent / "styles").glob("*.css"))

    def __init__(
        self,
        config: Config,
        driver_class: Type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
    ):
        super().__init__(driver_class, css_path, watch_css)
        self.config = config
        self.harvest = AsyncHarvest(config.token, config.account_id)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()

        with Vertical(id="main"):
            yield Actions(id="header")
            yield TimerContainer(harvest=self.harvest, id="timers")

        yield NewTimerModal()

    async def on_unmount(self):
        await self.harvest.close()

    @on(Button.Pressed, "#new")
    async def on_new(self, event: Button.Pressed):
        await self.run_action("open_new_modal")

    @on(NewTimerModal.Cancel)
    async def on_cancel(self, event: NewTimerModal.Cancel):
        self.close_new_modal()

    @on(NewTimerModal.NewTimer)
    async def on_new_timer(self, event: NewTimerModal.NewTimer):
        self.close_new_modal()
        container = self.query_one(TimerContainer)
        await container.add_timer(event.project, event.task, event.note)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_open_harvest(self) -> None:
        """An action to open Harvest."""
        webbrowser.open("https://atomicjolt.harvestapp.com")

    def action_open_new_modal(self):
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
    app = ScytheApp(config=Config.load(constants.CONFIG_FILE))
    app.run()
