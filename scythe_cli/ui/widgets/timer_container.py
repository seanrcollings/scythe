import asyncio
from datetime import datetime, timedelta
from textual import on, work
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal
from textual.widget import Widget
from textual.widgets import LoadingIndicator, Static, Button
from textual.reactive import reactive
from textual.message import Message

from scythe_cli.utils import get_seconds
from scythe_cli.harvest import AsyncHarvest

from .timer import Timer, TimeDisplay


class ViewingDay(Widget):
    class Back(Message):
        ...

    viewing_day: reactive[datetime] = reactive(datetime.now)

    def render(self):
        content = self.viewing_day.strftime("%Y-%m-%d")

        if self.viewing_day.date() == datetime.now().date():
            content += " [grey35](Today)[/grey35]"
        else:
            content += " [blue][@click='back'](Back to Today)[/][/blue]"

        return content

    def action_back(self):
        self.post_message(self.Back())


class TimerContainer(Widget):
    viewing_day: reactive[datetime] = reactive(datetime.now)

    def __init__(
        self,
        harvest: AsyncHarvest,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.harvest = harvest

    def compose(self) -> ComposeResult:
        with Horizontal(id="timers-actions"):
            yield Button("❮ Yesterday", id="yesterday")
            yield ViewingDay(id="today")
            yield Button("Tomorrow ❯", id="tomorrow")

        yield VerticalScroll(id="timers-list")

    def on_mount(self) -> None:
        def _inner():
            self.get_timers()

        self.set_interval(60, _inner)

    def watch_viewing_day(self, value: datetime) -> None:
        self.get_timers(loader=True)
        today = self.query_one("#today", ViewingDay)
        today.viewing_day = value

    @work(exclusive=True)
    async def get_timers(self, loader: bool = False) -> None:
        timers = self.query(VerticalScroll).first()

        if loader:
            timers.query("*").remove()
            await timers.mount(LoadingIndicator())

        today = self.viewing_day.strftime("%Y-%m-%d")
        data = await self.harvest.get_time_entries(
            {
                "from": today,
                "to": today,
            }
        )

        if loader:
            timers.query(LoadingIndicator).remove()
        else:
            timers.query("*").remove()

        if data["time_entries"]:
            await asyncio.wait(
                [
                    timers.mount(
                        Timer(
                            project=entry["project"]["name"],
                            task=entry["task"]["name"],
                            note=entry["notes"],
                            seconds=get_seconds(entry["hours"]),
                            is_running=entry["is_running"],
                            id=f"timer-{entry['id']}",
                        )
                    )
                    for entry in data["time_entries"]
                ]
            )
        else:
            await timers.mount(Static("No timers for today", id="no-timers"))

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

    @on(Button.Pressed, "#yesterday")
    def on_yesterday(self, event: Button.Pressed):
        self.viewing_day = self.viewing_day - timedelta(days=1)

    @on(ViewingDay.Back)
    def on_back(self, event: ViewingDay.Back):
        self.viewing_day = datetime.now()

    @on(Button.Pressed, "#tomorrow")
    def on_tomorrow(self, event: Button.Pressed):
        self.viewing_day = self.viewing_day + timedelta(days=1)

    async def add_timer(self, project: str, task: str, note: str):
        timers = self.query(VerticalScroll).first()
        await timers.mount(Timer(project=project, task=task, note=note))
