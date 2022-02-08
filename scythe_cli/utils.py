from logging import Logger
import typing as t
from arc.types import State

import math
import pydantic

from scythe_cli.cache import Cache
from scythe_cli.harvest_api import Harvest

T = t.TypeVar("T")


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
    minutes = math.floor(round(minutes, 2) * 60)
    hours = int(hours)
    return hours, minutes


def fmt_time(hours: int, minutes: int) -> str:
    minutes_str = str(minutes) if minutes >= 10 else f"0{minutes}"
    return f"{hours}:{minutes_str}"


class Columns:
    def __init__(self, *vals: str, padding: int = 2):
        self.vals = [v.split("\n") for v in vals]
        self.max_len = max(len(v) for v in self.vals)
        self.padding = padding

    def __str__(self):
        return self.to_string()

    def to_string(self, show_index: bool = False):
        string = ""
        for i in range(0, self.max_len):
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


class Config(pydantic.BaseSettings):
    token: str
    account_id: str
    user_id: str
    extensions: t.Optional[dict] = None


class ScytheState(State):
    config: Config
    harvest: Harvest
    cache: Cache
    logger: Logger
