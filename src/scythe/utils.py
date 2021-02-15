import functools
import math
import shutil
from pathlib import Path
from textwrap import wrap
from typing import Optional
import sys

import yaml

import requests
from arc.errors import ExecutionError
from arc.ui import SelectionMenu
from arc.utils import logger
from arc.color import fg, effects

from . import config_file


def config_required(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if not config_file.exists():
            raise ExecutionError(
                "Config file must be present to run this command. Run 'scythe init'"
            )
        return func(*args, **kwargs)

    return decorator


def load_file(file: Path) -> dict[str, str]:
    if not file.exists():
        return {}

    data: dict[str, str] = {}
    with file.open() as f:
        for line in f.readlines():
            key, value = line.strip("\n").split("=")
            key = key.lower()
            data[key] = value

    return data


def handle_response(res: requests.Response):
    if res.status_code >= 200 and res.status_code < 300:
        return True

    raise ExecutionError(f"Request failed with the following message: {res.text}")


def print_valid_response(res: requests.Response, worked: str):
    if handle_response(res):
        print(worked)


class Cache:
    NOT_LOADED = ExecutionError("Cache not yet loaded")

    def __init__(self, file: Path):
        self.cache_file = file
        self._data: dict = {}
        self.loaded = False

    # Dictionary Pass through functions
    def __getitem__(self, item):
        self.load()
        return self._data.get(item)

    def __setitem__(self, key, value):
        self.load()
        self._data[key] = value

    def __delitem__(self, key):
        self.load()
        del self._data[key]

    def pop(self, value):
        if isinstance(self._data, dict):
            return self._data.pop(value)

        raise Cache.NOT_LOADED

    def save(self):
        logger.debug("%sWriting cache...%s", fg.YELLOW, effects.CLEAR)
        with open(self.cache_file, "w") as file:
            file.write(yaml.dump(self._data))

    def load(self):
        if not self.loaded:
            logger.debug("Loading Cache")
            self._data = self.__load()
            self.loaded = True

    def __load(self):
        try:
            file = open(self.cache_file, "r")
            data: dict = yaml.load(file, yaml.Loader)
            file.close()
        except FileNotFoundError:
            data = {}
        return data


def paragraphize(string: str, length: int = 70, beginning: str = ""):
    if len(string) == 0:
        return ""
    return beginning + f"\n{beginning}".join(wrap(string, length)) + "\n"


def pick_time_entry(entries: list):

    columns = shutil.get_terminal_size((50, 20)).columns - 6
    entry_names = [
        f"{format_time(*parse_time(entry.hours))} - {entry.project['name']} - {entry.task['name']} "
        f"\n{paragraphize(entry.notes, length=columns, beginning=' |  ')}"
        for entry in entries
    ]

    return exist_or_exit(SelectionMenu(entry_names).run())


def parse_time(time: float):
    minutes, hours = math.modf(time)
    minutes = math.floor(round(minutes, 2) * 60)
    hours = int(hours)
    return hours, minutes


def format_time(hours, minutes):
    minutes_str = str(minutes) if minutes > 10 else f"0{minutes}"
    return f"{hours}:{minutes_str}"


def exist_or_exit(val):
    if val is None:
        sys.exit(0)

    return val
