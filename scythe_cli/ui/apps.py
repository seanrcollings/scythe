import datetime
from pathlib import Path
from typing import Type
import webbrowser

from textual import on
from textual.app import App, CSSPathType, ComposeResult
from textual.driver import Driver
from textual.widgets import Footer, Header, Button
from textual.containers import Vertical

from scythe_cli.harvest import AsyncHarvest, TimeEntry
from scythe_cli.ui.widgets import TimerContainer, Actions, TimerModal
from scythe_cli.ui.widgets.timer import Timer
from scythe_cli.ui.widgets.timer_modal import TimerModalAction


class ScytheApp(App):
    TITLE = "Scythe - Harvest in the terminal"
    BINDINGS = [
        ("q", "quit", "Quit"),
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

    async def action_quit(self):
        await self.harvest.close()
        self.exit()

    @on(Button.Pressed, "#new")
    async def on_new(self, event: Button.Pressed):
        await self.run_action("open_new_modal")

    @on(TimerContainer.ChangeDay)
    async def on_back(self, event: TimerContainer.ChangeDay):
        self.current_day = event.day

    @on(Timer.Edit)
    async def on_edit(self, event: Timer.Edit):
        self.push_screen(
            TimerModal(harvest=self.harvest, timer=event.timer.entry),
            callback=self.handle_timer_modal_close,
        )

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_open_harvest(self) -> None:
        """An action to open Harvest."""
        # TODO - Make this configurable
        webbrowser.open("https://atomicjolt.harvestapp.com")

    def action_open_new_modal(self):
        self.push_screen(
            TimerModal(harvest=self.harvest), callback=self.handle_timer_modal_close
        )

    async def handle_timer_modal_close(
        self, result: tuple[TimerModalAction, TimeEntry]
    ):
        self.console.log(f"Result: {result}")
        action, entry = result
        container = self.query_one(TimerContainer)

        match action:
            case TimerModalAction.NEW:
                await container.add_timer(entry)
            case TimerModalAction.EDIT:
                await container.update_timer(entry)
            case TimerModalAction.DELETE:
                await container.delete_timer(entry)


if __name__ == "__main__":
    from scythe_cli.harvest import AsyncHarvest
    from scythe_cli import utils

    harvest = utils.get_async_harvest()
    app = ScytheApp(harvest=harvest)
    app.run()
