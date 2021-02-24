from abc import ABC, abstractmethod
import time
from typing import cast, Generic, TypeVar
import threading

from .data_types import *

T = TypeVar("T")


class UI(ABC, Generic[T]):
    def __init__(self, content: CurseWindow, info, event_queue: EventQueue, *_, **__):
        self.content = content
        self.info = info
        self.event_queue = event_queue
        self.return_value: Optional[T] = None
        self.running = True
        self._thread = threading.Thread(target=self.update, daemon=True)

    def start(self):
        self._thread.start()

    def is_alive(self):
        return self._thread.is_alive()

    def on_key(self, key: str):
        """Handles keyboard input"""

    def done(self, value=None):
        self.return_value = value
        self.running = False

    def queue(self):
        self.render()
        self.content.noutrefresh()

    def update(self):
        self.render()
        while self.running:
            event, value = self.event_queue.get()
            self.info.send(f"Handling Event(type={event}, value={value})")
            if event == Event.KEY_PRESS:
                self.on_key(cast(str, value))
            else:
                self.event_queue.put((event, value))

            time.sleep(0.016)

    @abstractmethod
    def render(self):
        """Called each time update or
        on_key determine an update is needed
        """
