from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button


class Actions(Horizontal):
    def compose(self) -> ComposeResult:
        yield Button("New Timer", id="new")
