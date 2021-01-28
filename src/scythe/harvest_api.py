from typing import Union
import requests


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

    def get(self, url, *args, **kwargs):
        return super().get(f"{self.base_url}{url}", *args, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return super().post(f"{self.base_url}{url}", data, json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return super().put(f"{self.base_url}{url}", data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return super().patch(f"{self.base_url}{url}", data, **kwargs)

    def delete(self, url, *args, **kwargs):
        return super().delete(f"{self.base_url}{url}", *args, **kwargs)

    def me(self):
        return self.get("/users/me")

    def get_projects(self, user_id: int) -> requests.Response:
        return self.get(f"/users/{user_id}/project_assignments")

    def get_running_timer(self):
        timers = self.get("/time_entries").json()["time_entries"]
        timer: dict
        for timer in timers:
            if timer["is_running"]:
                return timer

        return None
