import curses
import time
from typing import Type, Optional

from .data_types import *
from .ui import UI, T
from ._init import wrapper


white_space_map = {"\n": "ENTER", " ": "SPACE", "\t": "TAB"}


def get_input(win: CurseWindow):
    try:
        key = win.getkey()
        if key in white_space_map:
            key = white_space_map[key]

        return key
    except Exception:
        return None


def main_loop(
    content_window: CurseWindow,
    event_queue: EventQueue,
    info,
    ui: Type[UI],
    *args,
    **kwargs
) -> Optional[T]:
    running = True
    content_window.nodelay(True)
    content_window.keypad(True)
    component = ui(content_window, info, event_queue, *args, **kwargs)
    component.start()

    while running:
        key = get_input(content_window)
        if key == "q":
            break
        elif key:
            event_queue.put((Event.KEY_PRESS, key))

        curses.doupdate()
        running = component.is_alive()
        time.sleep(0.016)

    return component.return_value


def run(ui, *args, **kwargs) -> T:
    return wrapper(main_loop, ui, *args, **kwargs)
