from .data_types import *


class Info:
    def __init__(self, window: CurseWindow):
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
