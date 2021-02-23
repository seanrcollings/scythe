import curses
from arc.formatters import Box

from .ui import run, UI
from .data_types import *


class Menu(UI):
    def __init__(self, content: CurseWindow, info, items):
        self.items = items
        self.selected_index = 0
        super().__init__(content, info)

    def on_key(self, key):
        if key == "KEY_UP" and self.selected_index != 0:
            self.selected_index -= 1

        elif key == "KEY_DOWN" and self.selected_index < len(self.items):
            self.selected_index += 1

    def _run(self):
        while True:
            self.content.clear()
            for idx, item in enumerate(self.items):
                if idx == self.selected_index:
                    self.content.addstr(
                        str(Box(f"({idx}) {item}")) + "\n", curses.color_pair(1)
                    )
                else:
                    self.content.addstr(str(Box(f"({idx}) {item}")) + "\n")


def menu(items: list):
    return run(Menu, items)
