import curses

from typing import Callable
from ._helpers import Info
from .data_types import *


def init_color():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)


def init(win: CurseWindow):
    curses.noecho()
    curses.cbreak()
    curses.curs_set(False)

    init_color()

    win.keypad(True)

    win.addstr("Press ")
    win.addstr("q", curses.color_pair(3))
    win.addstr(" to quit")
    win.noutrefresh()


def teardown(win: CurseWindow):
    win.clear()
    win.keypad(False)
    curses.echo()
    curses.nocbreak()
    curses.endwin()


def wrapper(func: Callable, *args, **kwargs):
    try:
        main_window: CurseWindow = curses.initscr()
        init(main_window)

        content_window: CurseWindow = main_window.subwin(
            curses.LINES - 6, curses.COLS, 1, 0
        )

        event_queue: EventQueue = queue.Queue()

        info: Info = Info(main_window.subwin(5, curses.COLS, curses.LINES - 5, 0))

        value = func(content_window, event_queue, info, *args, **kwargs)

    except KeyboardInterrupt:
        ...
    finally:
        teardown(main_window)

    return value
