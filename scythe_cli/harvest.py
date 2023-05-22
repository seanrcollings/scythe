import typing as t
import httpx
import msgspec


class TimeEntryProject(msgspec.Struct):
    id: int
    name: str


class TimeEntryTask(msgspec.Struct):
    id: int
    name: str


class TimeEntry(msgspec.Struct):
    id: int
    notes: str
    hours: float
    is_running: bool

    project: TimeEntryProject
    task: TimeEntryTask

    def seconds(self):
        return self.hours * 60 * 60


class TimeEntryResponse(msgspec.Struct):
    time_entries: list[TimeEntry]


class TaskAssignment(msgspec.Struct):
    id: int
    task: TimeEntryTask


class ProjectAssignment(msgspec.Struct):
    id: int
    project: TimeEntryProject
    task_assignments: list[TaskAssignment]
    is_active: bool


class ProjectAssignmentResponse(msgspec.Struct):
    project_assignments: list[ProjectAssignment]


class User(msgspec.Struct):
    id: int
    first_name: str
    last_name: str
    email: str


class HarvestError(httpx.HTTPError):
    def __init__(self, message: str, response: httpx.Response) -> None:
        super().__init__(message)
        self.response = response


def check(response: httpx.Response) -> httpx.Response:
    if response.status_code > 299:
        raise HarvestError(
            f"Request failed with status code {response.status_code}",
            response,
        )

    return response


class AsyncHarvest:
    def __init__(self, token: str, account_id: str):
        self.token = token
        self.account_id = account_id

        self.client = httpx.AsyncClient(
            base_url=f"https://api.harvestapp.com/api/v2/",
            headers={
                "Harvest-Account-Id": account_id,
                "Authorization": f"Bearer {token}",
                "User-Agent": "Scythe CLI (seanrcollings@gmail.com)",
            },
        )

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.__aexit__(exc_type, exc_value, traceback)

    async def close(self):
        await self.client.aclose()

    async def create_timer(self, data: t.Mapping[str, t.Any]) -> TimeEntry:
        response = check(await self.client.post("time_entries", json=data))
        return msgspec.json.decode(response.content, type=TimeEntry)

    async def start_timer(self, id: int) -> TimeEntry:
        response = check(await self.client.patch(f"time_entries/{id}/restart"))
        return msgspec.json.decode(response.content, type=TimeEntry)

    async def stop_timer(self, id: int) -> TimeEntry:
        response = check(await self.client.patch(f"time_entries/{id}/stop"))
        return msgspec.json.decode(response.content, type=TimeEntry)

    async def get_user_projects(self) -> list[ProjectAssignment]:
        response = check(await self.client.get(f"users/me/project_assignments"))
        return msgspec.json.decode(
            response.content, type=ProjectAssignmentResponse
        ).project_assignments

    async def get_time_entries(
        self, params: t.Mapping[str, str] | None = None
    ) -> list[TimeEntry]:
        response = check(
            await self.client.get(
                "time_entries",
                params=params,
            )
        )
        return msgspec.json.decode(
            response.content,
            type=TimeEntryResponse,
        ).time_entries


class Harvest:
    def __init__(self, token: str, account_id: str):
        self.token = token
        self.account_id = account_id

        self.client = httpx.Client(
            base_url=f"https://api.harvestapp.com/api/v2/",
            headers={
                "Harvest-Account-Id": account_id,
                "Authorization": f"Bearer {token}",
                "User-Agent": "Scythe CLI (seanrcollings@gmail.com)",
            },
        )

    def __enter__(self):
        self.client.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.__exit__(exc_type, exc_value, traceback)

    def close(self):
        self.client.close()

    def create_timer(self, data: t.Mapping[str, t.Any]) -> TimeEntry:
        response = check(self.client.post("time_entries", json=data))
        return msgspec.json.decode(response.content, type=TimeEntry)

    def start_timer(self, id: int) -> TimeEntry:
        response = check(self.client.patch(f"time_entries/{id}/restart"))
        return msgspec.json.decode(response.content, type=TimeEntry)

    def stop_timer(self, id: int) -> TimeEntry:
        response = check(self.client.patch(f"time_entries/{id}/stop"))
        return msgspec.json.decode(response.content, type=TimeEntry)

    def get_user(self) -> User:
        response = check(self.client.get("users/me"))
        return msgspec.json.decode(response.content, type=User)

    def get_user_projects(self) -> list[ProjectAssignment]:
        response = check(self.client.get(f"users/me/project_assignments"))
        return msgspec.json.decode(
            response.content, type=ProjectAssignmentResponse
        ).project_assignments

    def get_time_entries(
        self, params: t.Mapping[str, str] | None = None
    ) -> list[TimeEntry]:
        response = check(
            self.client.get(
                "time_entries",
                params=params,
            )
        )
        return msgspec.json.decode(
            response.content,
            type=TimeEntryResponse,
        ).time_entries
