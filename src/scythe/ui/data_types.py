from typing import TYPE_CHECKING, Any


# pylint: disable=no-name-in-module
if TYPE_CHECKING:
    from curses import _CursesWindow
    from curses.panel import _Curses_Panel

    CurseWindow = _CursesWindow
    CursePanel = _Curses_Panel
else:
    CurseWindow = Any
    CursePanel = Any
