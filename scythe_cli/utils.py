from __future__ import annotations
import re
import typing as t

import arc
import keyring

from scythe_cli.console import console
from scythe_cli.harvest import Harvest, AsyncHarvest


def _get_harvest(async_harvest: bool = False):
    access_token = keyring.get_password("scythe", "access_token")
    refresh_token = keyring.get_password("scythe", "refresh_token")

    if not access_token or not refresh_token:
        console.print("Please run [b]scythe init[/b] to authorize with Harvest.")
        arc.exit(1)

    harvest: Harvest | AsyncHarvest = (
        Harvest(access_token, refresh_token)
        if not async_harvest
        else AsyncHarvest(access_token, refresh_token)
    )

    @harvest.on_refresh
    def on_refresh(access_token, refresh_token):
        keyring.set_password("scythe", "access_token", access_token)
        keyring.set_password("scythe", "refresh_token", refresh_token)

    return harvest


def get_harvest() -> Harvest:
    return _get_harvest(False)


def get_async_harvest() -> AsyncHarvest:
    return _get_harvest(True)


def display_time(
    time: float, precision: t.Literal["hours", "minutes", "seconds"] = "seconds"
) -> str:
    """Converts a float representing seconds to a string with a given precision."""
    minutes, seconds = divmod(time, 60)
    hours, minutes = divmod(minutes, 60)

    match precision:
        case "hours":
            return f"{hours:02.0f}"
        case "minutes":
            return f"{hours:02.0f}:{minutes:02.0f}"
        case "seconds":
            return f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}"


def convert_time(time: str) -> float:
    """Converts a string to a float representing hours.

    Examples:
        >>> convert_time("1:30")
        1.5
        >>> convert_time(":30")
        0.5
    """
    if time.startswith(":"):
        time = time[1:]
        return int(time) / 60
    elif ":" not in time or time.endswith(":"):
        time = time.strip(":")
        return float(time)
    else:
        hours_str, minutes_str = time.split(":")
        hours = int(hours_str)
        minutes = int(minutes_str)
        return hours + (minutes / 60)
