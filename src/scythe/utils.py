from typing import Dict
from pathlib import Path
import functools

import requests
from arc.errors import ExecutionError
from arc.color import fg
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
    if res.status_code >= 200 or res.status_code < 300:
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