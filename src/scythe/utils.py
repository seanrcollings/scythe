import math
import sys
from dataclasses import dataclass
from pathlib import Path
from textwrap import wrap
from typing import TYPE_CHECKING, Optional
import re

import requests
from arc import Context
from arc.color import effects, fg
from arc.errors import ExecutionError

from .cache import Cache
from .harvest_api import HarvestApi
from .sync import Sync
from .ui import menu

if TYPE_CHECKING:
    from .helpers import Project


@dataclass
class Config:
    token: str
    account_id: str
    user_id: str
    # Atomic Jolt Specific Configs
    standup_link: Optional[str] = None
    training_link: Optional[str] = None

    @classmethod
    def from_file(cls, file: Path):
        if not file.exists():
            raise FileNotFoundError(f"{file} does not exist")

        data: dict[str, str] = {}
        with file.open() as f:
            for line in f.readlines():
                key, value = line.strip("\n").split("=", maxsplit=1)
                key = key.lower()
                data[key] = value

        return Config(**data)


class ScytheContext(Context):
    api: HarvestApi
    config: Config
    cache: Cache
    projects: Optional[list["Project"]]
    syncer: Sync


def handle_response(res: requests.Response):
    if res.status_code >= 200 and res.status_code < 300:
        return True

    raise ExecutionError(f"Request failed with the following message: {res.text}")


def print_valid_response(res: requests.Response, worked: str):
    if handle_response(res):
        print(f"{fg.GREEN}{worked}{effects.CLEAR}")


def exist_or_exit(val):
    if val is None:
        sys.exit(0)

    return val


def paragraphize(string: str, length: int = 70, beginning: str = ""):
    if len(string) == 0:
        return ""
    return beginning + f"\n{beginning}".join(wrap(string, length)) + "\n"


def pick_time_entry(entries: list):

    entry_names = [
        f"{format_time(*parse_time(entry.hours))} - {entry.project['name']} - {entry.task['name']} "
        f"\n{entry.notes}"
        for entry in entries
    ]

    return exist_or_exit(menu(entry_names))


def parse_time(time: float):
    minutes, hours = math.modf(time)
    minutes = math.floor(round(minutes, 2) * 60)
    hours = int(hours)
    return hours, minutes


def format_time(hours, minutes):
    minutes_str = str(minutes) if minutes >= 10 else f"0{minutes}"
    return f"{hours}:{minutes_str}"


def set_title(title: str):
    sys.stdout.write(f"\x1b]2;{title}\x07")


def clean(string):
    """Gets rid of escape sequences"""
    ansi_escape = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")
    return ansi_escape.sub("", str(string))
