import datetime
import logging
from pathlib import Path
from typing import Callable


import yaml
from arc.color import effects, fg
from arc.errors import ExecutionError

logger = logging.getLogger("arc_logger")


empty_cache: Callable[[], dict[str, dict]] = lambda: {
    "data": {},
    "meta": {},
}


class Cache:
    NOT_LOADED = ExecutionError("Cache not yet loaded")

    def __init__(self, file: Path):
        self.cache_file = file
        self._data: dict[str, dict] = empty_cache()
        self.loaded = False

    # Dictionary Pass through functions
    def __getitem__(self, item):
        self.load()
        return self._data["data"].get(item)

    def __setitem__(self, key, value):
        self.load()
        self._data["data"][key] = value
        self.meta[f"{key}_updated_at"] = datetime.datetime.now()

    def __delitem__(self, key):
        self.load()
        del self._data["data"][key]

    def get(self, value, default=None):
        return self._data["data"].get(value, default)

    def pop(self, value):
        self.load()
        return self._data["data"].pop(value)

    @property
    def meta(self):
        return self._data["meta"]

    def updated_at(self, value):
        return self.meta[f"{value}_updated_at"]

    def save(self):
        logger.debug("%sWriting cache...%s", fg.YELLOW, effects.CLEAR)
        self.meta["updated_at"] = datetime.datetime.now()
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
            data = empty_cache()
        return data or empty_cache()
