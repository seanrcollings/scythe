from typing import Dict
from pathlib import Path
import functools
from textwrap import wrap
import shutil

import requests
from arc.errors import ExecutionError
from . import config_file
from .selection_menu import SelectionMenu


def config_required(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if not config_file.exists():
            raise ExecutionError(
                "Config file must be present to run this command. Run 'scythe init'"
            )
        return func(*args, **kwargs)

    return decorator


def load_file(file: Path) -> Dict[str, str]:
    if not file.exists():
        return {}

    data: Dict[str, str] = {}
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
    def __init__(self, file: Path):
        self.cache_file = file
        self.cache_data = load_file(file)

    def read(self, key: str):
        return self.cache_data.get(key)

    def write(self, **kwargs):
        self.cache_data |= kwargs
        self.__write()

    def __write(self):
        with self.cache_file.open("w+") as file:
            file.write(
                "\n".join(
                    f"{key.upper()}={value}" for key, value in self.cache_data.items()
                )
            )


def paragraphize(string: str, length: int = 70, beginning: str = ""):
    if len(string) == 0:
        return ""
    return beginning + f"\n{beginning}".join(wrap(string, length)) + "\n"


def pick_time_entry(entries: list):

    columns = shutil.get_terminal_size((50, 20)).columns - 6
    entry_names = [
        f"{entry.hours} - {entry.project['name']} - {entry.task['name']} "
        f"\n{paragraphize(entry.notes, length=columns, beginning=' |  ')}"
        for entry in entries
    ]

    return SelectionMenu(entry_names).render()