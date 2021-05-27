import time

from arc.present import Box

from ..clock import clock
from .ui import UI
from .main import run
from .data_types import *
from .. import helpers, utils
from ..harvest_api import HarvestApi


class Running(UI):
    def __init__(
        self,
        content: CurseWindow,
        info,
        event_queue,
        api: HarvestApi,
        interval: int = 10,
        size: str = "small",
        clock_only: bool = False,
    ):
        super().__init__(content, info, event_queue)
        self.api = api
        self.size = size
        self.interval = interval
        self.clock_only = clock_only
        self.entry = None

    def update(self):
        self.render()
        while self.running:
            entry = self.api.get_running_timer()
            if not entry:
                self.done("No Timer Running")
                return

            self.entry = entry
            self.render()

            time.sleep(self.interval)

    def render(self):
        if not self.entry:
            self.content.addstr("Loading...")
            return

        entry = helpers.Timer(self.entry)
        hours, minutes = utils.parse_time(entry.hours)

        time_display = Box(
            f"{clock(hours, minutes, self.size)}",
            justify="center",
            padding={"top": 2, "bottom": 2, "left": 4, "right": 4},
            color="",
        )

        self.content.clear()
        self.content.addstr(utils.clean(time_display))
        self.content.noutrefresh()

        # if clock_only:

        # else:
        #     info_display = Box(
        #         f"{header('Project')}: {entry.project['name']}\n"
        #         f"{header('Task')}: {entry.task['name']}\n"
        #         f"{header('Notes')}: {entry.notes}\n",
        #         padding={"top": 2, "bottom": 2, "left": 4, "right": 4},
        #     )

        #     content.addstr(
        #         f"{info_display}\n{time_display}\n"
        #         f"{header('Fetch Interval')}: {interval} seconds"
        #     )


def running_ui(*args, **kwargs):
    return run(Running, *args, **kwargs)
