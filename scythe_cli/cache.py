import typing as t
from datetime import datetime, timedelta
import time
import shelve
import sys


class Cache:
    cache: shelve.Shelf

    class KeyStale(KeyError):
        ...

    class Closed(Exception):
        ...

    DELAY = 0.05

    def __init__(self, cache_file: str, stale_after: timedelta = None):
        self.cache_file = cache_file
        self.stale_after = stale_after
        self.closed = True
        self.cache = None  # type: ignore

    def __enter__(self):
        while True:
            try:
                self.open()
                return self
            except Exception as e:
                print("Cache is unavailable, retrying in .05 seconds", file=sys.stderr)
                time.sleep(Cache.DELAY)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getitem__(self, item):
        self._asert_closed()
        data = self.cache[item]
        if self._is_stale(data):
            del self.cache[item]
            raise Cache.KeyStale(item)
        return data["value"]

    def __setitem__(self, key, value):
        self._asert_closed()
        self.cache[key] = {"value": value, "updated_at": datetime.now()}

    def __delitem__(self, key):
        self._asert_closed()
        del self.cache[key]

    def open(self):
        if self.closed:
            self.cache = shelve.open(self.cache_file)
            self.closed = False
        return self

    def close(self):
        if self.cache and not self.closed:
            self.cache.close()
            self.closed = True

    def get(self, key):
        self._asert_closed()
        data = self.cache.get(key)
        if data and self._is_stale(data):
            if data:
                del self.cache[key]
            return None
        if data:
            return data["value"]
        return None

    def updated_at(self, key) -> t.Optional[datetime]:
        data = self.cache.get(key)
        if data:
            return data["updated_at"]
        return None

    def set(self, key, value, update_expiration=True):
        self._asert_closed()
        if update_expiration:
            self[key] = value
        else:
            self.cache[key]["value"] = value

    def _is_stale(self, data):
        return (
            self.stale_after and datetime.now() - data["updated_at"] > self.stale_after
        )

    def _asert_closed(self):
        if self.closed:
            raise Cache.Closed("Cache is closed")
