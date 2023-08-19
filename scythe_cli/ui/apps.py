import datetime
from pathlib import Path
from typing import Type
import webbrowser

from textual import on
from textual.app import App, CSSPathType, ComposeResult
from textual.driver import Driver
from textual.widgets import Footer, Header, Button
from textual.containers import Vertical

from scythe_cli.harvest import AsyncHarvest
from scythe_cli.ui.widgets import TimerContainer, Actions, TimerModal
from scythe_cli.ui.widgets.timer import Timer


class ScytheApp(App):
    TITLE = "Scythe"
    BINDINGS = [
        ("q", "quit", "Quit"),
        # ("d", "toggle_dark", "Toggle dark mode"),
        ("o", "open_harvest", "Open Harvest"),
        ("n", "open_new_modal", "New Timer"),
    ]
    CSS_PATH = list((Path(__file__).parent / "styles").glob("*.css"))

    def __init__(
        self,
        harvest: AsyncHarvest,
        driver_class: Type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
    ):
        super().__init__(driver_class, css_path, watch_css)
        self.current_day = datetime.datetime.now()
        self.harvest = harvest

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()

        with Vertical(id="main"):
            yield Actions(id="header")
            yield TimerContainer(harvest=self.harvest, id="timers")

        yield TimerModal(harvest=self.harvest)

    async def action_quit(self):
        await self.harvest.close()
        self.exit()

    @on(Button.Pressed, "#new")
    async def on_new(self, event: Button.Pressed):
        await self.run_action("open_new_modal")

    @on(TimerModal.Cancel)
    async def on_cancel(self, event: TimerModal.Cancel):
        self.close_new_modal()
        self.query_one("#new").focus()

    @on(TimerModal.NewTimer)
    async def on_new_timer(self, event: TimerModal.NewTimer):
        self.close_new_modal()
        container = self.query_one(TimerContainer)
        await container.add_timer(event.entry)

    @on(TimerModal.UpdateTimer)
    async def on_update_timer(self, event: TimerModal.UpdateTimer):
        self.close_new_modal()
        container = self.query_one(TimerContainer)
        await container.update_timer(event.entry)

    @on(TimerModal.DeleteTimer)
    async def on_delete_timer(self, event: TimerModal.DeleteTimer):
        self.close_new_modal()
        container = self.query_one(TimerContainer)
        await container.delete_timer(event.entry)

    @on(TimerContainer.ChangeDay)
    async def on_back(self, event: TimerContainer.ChangeDay):
        self.current_day = event.day

    @on(Timer.Edit)
    async def on_edit(self, event: Timer.Edit):
        modal = self.query_one(TimerModal)
        modal.timer = event.timer.entry
        await self.run_action("open_new_modal")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_open_harvest(self) -> None:
        """An action to open Harvest."""
        webbrowser.open("https://atomicjolt.harvestapp.com")

    def action_open_new_modal(self):
        modal = self.query_one(TimerModal)
        modal.add_class("open")
        modal.query_one("#project").focus()

        main = self.query_one("#main")
        main.disabled = True

    def close_new_modal(self):
        modal = self.query_one(TimerModal)
        modal.remove_class("open")

        main = self.query_one("#main")
        main.disabled = False


if __name__ == "__main__":
    from scythe_cli.harvest import AsyncHarvest
    from scythe_cli import utils

    harvest = utils.get_async_harvest()
    app = ScytheApp(harvest=harvest)
    app.run()
