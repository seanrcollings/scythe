from collections import deque
from functools import cached_property
import json
import os
import typing as t
from pathlib import Path


class StackEntry(t.TypedDict):
    id: int
    project: str
    task: str
    notes: t.Optional[str]
    time: int


class TimerStack:
    def __init__(self, path: Path, max_size: int = 30):
        self.path = path
        self.max_size = max_size

    @cached_property
    def _stack(self) -> deque[StackEntry]:
        if not self.path.exists():
            return deque()

        with self.path.open("r") as f:
            contents = f.read()
            if not contents:
                return deque()

            return deque(json.loads(contents))

    @cached_property
    def item_ids(self) -> t.Collection[int]:
        return set(item["id"] for item in self._stack)

    def __iter__(self):
        return iter(self._stack)

    def __getitem__(self, index):
        return self._stack[index]

    def __len__(self):
        return len(self._stack)

    def __bool__(self):
        return bool(self._stack)

    def __contains__(self, item):
        return item in self._stack

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.save()

    def push(self, entry: StackEntry):
        if entry["id"] in self.item_ids:
            self._stack.remove(
                [item for item in self._stack if item["id"] == entry["id"]][0]
            )

        if len(self._stack) >= self.max_size:
            self._stack.pop()

        self._stack.appendleft(entry)

    def pop(self, idx: int):
        return self._stack.remove(self._stack[idx])

    def remove(self, entry: StackEntry):
        self._stack.remove(entry)

    def clear(self):
        self._stack.clear()

    def save(self):
        with self.path.open("w") as f:
            json.dump(list(self._stack), f)
