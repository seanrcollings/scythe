from typing import TYPE_CHECKING, Any, Optional, Union
import enum
import queue

# pylint: disable=no-name-in-module
if TYPE_CHECKING:
    from curses import _CursesWindow
    from curses.panel import _Curses_Panel

    CurseWindow = _CursesWindow
    CursePanel = _Curses_Panel
else:
    CurseWindow = Any
    CursePanel = Any


class Event(enum.Enum):
    QUIT = "quit"
    KEY_PRESS = "key_press"


EventQueue = queue.Queue[tuple[Event, Optional[Union[str, int]]]]
