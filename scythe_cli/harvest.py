import functools
import typing as t
import httpx
import msgspec
from scythe_cli import constants

from scythe_cli.stack import TimerStack


class TimeEntryProject(msgspec.Struct):
    id: int
    name: str


class TimeEntryTask(msgspec.Struct):
    id: int
    name: str


class TimeEntry(msgspec.Struct):
    id: int
    notes: str | None
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
    if not response.is_success:
        raise HarvestError(
            f"Request failed with status code {response.status_code}",
            response,
        )

    return response


def arefresh(func: t.Callable[..., t.Awaitable[t.Any]]):
    @functools.wraps(func)
    async def inner(inst: "AsyncHarvest", *args, **kwargs):
        try:
            return await func(inst, *args, **kwargs)
        except HarvestError as e:
            if e.response.status_code == 401:
                await inst._refresh()
                return await func(inst, *args, **kwargs)
            else:
                raise e

    return inner


class AsyncHarvest:
    def __init__(self, access_token: str, refresh_token: str):
        self.client = httpx.AsyncClient(
            base_url=f"https://api.harvestapp.com/api/v2/",
            headers={
                "User-Agent": "Scythe CLI (seanrcollings@gmail.com)",
            },
        )

        self.access_token = access_token
        self.refresh_token = refresh_token
        self.timer_stack = TimerStack(constants.STACK_DATA)

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.__aexit__(exc_type, exc_value, traceback)

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, value: str):
        self._access_token = value
        self.client.headers["Authorization"] = f"Bearer {value}"

    def on_refresh(self, func: t.Callable[[str, str], None]):
        self._on_refresh = func

    async def close(self):
        await self.client.aclose()
        self.timer_stack.save()

    @arefresh
    async def create_timer(self, data: t.Mapping[str, t.Any]) -> TimeEntry:
        response = check(await self.client.post("time_entries", json=data))
        entry = msgspec.json.decode(response.content, type=TimeEntry)
        self.timer_stack.push(
            {
                "id": entry.id,
                "project": entry.project.name,
                "task": entry.task.name,
                "notes": entry.notes,
                "time": entry.seconds(),
            }
        )
        return entry

    @arefresh
    async def update_timer(self, id: int, data: t.Mapping[str, t.Any]) -> TimeEntry:
        response = check(await self.client.patch(f"time_entries/{id}", json=data))
        return msgspec.json.decode(response.content, type=TimeEntry)

    @arefresh
    async def delete_timer(self, id: int) -> None:
        check(await self.client.delete(f"time_entries/{id}"))

        for idx, timer in enumerate(self.timer_stack):
            if timer["id"] == id:
                self.timer_stack.pop(idx)
                break

    @arefresh
    async def start_timer(self, id: int) -> TimeEntry:
        response = check(await self.client.patch(f"time_entries/{id}/restart"))
        entry = msgspec.json.decode(response.content, type=TimeEntry)
        self.timer_stack.push(
            {
                "id": entry.id,
                "project": entry.project.name,
                "task": entry.task.name,
                "notes": entry.notes,
                "time": entry.seconds(),
            }
        )
        return entry

    @arefresh
    async def stop_timer(self, id: int) -> TimeEntry:
        response = check(await self.client.patch(f"time_entries/{id}/stop"))
        entry = msgspec.json.decode(response.content, type=TimeEntry)
        return entry

    @arefresh
    async def get_user_projects(self) -> list[ProjectAssignment]:
        response = check(await self.client.get(f"users/me/project_assignments"))
        return msgspec.json.decode(
            response.content, type=ProjectAssignmentResponse
        ).project_assignments

    @arefresh
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

    @arefresh
    async def get_user(self) -> User:
        response = check(await self.client.get("users/me"))
        return msgspec.json.decode(response.content, type=User)

    async def _refresh(self):
        response = check(
            await self.client.post(
                "https://scythe.seancollings.dev/refresh",
                json={
                    "refresh_token": self.refresh_token,
                },
            )
        )

        if not response.is_success:
            raise HarvestError(
                f"Faield to refresh token",
                response,
            )

        data = response.json()
        self.access_token = data["access_token"]

        if hasattr(self, "_on_refresh"):
            self._on_refresh(self.access_token, self.refresh_token)


T = t.TypeVar("T", bound=t.Callable[..., t.Any])


def refresh(func: T) -> T:
    @functools.wraps(func)
    def inner(inst: "Harvest", *args, **kwargs):
        try:
            return func(inst, *args, **kwargs)
        except HarvestError as e:
            if e.response.status_code == 401:
                inst._refresh()
                breakpoint()
                return func(inst, *args, **kwargs)
            else:
                raise e

    return inner  # type: ignore


class Harvest:
    def __init__(self, access_token: str, refresh_token: str):
        self.client = httpx.Client(
            base_url=f"https://api.harvestapp.com/api/v2/",
            headers={
                "User-Agent": "Scythe CLI (seanrcollings@gmail.com)",
            },
        )

        self.access_token = access_token
        self.refresh_token = refresh_token

    def __enter__(self):
        self.client.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.__exit__(exc_type, exc_value, traceback)

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, value: str):
        self._access_token = value
        self.client.headers["Authorization"] = f"Bearer {value}"

    def on_refresh(self, func: t.Callable[[str, str], None]):
        self._on_refresh = func

    def close(self):
        self.client.close()

    @refresh
    def create_timer(self, data: t.Mapping[str, t.Any]) -> TimeEntry:
        response = check(self.client.post("time_entries", json=data))
        return msgspec.json.decode(response.content, type=TimeEntry)

    @refresh
    def start_timer(self, id: int) -> TimeEntry:
        response = check(self.client.patch(f"time_entries/{id}/restart"))
        return msgspec.json.decode(response.content, type=TimeEntry)

    @refresh
    def stop_timer(self, id: int) -> TimeEntry:
        response = check(self.client.patch(f"time_entries/{id}/stop"))
        return msgspec.json.decode(response.content, type=TimeEntry)

    @refresh
    def get_user(self) -> User:
        response = check(self.client.get("users/me"))
        return msgspec.json.decode(response.content, type=User)

    @refresh
    def get_user_projects(self) -> list[ProjectAssignment]:
        response = check(self.client.get(f"users/me/project_assignments"))
        return msgspec.json.decode(
            response.content, type=ProjectAssignmentResponse
        ).project_assignments

    @refresh
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

    @refresh
    def get_running_time_entry(self) -> t.Optional[TimeEntry]:
        response = check(
            self.client.get(
                "time_entries",
                params={
                    "is_running": "true",
                },
            )
        )

        entries = msgspec.json.decode(
            response.content,
            type=TimeEntryResponse,
        ).time_entries

        if len(entries) == 0:
            return None

        return entries[0]

    def _refresh(self):
        response = check(
            self.client.post(
                "https://scythe.seancollings.dev/refresh",
                json={
                    "refresh_token": self.refresh_token,
                },
            )
        )

        if not response.is_success:
            raise HarvestError(
                f"Faield to refresh token",
                response,
            )

        data = response.json()
        self.access_token = data["access_token"]

        if hasattr(self, "_on_refresh"):
            self._on_refresh(self.access_token, self.refresh_token)
