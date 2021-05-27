import curses
from arc.present import Box

from .ui import UI
from .main import run
from .data_types import *
from .. import utils


class Menu(UI[tuple[int, str]]):
    def __init__(self, content: CurseWindow, info, event_queue, items):
        super().__init__(content, info, event_queue)
        self.items = items
        self.selected_index = 0

    def on_key(self, key):
        if key == "KEY_UP" and self.selected_index != 0:
            self.selected_index -= 1
            self.queue()

        elif key == "KEY_DOWN" and self.selected_index < len(self.items) - 1:
            self.selected_index += 1
            self.queue()

        elif key == "ENTER":
            self.done((self.selected_index, self.items[self.selected_index]))

    def render(self):
        self.content.clear()
        for idx, item in enumerate(self.items):
            if idx == self.selected_index:
                self.content.addstr(
                    utils.clean(Box(f"({idx}) {item}", color="")) + "\n",
                    curses.color_pair(1),
                )
            else:
                self.content.addstr(
                    utils.clean(Box(f"({idx}) {item}", color="")) + "\n"
                )


def menu(items: list):
    return run(Menu, items)
