from __future__ import annotations
from logging import Logger
import typing as t
from arc.types import State

import math
import diskcache  # type: ignore
import pydantic
from rich.console import Console

T = t.TypeVar("T")


def get_hours_and_minutes(val: float) -> tuple[int, int]:
    minutes, hours = math.modf(val)
    minutes = math.ceil(round(minutes, 2) * 60)
    hours = int(hours)
    return hours, minutes


def get_seconds(hours: float) -> float:
    return hours * 60 * 60


def fmt_time(hours: int, minutes: int) -> str:
    minutes_str = str(minutes) if minutes >= 10 else f"0{minutes}"
    return f"{hours}:{minutes_str}"


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
    logger: Logger
    cache: diskcache.Cache
    console: Console
