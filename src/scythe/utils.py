import math
import sys
from dataclasses import dataclass
from pathlib import Path
from textwrap import wrap
from typing import Optional


import requests
import yaml
from arc.color import effects, fg
from arc.errors import ExecutionError
from arc.utils import logger

from .ui import menu


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
            logger.debug("%sLoading Cache%s", fg.YELLOW, effects.CLEAR)
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
    minutes_str = str(minutes) if minutes > 10 else f"0{minutes}"
    return f"{hours}:{minutes_str}"
