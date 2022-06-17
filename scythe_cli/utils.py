from __future__ import annotations
from logging import Logger
import typing as t
import shutil
from arc.types import State
from arc import prompt, utils
import arc

import math
import diskcache  # type: ignore
import pydantic
from rich.console import Console

from scythe_cli.harvest_api import Harvest

if t.TYPE_CHECKING:
    from scythe_cli.harvest_api import schemas

T = t.TypeVar("T")

SelectReturn = tuple[int, T]


def exist_or_exit(val: T, ctx) -> tuple:
    if val is None:
        ctx.exit()

    return val


def parse_time(string: str) -> float:
    if ":" in string:
        hours, minutes = [int(v) for v in string.split(":")]
        return hours + (minutes / 60)
    elif "." in string:
        return float(string)
    elif string.isnumeric:
        return int(string)

    raise ValueError(f"Invalid time string: {string}")


def get_hours_and_minutes(val: float) -> tuple[int, int]:
    minutes, hours = math.modf(val)
    minutes = math.ceil(round(minutes, 2) * 60)
    hours = int(hours)
    return hours, minutes


def fmt_time(hours: int, minutes: int) -> str:
    minutes_str = str(minutes) if minutes >= 10 else f"0{minutes}"
    return f"{hours}:{minutes_str}"


def select_project(assignments, ctx: arc.Context) -> tuple[schemas.Project, int]:
    projects = [a.project for a in assignments]
    print("Select a project:")
    p_idx, _ = t.cast(
        SelectReturn[str],
        exist_or_exit(prompt.select([p.name for p in projects]), ctx),
    )
    print()

    return projects[p_idx], p_idx


def select_task(task_assignments, ctx: arc.Context) -> tuple[schemas.Task, int]:
    tasks = [t.task for t in task_assignments]
    print("Select a task:")
    t_idx, _ = t.cast(
        SelectReturn[str],
        exist_or_exit(prompt.select([t.name for t in tasks]), ctx),
    )
    print()
    return tasks[t_idx], t_idx


class Columns:
    def __init__(self, *vals: str, padding: int = 2):
        self.vals = [v.split("\n") for v in vals]
        self.height = max(len(v) for v in self.vals)
        self.width = sum(utils.ansi_len(v[0]) for v in self.vals)
        self.padding = padding

    def __str__(self):
        return self.to_string()

    def to_string(self, show_index: bool = False):
        cols, _ = shutil.get_terminal_size()
        if cols < self.width:
            return "\n".join("\n".join(v) for v in self.vals) + "\n"
        else:
            string = ""
            for i in range(0, self.height):
                if show_index:
                    string += f"{i:<2} "
                for v in self.vals:
                    if len(v) > i:
                        string += f"{v[i]:<{len(v[0])}}"
                    else:
                        string += " " * len(v[0])

                    string += " " * self.padding
                string += "\n"
            return string


def truncate(string: str, width: int = 80) -> str:
    truncated = ""
    for line in string.split("\n"):
        if utils.ansi_len(line) > width:
            truncated += line[:width] + "\n"
        else:
            truncated += line + "\n"

    return truncated


class QuickStartConfig(pydantic.BaseModel):
    project_id: int
    task_id: int
    url: t.Optional[str]
    notes: t.Optional[str]


class Config(pydantic.BaseSettings):
    token: str
    account_id: str
    user_id: str
    quickstart: dict[str, QuickStartConfig]
    cache_for: int = 60
    autoload: list[str] = []


class ScytheState(State):
    config: Config
    harvest: Harvest
    logger: Logger
    cache: diskcache.Cache
    console: Console
