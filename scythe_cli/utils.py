import typing as t
from arc.types import State
import pydantic

from scythe_cli.cache import Cache
from scythe_cli.harvest_api import Harvest

T = t.TypeVar("T")


def exist_or_exit(val: T, ctx) -> T:
    if val is None:
        ctx.exit()

    return val


class Columns:
    def __init__(self, *vals: str, padding: int = 2):
        self.vals = [v.split("\n") for v in vals]
        self.max_len = max(len(v) for v in self.vals)
        self.padding = padding

    def __str__(self):
        return self.to_string()

    def to_string(self, show_index: bool = False):
        string = ""
        for i in range(0, self.max_len):
            if show_index:
                string += f"{i:<2} "
            for v in self.vals:
                if len(v) > i:
                    string += f"{v[i]:<{len(v[0])}}"
                else:
                    string += " " * len(v[0])
                string += " " * self.padding
            string += "\n"
        return string


class Config(pydantic.BaseSettings):
    token: str
    account_id: str
    user_id: str
    extensions: t.Optional[dict] = None


class ScytheState(State):
    config: Config
    harvest: Harvest
    cache: Cache