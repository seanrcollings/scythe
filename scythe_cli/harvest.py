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
        response = await self.client.post("time_entries", json=data)
        return msgspec.json.decode(response.content, type=TimeEntry)

    async def start_timer(self, id: int) -> TimeEntry:
        response = await self.client.patch(f"time_entries/{id}/restart")
        return msgspec.json.decode(response.content, type=TimeEntry)

    async def stop_timer(self, id: int) -> TimeEntry:
        response = await self.client.patch(f"time_entries/{id}/stop")
        return msgspec.json.decode(response.content, type=TimeEntry)

    async def get_user_projects(self) -> list[ProjectAssignment]:
        response = await self.client.get(f"users/me/project_assignments")
        return msgspec.json.decode(
            response.content, type=ProjectAssignmentResponse
        ).project_assignments

    async def get_time_entries(
        self, params: t.Mapping[str, str] | None = None
    ) -> list[TimeEntry]:
        response = await self.client.get(
            "time_entries",
            params=params,
        )
        return msgspec.json.decode(
            response.content,
            type=TimeEntryResponse,
        ).time_entries
