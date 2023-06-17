from __future__ import annotations
import typing as t
import math

import arc
import keyring

from scythe_cli.console import console
from scythe_cli.harvest import Harvest


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


def get_harvest():
    access_token = keyring.get_password("scythe", "access_token")
    refresh_token = keyring.get_password("scythe", "refresh_token")

    if not access_token or not refresh_token:
        console.print("Please run [b]scythe init[/b] to authorize with Harvest.")
        arc.exit(1)

    harvest = Harvest(access_token, refresh_token)

    @harvest.on_refresh
    def on_refresh(access_token, refresh_token):
        keyring.set_password("scythe", "access_token", access_token)
        keyring.set_password("scythe", "refresh_token", refresh_token)

    return harvest


def display_time(time: float):
    minutes, seconds = divmod(time, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02,.0f}:{minutes:02.0f}:{seconds:02.0f}"
