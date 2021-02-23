import time
from typing import Type
import curses
import threading
from .data_types import *


class UI(threading.Thread):
    def __init__(self, content: CurseWindow, info, *args, **kwargs):
        self.content = content
        self.info = info
        super().__init__(target=self._run, daemon=True)

    def _run(self):
        ...


class Info:
    def __init__(self, window):
        self._window = window
        self._window.border()
        self._window.move(1, 1)
        self._window.scrollok(True)
        self._window.noutrefresh()

        self.log: list[str] = []

    @property
    def pos(self) -> tuple[int, int]:
        y, x = self._window.getyx()
        return x, y

    def send(self, string: str, attr: int = 1, end="\n"):
        y = self.pos[1]
        self.log.append(string)
        self._window.move(y, 1)
        self._window.addstr(string + end, attr)
        self._window.border()
        self._window.refresh()

    def dump(self, filename="./log.txt"):
        with open(filename, "w+") as f:
            f.write("\n".join(self.log))


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


def main_loop(content_window: CurseWindow, info, component: UI):
    running = True
    content_window.nodelay(True)
    component.start()

    while running:
        try:
            key = content_window.getkey()
            if key == "q":
                break
        except Exception:
            ...
        finally:
            curses.doupdate()
            running = component.is_alive()

        time.sleep(0.016)


def run(ui: Type[UI], *args, **kwargs):
    try:
        main_window = curses.initscr()
        init(main_window)
        content_window = main_window.subwin(curses.LINES - 6, curses.COLS, 1, 0)
        info = Info(main_window.subwin(5, curses.COLS, curses.LINES - 5, 0))
        component = ui(content_window, info, *args, **kwargs)
        main_loop(content_window, info, component)

    except KeyboardInterrupt:
        ...
    finally:
        main_window.clear()
        main_window.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
