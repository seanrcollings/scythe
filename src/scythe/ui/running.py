import time

from arc.color import fg, effects
from arc.formatters import Box

from ..clock import clock
from .ui import run, UI
from .data_types import *
from .. import helpers, utils
from ..harvest_api import HarvestApi


class Running(UI):
    def __init__(
        self,
        content: CurseWindow,
        info,
        api: HarvestApi,
        interval: int = 10,
        size: str = "small",
        clock_only: bool = False,
    ):
        super().__init__(content, info)
        self.api = api
        self.size = size
        self.interval = interval
        self.clock_only = clock_only

    def _run(self):
        while entry := self.api.get_running_timer():
            entry = helpers.TimeEntry(entry)
            hours, minutes = utils.parse_time(entry.hours)

            time_display = Box(
                f"{clock(hours, minutes, self.size)}",
                justify="center",
                padding={"top": 2, "bottom": 2, "left": 4, "right": 4},
            )

            self.content.clear()
            self.content.addstr(str(time_display))
            self.content.noutrefresh()

            time.sleep(self.interval)

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
