import logging
from typing import Union
import datetime

import requests

logger = logging.getLogger("arc_logger")


class HarvestApi(requests.Session):
    def __init__(self, token: str, account_id: Union[str, int]):
        super().__init__()
        self.base_url = "https://api.harvestapp.com/v2"
        self.headers.update(
            {
                "Harvest-Account-Id": str(account_id),
                "Authorization": f"Bearer {token}",
                "User-Agent": "Scythe CLI",
            }
        )

    def get(self, url, **kwargs):
        logger.debug("Fetching %s", url)
        return super().get(f"{self.base_url}{url}", **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        logger.debug("Posting %s", url)
        return super().post(f"{self.base_url}{url}", data, json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return super().put(f"{self.base_url}{url}", data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return super().patch(f"{self.base_url}{url}", data, **kwargs)

    def delete(self, url, *args, **kwargs):
        logger.debug("Deleting %s", url)
        return super().delete(f"{self.base_url}{url}", *args, **kwargs)

    def me(self):
        return self.get("/users/me")

    def get_projects(self) -> requests.Response:
        return self.get("/users/me/project_assignments")

    def get_running_timer(self):
        timers = self.get("/time_entries?is_running=true").json()["time_entries"]
        return timers[0] if len(timers) > 0 else None

    def create_timer(
        self, project_id, task_id, notes: str = "", spent_date=datetime.date.today()
    ):
        return self.post(
            "/time_entries",
            {
                "project_id": project_id,
                "task_id": task_id,
                "spent_date": str(spent_date),
                "notes": notes,
            },
        )
