import typing as t
from datetime import datetime
import shelve


class Cache:
    cache: shelve.Shelf

    def __init__(self, cache_file: str):
        self.cache_file = cache_file

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def __getitem__(self, item):
        return self.cache[item]["value"]

    def __setitem__(self, key, value):
        self.cache[key] = {"value": value, "updated_at": datetime.now()}

    def __delitem__(self, key):
        del self.cache[key]

    def open(self):
        self.cache = shelve.open(self.cache_file)
        return self

    def close(self):
        self.cache.close()

    def get(self, key):
        data = self.cache.get(key)
        if data:
            return data["value"]
        return data

    def updated_at(self, key) -> t.Optional[datetime]:
        data = self.cache.get(key)
        if data:
            return data["updated_at"]
        return data

    def set(self, key, value):
        self.cache[key] = value
