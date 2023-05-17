import httpx
from textual import on, work
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import LoadingIndicator

from .timer import Timer, TimeDisplay


class TimerContainer(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield LoadingIndicator()

    def on_mount(self) -> None:
        self.get_timers()

    @work(exclusive=True)
    async def get_timers(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.harvestapp.com/v2/time_entries?page=1&per_page=10",
                headers={
                    "Harvest-Account-Id": "330810",
                    "Authorization": f"Bearer 2403856.pt.eYGF3Fol3gUe9V5uheXnunlAZ46ZYZS1UUJvNiehnRJrmqdtfyWvu7k8ikKzzYSWF72646mcV9VgqfBNKhOUnQ",
                },
            )

            data = response.json()
            self.query(LoadingIndicator).remove()

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

    def add_timer(self, project: str, task: str, note: str):
        self.mount(Timer(project=project, task=task, note=note))
