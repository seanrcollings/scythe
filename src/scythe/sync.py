from typing import Callable, Optional, Any, TYPE_CHECKING
import datetime

from .harvest_api import HarvestApi

if TYPE_CHECKING:
    from . import utils


class Sync:
    def __init__(
        self,
        api: HarvestApi,
        cache: "utils.Cache",
        **syncers: Callable[[HarvestApi], Optional[Any]]
    ):
        self.api = api
        self.cache = cache
        self.syncers = syncers

    def sync_all(self):
        for name in self.syncers:
            self.sync(name, save=False)
        self.cache.save()

    def sync(self, value: str, save: bool = True):
        synced = self.syncers[value](self.api)
        if synced:
            self.cache[value] = synced
        elif self.cache.get(value):
            self.cache.pop(value)

        self.cache.meta["synced_at"] = datetime.datetime.now()
        if save:
            self.cache.save()
