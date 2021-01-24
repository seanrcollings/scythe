from typing import Dict, Any, List, Optional
from pathlib import Path
import functools

import requests
from arc.errors import ExecutionError
from arc.color import effects, fg
from . import config_file, cache_file


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


def print_assignments(assignments: List[Dict[str, Any]], show_tasks: bool = False):
    for idx, assignment in enumerate(assignments):
        print(
            f"{effects.BOLD}{fg.GREEN}({idx}) "
            f"{assignment['project']['name']}{effects.CLEAR}"
        )

        if show_tasks:
            for idx, task_assignment in enumerate(assignment["task_assignments"]):
                print(f"\t({idx}) {task_assignment['task']['name']}")


def handle_response(res: requests.Response, worked: str):
    if res.status_code >= 200 or res.status_code < 300:
        print(worked)
    else:
        print(f"Request failed with the following message: {res.text}")


class Cache:
    def __init__(self, file: Path):
        self.cache_data = load_file(file)

    def read(self, key: str):
        return self.cache_data.get(key)

    def write(self, **kwargs):
        self.cache_data |= kwargs
        self.__write()

    def __write(self):
        with cache_file.open("w+") as file:
            file.write(
                "\n".join(
                    f"{key.upper()}={value}" for key, value in self.cache_data.items()
                )
            )
